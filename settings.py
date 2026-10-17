"""Write-only credential settings; never return the key to a browser."""
import asyncio
import re
from urllib.parse import urlsplit
from aiohttp import web
from .client import FormaClient, FormaError, environment_key_configured, key_status, save_key, remove_key


NO_STORE = {"Cache-Control": "no-store"}


def check_origin(request):
    origin = urlsplit(request.headers.get("Origin", ""))
    if (request.headers.get("X-Forma-Settings") != "1"
            or origin.netloc != request.host or origin.username or origin.password
            or origin.path or origin.query or origin.fragment
            or (origin.scheme != "https" and not (
                origin.scheme == "http" and origin.hostname in ("localhost", "127.0.0.1", "::1")))):
        raise web.HTTPForbidden(text="Open Forma settings from the same HTTPS ComfyUI instance (or localhost).", headers=NO_STORE)


def install_routes(routes):
    lock = asyncio.Lock()

    @routes.get("/forma/settings/key")
    async def status(request):
        return web.json_response(key_status(), headers=NO_STORE)

    @routes.post("/forma/settings/key")
    async def save(request):
        check_origin(request)
        if request.content_type != "application/json" or request.content_length is None or request.content_length > 256:
            return web.json_response({"error": "Invalid key request."}, status=400, headers=NO_STORE)
        try:
            body = await request.json()
        except (ValueError, UnicodeError):
            return web.json_response({"error": "Invalid key request."}, status=400, headers=NO_STORE)
        key = body.get("key") if isinstance(body, dict) else None
        if not isinstance(key, str) or not re.fullmatch(r"forma_[0-9a-f]{64}", key):
            return web.json_response({"error": "Paste a complete Forma API key."}, status=400, headers=NO_STORE)
        async with lock:
            if environment_key_configured():
                return web.json_response({"error": "The host manages this key through environment variables."}, status=409, headers=NO_STORE)
            try:
                # A balance read validates the key without buying generation.
                await asyncio.to_thread(lambda: FormaClient(api_key=key).request("/wallet"))
                save_key(key)
            except FormaError as error:
                return web.json_response({"error": str(error)}, status=400, headers=NO_STORE)
            except OSError:
                return web.json_response({"error": "Could not save the key. Check server file permissions."}, status=500, headers=NO_STORE)
        return web.json_response(key_status(), headers=NO_STORE)

    @routes.delete("/forma/settings/key")
    async def remove(request):
        check_origin(request)
        async with lock:
            if environment_key_configured():
                return web.json_response({"error": "The host manages this key through environment variables."}, status=409, headers=NO_STORE)
            try:
                remove_key()
            except (FormaError, OSError):
                return web.json_response({"error": "Could not remove the saved key."}, status=500, headers=NO_STORE)
        return web.json_response(key_status(), headers=NO_STORE)
