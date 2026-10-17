"""Small Forma client. Credentials never enter a ComfyUI graph or its metadata."""
import json
import os
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class FormaError(RuntimeError):
    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class FormaClient:
    def __init__(self):
        self.base = os.environ.get("FORMA_API_URL", "https://forma.cam/api/v1").rstrip("/")
        url = urlsplit(self.base)
        if (url.scheme != "https" and not (url.scheme == "http" and url.hostname in ("localhost", "127.0.0.1"))) or url.username or url.password or url.query or url.fragment:
            raise FormaError("FORMA_API_URL must use HTTPS (HTTP is allowed only on localhost).")
        self.key = os.environ.get("FORMA_API_KEY", "").strip()
        if not self.key and os.environ.get("FORMA_API_KEY_FILE"):
            self.key = Path(os.environ["FORMA_API_KEY_FILE"]).read_text().strip()
        if not self.key:
            raise FormaError("Create a key in Forma Account settings and set FORMA_API_KEY or FORMA_API_KEY_FILE before starting ComfyUI.")
        self.opener = build_opener(NoRedirect())

    def request(self, path, body=None):
        request = Request(self.base + path, headers={
            "Authorization": "Bearer " + self.key,
            "Content-Type": "application/json",
        }, data=json.dumps(body).encode() if body is not None else None)
        try:
            with self.opener.open(request, timeout=60) as response:
                return json.load(response)
        except HTTPError as error:
            error.close()
            # Never echo a response body: a proxy could reflect credentials or signed URLs.
            messages = {
                401: "Forma API key is invalid or revoked.",
                402: "Insufficient Forma balance. Add funds at forma.cam.",
                403: "This operation is not allowed by the Forma API.",
                404: "Forma job or API route not found.",
                409: "Forma rejected the quote, spending limit, or account state. Check your account and retry the same run number.",
                422: "Forma could not price or use these inputs.",
                429: "Forma is busy or rate limited. Retry the same run number shortly.",
            }
            raise FormaError(messages.get(error.code, "Forma could not complete the request. Retry the same run number to recover the job."), error.code) from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise FormaError("Lost contact with Forma. Retry the same run number to recover the job without a new charge.") from None

    def generate(self, options, run_number, node_id, max_cost_cents, interrupt=lambda: None, progress=lambda value: None):
        if not isinstance(max_cost_cents, int) or max_cost_cents < 0:
            raise FormaError("Maximum cost must be a non-negative number of USD cents.")
        account = self.request("/wallet")
        identity = json.dumps([account["accountId"], str(node_id), run_number, options], sort_keys=True, separators=(",", ":"))
        request_id = str(uuid.uuid5(uuid.NAMESPACE_URL, identity))
        interrupt()
        try:
            job = self.request("/requests/" + request_id)["job"]
        except FormaError as error:
            if error.status != 404:
                raise
            quote = self.request("/quotes", {**options, "requestId": request_id})["quote"]
            if quote["cents"] > max_cost_cents:
                raise FormaError(f"Forma quote is {quote['cents']} cents; your limit is {max_cost_cents} cents. No generation was submitted.")
            interrupt()
            job = self.request("/jobs", {"quoteId": quote["id"], "maxCostCents": max_cost_cents})["job"]
        deadline = time.monotonic() + 1800
        while True:
            interrupt()
            status = job["status"]
            if status == "COMPLETED":
                progress(100)
                return job
            if status in ("FAILED", "CANCELLED", "TIMED_OUT", "UNKNOWN"):
                raise FormaError(f"Forma job {job['id']}: {status}. Check this job in Forma. UNKNOWN jobs keep funds reserved; do not change the run number to retry them.")
            if status not in ("SUBMITTING", "IN_QUEUE", "IN_PROGRESS"):
                raise FormaError("Forma returned an unsupported job status.")
            if time.monotonic() >= deadline:
                raise FormaError(f"Still waiting for Forma job {job['id']}. Retry the same run number later.")
            progress(50 if status == "IN_PROGRESS" else 10)
            for _ in range(5):
                interrupt()
                time.sleep(1)
            job = self.request("/jobs/" + str(uuid.UUID(job["id"])))["job"]

    def download(self, job_id, directory, kind):
        job_id = str(uuid.UUID(job_id))
        request = Request(self.base + f"/jobs/{job_id}/download", headers={"Authorization": "Bearer " + self.key})
        path = None
        try:
            try:
                response = self.opener.open(request, timeout=120)
            except HTTPError as error:
                if error.code not in (301, 302, 303, 307, 308):
                    raise
                location = error.headers.get("Location", "")
                error.close()
                url = urlsplit(location)
                if url.scheme != "https" or not url.hostname or url.username or url.password:
                    raise FormaError("Forma returned an invalid media URL.")
                # Signed storage links get NO Forma authorization, even across redirects.
                response = self.opener.open(Request(location), timeout=120)
            with response:
                mime = response.headers.get_content_type()
                extension = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "video/mp4": ".mp4", "video/webm": ".webm"}.get(mime)
                if not extension or not mime.startswith(kind + "/"):
                    raise FormaError("Forma returned an unsupported media format.")
                path = Path(directory) / f"forma-{job_id}-{uuid.uuid4().hex}{extension}"
                size = 0
                with path.open("xb") as output:
                    while chunk := response.read(1024 * 1024):
                        size += len(chunk)
                        if size > 256 * 1024 * 1024:
                            raise FormaError("Forma output exceeds the 256 MB download limit.")
                        output.write(chunk)
                return path
        except (HTTPError, URLError, TimeoutError, OSError):
            if path:
                path.unlink(missing_ok=True)
            raise FormaError("Could not download this Forma result. Retry the same run number; generation will not be purchased again.") from None
        except FormaError:
            if path:
                path.unlink(missing_ok=True)
            raise
