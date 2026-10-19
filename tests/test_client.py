import importlib.util
import io
import json
import os
import tempfile
import unittest
import uuid
from email.message import Message
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

spec = importlib.util.spec_from_file_location("forma_client", Path(__file__).parents[1] / "client.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
FormaClient, FormaError = module.FormaClient, module.FormaError
OPTIONS = {"modelId": "seedream-v4-t2i", "kind": "image", "workflow": "text-to-image", "prompt": "A villa", "inputs": {"seed": 42}}


class MemoryClient(FormaClient):
    def __init__(self):
        self.jobs, self.calls = {}, []
        self.account = "account-a"
        self.status = "COMPLETED"
        self.lose_response = False

    def request(self, path, body=None):
        self.calls.append((path, body))
        if path == "/wallet":
            return {"accountId": self.account}
        if path.startswith("/requests/"):
            if path[10:] not in self.jobs:
                raise FormaError("not found", 404)
            return {"job": self.jobs[path[10:]]}
        if path == "/quotes":
            self.pending = body["requestId"]
            return {"quote": {"id": "quote", "cents": 5}}
        if path == "/jobs":
            job = {"id": str(uuid.uuid4()), "status": self.status}
            self.jobs[self.pending] = job
            if self.lose_response:
                self.lose_response = False
                raise FormaError("lost response")
            return {"job": job}
        if path.startswith("/jobs/"):
            return {"job": {"id": path[6:], "status": "COMPLETED"}}
        raise AssertionError(path)


class ClientTests(unittest.TestCase):
    def test_recovery_survives_lost_submission_response_and_budget_change(self):
        client = MemoryClient()
        client.lose_response = True
        with self.assertRaises(FormaError):
            client.generate(OPTIONS, 1, "1", 10)
        # Simulate a fresh process: no local journal or key participates in identity.
        recovered = MemoryClient()
        recovered.jobs = client.jobs
        job = recovered.generate(OPTIONS, 1, "1", 20)
        self.assertIn(job, client.jobs.values())
        self.assertFalse(any(path == "/jobs" for path, _ in recovered.calls))
        recovered.generate(OPTIONS, 2, "1", 20)
        self.assertEqual(len(recovered.jobs), 2)
        recovered.account = "account-b"
        recovered.generate(OPTIONS, 1, "1", 20)
        self.assertEqual(len(recovered.jobs), 3)

    def test_price_cap_prevents_submission(self):
        client = MemoryClient()
        with self.assertRaisesRegex(FormaError, "No generation was submitted"):
            client.generate(OPTIONS, 1, "1", 4)
        self.assertFalse(client.jobs)

    def test_unknown_and_failed_jobs_are_not_resubmitted(self):
        for state in ("UNKNOWN", "FAILED"):
            client = MemoryClient()
            client.status = state
            for _ in range(2):
                with self.assertRaisesRegex(FormaError, state):
                    client.generate(OPTIONS, 1, "1", 10)
            self.assertEqual(sum(path == "/jobs" for path, _ in client.calls), 1)

    def test_polling_and_interrupt_do_not_submit_twice(self):
        client = MemoryClient()
        client.status = "IN_QUEUE"
        with patch.object(module.time, "sleep"):
            self.assertEqual(client.generate(OPTIONS, 1, "1", 10)["status"], "COMPLETED")
        self.assertEqual(sum(path == "/jobs" for path, _ in client.calls), 1)
        def interrupt():
            raise RuntimeError("interrupted")
        with self.assertRaisesRegex(RuntimeError, "interrupted"):
            client.generate(OPTIONS, 2, "1", 10, interrupt=interrupt)
        self.assertEqual(len(client.jobs), 1)

    def test_configuration_requires_key_and_rejects_insecure_remote_url(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(FormaError, "Create a key"):
                FormaClient()
        with patch.dict(os.environ, {"FORMA_API_KEY": "secret", "FORMA_API_URL": "http://remote.example/api/v1"}, clear=True):
            with self.assertRaisesRegex(FormaError, "HTTPS"):
                FormaClient()
        with tempfile.TemporaryDirectory() as directory:
            key = Path(directory) / "secret.key"
            key.write_text("forma_test\n")
            with patch.dict(os.environ, {"FORMA_API_KEY_FILE": str(key)}, clear=True):
                self.assertEqual(FormaClient().key, "forma_test")

    def test_download_does_not_forward_key_to_signed_storage(self):
        with patch.dict(os.environ, {"FORMA_API_KEY": "private-test-key"}, clear=True):
            client = FormaClient()
        requests = []
        headers = Message()
        headers["Location"] = "https://storage.example/media?signature=private"
        media_headers = Message()
        media_headers["Content-Type"] = "video/mp4"
        response = io.BytesIO(b"test-video")
        response.headers = media_headers
        def open_request(req, timeout):
            requests.append(req)
            if len(requests) == 1:
                raise HTTPError(req.full_url, 302, "redirect", headers, None)
            return response
        with tempfile.TemporaryDirectory() as directory, patch.object(client.opener, "open", side_effect=open_request):
            output = client.download(str(uuid.uuid4()), directory, "video")
            self.assertEqual(output.read_bytes(), b"test-video")
        self.assertEqual(requests[0].get_header("Authorization"), "Bearer private-test-key")
        self.assertIsNone(requests[1].get_header("Authorization"))
        for request in requests:
            self.assertEqual(request.get_header("User-agent"), module.USER_AGENT)

    def test_upload_retries_keep_identity_and_bound_content(self):
        client = FormaClient(api_key="private-test-key")
        asset_id = str(uuid.uuid4())
        requests = []
        def open_request(request, timeout):
            requests.append(request)
            return io.BytesIO(json.dumps({"job": {"id": asset_id}}).encode())
        with patch.object(client.opener, "open", side_effect=open_request):
            for data, run in [(b"image-one", 1), (b"image-one", 1), (b"image-two", 1), (b"image-one", 2)]:
                self.assertEqual(client.upload(data, "image/png", run), "asset:" + asset_id)
        ids = [request.get_header("X-upload-id") for request in requests]
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(len(set(ids)), 3)
        self.assertEqual(requests[0].data, b"image-one")
        self.assertEqual(requests[0].get_header("Content-type"), "image/png")
        for data in (b"", b"x" * (128 * 1024 * 1024 + 1)):
            with self.assertRaises(FormaError):
                client.upload(data, "image/png", 1)

    def test_api_requests_identify_the_client(self):
        client = FormaClient(api_key="private-test-key")
        for body in (None, {"modelId": "example"}):
            response = io.BytesIO(b'{"ok":true}')
            with patch.object(client.opener, "open", return_value=response) as opened:
                self.assertEqual(client.request("/wallet" if body is None else "/quotes", body), {"ok": True})
                request = opened.call_args.args[0]
                self.assertEqual(request.get_header("User-agent"), module.USER_AGENT)
                self.assertEqual(request.get_header("Authorization"), "Bearer private-test-key")

    def test_proxy_errors_never_echo_secrets(self):
        with patch.dict(os.environ, {"FORMA_API_KEY": "private-test-key"}, clear=True):
            client = FormaClient()
        for error in (URLError("private-test-key"), HTTPError(client.base, 500, "private-test-key", {}, io.BytesIO(b'private-test-key'))):
            with patch.object(client.opener, "open", side_effect=error):
                with self.assertRaises(FormaError) as raised:
                    client.request("/wallet")
                self.assertNotIn("private-test-key", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
