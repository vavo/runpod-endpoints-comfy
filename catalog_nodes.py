"""Catalog-backed native ComfyUI selectors; legacy nodes remain compatible."""
import io as buffers
import json
import tempfile
import wave
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageOps
import folder_paths
from comfy.model_management import throw_exception_if_processing_interrupted
from comfy.utils import ProgressBar
from comfy_api.latest import io, InputImpl, VideoContainer, VideoCodec
from .client import FormaClient, FormaError
from .catalog import MODELS, WORKFLOWS, END_FRAMES, field_id, model_fields, selected_model, prepare_inputs


def field_schema(field):
    key = field_id(field)
    label = field["label"]
    tip = field.get("description", "")
    if field.get("media"):
        kind = field["media"]
        many = field["type"] == "array"
        native = {"image": io.Image, "video": io.Video, "audio": io.Audio}[kind]
        options = [] if field.get("required") else [io.DynamicCombo.Option("None", [])]
        options.extend([
            io.DynamicCombo.Option("Reference", [io.String.Input("value", default="", multiline=many,
                tooltip="Owned asset:UUID or public HTTPS URL. One reference per line for lists; connect Forma reference outputs here.")]),
            io.DynamicCombo.Option("Local", [native.Input("value", tooltip="Uploads this media to your Forma account." +
                (f" Image batches support up to {field.get('maxItems', 1)} references." if many and kind == "image" else ""))]),
        ])
        return io.DynamicCombo.Input(key, options=options, display_name=label, tooltip=tip)
    default = field.get("default")
    common = {"display_name": label, "tooltip": tip}
    def widget(widget_id, value):
        if field.get("choices"):
            return io.Combo.Input(widget_id, options=field["choices"], default=value, **common)
        if field["type"] in ("integer", "float", "number"):
            numeric = io.Int if field["type"] == "integer" else io.Float
            opts = {k: field[k] for k in ("min", "max", "step") if k in field}
            if numeric is io.Int:
                opts = {k: int(v) for k, v in opts.items()}
                opts["control_after_generate"] = False
            return numeric.Input(widget_id, default=value, **opts, **common)
        if field["type"] == "boolean":
            return io.Boolean.Input(widget_id, default=value, **common)
        if field["type"] == "array":
            return io.String.Input(widget_id, default=json.dumps(value or []), multiline=True,
                                   tooltip=tip + ' JSON list, e.g. [{"path":"https://...","scale":1}].', display_name=label)
        return io.String.Input(widget_id, default=value if value is not None else "", multiline="prompt" in field["name"], **common)
    if default is None and not field.get("required") and field["type"] in ("integer", "float", "number", "boolean"):
        value = field.get("min", False if field["type"] == "boolean" else 0)
        return io.DynamicCombo.Input(key, display_name=label, tooltip=tip, options=[
            io.DynamicCombo.Option("Default", []), io.DynamicCombo.Option("Set", [widget("value", value)])])
    if default is None:
        default = (field.get("choices") or [field.get("min", 0)])[0] if field["type"] in ("integer", "float", "number") else ""
    return widget(key, default)


def workflow_schema(kind):
    choices = []
    for workflow in WORKFLOWS[kind]:
        model_options = []
        for model in MODELS.values():
            if model["kind"] != kind or workflow not in model["workflows"] and not (workflow == "first-last-frame-to-video" and model["id"] in END_FRAMES):
                continue
            fields = model_fields(model, workflow)
            model_options.append(io.DynamicCombo.Option(model["id"], [field_schema(f) for f in fields]))
        choices.append(io.DynamicCombo.Option(workflow, [io.DynamicCombo.Input("model", options=model_options,
            tooltip="Choose a Forma model. Controls below follow its supported inputs.")]))
    return io.DynamicCombo.Input("workflow", options=choices, tooltip="Select a workflow, then a compatible model.")


