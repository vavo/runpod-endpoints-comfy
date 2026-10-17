# Changelog

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
