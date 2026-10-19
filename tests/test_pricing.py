import importlib
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

package = types.ModuleType('forma_price_test')
package.__path__ = [str(Path(__file__).parents[1])]
sys.modules[package.__name__] = package
pricing = importlib.import_module(package.__name__ + '.pricing')


class PriceRouteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        routes = web.RouteTableDef()
        pricing.install_price_routes(routes)
        app = web.Application()
        app.add_routes(routes)
        self.http = TestClient(TestServer(app))
        await self.http.start_server()
        self.headers = {'Origin': str(self.http.make_url('/')).rstrip('/'), 'X-Forma-Settings': '1'}
        self.quote = patch.object(pricing, 'check_price', return_value={'cents': 25, 'expires': 12345})
        self.check = self.quote.start()

    async def asyncTearDown(self):
        self.quote.stop()
        self.environment.stop()
        await self.http.close()

    async def test_same_origin_quote_response_has_no_credentials_or_quote_id(self):
        body = {'class_type': 'FormaVideo', 'inputs': {}}
        response = await self.http.post('/forma/price', json=body, headers=self.headers)
        self.assertEqual(response.status, 200)
        self.assertEqual(await response.json(), {'cents': 25, 'expires': 12345})
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.check.assert_called_once_with(body)

    async def test_cross_site_and_missing_header_requests_cannot_quote_or_upload(self):
        for headers in ({}, {'Origin': self.headers['Origin']}, {**self.headers, 'Origin': 'https://evil.example'}):
            response = await self.http.post('/forma/price', json={}, headers=headers)
            self.assertEqual(response.status, 403)
        self.check.assert_not_called()

    async def test_oversized_and_invalid_requests_are_rejected_before_quote(self):
        for body in ('invalid', 'x' * 262145):
            response = await self.http.post('/forma/price', data=body, headers={**self.headers, 'Content-Type': 'application/json'})
            self.assertEqual(response.status, 400)
        self.check.assert_not_called()

    async def test_unexpected_errors_do_not_leak_paths_or_credentials(self):
        self.check.side_effect = OSError('/private/key forma_secret')
        response = await self.http.post('/forma/price', json={}, headers=self.headers)
        self.assertEqual(response.status, 500)
        self.assertNotIn('forma_secret', await response.text())


class PriceInputTests(unittest.TestCase):
    def test_only_existing_input_files_and_no_symlink_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'input'; root.mkdir()
            inside = root / 'image.png'; inside.write_bytes(b'content')
            secret = Path(directory) / 'secret'; secret.write_bytes(b'private')
            (root / 'escape.png').symlink_to(secret)
            folder_paths = types.SimpleNamespace(get_input_directory=lambda: str(root), get_annotated_filepath=lambda name: str(root / name))
            with patch.dict(sys.modules, {'folder_paths': folder_paths}):
                self.assertEqual(pricing.input_path('image.png'), inside.resolve())
                for name in ('../secret', str(secret), 'escape.png', 'missing.png', '', ['node', 0]):
                    with self.subTest(name=name), self.assertRaises(pricing.FormaError):
                        pricing.input_path(name)


if __name__ == '__main__':
    unittest.main()
