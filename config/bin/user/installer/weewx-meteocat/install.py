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
                    "refresh_interval": "10800"
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
                ('bin/user', ['src/user/meteocat.py'])
            ]
        )