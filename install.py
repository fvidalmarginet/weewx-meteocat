from weecfg.extension import ExtensionInstaller

def loader():
    return MeteocatInstaller()

class MeteocatInstaller(ExtensionInstaller):
    def __init__(self):
        super(MeteocatInstaller, self).__init__(
            version="1.0.0",
            name="weewx-meteocat",
            description="Integracio de la prediccio municipal de Meteocat per a skins de WeeWX.",
            author="Vidal Marginet",
            config={
                "Meteocat": {
                    "api_key": "EL_TEU_API_KEY",
                    "city_code": "080193",
                    "refresh_interval": "10800",
                    "retry_interval": "300",
                    "cache_file": "/var/lib/weewx/meteocat_cache.json"
                },
                "Engine": {
                    "Services": {
                        "prep_services": "user.meteocat.MeteocatService"
                    }
                },
                "Cheetah": {
                    "search_list_extensions": "user.meteocat.MeteocatSearchList"
                }
            },
            files=[
                ('bin/user', ['src/user/meteocat.py']),
                ('examples', ['examples/meteocat.inc']),
                ('skins/Seasons/weather-icons', [
                    'assets/weather-icons/*.svg',
                    'assets/weather-icons/LICENSE'
                ]),
                ('skins/Seasons', ['config/skins/Seasons/meteocat.css'])
            ]
        )