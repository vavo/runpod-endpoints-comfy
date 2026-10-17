import numpy as np
import torch
from PIL import Image, ImageOps
import folder_paths
from comfy.model_management import throw_exception_if_processing_interrupted
from comfy.utils import ProgressBar
from comfy_api.latest import InputImpl
from .client import FormaClient


SETUP_INSTRUCTIONS = """GET YOUR FORMA API KEY

1. Open https://forma.cam and sign in or create an account.
2. Open Account settings → API keys → Create API key.
3. Name the key (for example ComfyUI) and copy it when shown. It is shown only once.
4. Add funds in Forma. These nodes use the same account balance.

CONFIGURE COMFYUI

Save the key in a private text file outside this node folder.
Set FORMA_API_KEY_FILE to that file's absolute path in the environment of the ComfyUI backend process, then restart ComfyUI.
Alternatively, configure FORMA_API_KEY in your host's secret/environment settings.
A .env file is not loaded automatically.

NEVER paste your key into this text box, any node input, a prompt, or a workflow JSON. This text is saved with the workflow.

One ComfyUI process uses one Forma account. Anyone who can queue these nodes can spend its balance. Revoke a key in Forma if it is exposed.

If API keys are not visible in Account settings, the Forma API rollout must be enabled before you can use these nodes.

Before queueing, review each node's maximum cost in USD cents. Keep run_number unchanged when retrying; increase it only to buy a new generation.

More help: README.md in runpod-endpoints-comfy"""


class FormaApiKeySetup:
    CATEGORY = "Forma"
    FUNCTION = "show"
    RETURN_TYPES = ()
    DESCRIPTION = "How to create a Forma key and configure ComfyUI. Instructions only; never paste credentials here."

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "instructions": ("STRING", {"multiline": True, "default": SETUP_INSTRUCTIONS,
                                       "tooltip": "Saved with the workflow. Never paste an API key here."}),
        }}

    def show(self, instructions):
        return ()


COMMON = {
    "seed": ("INT", {"default": 42, "min": -1, "max": 2147483647, "control_after_generate": False}),
    "run_number": ("INT", {"default": 1, "min": 1, "max": 2147483647, "control_after_generate": False,
                           "tooltip": "Keep unchanged to recover a job. Increase to purchase another generation with the same settings."}),
}


def generate(options, run_number, unique_id, max_cost_cents):
    client = FormaClient()
    progress = ProgressBar(100)
    job = client.generate(options, run_number, unique_id, max_cost_cents,
                         throw_exception_if_processing_interrupted, progress.update_absolute)
    path = client.download(job["id"], folder_paths.get_temp_directory(), options["kind"])
    return job, path


class FormaSeedreamImage:
    CATEGORY = "Forma"
    FUNCTION = "generate"
    RETURN_TYPES = ("IMAGE", "FORMA_IMAGE")
    RETURN_NAMES = ("image", "forma_image")
    DESCRIPTION = "Generate a Seedream image using your Forma balance. The Forma image connection animates the original without uploading it again."

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "prompt": ("STRING", {"multiline": True, "default": "A coastal villa at sunset, cinematic photography"}),
            "negative_prompt": ("STRING", {"multiline": True, "default": ""}),
            "size": ("STRING", {"default": "1280*720"}),
            **COMMON,
            "max_cost_cents": ("INT", {"default": 10, "min": 0, "max": 100000, "tooltip": "Maximum USD cents for this image."}),
        }, "hidden": {"unique_id": "UNIQUE_ID"}}

    def generate(self, prompt, negative_prompt, size, seed, run_number, max_cost_cents, unique_id):
        job, path = generate({
            "modelId": "seedream-v4-t2i", "kind": "image", "workflow": "text-to-image",
            "prompt": prompt, "inputs": {"negative_prompt": negative_prompt, "size": size, "seed": seed},
        }, run_number, unique_id, max_cost_cents)
        try:
            with Image.open(path) as image:
                pixels = np.array(ImageOps.exif_transpose(image).convert("RGB")).astype(np.float32) / 255.0
        finally:
            path.unlink(missing_ok=True)
        return (torch.from_numpy(pixels)[None,], f"asset:{job['id']}")


class FormaPrunaAnimate:
    CATEGORY = "Forma"
    FUNCTION = "generate"
    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("video",)
    DESCRIPTION = "Animate a Forma image using your account balance. Connect the VIDEO output to Save Video."

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "forma_image": ("FORMA_IMAGE",),
            "prompt": ("STRING", {"multiline": True, "default": "Slow camera push in, gentle movement, preserve the scene"}),
            "duration": ("INT", {"default": 5, "min": 1, "max": 10}),
            "resolution": (["720p", "1080p"],),
            "fps": ([24, 48],),
            "draft": ("BOOLEAN", {"default": False}),
            "save_audio": ("BOOLEAN", {"default": True}),
            "prompt_upsampling": ("BOOLEAN", {"default": True}),
            **COMMON,
            "max_cost_cents": ("INT", {"default": 25, "min": 0, "max": 100000, "tooltip": "Maximum USD cents for this video."}),
        }, "hidden": {"unique_id": "UNIQUE_ID"}}

    def generate(self, forma_image, prompt, duration, resolution, fps, draft, save_audio,
                 prompt_upsampling, seed, run_number, max_cost_cents, unique_id):
        _, path = generate({
            "modelId": "p-video", "kind": "video", "workflow": "image-to-video", "prompt": prompt,
            "inputs": {"image": forma_image, "duration": duration, "resolution": resolution, "fps": fps,
                       "draft": draft, "save_audio": save_audio, "prompt_upsampling": prompt_upsampling, "seed": seed},
        }, run_number, unique_id, max_cost_cents)
        return (InputImpl.VideoFromFile(str(path)),)


NODE_CLASS_MAPPINGS = {"FormaApiKeySetup": FormaApiKeySetup, "FormaSeedreamImage": FormaSeedreamImage, "FormaPrunaAnimate": FormaPrunaAnimate}
NODE_DISPLAY_NAME_MAPPINGS = {"FormaApiKeySetup": "Forma · API Key Setup", "FormaSeedreamImage": "Forma · Generate Image", "FormaPrunaAnimate": "Forma · Animate Image"}
