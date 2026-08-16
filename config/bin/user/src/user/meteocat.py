import os
import json
import time
import urllib.request
import urllib.error
import threading
import weewx
from weewx.engine import StdService
import weewx.cheetah

CACHE_FILE = "/var/lib/weewx/meteocat_cache.json"

class MeteocatService(StdService):
    def __init__(self, engine, config_dict):
        super(MeteocatService, self).__init__(engine, config_dict)
        
        # Carregar configuració de [Meteocat] a weewx.conf
        self.options = config_dict.get('Meteocat', {})
        self.api_key = self.options.get('api_key', '')
        self.city_code = self.options.get('city_code', '')
        self.refresh_interval = int(self.options.get('refresh_interval', 10800)) # 3h per defecte
        
        self.bind(weewx.NEW_ARCHIVE_RECORD, self.on_archive_record)
        self.last_fetch = 0
        weewx.log.loginfo("[Meteocat] Servei inicialitzat correctament.")

        # Executar la descàrrega inicial immediatament en arrencar
        self._trigger_fetch()

    def _trigger_fetch(self):
        self.last_fetch = time.time()
        weewx.log.loginfo("[Meteocat] Sol·licitant actualització de dades en segon pla...")
        thread = threading.Thread(target=self._fetch_and_cache)
        thread.daemon = True
        thread.start()

    def on_archive_record(self, event):
        now = time.time()
        if (now - self.last_fetch > self.refresh_interval) or not os.path.exists(CACHE_FILE):
            self._trigger_fetch()

    def on_archive_record(self, event):
        now = time.time()
        if (now - self.last_fetch > self.refresh_interval) or not os.path.exists(CACHE_FILE):
            self.last_fetch = now
            weewx.log.loginfo("[Meteocat] Sol·licitant actualització de dades en segon pla...")
            thread = threading.Thread(target=self._fetch_and_cache)
            thread.daemon = True
            thread.start()

    def _fetch_and_cache(self):
        if not self.api_key or not self.city_code:
            weewx.log.logerr("[Meteocat] Falta configurar api_key o city_code a weewx.conf")
            return

        url = f"https://api.meteo.cat/pronostic/v1/municipal/{self.city_code}"
        req = urllib.request.Request(url, headers={"X-Api-Key": self.api_key})
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    raw_data = json.loads(response.read().decode('utf-8'))
                    processed_data = self._process_meteocat(raw_data)
                    
                    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
                    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                        json.dump(processed_data, f, ensure_ascii=False)
                    weewx.log.loginfo("[Meteocat] Cache actualitzada amb èxit al disc.")
        except Exception as e:
            weewx.log.logerr(f"[Meteocat] Error al consultar l'API de Meteocat: {e}")

    def _process_meteocat(self, raw):
        # Mapeig i simplificació del JSON de Meteocat
        days_forecast = []
        for dies in raw.get('dies', []):
            sky_code = dies.get('variables', {}).get('estatCels', {}).get('valors', [{}])[0].get('codi', '1')
            
            days_forecast.append({
                "date": dies.get('data'),
                "sky_code": str(sky_code),
                "icon_class": self._map_sky_to_icon(sky_code),
                "max_temp": dies.get('variables', {}).get('tmax', {}).get('valor'),
                "min_temp": dies.get('variables', {}).get('tmin', {}).get('valor'),
                "rain_percent": dies.get('variables', {}).get('precipitacio', {}).get('valor', 0)
            })

        return {
            "updatedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
            "forecast": days_forecast
        }

    def _map_sky_to_icon(self, code):
        mapping = {
            "1": "wi-day-sunny",
            "2": "wi-day-cloudy",
            "3": "wi-cloudy",
            "4": "wi-rain",
        }
        return mapping.get(str(code), "wi-na")


class MeteocatSearchList(weewx.cheetah.SearchList):
    def __init__(self, generator):
        super(MeteocatSearchList, self).__init__(generator)

    def get_extension_list(self, valid_times, span):
        data = {"forecast": [], "updatedAt": "N/A"}
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                weewx.log.logerr(f"[Meteocat] Error llegint cache local: {e}")
                
        return [{'meteocat': data}]