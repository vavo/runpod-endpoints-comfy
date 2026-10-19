# Workflow examples

In ComfyUI, open **Templates → Extensions → runpod-endpoints-comfy** and click a workflow card. All ten modes below and both image-generation-to-video starters are installed with the custom nodes; users do not need to copy JSON files. After updating the package, restart ComfyUI and refresh the browser. Save an edited workflow normally to keep a personal copy.

Open `choose-model-image-to-video.json` on the ComfyUI canvas for the selectable starter. The original `image-to-video.json` keeps the legacy fixed-model nodes.

For your own image, open **[image-to-video-local.json](image-to-video-local.json)**. It contains Load Image → Forma Video → Save Video, with no image-generation node. Upload/select the image, choose your model, click **Check price**, review the spending limit, then Run.

All ten supported modes have a ready-wired **canvas** workflow. T2I and T2V need only a prompt; choose a model, click **Check price**, review the spending limit, then Run.

| Workflow | File | Connected loaders |
| --- | --- | --- |
| Text to image | [text-to-image.json](text-to-image.json) | None; Forma Image → Save Image |
| Text to video | [text-to-video.json](text-to-video.json) | None; Forma Video → Save Video |
| Image to video | [image-to-video-local.json](image-to-video-local.json) | Load Image |
| Image editing | [image-to-image-local.json](image-to-image-local.json) | Load Image |
| First/last frames | [first-last-frame-to-video-local.json](first-last-frame-to-video-local.json) | Two Load Image nodes |
| Reference video | [reference-to-video-local.json](reference-to-video-local.json) | Load Image |
| Talking portrait | [talking-portrait-local.json](talking-portrait-local.json) | Load Image + Load Audio |
| Motion transfer | [motion-transfer-local.json](motion-transfer-local.json) | Load Image + Load Video |
| Audio to video | [audio-to-video-local.json](audio-to-video-local.json) | Load Audio |
| Video editing | [video-to-video-local.json](video-to-video-local.json) | Load Video |

For media-based modes, choose your own file in each loader. Image lists accept a single image from the supplied loader; connect a supported image batch for more references when running. Check price supports direct loaders and literal references; it never runs preprocessing or generation nodes.

The files in `api/` are **API-format graphs** for ComfyUI's `/prompt` endpoint, not editor-format canvas files. They are kept in a subfolder so ComfyUI does not list them as canvas templates. Replace each `choose-your-…` filename with a file uploaded to ComfyUI before submitting. Media workflows include connected native loaders. For duration-priced workflows, use an owned uploaded reference so Forma can measure it. Review prompts, model controls and spending caps; these examples do not bypass billing.

| Mode | API template |
| --- | --- |
| text-to-image | [text-to-image-catalog-api.json](api/text-to-image-catalog-api.json) |
| image-to-image | [image-to-image-catalog-api.json](api/image-to-image-catalog-api.json) |
| text-to-video | [text-to-video-catalog-api.json](api/text-to-video-catalog-api.json) |
| image-to-video | [image-to-video-catalog-api.json](api/image-to-video-catalog-api.json) |
| first-last-frame-to-video | [first-last-frame-to-video-catalog-api.json](api/first-last-frame-to-video-catalog-api.json) |
| reference-to-video | [reference-to-video-catalog-api.json](api/reference-to-video-catalog-api.json) |
| video-to-video | [video-to-video-catalog-api.json](api/video-to-video-catalog-api.json) |
| audio-to-video | [audio-to-video-catalog-api.json](api/audio-to-video-catalog-api.json) |
| talking-portrait | [talking-portrait-catalog-api.json](api/talking-portrait-catalog-api.json) |
| motion-transfer | [motion-transfer-catalog-api.json](api/motion-transfer-catalog-api.json) |

In the editor, select **Local** on a media input to connect a standard Load Image, Load Video, or Load Audio node. Select **Reference** to reuse a Forma output. Image batches can supply multi-reference fields; audio/video list fields currently accept one clip. Use the built-in save nodes to retain outputs locally.

The same two generic generation nodes cover all these workflows; you do not need a separate node for each model. Changing the selector rebuilds the controls, so check connections afterward.
