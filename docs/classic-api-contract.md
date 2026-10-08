# MuPiBox Home Assistant API v1 — normative interoperability contract

**Status:** Protocol specification / implementation target, **NOT** a claim that Classic or NG already implements it. **Applies to:** MuPiBox Classic, MuPiBox NG, and the Home Assistant `mupibox` integration. **Version:** 1.0.0 (2026-10-08). **Language:** English for unambiguous machine/AI consumption. **Keywords:** MUST, MUST NOT, SHOULD and MAY have the meanings of RFC 2119.

> **AI/developer instruction:** Treat this file as the canonical *target protocol*, not as evidence of currently deployed endpoints. Do not silently reinterpret JSON names, units, authentication semantics or error codes. If a feature is absent, expose it as unsupported rather than emulating success. Preserve the existing NG legacy path.

## 0. Current implementation status and compatibility (question 5)

- `MuPiBox-homeassistant` main, commit `5dd75b3`, manifest `0.3.4`: legacy NG HTTP integration works through `/api/health`, `/api/info`, `/api/status`, `/api/command` etc. Its original admin-session authentication remains unchanged.
- Existing HACS support includes `classic_contract.py`: explicit `generation=classic` discovery recognition and response-normalization helpers. **Classic enrollment currently aborts with `classic_pairing_not_supported`**; it does not yet authenticate or control Classic.
- Neither the HACS v1 pairing client nor a NG v1 endpoint is asserted to exist. No interoperable live v1 test target is available yet. Tests can use the schemas/examples in this document and a mock HTTPS endpoint until box implementations exist.
- Keep domain `mupibox`, NG config-entry unique IDs, registry entries, entity unique-ID suffixes, stored passwords, historical HTTP URLs, and NG upgrade/migration behavior unchanged. Existing installations MUST NOT require re-pairing. New v1 connections are opt-in and select the v1 adapter; NEVER probe and then silently overwrite a working legacy NG connection.

## 1. Discovery and identity

Both generations advertise DNS-SD service `_mupibox._tcp.local.` (TCP). TXT fields (`UTF-8`, DNS-SD TXT values) are:

```text
product=mupibox
generation=classic                  # or ng
api_version=1
id=7e1f82a4-55ab-47d7-8b60-02e8dff65b90  # optional backward-compatible NG field
device_id=7e1f82a4-55ab-47d7-8b60-02e8dff65b90
pairing=required
transport=https
```

Port in SRV record is the **actual** TLS listener; SRV target is the advertised local hostname. TXT MUST NOT include codes, passwords, tokens, fingerprints treated as trustworthy, or private keys. `device_id` MUST be a persistent UUID (same across IP changes/reboots/updates). `generation` MUST equal `classic` or `ng` for a new v1-capable box; absence of `generation` is **legacy NG** for backwards compatibility. A Classic box MUST NOT advertise `generation=ng`. Zero-conf discovery is an untrusted hint, not authentication. Manual hostname/IP entry MUST be available for networks without multicast bridging.

`GET /api/ha/v1/info` is the authoritative **authenticated** source for device identity. Home Assistant MUST verify it matches discovered `device_id` and expected generation, and MUST NOT merge identities solely from IP or display name.

## 2. HTTPS identity and trust (question 2)

**All new v1 endpoints MUST use HTTPS** with TLS 1.2+ (TLS 1.3 preferred). Plain HTTP MUST NOT accept v1 pairing codes, access tokens or state-changing commands. Box-created private CA certificates are supported, but the integration MUST NOT install that CA into Home Assistant's global OS trust store or disable certificate checking for normal operation.

**Trust-on-first-pairing with out-of-band confirmation and SHA-256 SPKI pin:**

