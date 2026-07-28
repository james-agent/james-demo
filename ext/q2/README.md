# Q2 Helix connection package

Exclusive owner: **q2-authentication**. Other agents only **run**
`python3 scripts/q2_gate_check.py`; they must not edit this package.

## Authentication

- HTTP Basic Auth on every request (`Authorization: Basic base64(api_key:api_secret)`)
- Username = API Key, Password = API Secret
- Docs: https://docs.helix.q2.com/reference/authentication

## Environments

| Environment | Base URL |
|-------------|---------|
| Sandbox | `https://sandbox-api.helix.q2.com` |
| Production | `https://api.helix.q2.com` |

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
