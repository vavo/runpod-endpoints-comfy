# RunPod Endpoints for ComfyUI

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee-vavo-5F7FFF?style=for-the-badge&logo=buy-me-a-coffee&logoColor=white)](https://www.buymeacoffee.com/vavo) [![Sponsor on GitHub](https://img.shields.io/badge/Sponsor%20on-GitHub-24292F?style=for-the-badge&logo=github)](https://github.com/sponsors/vavo) [![Support on Patreon](https://img.shields.io/badge/Support%20on-Patreon-FF424D?style=for-the-badge&logo=patreon&logoColor=white)](https://www.patreon.com/vavo)

Custom nodes for [ComfyUI](https://github.com/comfyanonymous/ComfyUI) that run cloud image and video generation through [Forma](https://forma.cam), using your Forma API key and prepaid account balance. Inference runs remotely, so these nodes need no local model weights or inference GPU. Choose a workflow and model in the image or video node, or open a ready-wired example for any supported mode.

## Quick install

From your ComfyUI directory, using the Python interpreter that runs ComfyUI:

```sh
git clone https://github.com/vavo/runpod-endpoints-comfy.git custom_nodes/runpod-endpoints-comfy
python -m pip install -r custom_nodes/runpod-endpoints-comfy/requirements.txt
```

1. Restart ComfyUI and refresh the browser.
2. At [forma.cam](https://forma.cam), open **Account settings → API keys → Create API key** and add funds to your account.
3. Open **ComfyUI Settings → Forma → API key**, paste your key, and click **Save and test key**. This checks your balance without spending credits.
4. Open a [workflow example](workflows/README.md), choose a model, edit the prompt, and click **Check price** before queueing. Standalone [text-to-image](workflows/text-to-image.json) and [text-to-video](workflows/text-to-video.json) examples need no input files.

Requires Python 3.10+, current ComfyUI with native V3 `DynamicCombo`, `VIDEO` and `SaveVideo` support, and outbound HTTPS access to Forma. Keys are saved on the ComfyUI server, outside workflow JSON and browser storage.

## Models and workflows

The tables below list all **44 active models in Forma's catalog as of 19 October 2026**, excluding retired entries. Catalog availability can change.

**Current ComfyUI support:** all **39 image/video models** below are selectable in **Forma · Image (Choose Model)** and **Forma · Video (Choose Model)**. The five speech/text catalog entries are not enabled for Forma account-balance inference and are excluded from the selectors. Their billing must be implemented on Forma before they can be used here.

### Choosing a model

1. Add **Forma · Image (Choose Model)** or **Forma · Video (Choose Model)** from the Forma category.
2. Select **workflow**, then **model**. Only compatible models appear; changing either rebuilds the controls, so review the new settings and connections.
3. For media inputs, select **Local** to connect a native `IMAGE`, `VIDEO`, or `AUDIO`, or **Reference** to paste an owned `asset:UUID` / public HTTPS URL. Optional inputs also offer **None**. Reference lists take one value per line; local image batches supply multiple references up to the model's limit. To reuse generated media, connect a node's `forma_reference` STRING output to the next node's Reference value input.
4. Set prompts and model controls, then click **Check price**. The node shows the current Forma quote in USD and whether it fits **max_cost_cents**. Checking never starts inference or changes your cap. Click **Run** only when you accept the price; execution gets a fresh quote before purchasing.

FLF2V has its own selector entry and requires both starting and ending frames. RF2V uses `reference-to-video`. Audio-to-video, talking portraits and motion transfer have their required conditioning inputs. LoRA lists use a JSON field with `path` and `scale` entries. Safety follows the Forma account preference; it is not overridden by workflow controls.

Local media is uploaded to your Forma account before quoting. Uploads require a funded account, consume library storage, and follow its retention policy. Each file is limited to 128 MB (your proxy may impose a smaller limit); images are limited to 40 megapixels. Repeating identical bytes with the same run number reuses the owned upload. Keep run numbers unchanged when recovering a request. Expired/removed references stop with an error; intentionally replacing them requires a new run number.

### Start with your own image

Open **[image-to-video-local.json](workflows/image-to-video-local.json)** for `Load Image → Forma Video → Save Video`. Click **choose file to upload** in Load Image, select a model, enter your motion prompt and click **Check price**. This workflow has no image-generation branch.

The [workflow list](workflows/README.md) also includes ready-wired local I2I, first/last-frame, reference-video, talking-portrait and motion-transfer examples. Every required image has a Load Image node; audio/video conditioning has the matching loader. Choose your files before checking a price or running.

### Check price

Both **Choose Model** nodes have a **Check price** button and a **Price (USD)** field. This requests a server quote without queuing ComfyUI or purchasing inference. Editing inputs or letting the quote expire marks the displayed price stale. Your `max_cost_cents` remains a separate spending limit.

Price checks accept direct **Load Image**, **Load Video** (MP4), and **Load Audio** (WAV/MP3/FLAC) connections, or literal **Reference** values. Local files are uploaded to Forma first and use library storage; the account must be funded. They are read only from ComfyUI's input directory. Price checking never executes upstream nodes: a generated or processed reference must already exist and be supplied as an asset/HTTPS reference, or saved and selected in a Load node. The generated-image-to-video starter remains available for chained inference.

The new nodes output native `IMAGE`/`VIDEO` plus a `forma_reference` string. The original fixed-model nodes remain available for existing workflows.

### Workflow types

| Short name | Workflow |
| --- | --- |
| T2I | Text to image |
| I2I | Image to image / image editing |
| T2V | Text to video |
| I2V | Image to video |
| FLF2V | First and last frame to video; an I2V option on models with an ending-frame input |
| RF2V | Reference images to video (`reference-to-video` in Forma) |
| V2V | Video to video / video editing |
| A2V | Audio to video |
| Motion transfer | Transfer movement from a reference video to an image |
| Talking portrait | Animate a portrait using speech or singing |
| T2A | Text to audio / speech |
| Voice cloning | Generate speech using a voice sample |
| T2T | Text to text |

### Image models

| Model | Forma model ID | Workflows |
| --- | --- | --- |
| Flux Dev | `black-forest-labs-flux-1-dev` | T2I |
| Flux Kontext Dev | `black-forest-labs-flux-1-kontext-dev` | I2I |
| Flux Schnell | `black-forest-labs-flux-1-schnell` | T2I |
| FLUX.2 Klein 9B | `fal-flux-2-klein-9b` | T2I |
| Nano Banana 2 Edit | `google-nano-banana-2-edit` | I2I |
| Nano Banana Pro Edit | `nano-banana-pro-edit` | I2I |
| P-Image Edit | `p-image-edit` | I2I |
| P-Image T2I | `p-image-t2i` | T2I |
| Qwen Image | `qwen-image-t2i` | T2I |
| Qwen Image Edit | `qwen-image-edit` | I2I |
| Qwen Image Edit 2511 | `qwen-image-edit-2511` | I2I |
| Qwen Image Edit 2511 LoRA | `qwen-image-edit-2511-lora` | I2I |
| Qwen Image LoRA | `qwen-image-t2i-lora` | T2I |
| Seedream 4.0 Edit | `seedream-v4-edit` | I2I |
| Seedream 4.0 T2I | `seedream-v4-t2i` | T2I |
| WAN 2.6 T2I | `wan-2-6-t2i` | T2I |
| Z-Image Turbo | `z-image-turbo` | T2I, I2I |

### Video models

| Model | Forma model ID | Workflows |
| --- | --- | --- |
| Hailuo 02 Standard | `minimax-hailuo-02-std` | T2V, I2V, FLF2V |
| Hailuo 2.3 Fast | `minimax-hailuo-2-3-fast` | I2V |
| InfiniteTalk | `infinitetalk` | Talking portrait |
| Kling 3.0 Pro | `fal-kling-v3-pro-i2v` | I2V, FLF2V |
| Kling v2.6 Motion Control | `kling-v2-6-std-motion-control` | Motion transfer |
| Kling Video O1 R2V | `kling-video-o1-r2v` | RF2V |
| Pruna Video | `p-video` | T2V, I2V, A2V |
| Pruna Video Edit | `p-video-edit` | V2V |
| Seedance 1.5 Pro I2V (retiring soon) | `seedance-v1-5-pro-i2v` | I2V, FLF2V |
| Seedance 2.5 I2V | `seedance-2-5-i2v` | I2V, FLF2V |
| Seedance 2.5 T2V | `seedance-2-5-t2v` | T2V |
| SORA 2 I2V | `sora-2-i2v` | I2V |
| SORA 2 Pro I2V | `sora-2-pro-i2v` | I2V |
| Veo 3.1 Fast | `google-veo3-1-fast-i2v` | I2V, FLF2V |
| Vidu Q3 I2V | `vidu-q3-i2v` | I2V |
| Vidu Q3 T2V | `vidu-q3-t2v` | T2V |
| WAN 2.1 I2V 720p | `wan-2-1-i2v-720` | I2V |
| WAN 2.2 I2V 720p | `wan-2-2-i2v-720` | I2V |
| WAN 2.2 I2V 720p LoRA | `wan-2-2-t2v-720-lora` | I2V |
| WAN 2.5 | `wan-2-5` | I2V |
| WAN 2.6 I2V | `wan-2-6-i2v` | I2V |
| WAN 2.6 T2V | `wan-2-6-t2v` | T2V |

### Audio models (not enabled for account-balance inference)

| Model | Forma model ID | Workflows |
| --- | --- | --- |
| Chatterbox Turbo | `chatterbox-turbo` | T2A, Voice cloning |
| Minimax Speech 02 HD | `minimax-speech-02-hd` | T2A |

### Text models (not enabled for account-balance inference)

| Model | Forma model ID | Workflows |
| --- | --- | --- |
| IBM Granite 4.0 | `granite-4-0-h-small` | T2T |
| Moonshot Kimi | `moonshot-kimi` | T2T |
| Qwen3 32B AWQ | `qwen3-32b-awq` | T2T |

FLF2V uses the model's I2V workflow with an ending frame; it is not a separate Forma workflow ID. Seedance 2.5 T2V also accepts optional image, video, and audio references within its T2V workflow. Seedance 1.5 Pro I2V is marked as retiring soon in Forma; its suggested replacement is Seedance 2.5 I2V.

### Included ComfyUI nodes

| Node | Supported model / purpose |
| --- | --- |
| Forma · Image (Choose Model) | All 17 image models: T2I and I2I |
| Forma · Video (Choose Model) | All 22 video models: T2V, I2V, FLF2V, RF2V, V2V, A2V, talking portraits and motion transfer |
| Forma · API Key Setup | Instructions for creating, funding, and connecting a Forma account |
| Forma · Generate Image | Seedream 4.0 T2I (`seedream-v4-t2i`), T2I |
| Forma · Animate Image | Pruna Video (`p-video`), I2V from a Forma image reference |

## Installation details

Use the Python interpreter that runs ComfyUI. For Windows Portable, run the dependency command from the portable installation directory:

```powershell
.\python_embeded\python.exe -m pip install -r .\ComfyUI\custom_nodes\runpod-endpoints-comfy\requirements.txt
```

A GitHub ZIP also works: extract it into `custom_nodes/runpod-endpoints-comfy` so `__init__.py` is directly inside that folder. This package is not currently listed in Comfy Registry/Manager; use Git or ZIP installation.

If you previously installed `comfyui-forma` from the Forma repository, move that old folder out of `custom_nodes` before installing this package. Both expose the same node IDs; existing workflows remain compatible.

### Account and key setup

1. Install the package as above.
2. In Forma, open **Account settings → API keys → Create API key**. Save the key when it is shown. Add funds using Forma's existing top-up flow.
3. Open **ComfyUI Settings → Forma → API key**, paste the key in the masked field, and click **Save and test key**. Validation reads your balance without buying a generation. The key is saved on the ComfyUI server; no restart is needed after saving it.
4. Use **Remove saved key** to disconnect this instance. To disable the key everywhere, revoke it in Forma. Updating the custom-node package itself still requires a ComfyUI restart and browser refresh.
5. Open `workflows/image-to-video.json`, edit the prompts, and queue it. Both files are saved by the standard Save Image and Save Video nodes under ComfyUI's output directory.

The settings interface requires HTTPS for remote hosts; localhost HTTP is supported. RunPod proxy addresses are recognized from the server's pod ID and listening port. For another reverse proxy that rewrites Host, set `FORMA_COMFY_ORIGIN=https://your-comfy-host` on the server; forwarded headers are not trusted. A saved key lives in `.forma/api.key` beside ComfyUI's resolved user directory, outside the HTTP-accessible user-data folders. The directory is restricted to its owner and the file uses mode 0600 on POSIX systems. It is not encrypted against the server owner or other installed plugins. It is never written to browser local storage, normal ComfyUI settings, or workflow JSON. Everyone using that ComfyUI process uses the same Forma account; use a separate instance for each customer account. The host must permit installing custom nodes and making outbound HTTPS requests. This package has not been approved or published for any managed ComfyUI marketplace.

**Never put the key in a workflow, prompt, screenshot, or shared notebook.** Anyone with the key can generate using your balance and retrieve your creations. Keys can be revoked in Forma. The package never contacts RunPod directly.

### Advanced: environment variables or a key file

`FORMA_API_KEY` and `FORMA_API_KEY_FILE` remain supported. Host-managed environment configuration takes precedence and disables editing through the interface. Create a text file containing only your Forma key, outside the repository. On macOS/Linux, restrict its permissions and set its path in the same terminal or launcher that starts ComfyUI:

```sh
chmod 600 "$HOME/.config/forma/api.key"
export FORMA_API_KEY_FILE="$HOME/.config/forma/api.key"
python main.py
```

On Windows PowerShell, set the absolute path before starting your normal ComfyUI launcher:

```powershell
$env:FORMA_API_KEY_FILE = "$env:USERPROFILE\.config\forma\api.key"
# Start ComfyUI from this PowerShell session.
```

For Desktop or hosted installations, configure the variable in the environment of the ComfyUI backend process, then fully restart it. A `.env` file is not loaded automatically. `FORMA_API_KEY` takes precedence if both variables are set.

## Included workflows

- [Selectable image → video](workflows/choose-model-image-to-video.json): editor workflow with model/workflow dropdowns and native save nodes.
- [Selectable image → video, API format](workflows/choose-model-image-to-video-api.json): the same graph for `/prompt`.
- [Text → image](workflows/text-to-image.json): standalone Forma Image → Save Image.
- [Text → video](workflows/text-to-video.json): standalone Forma Video → Save Video.
- [Workflow examples](workflows/README.md): canvas workflows and API templates for all ten supported modes, with connected loaders wherever media is required.

### Legacy starter workflow

Open [image-to-video.json](workflows/image-to-video.json) on the ComfyUI canvas:

```text
Forma · Generate Image ── IMAGE ─────────── Save Image
                       └─ FORMA_IMAGE ─── Forma · Animate Image ── VIDEO ── Save Video
```

The [API-format workflow](workflows/image-to-video-api.json) is for ComfyUI's `/prompt` endpoint. Both legacy workflows use the same two fixed-model generation nodes plus the setup instructions node, followed by ComfyUI's built-in save nodes.

## Controls and charging

- **Forma · API Key Setup:** a reusable instructions text node in the Forma category. It explains account creation, one-time key creation, funding, ComfyUI settings, and key safety. It makes no API calls and needs no connection. The starter workflow places it first; never paste your key into its text box.

- **Forma · Generate Image:** prompt, negative prompt, size, seed, run number, and maximum image cost in USD cents. Outputs a standard `IMAGE` plus a `FORMA_IMAGE` reference.
- **Forma · Animate Image:** takes the `FORMA_IMAGE` reference directly. Controls include motion prompt, duration (1–10 seconds), resolution, frame rate, draft mode, audio output, prompt upsampling, seed, run number, and maximum video cost. Outputs native `VIDEO` for Save Video or further processing.
- A `FORMA_IMAGE` refers to the original image stored in your Forma account. Editing the standard `IMAGE` output does not change that reference. For local/edited images, use the new **Image/Video (Choose Model)** nodes with a **Local** media input.
- Each node obtains a server quote before submitting. Default caps are 10 cents for the image and 25 cents for the video; these are spending ceilings, not advertised prices. Requests use paid balance, not website trials. Forma applies your account's safety preference.
- If a quote exceeds the cap or the balance is insufficient, the node stops before inference. Each stage is billed separately: an image that completed remains charged if animation fails or exceeds its cap.

### Retry without another charge

The account, node ID, generation settings, and **run_number** determine a stable request ID. Queueing unchanged settings again recovers the same job, including after a timeout, restart, or key rotation within the same account. Changing only the spending cap does not create another generation.

Increase **run_number** to intentionally buy another generation with the same settings. Changing the prompt, seed, settings, source image, or node ID also produces a new request. Keep run numbers fixed while recovering an interrupted workflow; do not automatically increment them after each queue.

Completed results can be cached by ComfyUI. The native Save nodes remain responsible for durable local copies. Forma library expiry still applies; an expired result cannot be recovered by changing a spending cap.

Polling waits up to 30 minutes, then stops locally. Interrupting ComfyUI stops waiting; it does not cancel remote inference or promise a refund. Retry the same run number to recover. `UNKNOWN` means the provider submission could not be confirmed: funds remain reserved, and the user must check the job in Forma or contact support. The client never automatically buys a replacement.

## Development

`FORMA_API_URL` defaults to `https://forma.cam/api/v1`. Override it only in the server environment for development; remote URLs require HTTPS, while localhost allows HTTP. This URL is not a graph input. The Forma server must expose the API-key routes and `/uploads` for local reference inputs.

```sh
python3 -m unittest discover -s tests -v
```

`workflows/image-to-video-api.json` is the headless ComfyUI `/prompt` graph; `image-to-video.json` is the editor graph. See [the client API contract](docs/api.md) for the HTTP contract used by these nodes.


## Troubleshooting

| Symptom | Check |
| --- | --- |
| Missing Forma nodes | Check the startup log, the custom-node folder location, and dependencies in ComfyUI's Python environment. |
| Missing `VIDEO` / `SaveVideo` / `DynamicCombo` | Update ComfyUI and its frontend together, restart, then refresh the browser. |
| Upload 403 | Add funds to the Forma account that issued the API key. |
| Upload 410 | The reference expired or was removed. Use a new run number only for an intentional new generation. |
| Upload 413 | Reduce the media size or free Forma library storage; also check your proxy upload limit. |
| 401 | Save an active key in **Settings → Forma → API key**. For environment-managed keys, update the backend configuration and restart ComfyUI. |
| 402 | Add funds to the same Forma account that issued the key. |
| 409 or price-cap error | Review account state and your cost ceiling; keep the run number unchanged when retrying. |
| 429 | Wait briefly, then retry with the same run number. |
| No API keys in Forma | Sign in and open **Account settings → API keys**. Contact support if the section is missing. |
| `UNKNOWN` | Check the job in Forma or contact support; do not buy a replacement automatically. |

## License

[MIT](LICENSE), copyright 2026 Michal Vavak. The license covers this node package; Forma service usage and provider models retain their own terms.

## Contributing and support

Read [CONTRIBUTING.md](CONTRIBUTING.md), [CHANGELOG.md](CHANGELOG.md), and [SECURITY.md](SECURITY.md). Report reproducible node bugs through [GitHub Issues](https://github.com/vavo/runpod-endpoints-comfy/issues), with credentials, signed URLs, and private prompts removed.

The initial package was extracted from Forma's tested integration. Client unit tests cover request recovery, spending caps, terminal states, interruption, HTTPS configuration, redirect credential handling, and sanitized errors. ComfyUI verification uses synthetic media and mocked inference, plus a live quote-only check on the installed pod. See [verification results](docs/verification.md). No paid provider generation was run for this update.

---

Part of [Lora Pilot family](https://github.com/vavo/lora-pilot).
