# MuPiBox Home Assistant API v1 — normative interoperability contract

**Status:** Normative shared protocol plus versioned implementation notes. Classic support is an implementation target; NG/HACS features are listed only where inspected in source. **Applies to:** MuPiBox Classic, MuPiBox NG, and the Home Assistant `mupibox` integration. **Document revision:** 1.1.0 (2026-10-08). **Wire protocol:** `api_version=1` (unchanged; backwards-compatible feature additions). **Language:** English for unambiguous machine/AI consumption. **Keywords:** MUST, MUST NOT, SHOULD and MAY have the meanings of RFC 2119.

> **AI/developer instruction:** This is the normative shared protocol for Classic, NG and HACS. Implementation status is explicitly generation-specific; the specification alone does not prove a Classic feature is deployed. Do not silently reinterpret JSON names, units, authentication semantics or error codes. If a feature is absent, expose it as unsupported rather than emulating success. Preserve local NG compatibility, but do not re-enable retired HTTP onboarding.

## 0. Implementation status and compatibility (2026-10-08)

| Component | Verified source status | Required follow-up |
|---|---|---|
| NG | Secure API v1 over HTTPS :8443, separate trusted fingerprint in local Admin -> Smart Home, locally approved six-digit pairing, `read`/`control`/`notify`/`power` scopes and endpoints defined below. Local HTTP :8090 remains for box operation; insecure 8090 mDNS onboarding has been retired. | Verify the actual requested scopes are shown and approved locally, not only in the HA dialog. |
| HACS | `mupibox` v0.4.8: secure mDNS discovery, first-time fingerprint verification, scoped token pairing, **Configure** options flow to expand/reduce scopes without deleting the HA config entry, media controls, diagnostics, update sensor, output selection, screenshot, scoped notifications/power. | Cross-generation contract tests against Classic when Classic is ready. |
| Classic | This document specifies the target contract, **not** a confirmed Classic implementation or a claim that Classic can presently pair with this HACS release. | Implement and test the complete v1 discovery/trust/pairing/scope/endpoints profile and UI parity below before declaring compatibility. |

**Compatibility invariants:** Keep Home Assistant domain `mupibox`; stable `device_id`, config entry, HA device identity, registry entity IDs and automations during scope renewal. A new API-v1 integration MUST NOT offer legacy optional-admin-password pairing; local legacy NG endpoints may continue for device operation. Existing unrelated Classic and NG devices must not be removed or migrated automatically.

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

Port in SRV record is the **actual** TLS listener; SRV target is the advertised local hostname. TXT MUST NOT include codes, passwords, tokens, fingerprints treated as trustworthy, or private keys. `device_id` MUST be a persistent UUID (same across IP changes/reboots/updates). `generation` MUST equal `classic` or `ng` for v1-capable boxes. Advertisements lacking `generation` or `transport=https` are legacy hints only; the v1 HACS onboarding flow MUST NOT prompt for a legacy admin password or use HTTP. A Classic box MUST NOT advertise `generation=ng`. Zero-conf discovery is an untrusted hint, not authentication. Manual hostname/IP entry MUST be available for networks without multicast bridging.

`GET /api/ha/v1/info` is the authoritative **authenticated** source for device identity. Home Assistant MUST verify it matches discovered `device_id` and expected generation, and MUST NOT merge identities solely from IP or display name.

## 2. HTTPS identity and trust (question 2)

**All new v1 endpoints MUST use HTTPS** with TLS 1.2+ (TLS 1.3 preferred). Plain HTTP MUST NOT accept v1 pairing codes, access tokens or state-changing commands. Box-created private CA certificates are supported, but the integration MUST NOT install that CA into Home Assistant's global OS trust store or disable certificate checking for normal operation.

**Trust-on-first-pairing with out-of-band confirmation and SHA-256 SPKI pin:**

