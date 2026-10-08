# MuPiBox Classic: Home Assistant API v1 (draft)

This is a preparatory contract; Classic pairing and control are not yet implemented.

## Backward compatibility

- Keep the existing `mupibox` domain, NG configuration entries, unique IDs and entity IDs.
- Legacy NG mDNS advertisements without a `generation` TXT record remain NG.
- Classic advertises `generation=classic` and is currently detected but not configured as NG.
- Do not change the existing NG API client or NG admin-cookie authentication.

## Classic firmware contract

mDNS: `_mupibox._tcp.local.` with `product=mupibox`, `generation=classic`, `api_version=1`, `device_id=<persistent UUID>`, `pairing=required`. Advertise the actual API port. No secrets in TXT records.

Endpoints:

- `GET /api/ha/v1/health` -> `{ "ok": true, "api_version": 1 }`
- `GET /api/ha/v1/info` -> `{ "generation": "classic", "api_version": 1, "device_id": "<uuid>", "name": "...", "capabilities": ["play", "pause", "volume"] }`
- `GET /api/ha/v1/state` -> `{ "playback": { "state": "playing", "provider": "local", "title": "...", "artist": "...", "duration": 100, "position": 42, "cover_url": "/api/ha/v1/media/cover/current", "volume": 35, "muted": false }, "device": {} }`
- `POST /api/ha/v1/control` -> `{ "command": "pause" }` or `{ "command": "set_volume", "value": 35 }`

Responses should use null for unavailable values. The ID remains stable across reboots, upgrades and IP changes. Playback state must include changes initiated by buttons, RFID and Spotify Connect. Advertise only working capabilities.

Security: explicit, time-limited user-approved pairing, individual revocable authorization, rate-limited verification and authenticated encryption for credentials and commands. Plain HTTP bearer tokens are insufficient against attackers on the LAN.

## Next steps before Classic onboarding is enabled

1. Build a Classic-specific pairing flow and token store, separate from NG passwords.
2. Build a Classic API adapter that maps state using `classic_contract.normalize_classic_state` and routes commands.
3. Expose only entity features and maintenance commands advertised by Classic capabilities.
4. Integration-test mixed NG/Classic, duplicate zeroconf, IP change, HA restart, revocation, API failures, previous NG entity IDs and registry migration.
5. Enable Classic in config flow only after these tests succeed; release a new integration version.