def upload_media(client, field, selection, run_number):
    source = selection[field_id(field)]
    if source == "None":
        return None
    if source == "Reference":
        value = selection["value"].strip()
        return [line.strip() for line in value.splitlines() if line.strip()] if field["type"] == "array" else value
    if source != "Local":
        raise FormaError("Choose a valid media source.")
    value = selection["value"]
    throw_exception_if_processing_interrupted()
    if field["media"] == "image":
        maximum = field.get("maxItems", 1) if field["type"] == "array" else 1
        if len(value) < 1 or len(value) > maximum:
            raise FormaError(f"{field['label']} accepts 1–{maximum} images; split the batch first.")
        refs = []
        for frame in value:
            if frame.shape[0] * frame.shape[1] > 40000000:
                raise FormaError("Reference images must be at most 40 megapixels.")
            data = buffers.BytesIO()
            Image.fromarray((frame.detach().cpu().clamp(0, 1).numpy() * 255).round().astype(np.uint8)).save(data, format="PNG")
            refs.append(client.upload(data.getvalue(), "image/png", run_number))
        return refs if field["type"] == "array" else refs[0]
    if field["media"] == "audio":
        waveform = value["waveform"]
        if waveform.shape[0] != 1:
            raise FormaError("Connect one audio clip at a time.")
        sample_rate = int(value["sample_rate"])
        if waveform.numel() * 2 + 44 > 128 * 1024 * 1024:
            raise FormaError("Audio reference exceeds the 128 MB upload limit.")
        data = buffers.BytesIO()
        pcm = (waveform[0].detach().cpu().clamp(-1, 1).numpy().T * 32767).round().astype("<i2")
        with wave.open(data, "wb") as output:
            output.setnchannels(pcm.shape[1])
            output.setsampwidth(2)
            output.setframerate(sample_rate)
            output.writeframes(pcm.tobytes())
        reference = client.upload(data.getvalue(), "audio/wav", run_number)
    else:
        with tempfile.TemporaryDirectory(dir=folder_paths.get_temp_directory()) as directory:
            path = Path(directory) / "reference.mp4"
            value.save_to(str(path), format=VideoContainer.MP4, codec=VideoCodec.H264)
            if path.stat().st_size > 128 * 1024 * 1024:
                raise FormaError("Video reference exceeds the 128 MB upload limit.")
            reference = client.upload(path.read_bytes(), "video/mp4", run_number)
    return [reference] if field["type"] == "array" else reference


class FormaCatalogBase(io.ComfyNode):
    KIND = None

    @classmethod
    def define_schema(cls):
        output = io.Image if cls.KIND == "image" else io.Video
        return io.Schema(
            node_id="Forma" + cls.KIND.title(), display_name="Forma · " + cls.KIND.title() + " (Choose Model)",
            category="Forma", description="Select a workflow and model. Uses your Forma balance and checks the spending cap before inference.",
            inputs=[workflow_schema(cls.KIND),
                    io.Int.Input("run_number", default=1, min=1, max=2147483647, control_after_generate=False,
                                 tooltip="Keep unchanged to recover. Increase only to purchase a new generation."),
                    io.Int.Input("max_cost_cents", default=10 if cls.KIND == "image" else 25, min=0, max=100000,
                                 tooltip="Maximum price in USD cents; increase only after reviewing the price.")],
            outputs=[output.Output(cls.KIND), io.String.Output("forma_reference", tooltip="Owned asset reference, usable in another Forma node's Reference input.")],
            hidden=[io.Hidden.unique_id],
        )

    @classmethod
    def execute(cls, workflow, run_number, max_cost_cents):
        model, mode, values = selected_model(cls.KIND, workflow)
        client = FormaClient()
        # Validate fields and required media before uploading anything.
        inputs, prompt = prepare_inputs(model, mode, values)
        for field in model_fields(model, mode):
            if field.get("media"):
                value = upload_media(client, field, values[field_id(field)], run_number)
                if value not in (None, "", []):
                    inputs[field["name"]] = value
        options = {"modelId": model["id"], "kind": cls.KIND,
                   "workflow": "image-to-video" if mode == "first-last-frame-to-video" else mode,
                   "prompt": prompt, "inputs": inputs}
        progress = ProgressBar(100)
        job = client.generate(options, run_number, cls.hidden.unique_id, max_cost_cents,
                              throw_exception_if_processing_interrupted, progress.update_absolute)
        path = client.download(job["id"], folder_paths.get_temp_directory(), cls.KIND)
        reference = "asset:" + job["id"]
        if cls.KIND == "video":
            return io.NodeOutput(InputImpl.VideoFromFile(str(path)), reference)
        try:
            with Image.open(path) as image:
                pixels = np.asarray(ImageOps.exif_transpose(image).convert("RGB")).astype(np.float32) / 255
            return io.NodeOutput(torch.from_numpy(pixels)[None,], reference)
        finally:
            path.unlink(missing_ok=True)


class FormaImage(FormaCatalogBase):
    KIND = "image"


class FormaVideo(FormaCatalogBase):
    KIND = "video"
