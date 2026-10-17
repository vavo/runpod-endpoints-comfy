# Security

## Credentials and account authority

A Forma API key can spend the issuing account's available balance and retrieve its creations. Store it in the ComfyUI backend environment or a restricted file outside the repository. Never include it in workflows, screenshots, issues, logs or commits. Revoke exposed keys in Forma Account settings.

One ComfyUI process uses one configured Forma account. Everyone able to queue these nodes can spend that account's balance. Installed plugins share the same process and can access its environment; use a trusted, separate instance for each account.

The node's cost ceiling is a per-request guard, not an account-level spending budget. Image and video are separately charged. Interrupting a workflow does not cancel remote generation. Retry the same settings and run number to recover an existing job.

The default API endpoint is HTTPS. Endpoint overrides are trusted operator configuration. Automatic redirects are disabled; signed media redirects never receive the Forma Authorization header. Downloads have MIME and size checks. Previously issued signed URLs retain their normal expiry after key revocation.

## Reporting

Do not post credentials or exploitable security details in public issues. Use the repository's **Security → Report a vulnerability** option when available. Otherwise contact the maintainer through their [GitHub profile](https://github.com/vavo) to arrange a private report.

Include the affected version, minimal reproduction, expected versus observed behavior, and impact. Redact keys, private prompts and signed media URLs.