1. Client discovers the box and opens a TLS connection solely to inspect the presented leaf certificate and its public key (no secret/code/Authorization header is sent yet). An untrusted self-signed/private-CA chain is allowed **only for this inspection step**.
2. Compute SHA-256 of DER-encoded SubjectPublicKeyInfo of the **leaf public key**; encode as lowercase hex (64 chars). Call this `spki_sha256` (NOT certificate DER fingerprint and NOT CA fingerprint).
3. Box displays the identical fingerprint via a trusted local screen/admin UI, alongside hostname/identity. User MUST compare and explicitly accept the matching values in Home Assistant; mDNS data alone is insufficient. Never auto-accept the first network fingerprint.
4. Save the accepted pin **per persistent device ID**. Every subsequent HTTPS request MUST validate the server key against the saved pin and validate protocol TLS normally. Do not suppress hostname verification or blindly trust all keys; a carefully scoped custom TLS verifier may substitute the pinned key for an otherwise untrusted CA, but MUST reject different keys.
5. A certificate renewal with the same SPKI continues working; a key change MUST stop requests before secrets are sent and require explicit re-approval using a new trusted out-of-band comparison.

If the user instead provisions and verifies a trusted box CA through a **dedicated per-device/per-integration CA bundle**, that is an acceptable alternative. The implementation MUST document which mode is active; never silently fall back from validated trust to insecure HTTP or nonvalidated HTTPS. Certificate validity and trust policy (including expiration and SAN/hostname behavior) MUST be documented and consistently enforced. Legacy NG HTTP and HTTPS settings remain untouched.

## 3. Auth and pairing (question 1)

All JSON requests/responses are UTF-8 with `Content-Type: application/json`. Paths below are relative to `https://<box-host>:<advertised-port>/api/ha/v1`. Pairing requires **locally initiated approval** via display or local administrative action; arbitrary unauthenticated callers cannot force an unattended pairing display. Client generates persistent random UUID `client_id`, not a password.

### POST `/pair/start`

```json
{
  "client_name": "Home Assistant",
  "client_id": "ha-8c4c4f52-6e35-44dd-930a-bdb838cd60d8",
  "requested_scopes": ["read", "control"]
}
```

Successful response `200 OK` (only after local approval, or approval explicitly enabled for a short local window):

```json
{
  "pairing_id": "fbf1144d-a7e8-47fa-b9c6-803753a2e384",
  "expires_in": 300,
  "code_length": 6,
  "confirmation": "display_code"
}
```

The box displays a random **six-digit** code preserving leading zeros. **The code MUST NOT appear in API responses, logs, mDNS, or telemetry.** `expires_in` is seconds, maximum 300 from issuance; the UI clearly indicates expiration. One active pairing attempt per box; another start MUST NOT silently replace a pending attempt: respond `409 pairing_in_progress` (local user may cancel and restart). Each `pairing_id` has at most **five failed confirm attempts**; after that invalidate it and enforce a cooldown. Rate-limit starts per box and attempts across source addresses. Pairing identifiers are unpredictable, single-use, and never credentials by themselves.

### POST `/pair/confirm`

```json
{
  "pairing_id": "fbf1144d-a7e8-47fa-b9c6-803753a2e384",
  "client_id": "ha-8c4c4f52-6e35-44dd-930a-bdb838cd60d8",
  "code": "482913"
}
```

Successful response `200 OK`:

```json
{
  "success": true,
  "access_token": "GENERATED_SECRET",
  "token_type": "Bearer",
  "scopes": ["read", "control"],
  "device_id": "7e1f82a4-55ab-47d7-8b60-02e8dff65b90"
}
```

Tokens MUST contain >=256 bits from a CSPRNG, be treated as secrets and stored hashed/protected server-side and in HA credential storage; they remain valid until explicitly revoked (or rotated), not until box reboot. `client_id` MUST equal the start request. The code MUST be checked with constant-time comparison after normalizing only documented whitespace, and invalidated immediately on success/expiry/cancel/max attempts. Client MUST verify returned `device_id` against the confirmed TLS trust and discovered identity before saving the credential. Requested scopes MUST be displayed on the device; server grants only explicitly locally approved scopes and returns the **actual** grant. A client MUST NOT assume all requested scopes were granted.

