"""Forma catalog snapshot and input validation, without ComfyUI dependencies."""
import json
import math
import re
from pathlib import Path
from urllib.parse import urlsplit
from .client import FormaError

MODELS = {m["id"]: m for m in json.loads((Path(__file__).parent / "models.json").read_text())}
WORKFLOWS = {
    "image": ["text-to-image", "image-to-image"],
    "video": ["text-to-video", "image-to-video", "first-last-frame-to-video", "reference-to-video",
              "video-to-video", "audio-to-video", "talking-portrait", "motion-transfer"],
}
END_FRAMES = {m["id"]: f["name"] for m in MODELS.values() for f in m["fields"]
              if f["name"] in ("last_image", "end_image", "end_image_url") and "image-to-video" in m["workflows"]}
HIDDEN_FIELDS = {"enable_safety_checker", "disable_safety_checker", "enable_base64_output"}


def field_id(field):
    return field["name"].replace(".", "__")


def model_fields(model, workflow):
    fields = []
    for field in model["fields"]:
        if field.get("hidden") or field["name"] in HIDDEN_FIELDS:
            continue
        field = dict(field)
        # These modes require otherwise optional conditioning inputs.
        if (workflow == "image-to-" + model["kind"] and field["name"] == "image" or
                workflow == "audio-to-video" and field["name"] == "audio" or
                workflow == "first-last-frame-to-video" and field["name"] in ("image", "start_image_url", END_FRAMES.get(model["id"]))):
            field["required"] = True
        fields.append(field)
    return fields


def selected_model(kind, selection):
    mode = selection.get("workflow")
    values = selection.get("model", {})
    model = MODELS.get(values.get("model"))
    supported = model and (mode in model["workflows"] or mode == "first-last-frame-to-video" and model["id"] in END_FRAMES)
    if mode not in WORKFLOWS[kind] or not supported or model["kind"] != kind:
        raise FormaError("Choose a compatible Forma model and workflow.")
    return model, mode, values


def valid_reference(value):
    if re.fullmatch(r"asset:[a-f0-9-]{36}", value):
        return True
    try:
        url = urlsplit(value)
        return url.scheme == "https" and bool(url.hostname) and not url.username and not url.password and not url.port
    except ValueError:
        return False


def prepare_inputs(model, workflow, values):
    inputs, prompt = {}, ""
    fields = model_fields(model, workflow)
    if set(values) - {"model", *(field_id(f) for f in fields)}:
        raise FormaError("These controls do not belong to the selected model.")
    for field in fields:
        key = field_id(field)
        value = values.get(key, field.get("default"))
        if field.get("media"):
            if not isinstance(value, dict) or value.get(key) not in ("None", "Reference", "Local"):
                raise FormaError(f"Choose a source for {field['label']}.")
            source = value[key]
            media = value.get("value")
            if source == "None" or source == "Reference" and not str(media or "").strip():
                if field.get("required"):
                    raise FormaError(f"Add {field['label'].lower()}.")
            elif source == "Reference":
                refs = [r.strip() for r in str(media).splitlines() if r.strip()]
                maximum = field.get("maxItems", 1) if field["type"] == "array" else 1
                if not refs or len(refs) > maximum or not all(valid_reference(r) for r in refs):
                    raise FormaError(f"{field['label']}: use up to {maximum} owned asset references or public HTTPS URLs.")
            elif source == "Local" and media is None:
                raise FormaError(f"Connect {field['label'].lower()}.")
            continue
        if isinstance(value, dict):
            if value.get(key) == "Default":
                continue
            if value.get(key) != "Set":
                raise FormaError(f"Check {field['label'].lower()}.")
            value = value.get("value")
        if value in (None, ""):
            if field.get("required"):
                raise FormaError(f"Add {field['label'].lower()}.")
            continue
        if field["type"] == "array":
            try:
                value = json.loads(value)
            except (ValueError, TypeError):
                raise FormaError(f"{field['label']}: enter a JSON list.") from None
            if not isinstance(value, list) or len(value) > 4 or any(not isinstance(x, dict) or set(x) != {"path", "scale"} or not isinstance(x["path"], str) or not isinstance(x["scale"], (int, float)) or not 0 <= x["scale"] <= 2 for x in value):
                raise FormaError(f"{field['label']}: use up to four path/scale entries, with strength 0–2.")
        elif field["type"] in ("integer", "number", "float"):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or field["type"] == "integer" and int(value) != value:
                raise FormaError(f"Check {field['label'].lower()}.")
            if value < field.get("min", -math.inf) or value > field.get("max", math.inf) or field.get("step") and value % field["step"]:
                raise FormaError(f"Check {field['label'].lower()} range and step.")
            if field["type"] == "integer":
                value = int(value)
        elif field["type"] == "boolean":
            if not isinstance(value, bool):
                raise FormaError(f"Check {field['label'].lower()}.")
        elif not isinstance(value, str) or len(value) > field.get("maxLength", 10000):
            raise FormaError(f"Check {field['label'].lower()} length.")
        if field.get("choices") and value not in field["choices"]:
            raise FormaError(f"Choose a supported {field['label'].lower()}.")
        if field["name"] == "prompt":
            prompt = value.strip()
            if field.get("required") and not prompt:
                raise FormaError("Enter a prompt.")
        else:
            inputs[field["name"]] = value
    return inputs, prompt
