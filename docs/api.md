# Forma API used by these nodes

Default base: `https://forma.cam/api/v1`. Every request uses `Authorization: Bearer <FORMA_API_KEY>`. Browser cookies and RunPod provider keys are not used.

| Request | Purpose |
| --- | --- |
| GET `/wallet` | Account identity and available balance |
| GET `/requests/:requestId` | Recover the account's existing generation |
| POST `/uploads` | Upload raw reference bytes with media Content-Type and stable X-Upload-Id UUID |
| POST `/quotes` | Price validated model inputs in USD cents |
| POST `/jobs` | Submit an owned quote with `maxCostCents` |
| GET `/jobs/:jobId` | Poll the owned generation |
| GET `/jobs/:jobId/download` | Download output, possibly through a signed HTTPS redirect |

The client derives a stable request UUID from account, node ID, run number and generation options. It checks for an existing job before quoting or submitting. Changing only the cost ceiling leaves this identity unchanged.

Quotes use `requestId`, `modelId`, `kind`, `workflow`, `prompt`, and model-specific `inputs`. Submission uses `quoteId` and integer `maxCostCents`. The server validates prices, account ownership and balance; client settings do not grant access to someone else's assets.

The legacy image node submits `seedream-v4-t2i` / `text-to-image`. Animation submits `p-video` / `image-to-video` with `image: asset:<owned-image-job-id>`. Output image editing does not alter this server-side reference.

`COMPLETED` is ready to download. The client polls `SUBMITTING`, `IN_QUEUE` and `IN_PROGRESS`. `FAILED`, `CANCELLED`, `TIMED_OUT` and `UNKNOWN` stop the client. An `UNKNOWN` submission may already exist at the provider and retains reserved funds; it must not trigger an automatic replacement purchase.

Download redirects receive no Forma authorization header. A signed media URL is itself a temporary bearer capability. Keep it out of public logs and issue reports.

The deployed Forma API is authoritative for availability, model pricing, rate limits and account state. This repository contains the client only.

## Catalog nodes and uploads

`FormaImage` and `FormaVideo` use native V3 dynamic inputs. In API-format graphs the selectors are `workflow` and `workflow.model`, followed by flattened names such as `workflow.model.prompt` or `workflow.model.image.value`. A media selector uses `None`, `Reference` or `Local`; its `value` holds the reference string or a native ComfyUI link. See the bundled API examples for exact names.

The bundled `models.json` mirrors Forma's managed image/video catalog. Server quotes remain authoritative for availability, supported inputs and pricing. `first-last-frame-to-video` is a node selector alias that sends `image-to-video` with both frame inputs to Forma.

Uploads send raw PNG, MP4 or WAV bytes to `/uploads`, with `X-Upload-Id` derived from MIME type, SHA-256 of the bytes and run number. Forma scopes that UUID to the authenticated account and returns the same asset for identical retries; changed bytes under the same ID return 409 and removed/expired assets return 410. Reference uploads require a funded account, are limited to 128 MB and retain existing library quotas and retention. Uploads are not inference purchases. Never retry with a new run number automatically.
