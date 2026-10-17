# Forma API used by these nodes

Default base: `https://forma.cam/api/v1`. Every request uses `Authorization: Bearer <FORMA_API_KEY>`. Browser cookies and RunPod provider keys are not used.

| Request | Purpose |
| --- | --- |
| GET `/wallet` | Account identity and available balance |
| GET `/requests/:requestId` | Recover the account's existing generation |
| POST `/quotes` | Price validated model inputs in USD cents |
| POST `/jobs` | Submit an owned quote with `maxCostCents` |
| GET `/jobs/:jobId` | Poll the owned generation |
| GET `/jobs/:jobId/download` | Download output, possibly through a signed HTTPS redirect |

The client derives a stable request UUID from account, node ID, run number and generation options. It checks for an existing job before quoting or submitting. Changing only the cost ceiling leaves this identity unchanged.

Quotes use `requestId`, `modelId`, `kind`, `workflow`, `prompt`, and model-specific `inputs`. Submission uses `quoteId` and integer `maxCostCents`. The server validates prices, account ownership and balance; client settings do not grant access to someone else's assets.

The image node submits `seedream-v4-t2i` / `text-to-image`. Animation submits `p-video` / `image-to-video` with `image: asset:<owned-image-job-id>`. Output image editing does not alter this server-side reference.

`COMPLETED` is ready to download. The client polls `SUBMITTING`, `IN_QUEUE` and `IN_PROGRESS`. `FAILED`, `CANCELLED`, `TIMED_OUT` and `UNKNOWN` stop the client. An `UNKNOWN` submission may already exist at the provider and retains reserved funds; it must not trigger an automatic replacement purchase.

Download redirects receive no Forma authorization header. A signed media URL is itself a temporary bearer capability. Keep it out of public logs and issue reports.

The deployed Forma API is authoritative for availability, model pricing, rate limits and account state. This repository contains the client only.
