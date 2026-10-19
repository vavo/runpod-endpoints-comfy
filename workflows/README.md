# Workflow examples

Open `choose-model-image-to-video.json` on the ComfyUI canvas for the selectable starter. The original `image-to-video.json` keeps the legacy fixed-model nodes.

The following files are **API-format graphs** for ComfyUI's `/prompt` endpoint, not editor-format canvas files. Replace example HTTPS references with your own owned asset references or media URLs before submitting. For duration-priced workflows, use an owned uploaded reference so Forma can measure it. Review prompts, model controls and spending caps; these examples do not bypass billing.

| Mode | API template |
| --- | --- |
| text-to-image | [text-to-image-catalog-api.json](text-to-image-catalog-api.json) |
| image-to-image | [image-to-image-catalog-api.json](image-to-image-catalog-api.json) |
| text-to-video | [text-to-video-catalog-api.json](text-to-video-catalog-api.json) |
| image-to-video | [image-to-video-catalog-api.json](image-to-video-catalog-api.json) |
| first-last-frame-to-video | [first-last-frame-to-video-catalog-api.json](first-last-frame-to-video-catalog-api.json) |
| reference-to-video | [reference-to-video-catalog-api.json](reference-to-video-catalog-api.json) |
| video-to-video | [video-to-video-catalog-api.json](video-to-video-catalog-api.json) |
| audio-to-video | [audio-to-video-catalog-api.json](audio-to-video-catalog-api.json) |
| talking-portrait | [talking-portrait-catalog-api.json](talking-portrait-catalog-api.json) |
| motion-transfer | [motion-transfer-catalog-api.json](motion-transfer-catalog-api.json) |

In the editor, select **Local** on a media input to connect a standard Load Image, Load Video, or Load Audio node. Select **Reference** to reuse a Forma output. Image batches can supply multi-reference fields; audio/video list fields currently accept one clip. Use the built-in save nodes to retain outputs locally.

The same two generic generation nodes cover all these workflows; you do not need a separate node for each model. Changing the selector rebuilds the controls, so check connections afterward.
