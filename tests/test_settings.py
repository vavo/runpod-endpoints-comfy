import importlib.util
import os
import stat
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

ROOT = Path(__file__).parents[1]
package = types.ModuleType("forma_settings_test")
package.__path__ = [str(ROOT)]
sys.modules[package.__name__] = package

def load(name):
    spec = importlib.util.spec_from_file_location(package.__name__ + "." + name, ROOT / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

client = load("client")
settings = load("settings")
KEY = "forma_" + "a" * 64

class SettingsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / ".forma" / "api.key"
        self.path_patch = patch.object(client, "saved_key_path", return_value=self.path)
        self.path_patch.start()
        self.env_patch = patch.dict(os.environ, {}, clear=True)
        self.env_patch.start()
        self.wallet = patch.object(client.FormaClient, "request", return_value={"accountId": "test", "availableCents": 0})
        self.request = self.wallet.start()
        routes = web.RouteTableDef()
        settings.install_routes(routes)
        app = web.Application()
        app.add_routes(routes)
        self.http = TestClient(TestServer(app))
        await self.http.start_server()
        self.headers = {"Origin": str(self.http.make_url("/")).rstrip("/"), "X-Forma-Settings": "1"}

    async def asyncTearDown(self):
        await self.http.close()
        self.wallet.stop()
        self.env_patch.stop()
        self.path_patch.stop()
        self.temp.cleanup()

    async def save(self, key=KEY, headers=None):
        return await self.http.post("/forma/settings/key", json={"key": key}, headers=self.headers if headers is None else headers)

    async def test_save_is_private_persistent_and_never_returned(self):
        response = await self.save()
        self.assertEqual(response.status, 200)
        self.assertNotIn(KEY, await response.text())
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.request.assert_called_once_with("/wallet")
        self.assertEqual(self.path.read_text().strip(), KEY)
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.path.parent.stat().st_mode), 0o700)
        self.assertEqual(client.FormaClient().key, KEY)
        response = await self.http.get("/forma/settings/key")
        self.assertEqual(await response.json(), {"configured": True, "managed": False})
        response = await self.http.delete("/forma/settings/key", headers=self.headers)
        self.assertEqual(response.status, 200)
        self.assertFalse(self.path.exists())
        with self.assertRaises(client.FormaError): client.FormaClient()

    async def test_cross_site_missing_origin_and_missing_custom_header_are_denied(self):
        for headers in ({}, {**self.headers, "Origin": "https://evil.example"}, {"Origin": self.headers["Origin"]}):
            response = await self.save(headers=headers)
            self.assertEqual(response.status, 403)
            response = await self.http.delete("/forma/settings/key", headers=headers)
            self.assertEqual(response.status, 403)
        self.request.assert_not_called()
        self.assertFalse(self.path.exists())

    async def test_runpod_proxy_uses_only_the_trusted_pod_and_actual_port(self):
        server = types.SimpleNamespace(PromptServer=types.SimpleNamespace(instance=types.SimpleNamespace(port=5555)))
        with patch.dict(os.environ, {"RUNPOD_POD_ID": "mypod"}), patch.dict(sys.modules, {"server": server}):
            response = await self.save(headers={**self.headers, "Origin": "https://mypod-5555.proxy.runpod.net"})
            self.assertEqual(response.status, 200)
            for origin in ("https://otherpod-5555.proxy.runpod.net", "https://mypod-8888.proxy.runpod.net"):
                response = await self.save(headers={**self.headers, "Origin": origin, "X-Forwarded-Host": origin.split("//")[1]})
                self.assertEqual(response.status, 403)
                self.assertIn("error", await response.json())

    async def test_custom_proxy_requires_explicit_server_configuration(self):
        headers = {**self.headers, "Origin": "https://comfy.example"}
        self.assertEqual((await self.save(headers=headers)).status, 403)
        with patch.dict(os.environ, {"FORMA_COMFY_ORIGIN": "https://comfy.example"}):
            self.assertEqual((await self.save(headers=headers)).status, 200)

    async def test_http_remote_origin_is_denied_even_with_matching_host(self):
        response = await self.save(headers={"Origin": "http://public.example", "Host": "public.example", "X-Forma-Settings": "1"})
        self.assertEqual(response.status, 403)
        self.request.assert_not_called()

    async def test_bad_input_and_large_requests_never_contact_forma(self):
        for key in ("secret", None, "a" * 1024):
            self.assertEqual((await self.save(key)).status, 400)
        response = await self.http.post("/forma/settings/key", data="invalid", headers=self.headers)
        self.assertEqual(response.status, 400)
        self.request.assert_not_called()

    async def test_invalid_key_does_not_replace_existing_credential(self):
        client.save_key(KEY)
        self.request.side_effect = client.FormaError("Forma API key is invalid or revoked.", 401)
        response = await self.save("forma_" + "b" * 64)
        self.assertEqual(response.status, 400)
        self.assertEqual(self.path.read_text().strip(), KEY)

    async def test_environment_takes_precedence_and_cannot_be_changed_from_ui(self):
        client.save_key(KEY)
        with patch.dict(os.environ, {"FORMA_API_KEY": "host-managed"}):
            self.assertEqual(client.FormaClient().key, "host-managed")
            self.assertEqual((await self.save()).status, 409)
            self.assertEqual((await self.http.delete("/forma/settings/key", headers=self.headers)).status, 409)
            self.request.assert_not_called()
        self.assertEqual(self.path.read_text().strip(), KEY)

    async def test_symlinked_storage_directory_is_rejected(self):
        target = Path(self.temp.name) / "target"
        target.mkdir()
        self.path.parent.symlink_to(target, target_is_directory=True)
        response = await self.save()
        self.assertEqual(response.status, 400)
        self.assertFalse((target / "api.key").exists())

if __name__ == "__main__":
    unittest.main()
