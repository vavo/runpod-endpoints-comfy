# Changelog

## 0.4.0 — 2026-10-19

- Add Check price and a USD quote display to both model-selecting nodes, with spending-cap comparison and stale-price detection.
- Quote checks never queue a graph or submit inference; local reference reads are restricted to the ComfyUI input folder and protected by the existing same-origin checks.
- Add eight canvas workflows with connected native media loaders, including a standalone image-to-video workflow and two Load Image nodes for first/last-frame video.
- Update media API templates with native loaders and preserve saved Forma links when dynamic controls rebuild.


## [0.3.0] - 2026-10-19

- Added native workflow/model selectors for all 39 Forma balance-enabled image/video models, with model-specific controls and ten workflow modes.
- Added local IMAGE, VIDEO and AUDIO reference uploads, multi-image batches, first/last-frame inputs and reusable Forma reference outputs.
- Bound upload retries to content and run number; preserved per-generation caps, recovery and credential protections.
- Added selectable editor/API starter workflows and API examples for every supported mode. Legacy nodes/workflows remain compatible.
- Speech, voice cloning and text catalog models remain unavailable until Forma implements their account-balance billing.

## [0.2.3] - 2026-10-17

- Identify API and download requests with a Forma ComfyUI user agent so the API edge accepts the client instead of rejecting Python’s default user agent with HTTP 403.
- Cover request identification and credential-free storage downloads in client tests.

## [0.2.2] - 2026-10-17

- Accept the exact RunPod proxy origin derived from trusted pod configuration, plus explicitly configured reverse-proxy origins. Reject other pods/ports and untrusted forwarded headers.
- Return readable JSON errors when origin checks fail.

## [0.2.1] - 2026-10-17

- Register the Forma settings panel through the compatible settings API so it also appears on older hosted ComfyUI frontends.

## [0.2.0] - 2026-10-17

- Added Settings → Forma with a masked key field, Save and test key, and Remove saved key.
- Keys persist privately on the ComfyUI server, outside workflow JSON, normal settings and browser storage. Saving validates access without spending credits and takes effect without restarting.
- Preserved environment/key-file configuration with host-managed precedence. Added same-origin write protection, bounded input, restrictive file permissions and credential lifecycle tests.
- Updated starter workflow instructions and declared the existing ComfyUI aiohttp dependency.

## [0.1.0] - 2026-10-17

### Added

- Reusable Forma API Key Setup text node, placed beside the starter workflow with account/key/funding and credential safety instructions.

- Standalone ComfyUI custom-node package using a Forma account and existing prepaid balance.
- Seedream 4.0 image generation and Pruna Video animation, with standard IMAGE and VIDEO outputs.
- Editor and API-format image-to-video workflows using built-in Save Image and Save Video nodes.
- Per-node quote checks and spending ceilings, stable request recovery, and interruptible polling.
- Environment/key-file authentication, HTTPS validation, credential-free storage redirects, and bounded downloads.
- Package metadata, dependency manifest, sponsor links, installation and security documentation, client tests, and CI.

### Compatibility

- Preserves `FormaSeedreamImage`, `FormaPrunaAnimate`, and `FORMA_IMAGE` from the original Forma integration.
- Requires a deployed Forma API v1 and current ComfyUI native video support.
- Registry publication and live Forma activation are separate from this source release.
