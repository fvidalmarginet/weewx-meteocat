import importlib.util
import json
import os
import sys
import tempfile
import threading
import unittest
from unittest import mock

# Mock WeeWX modules before importing the extension
# This allows tests to run without WeeWX installed in the environment
weewx_mock = mock.MagicMock()
weewx_mock.NEW_ARCHIVE_RECORD = 'NEW_ARCHIVE_RECORD'
sys.modules['weewx'] = weewx_mock
sys.modules['weewx.engine'] = mock.MagicMock(StdService=object)
sys.modules['weewx.cheetahgenerator'] = mock.MagicMock(SearchList=object)

MODULE_PATH = os.path.join(os.path.dirname(__file__), '..', 'src', 'user', 'meteocat.py')
spec = importlib.util.spec_from_file_location('meteocat_extension', MODULE_PATH)
meteocat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(meteocat)


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return json.dumps({
            'dies': [{
                'data': '2026-08-19Z',
                'variables': {
                    'estatCel': {'valor': 3},
                    'tmax': {'valor': '30'},
                    'tmin': {'valor': '20'},
                    'precipitacio': {'valor': '25'},
                },
            }],
        }).encode('utf-8')


class MeteocatTests(unittest.TestCase):
    def test_processes_real_meteocat_sky_schema(self):
        service = meteocat.MeteocatService.__new__(meteocat.MeteocatService)
        result = service._process_meteocat({'dies': [{'variables': {
            'estatCel': {'valor': 3},
        }}]})
        self.assertEqual(result['forecast'][0]['sky_code'], '3')
        self.assertEqual(result['forecast'][0]['description'], 'Mostly cloudy')
        self.assertEqual(result['forecast'][0]['icon_class'], 'cloudy-2-day.svg')

    def test_fetch_writes_valid_cache_atomically(self):
        service = meteocat.MeteocatService.__new__(meteocat.MeteocatService)
        service.api_key = 'test-key'
        service.city_code = '080193'
        service.cache_file = os.path.join(tempfile.mkdtemp(), 'meteocat.json')
        service._fetch_lock = threading.Lock()
        service._fetch_lock.acquire()

        with mock.patch.object(meteocat.urllib.request, 'urlopen', return_value=FakeResponse()):
            service._fetch_and_cache()

        with open(service.cache_file, encoding='utf-8') as stream:
            data = json.load(stream)
            self.assertEqual(data['forecast'][0]['icon_class'], 'cloudy-2-day.svg')
            self.assertEqual([
                name for name in os.listdir(os.path.dirname(service.cache_file))
                if name.startswith('.meteocat-')
            ], [])


if __name__ == '__main__':
    unittest.main()