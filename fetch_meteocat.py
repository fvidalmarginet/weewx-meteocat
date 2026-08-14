#!/usr/bin/env python3
"""
fetch_meteocat.py
Script per descarregar la predicció meteorològica diària de l'API de Meteocat
i generar el fitxer forecast.json per al giny web de WeeWX.

Aquest script està dissenyat per ser executat de forma periòdica (p. ex., via cron a les 09:00).
No té dependències externes (només llibreries estàndard de Python) per ser ultra ràpid.
"""

import os
import json
import argparse
from datetime import datetime, timedelta
import urllib.request
import urllib.error

# Configurar traduccions al català per evitar problemes de localització (locale) a l'OS
DIES_SETMANA = ["Dilluns", "Dimarts", "Dimecres", "Dijous", "Divendres", "Dissabte", "Diumenge"]
MESOS = [
    "de gener", "de febrer", "de març", "d'abril", "de maig", "de juny",
    "de juliol", "d'agost", "de setembre", "d'octubre", "de novembre", "de desembre"
]

# Mapa de símbols de Meteocat a icones de Weather Icons i descripcions
# Basat en els codis oficials d'estat del cel de Meteocat
SIMBOLS_METEOCAT = {
    "1": {"icon": "wi-day-sunny", "desc": "Assolellat"},
    "2": {"icon": "wi-day-cloudy", "desc": "Sol i núvols"},
    "3": {"icon": "wi-cloudy", "desc": "Interval de núvols"},
    "4": {"icon": "wi-cloudy", "desc": "Ennuvolat"},
    "5": {"icon": "wi-day-cloudy-high", "desc": "Núvols alts"},
    "6": {"icon": "wi-cloudy", "desc": "Cobert"},
    "10": {"icon": "wi-day-showers", "desc": "Ruixats"},
    "11": {"icon": "wi-rain", "desc": "Pluja"},
    "12": {"icon": "wi-rain-mix", "desc": "Aigua-neu"},
    "13": {"icon": "wi-snow", "desc": "Neu"},
    "14": {"icon": "wi-day-thunderstorm", "desc": "Furtuna de dia"},
    "15": {"icon": "wi-thunderstorm", "desc": "Furtuna"},
    "16": {"icon": "wi-hail", "desc": "Calabruix"},
    "20": {"icon": "wi-fog", "desc": "Boira"},
    "21": {"icon": "wi-day-fog", "desc": "Boirina"},
}

def format_catalan_date(dt, include_weekday=False):
    """Retorna una data formatada en català: '9 d'agost' o 'Diumenge, 9 d'agost'"""
    day = dt.day
    month_name = MESOS[dt.month - 1]
    
    # Ajustar la preposició 'de' o 'd'' segons com comenci el mes
    # d'abril, d'agost, d'octubre
    if month_name.startswith("de a") or month_name.startswith("de o"):
        month_name = "d'" + month_name[3:]
        
    date_str = f"{day} {month_name}"
    
    if include_weekday:
        weekday_name = DIES_SETMANA[dt.weekday()]
        return f"{weekday_name}, {date_str}"
    
    return date_str

def get_mock_data(municipi_nom):
    """Retorna dades de prova simulades de l'API de Meteocat"""
    print("S'estan utilitzant dades simulades (Mock Mode)")
    avui = datetime.now()
    
    # Si no es proporciona nom, usar un nom per defecte
    if not municipi_nom:
        municipi_nom = f"Municipi {avui.strftime('%Y')}"
    
    mock_response = {
        "location": municipi_nom,
        "updatedAt": f"Actualitzat avui a les {avui.strftime('%H:%M')}",
        "forecast": []
    }
    
    # Simulem 8 dies de predicció
    codis_simulats = ["1", "2", "3", "10", "2", "1", "1", "2"]
    maxs_simulades = [31, 30, 29, 28, 29, 31, 32, 30]
    mins_simulades = [22, 22, 21, 21, 20, 21, 22, 22]
    pluies_simulades = [5, 10, 20, 45, 20, 5, 5, 10]
    
    for i in range(8):
        dia_dt = datetime.fromordinal(avui.toordinal() + i)
        
        # El primer dia és "AVUI", els altres tenen el nom del dia en majúscules
        if i == 0:
            day_name = "AVUI"
            date_str = format_catalan_date(dia_dt, include_weekday=True)
        else:
            day_name = DIES_SETMANA[dia_dt.weekday()].upper()
            date_str = format_catalan_date(dia_dt, include_weekday=False)
            
        simbol_code = codis_simulats[i]
        simbol_info = SIMBOLS_METEOCAT.get(simbol_code, {"icon": "wi-day-sunny", "desc": "Assolellat"})
        
        mock_response["forecast"].append({
            "dayName": day_name,
            "date": date_str,
            "iconClass": simbol_info["icon"],
            "maxTemp": maxs_simulades[i],
            "minTemp": mins_simulades[i],
            "description": simbol_info["desc"],
            "rainPercent": pluies_simulades[i]
        })
        
    return mock_response

def fetch_from_api(api_key, codi_municipi):
    """Realitza la crida real a l'API de Meteocat"""
    # URL de l'API de Meteocat per a la predicció municipal a 8 dies
    # Endpoint: https://api.meteo.cat/pronostic/v1/municipal/{codi}
    url = f"https://api.meteo.cat/pronostic/v1/municipal/{codi_municipi}"
    
    req = urllib.request.Request(url)
    req.add_header("x-api-key", api_key)
    req.add_header("Accept", "application/json")
    
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status == 200:
                return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"Error HTTP de l'API de Meteocat: {e.code} - {e.reason}")
        raise e
    except Exception as e:
        print(f"Error de connexió: {e}")
        raise e

