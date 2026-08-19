import glob
import os
from weecfg.extension import ExtensionInstaller


def loader():
    return MeteocatInstaller()


class MeteocatInstaller(ExtensionInstaller):
    def __init__(self):
        # Expand wildcard so every SVG icon is listed explicitly
        icon_dir = os.path.join('assets', 'weather-icons')
        svg_files = glob.glob(os.path.join(icon_dir, '*.svg'))
        svg_files.append(os.path.join(icon_dir, 'LICENSE'))

        super(MeteocatInstaller, self).__init__(
            version="1.0.0",
            name="weewx-meteocat",
            description="Municipal Meteocat forecast integration for WeeWX skins.",
            author="Vidal Marginet",
            config={
                "Meteocat": {
                    "api_key": "YOUR_API_KEY",
                    "city_code": "080193",
                    "refresh_interval": "10800",
                    "retry_interval": "300",
                    "cache_file": "meteocat_cache.json"
                },
                "Engine": {
                    "Services": {
                        "archive_services": "user.meteocat.MeteocatService"
                    }
                },
                "CheetahGenerator": {
                    "search_list_extensions": "user.meteocat.MeteocatSearchList"
                }
            },
            files=[
                ('bin/user', ['src/user/meteocat.py']),
                ('skins/Seasons', ['examples/meteocat.inc']),
                ('skins/Seasons/weather-icons', svg_files),
                ('skins/Seasons', ['config/skins/Seasons/meteocat.css'])
            ]
        )