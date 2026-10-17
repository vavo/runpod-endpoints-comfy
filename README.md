# RunPod Endpoints for ComfyUI

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee-vavo-5F7FFF?style=for-the-badge&logo=buy-me-a-coffee&logoColor=white)](https://www.buymeacoffee.com/vavo) [![Sponsor on GitHub](https://img.shields.io/badge/Sponsor%20on-GitHub-24292F?style=for-the-badge&logo=github)](https://github.com/sponsors/vavo) [![Support on Patreon](https://img.shields.io/badge/Support%20on-Patreon-FF424D?style=for-the-badge&logo=patreon&logoColor=white)](https://www.patreon.com/vavo)

**Cloud image and video generation through [Forma](https://forma.cam), using your Forma account balance.**

Generate an image with Seedream 4.0, then animate it with Pruna Video using your Forma account balance. Inference runs through Forma; no local model weights or GPU inference are needed by these nodes.

## Installation

Requires Python 3.10+ and a current ComfyUI installation with native `VIDEO` and `SaveVideo` support. Inference runs in the cloud; these nodes do not require a local inference GPU. ComfyUI still needs its normal Python dependencies and must be able to reach Forma over HTTPS.

Forma API keys and account top-ups are available at [forma.cam](https://forma.cam).

### Manual install

From your ComfyUI directory:

```sh
git clone https://github.com/vavo/runpod-endpoints-comfy.git custom_nodes/runpod-endpoints-comfy
python -m pip install -r custom_nodes/runpod-endpoints-comfy/requirements.txt
```

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

The settings interface requires HTTPS for remote hosts; localhost HTTP is supported. A saved key lives in `.forma/api.key` beside ComfyUI's resolved user directory, outside the HTTP-accessible user-data folders. The directory is restricted to its owner and the file uses mode 0600 on POSIX systems. It is not encrypted against the server owner or other installed plugins. It is never written to browser local storage, normal ComfyUI settings, or workflow JSON. Everyone using that ComfyUI process uses the same Forma account; use a separate instance for each customer account. The host must permit installing custom nodes and making outbound HTTPS requests. This package has not been approved or published for any managed ComfyUI marketplace.

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

## Included workflow

Open [image-to-video.json](workflows/image-to-video.json) on the ComfyUI canvas:

```text
Forma · Generate Image ── IMAGE ─────────── Save Image
                       └─ FORMA_IMAGE ─── Forma · Animate Image ── VIDEO ── Save Video
```

The [API-format workflow](workflows/image-to-video-api.json) is for ComfyUI's `/prompt` endpoint. Both workflows use the same two generation nodes plus the setup instructions node, followed by ComfyUI's built-in save nodes.

## Controls and charging

- **Forma · API Key Setup:** a reusable instructions text node in the Forma category. It explains account creation, one-time key creation, funding, backend environment setup, and key safety. It makes no API calls and needs no connection. The starter workflow places it first; never paste your key into its text box.

- **Forma · Generate Image:** prompt, negative prompt, size, seed, run number, and maximum image cost in USD cents. Outputs a standard `IMAGE` plus a `FORMA_IMAGE` reference.
- **Forma · Animate Image:** takes the `FORMA_IMAGE` reference directly. Controls include motion prompt, duration (1–10 seconds), resolution, frame rate, draft mode, audio output, prompt upsampling, seed, run number, and maximum video cost. Outputs native `VIDEO` for Save Video or further processing.
- A `FORMA_IMAGE` refers to the original image stored in your Forma account. Editing the standard `IMAGE` output does not change that reference. Uploading an arbitrary local/edited image is outside this first version.
- Each node obtains a server quote before submitting. Default caps are 10 cents for the image and 25 cents for the video; these are spending ceilings, not advertised prices. Requests use paid balance, not website trials. Forma applies your account's safety preference.
- If a quote exceeds the cap or the balance is insufficient, the node stops before inference. Each stage is billed separately: an image that completed remains charged if animation fails or exceeds its cap.

### Retry without another charge

The account, node ID, generation settings, and **run_number** determine a stable request ID. Queueing unchanged settings again recovers the same job, including after a timeout, restart, or key rotation within the same account. Changing only the spending cap does not create another generation.

Increase **run_number** to intentionally buy another generation with the same settings. Changing the prompt, seed, settings, source image, or node ID also produces a new request. Keep run numbers fixed while recovering an interrupted workflow; do not automatically increment them after each queue.

Completed results can be cached by ComfyUI. The native Save nodes remain responsible for durable local copies. Forma library expiry still applies; an expired result cannot be recovered by changing a spending cap.

Polling waits up to 30 minutes, then stops locally. Interrupting ComfyUI stops waiting; it does not cancel remote inference or promise a refund. Retry the same run number to recover. `UNKNOWN` means the provider submission could not be confirmed: funds remain reserved, and the user must check the job in Forma or contact support. The client never automatically buys a replacement.

## Development

`FORMA_API_URL` defaults to `https://forma.cam/api/v1`. Override it only in the server environment for development; remote URLs require HTTPS, while localhost allows HTTP. This URL is not a graph input. The Forma server must have API-key support deployed before this package can use it.

```sh
python3 -m unittest discover -s tests -v
```

`workflows/image-to-video-api.json` is the headless ComfyUI `/prompt` graph; `image-to-video.json` is the editor graph. See [the client API contract](docs/api.md) for the HTTP contract used by these nodes.


## Troubleshooting

| Symptom | Check |
| --- | --- |
| Missing Forma nodes | Check the startup log, the custom-node folder location, and dependencies in ComfyUI's Python environment. |
| Missing `VIDEO` / `SaveVideo` | Update ComfyUI to a version with native video support. |
| 401 | Configure an active Forma key in the backend process and restart it. |
| 402 | Add funds to the same Forma account that issued the key. |
| 409 or price-cap error | Review account state and your cost ceiling; keep the run number unchanged when retrying. |
| 429 | Wait briefly, then retry with the same run number. |
| No API keys in Forma | The required backend rollout is not available for your account yet. |
| `UNKNOWN` | Check the job in Forma or contact support; do not buy a replacement automatically. |

## License

[MIT](LICENSE), copyright 2026 Michal Vavak. The license covers this node package; Forma service usage and provider models retain their own terms.

## Contributing and support

Read [CONTRIBUTING.md](CONTRIBUTING.md), [CHANGELOG.md](CHANGELOG.md), and [SECURITY.md](SECURITY.md). Report reproducible node bugs through [GitHub Issues](https://github.com/vavo/runpod-endpoints-comfy/issues), with credentials, signed URLs, and private prompts removed.

The initial package was extracted from Forma's tested integration. Client unit tests cover request recovery, spending caps, terminal states, interruption, HTTPS configuration, redirect credential handling, and sanitized errors. Local ComfyUI verification uses synthetic media and mocked inference; it does not certify live provider output or production deployment.

---

Part of [Lora Pilot family](https://github.com/vavo/lora-pilot).