1. Client discovers the box and opens a TLS connection solely to inspect the presented leaf certificate and its public key (no secret/code/Authorization header is sent yet). An untrusted self-signed/private-CA chain is allowed **only for this inspection step**.
2. Compute SHA-256 of DER-encoded SubjectPublicKeyInfo of the **leaf public key**; encode as lowercase hex (64 chars). Call this `spki_sha256` (NOT certificate DER fingerprint and NOT CA fingerprint).
3. Box presents the identical fingerprint in an authenticated **local Admin -> Smart Home** interface (physical trusted display MAY additionally present it), alongside the device identity. Both Classic and NG MUST expose this explicitly in the local setup UI. The user compares and explicitly accepts the matching value in Home Assistant; mDNS data alone is insufficient. Never auto-accept the first network fingerprint. The **six-digit code** is displayed on the physical box only, after pairing starts; it is distinct from the fingerprint.
4. Save the accepted pin **per persistent device ID**. Every subsequent HTTPS request MUST validate the server key against the saved pin and validate protocol TLS normally. Do not suppress hostname verification or blindly trust all keys; a carefully scoped custom TLS verifier may substitute the pinned key for an otherwise untrusted CA, but MUST reject different keys.
5. A certificate renewal with the same SPKI continues working; a key change MUST stop requests before secrets are sent and require explicit re-approval using a new trusted out-of-band comparison.

If the user instead provisions and verifies a trusted box CA through a **dedicated per-device/per-integration CA bundle**, that is an acceptable alternative. The implementation MUST document which mode is active; never silently fall back from validated trust to insecure HTTP or nonvalidated HTTPS. Certificate validity and trust policy (including expiration and SAN/hostname behavior) MUST be documented and consistently enforced. Existing local NG HTTP behavior remains available for the box, but HTTP discovery/enrollment MUST NOT be offered in new HACS setups.

### 2.1. Classic/NG Admin fingerprint copying — required UX parity

Both generations MUST provide a clearly visible, monospaced **64-character lowercase hex SHA-256 SPKI fingerprint**, grouping characters for readability if desired, and a **"Copy fingerprint"** button. The copied value MUST contain exactly 64 hex characters, **without formatting spaces**, ready to paste in HA. It MUST NOT copy a CA fingerprint, TLS certificate DER fingerprint, pairing code or secret.

**Browser compatibility is mandatory:** Admin interfaces may be accessed via `http://<local-box>` and consequently run in an **insecure browser context** where `navigator.clipboard.writeText` is unavailable or rejected. Implement the following behavior in **both Classic and NG**:

