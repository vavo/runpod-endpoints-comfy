"""Quote-only route. Never execute a submitted graph or purchase inference."""
import asyncio
import uuid
from pathlib import Path
from aiohttp import web
from .client import FormaClient, FormaError
from .settings import check_origin, NO_STORE


def input_path(name):
    import folder_paths
    if not isinstance(name, str) or not name or len(name) > 1024:
        raise FormaError("Choose a file in the connected Load node first.")
    root = Path(folder_paths.get_input_directory()).resolve()
    path = Path(folder_paths.get_annotated_filepath(name)).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise FormaError("Price checks can read only files inside ComfyUI's input folder.")
    if path.stat().st_size > 128 * 1024 * 1024:
        raise FormaError("Reference exceeds the 128 MB upload limit.")
    return path


def local_media(field, link, sources):
    from PIL import Image, ImageOps, ImageSequence
    import numpy as np
    import torch
    from comfy_api.latest import InputImpl
    kind = field["media"]
    expected, key = {"image": ("LoadImage", "image"), "video": ("LoadVideo", "file"),
                     "audio": ("LoadAudio", "audio")}[kind]
    if not isinstance(link, list) or len(link) != 2 or link[1] != 0:
        raise FormaError(f"Connect {expected} to check this price.")
    source = sources.get(str(link[0]), {})
    if source.get("class_type") != expected or not isinstance(source.get("inputs"), dict):
        raise FormaError(f"Price checks support a direct {expected} connection or a Reference. Upstream nodes are never run.")
    path = input_path(source["inputs"].get(key))
    if kind in ("video", "audio"):
        with path.open("rb") as file:
            header = file.read(12)
        valid = (header[4:8] == b"ftyp" if kind == "video" else
                 header.startswith((b"fLaC", b"ID3")) or header[:4] == b"RIFF" and header[8:12] == b"WAVE" or
                 len(header) >= 2 and header[0] == 255 and header[1] & 224 == 224)
        if not valid:
            raise FormaError("Price checks accept MP4 video and WAV, MP3 or FLAC audio files.")
    if kind == "video":
        return InputImpl.VideoFromFile(str(path))
    if kind == "audio":
        from comfy_extras.nodes_audio import load
        waveform, rate = load(str(path))
        return {"waveform": waveform.unsqueeze(0), "sample_rate": rate}
    maximum = field.get("maxItems", 1) if field["type"] == "array" else 1
    frames = []
    with Image.open(path) as image:
        for frame in ImageSequence.Iterator(image):
            if len(frames) >= maximum or frame.width * frame.height > 40000000:
                raise FormaError(f"{field['label']} accepts up to {maximum} images, each at most 40 megapixels.")
            frame = ImageOps.exif_transpose(frame).convert("RGB")
            frames.append(torch.from_numpy(np.array(frame).astype(np.float32) / 255))
    if not frames or any(frame.shape != frames[0].shape for frame in frames):
        raise FormaError("Use reference images with matching dimensions.")
    return torch.stack(frames)


def check_price(body):
    from comfy_api.latest import _io
    from .catalog_nodes import FormaImage, FormaVideo, upload_media
    from .catalog import selected_model, prepare_inputs, model_fields, field_id
    if not isinstance(body, dict) or body.get("class_type") not in ("FormaImage", "FormaVideo"):
        raise FormaError("Choose a Forma Image or Video node.")
    flat = body.get("inputs")
    sources = body.get("sources", {})
    if not isinstance(flat, dict) or len(flat) > 100 or not isinstance(sources, dict) or len(sources) > 64:
        raise FormaError("Invalid price-check inputs.")
    run = flat.get("run_number")
    if isinstance(run, bool) or not isinstance(run, int) or not 1 <= run <= 2147483647:
        raise FormaError("Set a valid run number before checking the price.")
    cls = FormaImage if body["class_type"] == "FormaImage" else FormaVideo
    _, _, dynamic = _io.get_finalized_class_inputs(cls.INPUT_TYPES(), flat, include_hidden=True)
    nested = _io.build_nested_inputs(dict(flat), dynamic)
    model, mode, values = selected_model(cls.KIND, nested.get("workflow", {}))
    # Resolve only the three explicitly supported file loaders, never arbitrary nodes.
    for field in model_fields(model, mode):
        if not field.get("media"):
            continue
        key = field_id(field)
        selection = values.get(key, {})
        if isinstance(selection, dict) and selection.get(key) == "Local":
            selection["value"] = local_media(field, selection.get("value"), sources)
        elif isinstance(selection, dict) and isinstance(selection.get("value"), list):
            raise FormaError("This reference comes from another node. Connect Load Image with Local selected, or paste an existing Forma asset/HTTPS reference. Check price never runs upstream generation.")
    inputs, prompt = prepare_inputs(model, mode, values)
    client = FormaClient()
    for field in model_fields(model, mode):
        if field.get("media"):
            value = upload_media(client, field, values[field_id(field)], run)
            if value not in (None, "", []):
                inputs[field["name"]] = value
    options = {"modelId": model["id"], "kind": cls.KIND,
               "workflow": "image-to-video" if mode == "first-last-frame-to-video" else mode,
               "prompt": prompt, "inputs": inputs, "requestId": str(uuid.uuid4())}
    quote = client.request("/quotes", options)["quote"]
    return {"cents": quote["cents"], "expires": quote["expires"]}


def install_price_routes(routes):
    lock = asyncio.Lock()

    @routes.post("/forma/price")
    async def price(request):
        check_origin(request)
        if request.content_type != "application/json" or request.content_length is None or request.content_length > 262144:
            return web.json_response({"error": "Invalid price-check request."}, status=400, headers=NO_STORE)
        if lock.locked():
            return web.json_response({"error": "A price check is already running. Try again shortly."}, status=429, headers=NO_STORE)
        try:
            body = await request.json()
            async with lock:
                result = await asyncio.to_thread(check_price, body)
            return web.json_response(result, headers=NO_STORE)
        except FormaError as error:
            return web.json_response({"error": str(error)}, status=400, headers=NO_STORE)
        except (ValueError, TypeError, KeyError, AttributeError, IndexError):
            return web.json_response({"error": "Check the model controls and connected media, then try again."}, status=400, headers=NO_STORE)
        except Exception:
            return web.json_response({"error": "Price check failed. Verify the media file and Forma connection."}, status=500, headers=NO_STORE)
