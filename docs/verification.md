# Verification — 2026-10-19

Version 0.4.1 (runtime revision `9e683e1`) was installed on the existing RunPod ComfyUI instance. The queue was empty before the service restart. Existing credentials and user workflows were preserved; eight new canvas examples were added under the user's `workflows/Forma` folder.

- 29 Python tests pass locally and on the pod. Coverage includes same-origin enforcement, request-size limits, error redaction, and rejecting file reads outside ComfyUI's input directory, including symlink escapes.
- Three JavaScript regression tests cover restoring saved Forma connections after dynamic input rebuilding, preserving existing connections, and leaving other node types untouched.
- All ten API templates validate against real ComfyUI schemas. Quote-only execution for all ten workflow types was exercised with native PNG/WAV/MP4 serialization and mocked Forma responses: ten quote requests, eleven reference uploads, zero job submissions.
- The standalone image-to-video canvas loads with Load Image already connected. A live browser price check using a synthetic reference returned $0.16 USD for Pruna Video, five seconds, 720p, 24 fps. The $0.25 limit remained unchanged. Changing duration marked the quote stale; restoring the settings and checking again returned $0.16.
- The wallet response was unchanged after the live checks and the ComfyUI queue remained empty. No paid inference was submitted. This confirms price-check behavior, not successful provider generation for every model.

Price checks may upload selected local references and use Forma library storage. They never execute upstream graph nodes. Saved/generated references must be selected through supported loaders or supplied as literal asset/HTTPS references.

## Native Templates menu

The installed pod lists 12 canvas templates under **Templates → Extensions → runpod-endpoints-comfy**: all ten modes plus the two image-generation-to-video starters. All 12 template URLs returned editor graphs; saved links passed validation against ComfyUI’s native template routes. Opening image-to-video directly from its template card restored Load Image → Forma Video → Save Video without importing a file. API-only graphs are kept in `workflows/api/` and excluded from the template list. README screenshots were captured separately in a clean local ComfyUI instance running the same package on 19 October 2026; no paid inference was submitted.
