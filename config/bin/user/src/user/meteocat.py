import os
import json
import logging
import tempfile
import time
from datetime import datetime
import urllib.request
import urllib.error
import threading
import weewx
from weewx.engine import StdService
import weewx.cheetah

log = logging.getLogger(__name__)

DEFAULT_CACHE_FILE = "/var/lib/weewx/meteocat_cache.json"

class MeteocatService(StdService):
    def __init__(self, engine, config_dict):
        super(MeteocatService, self).__init__(engine, config_dict)
        
        # Carregar configuració de [Meteocat] a weewx.conf
        self.options = config_dict.get('Meteocat', {})
        self.api_key = self.options.get('api_key', '')
        self.city_code = self.options.get('city_code', '')
        self.refresh_interval = int(self.options.get('refresh_interval', 10800)) # 3h per defecte
        self.retry_interval = int(self.options.get('retry_interval', 300))
        self.cache_file = self.options.get('cache_file', DEFAULT_CACHE_FILE)
        self._fetch_lock = threading.Lock()
        
        self.bind(weewx.NEW_ARCHIVE_RECORD, self.on_archive_record)
        self.last_fetch = 0
        log.info("[Meteocat] Servei inicialitzat correctament.")

        # Executar la descàrrega inicial immediatament en arrencar
        self._trigger_fetch()

    def _trigger_fetch(self):
        if not self._fetch_lock.acquire(blocking=False):
            return
        self.last_fetch = time.time()
        log.info("[Meteocat] Sol·licitant actualització de dades en segon pla...")
        thread = threading.Thread(target=self._fetch_and_cache)
        thread.daemon = True
        thread.start()

    def on_archive_record(self, event):
        now = time.time()
        interval = self.refresh_interval if os.path.exists(self.cache_file) else self.retry_interval
        if now - self.last_fetch > interval:
            self._trigger_fetch()

    def on_archive_record(self, event):
        now = time.time()
        if (now - self.last_fetch > self.refresh_interval) or not os.path.exists(self.cache_file):
            self.last_fetch = now
            log.info("[Meteocat] Sol·licitant actualització de dades en segon pla...")
            thread = threading.Thread(target=self._fetch_and_cache)
            thread.daemon = True
            thread.start()

    def _fetch_and_cache(self):
        if not self.api_key or not self.city_code:
            log.error("[Meteocat] Falta configurar api_key o city_code a weewx.conf")
            return

        url = f"https://api.meteo.cat/pronostic/v1/municipal/{self.city_code}"
        req = urllib.request.Request(url, headers={"X-Api-Key": self.api_key})
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    raw_data = json.loads(response.read().decode('utf-8'))
                    processed_data = self._process_meteocat(raw_data)
                    
                    cache_dir = os.path.dirname(self.cache_file) or "."
                    os.makedirs(cache_dir, exist_ok=True)
                    with tempfile.NamedTemporaryFile(
                            mode='w', encoding='utf-8', dir=cache_dir,
                            prefix='.meteocat-', suffix='.tmp', delete=False) as f:
                        json.dump(processed_data, f, ensure_ascii=False)
                        temporary_file = f.name
                    os.replace(temporary_file, self.cache_file)
                    log.info("[Meteocat] Cache actualitzada amb èxit al disc.")
        except Exception as e:
            log.error(f"[Meteocat] Error al consultar l'API de Meteocat: {e}")
        finally:
            self._fetch_lock.release()

    def _process_meteocat(self, raw):
        # Mapeig i simplificació del JSON de Meteocat
        days_forecast = []
        today = time.strftime("%Y-%m-%d")
        for dies in raw.get('dies', []):
            sky_code = dies.get('variables', {}).get('estatCels', {}).get('valors', [{}])[0].get('codi', '1')
            date = str(dies.get('data', '')).rstrip('Z')
            try:
                parsed_date = datetime.strptime(date, "%Y-%m-%d")
                date_label = parsed_date.strftime("%d/%m")
                day_name = "AVUI" if date == today else self._day_name(parsed_date.weekday())
            except ValueError:
                date_label = date
                day_name = ""
            
            days_forecast.append({
                "date": date_label,
                "day_name": day_name,
                "sky_code": str(sky_code),
                "icon_class": self._map_sky_to_icon(sky_code),
                "description": self._map_sky_to_description(sky_code),
                "max_temp": dies.get('variables', {}).get('tmax', {}).get('valor'),
                "min_temp": dies.get('variables', {}).get('tmin', {}).get('valor'),
                "rain_percent": dies.get('variables', {}).get('precipitacio', {}).get('valor', 0)
            })

        return {
            "updatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
            "forecast": days_forecast
        }

    def _day_name(self, weekday):
        return ("DILLUNS", "DIMARTS", "DIMECRES", "DIJOUS", "DIVENDRES", "DISSABTE", "DIUMENGE")[weekday]

    def _map_sky_to_description(self, code):
        mapping = {
            "1": "Cel serè",
            "2": "Poc ennuvolat",
            "3": "Parcialment ennuvolat",
            "4": "Ennuvolat",
            "5": "Pluja",
            "6": "Pluja i aiguaneu",
            "7": "Neu",
            "8": "Tempesta",
            "9": "Boira",
        }
        return mapping.get(str(code), "Condicions variables")

    def _map_sky_to_icon(self, code):
        mapping = {
            "1": "clear-day.svg",
            "2": "cloudy-1-day.svg",
            "3": "cloudy-2-day.svg",
            "4": "cloudy.svg",
            "5": "rainy-1-day.svg",
            "6": "rain-and-sleet-mix.svg",
            "7": "snowy-1-day.svg",
            "8": "thunderstorms.svg",
            "9": "fog.svg",
        }
        return mapping.get(str(code), "cloudy.svg")


class MeteocatSearchList(weewx.cheetah.SearchList):
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
            except Exception as e:
                log.error(f"[Meteocat] Error llegint cache local: {e}")
                
        return [{'meteocat': data}]