### `POST /pair/revoke`

Authenticated using bearer token; payload `{ "client_id": "ha-8c4c4f52-6e35-44dd-930a-bdb838cd60d8" }`. Clients MAY revoke **their own** token; local admin UI can revoke any client. Success is `{ "success": true }`; token must stop working immediately. Granting new scopes requires fresh local approval/re-pairing; no silent privilege escalation. A client can re-pair after revocation. `GET /pair/clients` and admin-only remote revocation are NOT required by v1.

## 4. Permissions (question 3)

**One independently revocable bearer token per client installation, with scopes** (not two tokens). Scope meanings:

| Scope | Permits |
|---|---|
| `read` | `/info`, `/state`, `/media/cover/current`, status endpoints |
| `control` | play/pause/stop/next/previous/seek/set_volume/mute/unmute |
| `notify` | spoken or on-screen notifications, when implemented |
| `power` | reboot and shutdown |
| `admin` | other maintenance functions, if explicitly implemented |

Default request is `["read","control"]`. `notify`, `power`, and `admin` need explicit consent on box display and MUST NOT be implicitly granted by `control`. Every endpoint validates scope server-side. All protected requests use `Authorization: Bearer <access_token>` over verified HTTPS; no token in query strings. An unpaired client can access only the minimal `/health`, pairing actions, and TLS inspection path. Successful commands are not proof of expanded privilege.

## 5. Endpoint wire contract

### `GET /health` (unauthenticated; minimal only)

```json
{"ok":true,"api_version":1}
```

### `GET /info` (`read`)

```json
{
  "api_version": 1,
  "device_id": "7e1f82a4-55ab-47d7-8b60-02e8dff65b90",
  "name": "MuPiBox Kinderzimmer",
  "product": "mupibox",
  "generation": "classic",
  "software_version": "EXAMPLE_ONLY",
  "manufacturer": "MuPiBox",
  "model": "MuPiBox Classic",
  "capabilities": ["play", "pause", "stop", "next", "previous", "set_volume", "mute", "seek", "media_metadata"]
}
```

### `GET /state` (`read`)

```json
{
  "playback": {
    "state": "playing",
    "provider": "spotify",
    "title": "Example title",
    "artist": "Example artist",
    "album": "Example album",
    "media_id": null,
    "duration": 235,
    "position": 68,
    "cover_url": "/api/ha/v1/media/cover/current",
    "volume": 42,
    "muted": false
  },
  "device": {
    "battery_percent": null,
    "charging": null,
    "wifi_signal_dbm": -56,
    "ip_address": "192.0.2.10",
    "uptime_seconds": 14622
  }
}
```

`playback.state` is one of `playing`, `paused`, `idle`, `buffering`, `unavailable`. Duration/position are in **seconds**, volume is **integer 0–100**; unavailable measurements are JSON `null`, never fabricated. Status MUST describe real playback regardless of initiating source (touch, RFID, hardware buttons, Spotify Connect, HA). `cover_url` MUST be a same-device relative URL or validated absolute HTTPS URL; it MUST NOT embed secrets. `/media/cover/current` requires `read`. Capabilities accurately describe functioning methods (e.g. `set_volume`, not `volume`). Unsupported capabilities MUST NOT be exposed as functional entities or controls.

### `POST /control` (`control`, or `power` for reboot/shutdown)

```json
{"command":"pause"}
```

```json
{"command":"set_volume","value":35}
```

```json
{"command":"seek","position":90}
```

Allowed `command`: `play`, `pause`, `stop`, `next`, `previous`, `set_volume`, `mute`, `unmute`, `seek`, `restart`, `shutdown`. Position is seconds; volume is 0–100. `restart` / `shutdown` MUST require `power`, even when `control` is present. Unknown or unadvertised commands MUST fail; no false-success responses. On accepted completed action return HTTP 200 `{ "success": true }`. On an asynchronous action the server MAY return 202 `{ "success": true, "accepted": true }` but MUST NOT claim execution completed.