def parse_meteocat_response(api_data, municipi_nom=None):
    """Processa la resposta de Meteocat i la converteix al format forecast.json"""
    # L'API de Meteocat retorna les dades estructurades per dies
    # Resposta estàndard: codiMunicipi + dies[]
    
    codi_municipi = api_data.get("codiMunicipi", "")
    # Si no es proporciona nom, usar el codi del municipi
    if not municipi_nom:
        municipi_nom = f"Municipi {codi_municipi}"
    
    updated_at_str = f"Actualitzat avui a les {datetime.now().strftime('%H:%M')}"
    forecast_list = []
    dies = api_data.get("dies", [])
    
    avui = datetime.now()
    
    for idx, dia_data in enumerate(dies[:8]):
        # Parsejar data, p.ex. "2017-04-18Z"
        data_raw = dia_data.get("data", "")
        if data_raw:
            try:
                # Retallem la "Z" si hi és
                date_clean = data_raw.split("Z")[0]
                dia_dt = datetime.strptime(date_clean, "%Y-%m-%d")
            except Exception:
                dia_dt = datetime.fromordinal(avui.toordinal() + idx)
        else:
            dia_dt = datetime.fromordinal(avui.toordinal() + idx)

        # La data real del sistema és la que determina si el dia és AVUI/DEMÀ/nom del dia.
        # L'API pot retornar encara el darrer dia de la predicció fins a la propera actualització.
        dia_reial = dia_dt.date()
        avui_date = avui.date()

        if dia_reial == avui_date:
            day_name = "AVUI"
            date_str = format_catalan_date(dia_dt, include_weekday=True)
        elif dia_reial == avui_date + timedelta(days=1):
            day_name = "DEMÀ"
            date_str = format_catalan_date(dia_dt, include_weekday=False)
        else:
            day_name = DIES_SETMANA[dia_dt.weekday()].upper()
            date_str = format_catalan_date(dia_dt, include_weekday=False)
            
        # Extraure variables (estatCel, temperatures, precipitació)
        variables = dia_data.get("variables", {})
        
        # 1. Estat del cel (símbol d'icona)
        estat_cel = variables.get("estatCel", {})
        simbol_code = str(estat_cel.get("valor", "1"))
        simbol_info = SIMBOLS_METEOCAT.get(simbol_code, {"icon": "wi-day-sunny", "desc": "Assolellat"})
        
        # 2. Temperatures màxima i mínima
        tmax = variables.get("tmax", {})
        tmin = variables.get("tmin", {})
        
        tmax_val = tmax.get("valor", 20) if isinstance(tmax, dict) else 20
        tmin_val = tmin.get("valor", 10) if isinstance(tmin, dict) else 10
        
        try:
            max_temp = int(round(float(tmax_val)))
            min_temp = int(round(float(tmin_val)))
        except (ValueError, TypeError):
            max_temp = 20
            min_temp = 10
        
        # 3. Probabilitat de pluja (en format %)
        precipitacio = variables.get("precipitacio", {})
        precip_val = precipitacio.get("valor", 0) if isinstance(precipitacio, dict) else 0
        
        try:
            rain_percent = int(round(float(precip_val)))
        except (ValueError, TypeError):
            rain_percent = 0
        
        forecast_list.append({
            "dayName": day_name,
            "date": date_str,
            "iconClass": simbol_info["icon"],
            "maxTemp": max_temp,
            "minTemp": min_temp,
            "description": simbol_info["desc"],
            "rainPercent": rain_percent
        })
        
    return {
        "location": municipi_nom,
        "updatedAt": updated_at_str,
        "forecast": forecast_list
    }

def main():
    parser = argparse.ArgumentParser(description="Descarrega predicció de Meteocat.")
    parser.add_argument("--key", "-k", help="Meteocat API Key (o utilitza la variable d'entorn METEOCAT_API_KEY)")
    parser.add_argument("--municipi", "-m", default="080193", help="Codi de municipi INE (per defecte Barcelona: 080193)")
    parser.add_argument("--nom", "-n", default="", help="Nom personalitzat de la ubicació (si no es proporciona, es mostrarà 'Municipi XXXX')")
    parser.add_argument("--output", "-o", default="prototype/forecast.json", help="Ruta d'escriptura del fitxer de sortida")
    parser.add_argument("--mock", action="store_true", help="Força l'ús de dades de prova simulades")
    
    args = parser.parse_args()
    
    api_key = args.key or os.environ.get("METEOCAT_API_KEY")
    
    # Decidir si fem crida real o mode mock
    if args.mock or not api_key:
        if not api_key and not args.mock:
            print("Avís: No s'ha definit cap API Key de Meteocat.")
        output_data = get_mock_data(args.nom)
    else:
        try:
            print(f"Descarregant predicció per al municipi {args.municipi}...")
            raw_data = fetch_from_api(api_key, args.municipi)
            output_data = parse_meteocat_response(raw_data, args.nom)
        except Exception as e:
            print(f"Error en obtenir les dades reals de l'API: {e}")
            print("Es generaran dades simulades de contingència.")
            output_data = get_mock_data(args.nom)
            
    # Assegurar que el directori de sortida existeix
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    # Guardar el fitxer forecast.json
    try:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        print(f"S'ha generat correctament el fitxer: {args.output}")
    except Exception as e:
        print(f"Error en escriure el fitxer de sortida: {e}")

if __name__ == "__main__":
    main()