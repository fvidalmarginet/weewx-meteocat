import os
import json
import logging
import tempfile
import time
from datetime import datetime
import urllib.request
import threading
import weewx
from weewx.engine import StdService
import weewx.cheetahgenerator

log = logging.getLogger(__name__)

DEFAULT_CACHE_FILE = "meteocat_cache.json"


class MeteocatService(StdService):
    """Background service that fetches and caches the Meteocat municipal forecast."""

    def __init__(self, engine, config_dict):
        super(MeteocatService, self).__init__(engine, config_dict)

        self.options = config_dict.get('Meteocat', {})
        self.api_key = self.options.get('api_key', '')
        self.city_code = self.options.get('city_code', '')
        self.refresh_interval = int(self.options.get('refresh_interval', 10800))
        self.retry_interval = int(self.options.get('retry_interval', 300))
        self.cache_file = self.options.get('cache_file', DEFAULT_CACHE_FILE)
        self._fetch_lock = threading.Lock()

        self.bind(weewx.NEW_ARCHIVE_RECORD, self.on_archive_record)
        self.last_fetch = 0
        log.info("[Meteocat] Service initialized successfully.")

        self._trigger_fetch()

    def _trigger_fetch(self):
        if not self._fetch_lock.acquire(blocking=False):
            return
        log.info("[Meteocat] Requesting background forecast update...")
        thread = threading.Thread(target=self._fetch_and_cache)
        thread.daemon = True
        thread.start()

    def on_archive_record(self, event):
        now = time.time()
        interval = self.refresh_interval if os.path.exists(self.cache_file) else self.retry_interval
        if now - self.last_fetch > interval:
            self._trigger_fetch()

    def _fetch_and_cache(self):
        try:
            if not self.api_key or not self.city_code or self.api_key == "YOUR_API_KEY":
                log.error("[Meteocat] A valid api_key and city_code must be configured in weewx.conf")
                return

            url = f"https://api.meteo.cat/pronostic/v1/municipal/{self.city_code}"
            req = urllib.request.Request(url, headers={"X-Api-Key": self.api_key})

            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    raw_data = json.loads(response.read().decode('utf-8'))
                    processed_data = self._process_meteocat(raw_data)

                    cache_dir = os.path.dirname(self.cache_file) or "."
                    os.makedirs(cache_dir, exist_ok=True)
                    with tempfile.NamedTemporaryFile(
                            mode='w', encoding='utf-8', dir=cache_dir,
                            prefix='.meteocat-', suffix='.tmp', delete=False) as f:
                        json.dump(processed_data, f, ensure_ascii=False, indent=2)
                        temporary_file = f.name
                    os.replace(temporary_file, self.cache_file)
                    self.last_fetch = time.time()
                    log.info("[Meteocat] Cache updated successfully.")
        except Exception as e:
            log.error(f"[Meteocat] Meteocat API request failed: {e}")
        finally:
            self._fetch_lock.release()

    def _process_meteocat(self, raw):
        days_forecast = []
        today = time.strftime("%Y-%m-%d")
        for day_data in raw.get('dies', []):
            sky_code = self._extract_sky_code(day_data.get('variables', {}))
            date = str(day_data.get('data', '')).rstrip('Z')
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d")
                date_label = parsed_date.strftime("%d/%m")
                day_name = "Today" if date == today else self._day_name(parsed_date.weekday())
            except ValueError:
                date_label = date
                day_name = ""

            max_temp = day_data.get('variables', {}).get('tmax', {}).get('valor')
            min_temp = day_data.get('variables', {}).get('tmin', {}).get('valor')

            days_forecast.append({
                "date": date_label,
                "day_name": day_name,
                "sky_code": str(sky_code),
                "icon_class": self._map_sky_to_icon(sky_code),
                "description": self._map_sky_to_description(sky_code),
                "max_temp": max_temp if max_temp is not None else "N/A",
                "min_temp": min_temp if min_temp is not None else "N/A",
                "rain_percent": day_data.get('variables', {}).get('precipitacio', {}).get('valor', 0)
            })

        return {
            "updatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
            "forecast": days_forecast
        }

    def _extract_sky_code(self, variables):
        sky_state = variables.get('estatCel', {})
        if 'valor' in sky_state:
            return sky_state['valor']
        legacy_values = variables.get('estatCels', {}).get('valors', [{}])
        return legacy_values[0].get('codi', '0')

    def _day_name(self, weekday):
        return ("Monday", "Tuesday", "Wednesday", "Thursday",
                "Friday", "Saturday", "Sunday")[weekday]

    def _map_sky_to_description(self, code):
        mapping = {
            "1": "Clear sky",
            "2": "Partly cloudy",
            "3": "Mostly cloudy",
            "4": "Overcast",
            "5": "Very cloudy",
            "6": "Covered",
            "20": "Rain",
            "21": "Light rain",
            "22": "Moderate rain",
            "23": "Heavy rain",
            "24": "Showers",
            "25": "Thunderstorms",
            "26": "Snow",
            "27": "Sleet",
            "28": "Hail",
            "29": "Fog",
        }
        return mapping.get(str(code), "Variable conditions")

    def _map_sky_to_icon(self, code):
        mapping = {
            "1": "clear-day.svg",
            "2": "cloudy-1-day.svg",
            "3": "cloudy-2-day.svg",
            "4": "cloudy-3-day.svg",
            "5": "cloudy.svg",
            "6": "cloudy.svg",
            "20": "rainy-1-day.svg",
            "21": "rainy-1-day.svg",
            "22": "rainy-2-day.svg",
            "23": "rainy-3-day.svg",
            "24": "rainy-2-day.svg",
            "25": "thunderstorms.svg",
            "26": "snowy-1-day.svg",
            "27": "rain-and-snow-mix.svg",
            "28": "hail.svg",
            "29": "fog.svg",
        }
        return mapping.get(str(code), "cloudy.svg")


class MeteocatSearchList(weewx.cheetahgenerator.SearchList):
    """Exposes the cached Meteocat forecast to Cheetah templates as $meteocat."""

    def __init__(self, generator):
        super(MeteocatSearchList, self).__init__(generator)
        options = getattr(generator, 'config_dict', {}).get('Meteocat', {})
        self.cache_file = options.get('cache_file', DEFAULT_CACHE_FILE)

    def get_extension_list(self, valid_times, span):
        data = {"forecast": [], "updatedAt": "N/A"}
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for day in data.get('forecast', []):
                    day.setdefault('day_name', '')
                    day.setdefault('description', 'Variable conditions')
            except Exception as e:
                log.error(f"[Meteocat] Error reading local cache: {e}")

        return [{'meteocat': data}]