## 6. Consistent errors (question 4)

Any unsuccessful API response MUST use this body (never raw HTML or traceback):

```json
{
  "success": false,
  "error": "invalid_value",
  "message": "Volume must be between 0 and 100"
}
```

`error` is stable machine-readable ASCII snake_case; `message` is human-readable diagnostic, no secrets or internal paths. HTTP status has normative meaning:

| HTTP | error | Meaning |
|---|---|---|
| 400 | `invalid_request` | Malformed JSON/missing fields |
| 400 | `invalid_value` | Wrong type/range |
| 401 | `unauthorized` | Missing/invalid/revoked token |
| 403 | `insufficient_scope` | Authenticated but missing scope |
| 403 | `pairing_not_enabled` | Local pairing not enabled |
| 403 | `invalid_pairing_code` | Incorrect code (avoid exposing validity details) |
| 404 | `not_found` | Unknown path/resource |
| 409 | `pairing_in_progress` | Another pending pairing |
| 409 | `provider_unavailable` | Provider cannot execute command |
| 410 | `pairing_expired` | Expired/invalidated pairing transaction |
| 422 | `unsupported_command` | Not supported/advertised |
| 429 | `rate_limited` | Too many attempts; add `Retry-After` header |
| 500 | `internal_error` | Unexpected failure |
| 503 | `temporarily_unavailable` | Device/player temporarily offline |

On TLS pin mismatch the client MUST reject the connection **before any HTTP request** rather than treating it as an API error. All clients MUST handle non-2xx codes and SHOULD show `message` while basing logic on `error`.

## 7. Optional real-time events

`GET /events` MAY offer authenticated HTTPS WebSocket (`wss://.../api/ha/v1/events`, `read` scope); full-state polling MUST work even without WebSockets. Event example:

```json
{"event":"playback_changed","sequence":1024,"data":{"state":"playing","title":"Example","position":23,"volume":35}}
```

Events MUST NOT contain credentials. On reconnect, clients re-fetch `/state`; maintain heartbeats and avoid assuming events were delivered while disconnected.

## 8. Acceptance checklist / tests for both Classic and NG

1. Two Classic devices and one NG device discovered under one service, each with unique persistent identity; legacy NG advertisements without `generation` still work.
2. Manual host/IP setup works when multicast is unavailable.
3. HTTPS first-contact verification requires matching out-of-band SPKI fingerprint, and fails closed on key mismatch.
4. Pairing cannot be remotely forced; six-digit code (including leading zero) works exactly once for <=300 s; wrong code fails; sixth incorrect attempt is impossible; throttling applies across source IPs.
5. Scope grant matches local approval; `control` token cannot call `restart`, `shutdown` or `admin` routes; revocation takes effect immediately.
6. JSON errors, HTTP statuses and secure command validation match this document.
7. `/state` reflects touchscreen/RFID/Spotify changes; missing hardware metrics are null, not zeros.
8. IP change, reboot, reconnect and certificate renewal with same SPKI preserve configuration; different SPKI requires approval.
9. Existing NG HACS config entries, entity IDs, automations and legacy admin credentials remain unchanged after installing integration updates.
10. Run tests against a mocked v1 server first, then against both actual generations; do not declare interoperability until both pass.

## 9. Ownership and release gate

Classic maintainer: implement advertisement, TLS identity display, pairing/token/scopes, API routes, actual status/control. NG maintainer: implement compatible v1 adapter **in addition** to legacy endpoints. HACS maintainer: implement TLS pinning, v1 onboarding/token storage and per-generation adapter. Classic discovery stays blocked in HACS until the pairing/client implementation is complete and tested. **This document is the agreed target protocol, not a report of delivered runtime functionality.**
