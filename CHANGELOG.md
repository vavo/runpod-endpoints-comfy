# Changelog

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