1. When `navigator.clipboard.writeText` exists **and** `window.isSecureContext` is true, attempt it and await success.
2. Otherwise, or on rejection, use a temporary focusable text input/textarea containing the ungrouped fingerprint, select its entire content, and try the browser's synchronous `document.execCommand('copy')` compatibility fallback from the user click handler.
3. If both paths fail, visibly select the fingerprint on the page and tell the user to use Ctrl+C (or their platform's Copy action); never show a false "copied" success toast.
4. Keep the fingerprint manually selectable (`user-select:text`/`all`), readable on small and mobile screens, without clipping, and never require external scripts, internet access or permission to read clipboard contents.
5. Prefer HTTPS for Admin wherever feasible; browser-specific clipboard behavior MUST NOT prevent secure first pairing or scope renewal.

**Acceptance:** Test Chromium/Firefox desktop on local HTTP, an HTTPS secure context, and mobile browser behavior. Simulate missing `navigator.clipboard`, `writeText` rejection and `execCommand('copy')` failure. Verify copy value exactly matches the SPKI of the TLS leaf public key with case-insensitive HA normalization. Don't silently change fingerprint/key material to make copying easier.

## 3. Auth and pairing (question 1)

All JSON requests/responses are UTF-8 with `Content-Type: application/json`. Paths below are relative to `https://<box-host>:<advertised-port>/api/ha/v1`. Pairing requires **locally initiated approval** via display or local administrative action; arbitrary unauthenticated callers cannot force an unattended pairing display. Client generates a persistent random UUID `client_id`, not a password. A new device is discovered via mDNS and the user clicks **Add**; no manual address entry or separate HA "start pairing" button should be required. After fingerprint confirmation HA automatically issues `/pair/start` when local approval is active, then prompts for the code.

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

### In-place scope renewal (mandatory for both Classic and NG)

HA **Settings -> Devices & services -> MuPiBox -> Configure** MUST offer the current `notify` and `power` permissions, keeping `read` and `control` required. On user change, HA asks for fresh local approval and performs `/pair/start` and `/pair/confirm` with a **new `client_id` and locally displayed PIN**. The client MUST verify `device_id` and actual returned scopes, save the new scoped bearer credential **in the existing config entry**, reload the integration, and only then revoke the previous client token if possible. It MUST NOT delete/recreate the HA device or reset entity IDs, dashboard cards and automations. Failure/cancel MUST leave the old valid credential and configuration untouched. There is no silent token privilege escalation. If the new token was issued but identity/scope verification failed, revoke the new token.

The local Admin approval window and pending PIN are separate: re-opening Admin during a pending pairing MUST NOT invalidate the displayed code. A successful `/pair/confirm` MUST clear the on-screen PIN immediately, while an expired/cancelled attempt MUST clear or visibly invalidate it. Classic MUST use the same logical flow, even if its Admin UI differs.

### `POST /pair/revoke`

Authenticated using bearer token; payload `{ "client_id": "ha-8c4c4f52-6e35-44dd-930a-bdb838cd60d8" }`. Clients MAY revoke **their own** token; local admin UI can revoke any client. Success is `{ "success": true }`; token must stop working immediately. Granting new scopes requires fresh local approval/re-pairing; no silent privilege escalation. A client can re-pair after revocation. `GET /pair/clients` and admin-only remote revocation are NOT required by v1.

## 4. Permissions (question 3)

**One independently revocable bearer token per client installation, with scopes** (not two tokens). Scope meanings:

| Scope | Permits |
|---|---|
| `read` | `/info`, `/state`, `/outputs`, `/update`, `/screenshot` and supported read-only status endpoints; media cover endpoint if implemented |
| `control` | play/pause/stop/next/previous/seek/set_volume, audio output selection; mute/unmute only if advertised and implemented |
| `notify` | `/speak` TTS and `/message` on-screen notifications |
| `power` | `/power` with `reboot` or `poweroff` |
| `admin` | other maintenance functions, if explicitly implemented |

Default request is `["read","control"]`. `notify`, `power`, and `admin` need explicit user consent; the actual set MUST be clearly presented in the HA confirmation screen **and verified by the box-local approval UI** before granting. `notify` and `power` MUST NOT be implicitly granted by `control`. (NG presently arms a pairing window through Admin; explicit per-scope local display/approval remains an identified NG hardening task, not an accomplished guarantee.) Every endpoint validates scope server-side. All protected requests use `Authorization: Bearer <access_token>` over verified HTTPS; no token in query strings. An unpaired client can access only the minimal `/health`, pairing actions, and TLS inspection path. Successful commands are not proof of expanded privilege.

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

`playback.state` is one of `playing`, `paused`, `idle`, `buffering`, `unavailable`. Duration/position are in **seconds**, volume is **integer 0–100**; unavailable measurements are JSON `null`, never fabricated. Status MUST describe real playback regardless of initiating source (touch, RFID, hardware buttons, Spotify Connect, HA). `cover_url` MUST be a same-device relative URL or validated absolute HTTPS URL; it MUST NOT embed secrets. If implemented, `/media/cover/current` requires `read`; currently do not assume every generation implements it. Capabilities accurately describe functioning methods (e.g. `set_volume`, not `volume`). Unsupported capabilities MUST NOT be exposed as functional entities or controls.

### `POST /control` (`control`)

```json
{"command":"pause"}
```

```json
{"command":"set_volume","value":35}
```

```json
{"command":"seek","position":90}
```

Allowed base `command`: `play`, `pause`, `stop`, `next`, `previous`, `set_volume`, `seek`. `mute` and `unmute` MAY be implemented and advertised. Position is seconds; volume is 0–100. `restart` and `shutdown` MUST NOT be performed through `/control`; use dedicated `/power` with `power` scope. Unknown or unadvertised commands MUST fail; no false-success responses. On accepted completed action return HTTP 200 `{ "success": true }`. On an asynchronous action the server MAY return 202 `{ "success": true, "accepted": true }` but MUST NOT claim execution completed.

### `GET /update` (`read`)

Returns an update-check result, **not an install operation**:

```json
{"update_available":true,"channel":"test","release":{"version":"EXAMPLE_ONLY"}}
```

When no update is available `update_available` is `false` and `release` MAY be `null`. The box MUST use its configured release channel and must not invent availability if manifest checks fail. HA exposes a binary diagnostic sensor and may poll at a low frequency (e.g. 10 minutes). Availability of a release MUST NOT trigger installation automatically.

### `POST /power` (`power`)

```json
{"action":"reboot"}
```

Allowed `action` values: `reboot`, `poweroff`. Successful scheduling (not completion) responds HTTP **202** with `{"success":true,"accepted":true}`. `read`, `control` and `notify` alone MUST return `403 insufficient_scope`. Box-specific shutdown sound/cleanup MUST still execute through the normal device lifecycle. HA MUST confirm destructive power actions in the UI. If `power` scope was not granted, do not render active power buttons.

### `POST /message` (`notify`)

```json
{"title":"Home Assistant","message":"Please come downstairs","duration_ms":8000}
```

Response `200 {"success":true}` on accepted display. `message` required; enforce device-appropriate length bounds (NG: <=1000 UTF-8 bytes), `title` optional (NG: <=120 bytes), `duration_ms` optional (NG: 0–30000), and reject invalid input without rendering arbitrary HTML. Reuse the normal box notification surface; do not put messages into the PIN display channel.

### `POST /speak` (`notify`)

```json
{"text":"Dinner is ready"}
```

Response `200 {"success":true}` when audio playback was accepted. `text` must be nonempty and bounded (NG: <=1000 bytes). Follow existing device TTS routing, notification sound, interruption and resume semantics. Do not claim audio playback is completed if it only started. Reject requests with insufficient scope.

### `GET /outputs` (`read`) and `POST /outputs/select` (`control`)

Example read response:

```json
{"targets":[{"id":"local","name":"This MuPiBox","selectable":true,"available":true,"active":true}]}
```

The box advertises actual local/Bluetooth/network output targets with stable IDs, real availability, active flag and human name; do not fabricate missing outputs. To select:

```json
{"target_id":"local"}
```

Selection returns `200 {"success":true}` on success, or an appropriate error if unavailable/blocked by parental controls. **Classic MUST honor its own output hardware and parental-control capabilities**; if selection is unavailable, report that truthfully rather than creating dead UI controls.

### `GET /screenshot` (`read`, optional if a framebuffer/display is available)

Response `200 OK`, `Content-Type: image/png`, `Cache-Control: no-store`, body is PNG bytes; on failure use the normal JSON error envelope. The screenshot MUST reflect the actual display, not a fabricated preview. HA MUST limit payload size and treat it as potentially sensitive data. Classic MAY omit this feature on unsupported hardware and HACS MUST hide/unavailable the camera accordingly. NEVER return a screen capture without valid read scope. Any captured PIN is sensitive; the screenshot path SHOULD suppress or redact an active pairing code, and this behavior needs security testing before shipping to Classic.

### `GET /state` optional `metrics` extension (`read`)

The state JSON MAY include a `metrics` object with `cpu_percent`, `temperature_c`, `ram_percent`, `disk_percent` as numeric measurements. Only report observed values, not invented zeros; on Classic without these sensors, omit keys or expose unavailable entity states. This is an additive API-v1 extension and does not change playback or device fields.

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

1. Two Classic devices and one NG device securely discovered under `_mupibox._tcp.local.` with independent persistent IDs and HTTPS SRV ports; insecure legacy HTTP advertisements never trigger admin-password onboarding.
2. Manual host/IP setup works when multicast is unavailable.
3. HTTPS first-contact verification requires matching out-of-band SPKI fingerprint, and fails closed on key mismatch.
4. Pairing cannot be remotely forced; six-digit code (including leading zero) works exactly once for <=300 s; wrong code fails; sixth incorrect attempt is impossible; throttling applies across source IPs.
5. Scope grant matches local approval; `control` token cannot call `/power`, `/message`, `/speak` or admin routes; only `notify` can message/speak and only `power` can reboot/poweroff; revocation takes effect immediately.
6. JSON errors, HTTP statuses and secure command validation match this document.
7. `/state` reflects touchscreen/RFID/Spotify changes; missing hardware metrics are null, not zeros.
8. IP change, reboot, reconnect and certificate renewal with same SPKI preserve configuration; different SPKI requires approval.
9. Existing HACS config entry, device identity, entity IDs, dashboards and automations survive **Configure -> scope renewal** for both generations. Failure/cancel preserves old token; successful renewal revokes it after the new token is persisted.
10. Classic Admin fingerprint button copies exactly 64 raw hex chars over HTTP (clipboard fallback and manual-selection fallback), plus HTTPS where available. Fingerprint is independently verified in HA before PIN request.
11. Pairing PIN appears centered and legible on small displays, including leading zeros; disappears immediately on success and on expiry/cancel. Reopening Admin must not clear active PIN.
12. `/update`, `/power`, `/message`, `/speak`, `/outputs`, `/outputs/select`, and optional `/screenshot` are tested for both success and missing-scope denial; missing Classic hardware/features are explicitly unavailable.
13. Run tests against a mocked v1 server first, then against both actual generations; do not declare interoperability until both pass.

## 9. Ownership and release gate

Classic maintainer: implement mDNS HTTPS advertisement, Admin fingerprint presentation and HTTP-safe copy fallback, PIN display, token/scopes with in-place renewal, all required API-v1 routes and real status/control. NG maintainer: maintain endpoint parity and close outstanding local per-scope approval hardening; preserve local 8090 operation without re-enabling legacy mDNS onboarding. HACS maintainer: keep a single `mupibox` integration and existing entity registry, secure pairing and **Configure** reauthorization for both generations, hide unsupported features. **Classic discovery MUST remain unavailable for completed v1 setup until Classic has passed the interoperability suite; this document is not evidence that it has.**

## 10. NG implementation profile and Classic parity checklist (2026-10-08)

**Currently in NG:** HTTPS listener on TCP 8443 beside the local HTTP API on TCP 8090. mDNS advertises only secure v1 enrollment. Local Admin -> Smart Home -> "Home Assistant sicher koppeln (API v1)" invokes `POST /api/ha/v1/pair/enable` under a pre-existing authenticated Admin session, opens a 60-second approval window and shows the full SPKI fingerprint **in Admin, not on the playback display**. The secure HTTPS endpoint `GET /api/ha/v1/tls/ca` publishes only the public CA PEM. HACS verifies first-contact SPKI out-of-band, obtains the CA via the verified device key and uses a private per-device trust context for subsequent HTTPS requests. Once `/pair/start` succeeds, the random PIN is shown prominently on the physical display for at most 300 seconds and cleared immediately after confirmation.

**Fingerprint copy on NG Admin:** The copy button prefers `navigator.clipboard.writeText` in a secure browser context, falls back to a selected hidden textarea and `document.execCommand('copy')` on HTTP, then selects the visible text and instructs manual copy if browser policy blocks both. Classic MUST implement equivalent **behavior**, not necessarily the same HTML/JavaScript structure. The box does **not** need to enable HTTPS on its entire Admin UI to satisfy this copy requirement.

**NG secured routes:** `/health`, `/info`, `/state` with metrics, `/control`, `/update`, `/power`, `/message`, `/speak`, `/outputs`, `/outputs/select`, `/screenshot`, `/pair/start`, `/pair/confirm`, `/pair/revoke`. Screenshot returns PNG, not JSON. `/pair/display` is strictly loopback-only for NG QML and MUST NOT be exposed to remote clients. Power and notification scopes were added as optional approvals; preexisting tokens do not gain them automatically.

**HACS setup and scope renewal:** New secure mDNS discovery directly opens the fingerprint verification form and then initiates pairing automatically when the box is locally approved. HACS v0.4.8 exposes a **Configure** options flow to request optional `notify` and `power` permissions, obtain a new PIN/credential and update the **existing** HA config entry. The new token is persisted before old-token revocation. For Classic the same HA UX and endpoints MUST work; do not implement a separate Classic-specific password-based enrollment.

**Classic implementation tasks / release gates** (none may be assumed complete without testing):

- Advertise `_mupibox._tcp.local.` with `generation=classic`, `api_version=1`, `transport=https`, `device_id`, `pairing=required`, and correct SRV port; verify persistent ID through updates and host changes.
- Use locally trusted Admin page (and optionally screen) to present a correctly computed 64-char SPKI fingerprint, a copy button that works or degrades gracefully over **HTTP**, and a local 60-second pairing approval. Keep PIN strictly on local player/display with accessible typography.
- Implement and test the shared HTTPS, CA/public-key verification, locally approved pairing/PIN/token rotation and exact `read`/`control`/`notify`/`power` authorization. Show requested scopes at local consent and clear PIN immediately on success.
- Implement real player volume/navigation, TTS/notification, power actions, update status, output targets/selection and optional screenshot/metrics. Advertise only implemented capabilities and never synthesize unsupported readings.
- Test **Configure** scope renewal in HA without deleting or renaming existing Classic entries, and test each route with missing/valid/insufficient scopes. Keep old credentials intact on declined, expired or failed reauthorization.

**Known parity/security gaps for follow-up:** The current NG local PIN panel shows the code but not a separate explicit list of requested scopes before the approval; add that verification/consent before claiming strict per-scope local confirmation is complete. A screenshot of an active PIN may disclose it to any holder of the `read` token; suppress/redact pending PINs on capture or introduce a stronger capture scope before fully enabling this on Classic. Revisit the HTTPS/HTTP Admin trust boundary when designing Classic's approval mechanism: visible fingerprint on an untrusted network HTTP connection alone is not cryptographic proof of the box's identity; the user needs a **trusted local** reference.
