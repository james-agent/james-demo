# Q2 Helix connection package

Exclusive owner: **q2-authentication**. Other agents only **run**
`python3 scripts/q2_gate_check.py`; they must not edit this package.

## Modules

| Module | Responsibility |
|--------|----------------|
| `config.py` | `get_q2_config()` — load `Q2_HELIX_*` from env / `.env` |
| `client.py` | `HelixClient` / `get_helix_client()` — Basic Auth HTTP facade |
| `scripts/q2_gate_check.py` | CLI gate: PASS / CONFIG_ERROR / API_BUSINESS_ERROR |

## Authentication

- HTTP Basic Auth on every request (`Authorization: Basic base64(api_key:api_secret)`)
- Username = API Key, Password = API Secret
- Docs: https://docs.helix.q2.com/reference/authentication

## Environments

| Environment | Base URL |
|-------------|---------|
| Sandbox | `https://sandbox-api.helix.q2.com` |
| Production | `https://api.helix.q2.com` |

## Gate check

From the repository root (after copying `.env.example` → `.env` and filling secrets):

```bash
python3 scripts/q2_gate_check.py
```

## IP whitelisting (production)

Production (and often sandbox) requires your egress IP to be whitelisted with Q2.
A sandbox whitelist entry does **not** automatically apply to production and vice versa.
On HTTP 403, contact Q2/Helix support with the public IP of the calling host.

## Rate limiting

Helix may return HTTP 429 when limits are exceeded. Callers should back off and retry.
This client uses `httpx` connection pooling (`max_connections=20`, keepalive=10) to
reuse TCP connections and reduce handshake overhead.

## Security

- Store credentials only in `.env` / secrets manager — never in source or logs
- Middleware-only access — never call Helix from browser/frontend code
- Downstream code must import `get_helix_client()` / `get_q2_config()` only; do not recreate auth
