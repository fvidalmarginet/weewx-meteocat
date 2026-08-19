# WeeWX Meteocat Extension

A WeeWX extension that retrieves the official municipal forecast from the [Meteocat API](https://api.meteocat.gencat.cat/) and exposes it to WeeWX Cheetah templates.

The extension:

- Fetches the municipal forecast using an API key and municipality code.
- Refreshes the forecast in the background without blocking WeeWX archive processing.
- Stores the latest successful response in a local JSON cache.
- Exposes the forecast as `$meteocat` to Cheetah templates.
- Includes the [Makin-Things/weather-icons](https://github.com/Makin-Things/weather-icons) SVG set under its MIT license.
- Provides a ready-to-use forecast widget for the WeeWX Seasons skin.

## Requirements

- WeeWX 5.x
- Python 3
- A Meteocat API key
- A WeeWX skin based on Cheetah templates

The included widget is designed for the Seasons skin. The service and SearchList can also be used from another skin.

## Installation

Run the following command from the root of the extension repository:

```bash
weectl extension install .
```

If WeeWX is installed in a virtual environment, use the `weectl` executable from that environment. For example:

```bash
/path/to/venv/bin/weectl extension install /path/to/weewx-meteocat
```

The installer copies the service to `bin/user`, installs the example template, and installs the Seasons widget CSS and weather icons.

## Configuration

Open the WeeWX configuration file, normally `weewx.conf`, and edit the `[Meteocat]` section:

```ini
[Meteocat]
    api_key = YOUR_METEOCAT_API_KEY
    city_code = 080193
    refresh_interval = 10800
    retry_interval = 300
    cache_file = /var/lib/weewx/meteocat_cache.json
```

Replace `YOUR_METEOCAT_API_KEY` with the key issued by Meteocat. Set `city_code` to the six-digit Meteocat municipality code for the location you want to display.

Options:

- `api_key`: API key sent in the `X-Api-Key` request header.
- `city_code`: Meteocat municipal forecast code.
- `refresh_interval`: normal refresh interval in seconds. The default is three hours.
- `retry_interval`: retry interval in seconds when no cache exists. The default is five minutes.
- `cache_file`: path to the local JSON cache. The WeeWX user must be able to create and update this file.

Do not commit your real API key to a public repository.

## Skin Integration

The installer includes the Seasons widget, but the Seasons skin must include the widget from its main template. Add this line to `skins/Seasons/index.html.tmpl` if it is not already present:

```cheetah
#include "meteocat.inc"
```

The included widget is installed as:

```text
skins/Seasons/meteocat.inc
skins/Seasons/meteocat.css
skins/Seasons/weather-icons/
```

The Seasons `skin.conf` must register the SearchList and copy the widget assets:

```ini
[CheetahGenerator]
    search_list_extensions = user.meteocat.MeteocatSearchList

[CopyGenerator]
    copy_always = weather-icons/*.svg, weather-icons/LICENSE, meteocat.css
```

A custom skin can use the same `$meteocat` object and include its own markup instead.

## Template Data

The SearchList exposes one object named `meteocat`:

```cheetah
$meteocat.updatedAt
#for $day in $meteocat.forecast
$day.day_name
$day.date
$day.icon_class
$day.description
$day.max_temp
$day.min_temp
$day.rain_percent
#end for
```

`icon_class` contains an SVG filename, such as `clear-day.svg`. The included Seasons widget references it with:

```html
<img src="weather-icons/$day.icon_class" alt="$day.sky_code" width="56" height="48" />
```

## Cache and Updates

The service performs an initial background request when WeeWX starts. It refreshes the cache after `refresh_interval` seconds. If the cache does not exist, failed requests are retried using `retry_interval`.

Cache writes are atomic, so the template generator does not read a partially written JSON file. If the API is unavailable, the last successful forecast remains available.

To regenerate the HTML reports manually using the last record in the WeeWX database:

```bash
cd /path/to/weewx-root
weectl report run SeasonsReport --config=/path/to/weewx.conf
```

Avoid passing a future `--epoch` value when using a simulator or an old database. WeeWX skips templates when that timestamp is not present in the database.

## Troubleshooting

### The widget shows `N/A`

Check that:

1. `api_key` and `city_code` are configured.
2. The cache directory is writable by the WeeWX process.
3. The WeeWX log contains no `[Meteocat]` API errors.
4. The generated report includes `meteocat.inc`.

### The page does not contain the widget

Make sure the active report uses the Seasons skin and that `index.html.tmpl` contains:

```cheetah
#include "meteocat.inc"
```

Then regenerate the report:

```bash
weectl report run SeasonsReport --config=/path/to/weewx.conf
```

### Module path differs in a local installation

A standard extension installation uses:

```ini
user.meteocat.MeteocatService
user.meteocat.MeteocatSearchList
```

If a manually copied installation places the module under `bin/user/src/user`, use:

```ini
user.src.user.meteocat.MeteocatService
user.src.user.meteocat.MeteocatSearchList
```

Use the same module path consistently in the WeeWX service and Cheetah SearchList configuration.

## Development

Create or activate a Python virtual environment containing WeeWX, then run the tests from the repository root:

```bash
python -m unittest discover -s tests -v
python -m py_compile src/user/meteocat.py install.py
```

The extension does not require Docker or another container runtime for local development.

## License

No separate license file is currently included for the extension code. The bundled weather icons are from [Makin-Things/weather-icons](https://github.com/Makin-Things/weather-icons) and are distributed under the MIT license included in `assets/weather-icons/LICENSE`.
