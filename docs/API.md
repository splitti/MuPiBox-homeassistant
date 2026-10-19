# MuPiBox Home Assistant API reference

> **Current integration: 0.5.3 (19 October 2026).** MuPiBox is in the [official HACS catalog](https://github.com/hacs/default/pull/11101). The normal HACS setup and all **new** Home Assistant connections use the secure **HTTPS API v1**. The legacy HTTP material further below is retained **only** for existing NG installations and firmware developers; it is not a current onboarding guide.

## Install and pair (Classic / NG API v1)

1. In **HACS**, search for **MuPiBox**, download it, and restart Home Assistant. No custom repository is required after the catalog refresh.
2. Enable automatic discovery on the box; Home Assistant discovers `_mupibox._tcp.local.` with a distinct **Classic** or **NG** device label and the box's friendly name. Or choose **Add integration → MuPiBox** and provide the HTTPS hostname/IP and port **8443**.
3. On the box's local **Admin → Smart Home** page, begin secure Home Assistant pairing. Compare the **SHA-256 SPKI** fingerprint (64 hex characters) with the value Home Assistant asks you to confirm. mDNS labels alone do not prove identity.
4. Approve pairing locally and enter the box's **six-digit pairing code** (valid up to 300 seconds). Default permissions are `read` and `control`. Optional `notify` enables TTS/on-screen messages; optional `power` enables reboot, shutdown and the optional timer control.
5. To change permissions later without losing entity IDs, open the installed device's **Configure** options and approve a fresh code locally. New scopes are never silently assigned.

**No Admin password, insecure HTTP fallback or port 8090 is used for new API v1 pairing.** Classic requires a firmware implementation advertising and serving the shared HTTPS API v1 contract; Classic branding or Smart Discovery alone does not prove that its build has every endpoint.

## Secure v1 entities and capabilities

| Home Assistant entity | Secure v1 API / permission | Condition |
| --- | --- | --- |
| `media_player` | `GET /state`, `POST /control`; `read`/`control` | Provider-neutral playback |
| Sensors | `GET /state`, `GET /info`; `read` | Battery, MuPiHAT fields, Wi-Fi, CPU/RAM/storage, operating state, active provider and version, if reported |
| Binary sensors | `GET /state`, `GET /update`; `read` | Network/Wi-Fi, charging, external power if reported, update availability |
| `select` audio output | `GET /outputs`, `POST /outputs/select`; `read`/`control` | Supported targets supplied by the box |
| `camera` display screenshot | `GET /screenshot`; `read` | Device must supply screenshot |
| `notify` display message and TTS | `POST /message`, `POST /speak`; `notify` | Optional, explicitly approved |
| `button` reboot/poweroff | `POST /power`; `power` | Optional, explicitly approved |
| `sensor` shutdown timestamp | `GET /state`; `read` | Only if `capabilities` includes `sleep_timer` |
| `number` sleep timer | `POST /sleep_timer`; `power` | Only if `sleep_timer` supported; 0–720 minutes, 0 cancels |

All paths in this table are relative to `https://BOX:8443/api/ha/v1/`. API v1 uses a **pinned and validated HTTPS identity**, bearer token and scope checks, not the older Admin session. The sleep timer causes a **real system shutdown**; it is not a parental-control playback timer.

**Not currently offered by secure v1:** legacy local-library browsing, direct `spotify:` URI navigation, rescan-library button, UI-restart button and individual provider-health sensors. See the [normative Classic/NG contract](classic-api-contract.md), [Classic sleep-timer guide](CLASSIC_SLEEP_TIMER.md), and [dashboard compatibility guide](DASHBOARD.md).

---

## Legacy HTTP reference — existing NG configuration entries only

The information below documents the older local API on port `8090`. It remains useful for existing installations and device-local tooling, but is **not** the HACS install/configuration path for new devices. Do not use its examples for new HTTPS v1 pairings.

MuPiBox exposes a local HTTP API on port `8090` by default. The Home Assistant custom integration in `custom_components/mupibox` maps the stable player/status endpoints to native Home Assistant devices and entities.

The integration uses **local polling**. Player, system, Spotify and MuPiHAT state are polled every 5 seconds. Lightweight CPU/RAM/storage metrics are refreshed every 10 seconds, provider connectivity summaries every 30 seconds, the local library at most once per minute and static information such as the software version less frequently.

## Installation

### HACS

Install the integration from this repository with HACS:

1. Open **HACS → Integrations**.
2. Open the menu and choose **Custom repositories**.
3. Add `https://github.com/splitti/MuPiBox-homeassistant` as category **Integration**.
4. Install **MuPiBox**.
5. Restart Home Assistant.
6. A discovery-enabled MuPiBox appears automatically under **Settings → Devices & services → Discovered**. Select **Configure** and confirm the device.
7. Optionally enter the MuPiBox Admin password if protected maintenance controls should be available.
8. If mDNS is unavailable on the network, use **Add integration → MuPiBox** and enter the hostname/IP and port manually.

MuPiBox advertises `_mupibox._tcp.local.` and includes its persistent `box_id` in the TXT records. The integration verifies that ID against `GET /api/info` before creating the config entry. The same ID is used across DHCP address changes.

For development before a HACS-visible release, copy `custom_components/mupibox` into `<HA config>/custom_components/mupibox` and restart Home Assistant.

## Home Assistant entities

One Home Assistant device is created per configured MuPiBox.

| Entity | Purpose | MuPiBox API |
| --- | --- | --- |
| `media_player` Player | One logical box player; automatically follows local/streamed playback or Spotify | `GET /api/status`, `GET /api/spotify/status`, `POST /api/command`, `POST /api/spotify/command` |
| `notify` Display message | Show a transient text message on the touch display | `POST /api/message` |
| `notify` TTS announcement | Speak text using the globally configured MuPiBox TTS engine | `POST /api/speak` |
| `camera` Display | Current display screenshot on demand | `GET /api/admin/screenshot` |
| Battery / MuPiHAT sensors | Battery %, voltage/current, charging, external power and HAT temperature | `GET /api/mupihat/status` |
| Wi-Fi signal/quality | RSSI, quality, interface and IPv4 address | `GET /api/system` |
| CPU/RAM/storage/temperature | Lightweight system diagnostics | `GET /api/system/metrics` |
| Active provider | Current playback source (`local`, `spotify`, `radio`, `podcast`, etc.) | `GET /api/status`, `GET /api/spotify/status` |
| Provider status | Spotify, Music Assistant, Jellyfin, Audible and Sendspin connection/configuration state | `GET /api/providers/status` |
| Version / playback engine / TTS provider | Diagnostics | `GET /api/info`, `GET /api/status` |
| Audio output selector | Currently active local/Bluetooth/Sonos/Music Assistant output target and direct routing control | `GET /api/output-targets`, `POST /api/output-targets/select` |
| Network/Wi-Fi/Spotify/TTS binary sensors | Connectivity and feature state | `GET /api/system`, `/api/spotify/status`, `/api/info` |
| Rescan library button | Re-read local media | `POST /api/admin/library/rescan` |
| Restart UI button | Trigger the native UI restart generation | `POST /api/admin/ui/restart` |
| Reboot / Power off buttons | Schedule operating-system reboot or shutdown | `POST /api/admin/system/power` |

If an admin password is enabled on the MuPiBox but not stored in the Home Assistant config entry, normal playback, status and TTS remain available; protected maintenance buttons are unavailable.

## Messages and TTS from Home Assistant

The integration creates two **Notify entities**. `Display message` shows text on the MuPiBox touch screen without interrupting playback. `TTS announcement` speaks the text using the box's configured TTS provider.

Example automation action:

```yaml
action: notify.send_message
target:
  entity_id: notify.mupibox_tts_announcement
data:
  message: "Essen ist fertig."
```


Display-only example:

```yaml
action: notify.send_message
target:
  entity_id: notify.mupibox_display_message
data:
  title: "Home Assistant"
  message: "Essen ist fertig."
```

`POST /api/message` feeds the native transient-message overlay already used by the touch UI. Messages expire automatically and are not stored as a history on the box.

`POST /api/speak` intentionally pauses currently playing local audio and Spotify before the announcement. MuPiBox currently does not automatically resume the previous source afterwards.

## Local media browser

The Local Player exposes the MuPiBox local library through Home Assistant's media browser. Folders are playable as a whole; individual tracks are playable through a stable synthetic media ID based on the MuPiBox folder ID and queue index.

The underlying API contract is:

```json
POST /api/command
{
  "action": "folder",
  "folder_id": "<folder-id>"
}
```

or for an item within a folder:

```json
POST /api/command
{
  "action": "resume",
  "folder_id": "<folder-id>",
  "item_index": 3
}
```

## API authentication

Public player/status routes do not require the Admin session. When an Admin password is configured, `/api/admin/*` and externally called `/api/connectivity/*` routes require a MuPiBox Admin session.

Authentication is cookie based:

```bash
curl -c mupibox.cookies \
  -H 'Content-Type: application/json' \
  -d '{"password":"YOUR_ADMIN_PASSWORD"}' \
  http://MUPIBOX:8090/api/admin/login
```

Use the returned cookie for protected calls:

```bash
curl -b mupibox.cookies http://MUPIBOX:8090/api/admin/system
```

The Home Assistant integration performs this login itself and keeps the returned session cookie only in memory. The configured password is not sent on public status/player requests.

## Public API reference

### Health and information

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/health` | Liveness and MuPiBox version |
| GET | `/api/info` | Version, persistent `box_id`, simulation flag, audio backend, TTS/power/display/theme summary |
| GET | `/api/system` | Network and Wi-Fi RSSI/quality state |
| GET | `/api/system/metrics` | CPU, RAM, storage, load, temperature and uptime metrics |
| GET | `/api/mupihat/status` | MuPiHAT battery/power/temperature telemetry |
| GET | `/api/providers/status` | Safe provider configuration/connectivity summary without credentials |
| GET | `/api/ui-state` | UI restart generation plus a currently active transient message |
| POST | `/api/message` | Show a transient message on the native touch UI |
| GET | `/api/home` | Data-driven categories, rows and normalized items |
| GET | `/api/library` | Local folders, tracks, stable IDs and cover URLs |
| GET | `/api/cover/{id}` | Cover image for a local folder |

### Local player

Read status:

```bash
curl http://MUPIBOX:8090/api/status
```

Transport examples:

```bash
curl -H 'Content-Type: application/json' \
  -d '{"action":"pause"}' \
  http://MUPIBOX:8090/api/command

curl -H 'Content-Type: application/json' \
  -d '{"action":"seek","value":120}' \
  http://MUPIBOX:8090/api/command

curl -H 'Content-Type: application/json' \
  -d '{"action":"volume","value":30}' \
  http://MUPIBOX:8090/api/command
```

Supported local actions in the current controller are `folder`, `resume`, `volume`, `volume_delta`, `stop`, `play`, `pause`, `toggle`, `next`, `previous` and `seek`. Local seek values are in **seconds**. Volume is the MuPiBox 0..`max_volume` value, not a 0..1 fraction.

### Spotify Connect

Status:

```bash
curl http://MUPIBOX:8090/api/spotify/status
```

Control:

```bash
curl -H 'Content-Type: application/json' \
  -d '{"action":"next"}' \
  http://MUPIBOX:8090/api/spotify/command

curl -H 'Content-Type: application/json' \
  -d '{"action":"seek","value":90000}' \
  http://MUPIBOX:8090/api/spotify/command
```

Supported actions are `pause`, `resume`/`play`, `next`, `previous`, `seek` and `volume`. Spotify seek values are in **milliseconds**. Spotify volume uses go-librespot's `volume_steps` range returned by `/api/spotify/status`.

### TTS

```bash
curl -H 'Content-Type: application/json' \
  -d '{
    "source_type":"home-assistant",
    "source_ref":"manual-test",
    "text":"Hallo von Home Assistant"
  }' \
  http://MUPIBOX:8090/api/speak
```

This uses the globally configured MuPiBox TTS language/voice. On a cache miss the request may take several seconds while Piper renders the text.

## Admin API reference

These routes require an Admin session when Admin protection is enabled.

### General settings and navigation

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/admin/auth` | Protection/authentication state; callable without login |
| POST | `/api/admin/login` | Create Admin session |
| POST | `/api/admin/logout` | Clear Admin sessions |
| PUT | `/api/admin/password` | Set/change Admin password |
| GET/PUT | `/api/admin/settings` | Persistent box settings |
| GET/PUT | `/api/admin/navigation` | Persistent categories/rows |
| GET | `/api/admin/local-directories` | Local directory tree |
| POST | `/api/admin/library/rescan` | Rescan local library |
| POST | `/api/admin/ui/restart` | Signal native UI restart |

### System and audio

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/admin/system` | Boot analysis, swap, CPU governors, interfaces, network backend |
| POST | `/api/admin/system/power` | `{ "action": "reboot" }` or `{ "action": "poweroff" }` |
| GET | `/api/admin/screenshot` | PNG screenshot of the box display |
| GET/PUT | `/api/admin/samba` | Samba configuration/runtime state |
| GET | `/api/admin/audio/status` | ALSA/mpv device and MuPiHAT audio detection |
| PUT | `/api/admin/audio/device` | Select mpv audio device |
| PUT | `/api/admin/audio/mupihat` | Enable/disable managed MuPiHAT audio overlay |

### TTS administration

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/admin/tts/status` | Engine, generation and cache status |
| GET/PUT | `/api/admin/tts/config` | Global TTS configuration |
| GET | `/api/admin/tts/voices?language=de` | Installed/available voices |
| POST | `/api/admin/tts/test` | Render/play one test clip |
| POST | `/api/admin/tts/cache/rebuild` | Start a fresh generation |
| POST | `/api/admin/tts/cache/fill-missing` | Queue missing entries |
| POST | `/api/admin/tts/cache/cleanup` | Purge stale generations |

### Backup and release management

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/admin/backup` | ZIP backup; `?include_media=true` optionally includes local media |
| POST | `/api/admin/restore` | Restore multipart backup |
| GET | `/api/admin/releases` | GitHub releases and rollback availability |
| POST | `/api/admin/releases/switch` | Start update/rollback to requested target |

## Connectivity API

External requests to `/api/connectivity/*` are Admin-protected when an Admin password is configured. They are intentionally **not** mapped to Home Assistant controls in the first integration version, because changing the active adapter/IP can disconnect Home Assistant from the box.

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/connectivity/wifi/adapters` | Detected Wi-Fi adapters and active selection |
| POST | `/api/connectivity/wifi/adapters/state` | Select/enable adapter |
| PUT | `/api/connectivity/wifi/preferences` | Select primary adapter and optionally disable onboard Wi-Fi |
| GET | `/api/connectivity/wifi` | Scan networks; optional `?interface=` |
| POST | `/api/connectivity/wifi/connect` | Connect to a Wi-Fi network |
| GET | `/api/connectivity/bluetooth` | Scan Bluetooth devices |
| POST | `/api/connectivity/bluetooth/command` | Pair/connect/disconnect/remove a Bluetooth device |

## Security notes

MuPiBox is designed for a trusted local network. Do not forward port `8090` directly from the Internet. If Home Assistant reaches the box across an untrusted network segment, use a TLS reverse proxy and enable **Use HTTPS** in the integration.

The Home Assistant integration does not use or read go-librespot's persisted Spotify credentials. Spotify control goes only through MuPiBox's local `/api/spotify/*` abstraction.

## Troubleshooting

Check the public endpoints from the Home Assistant host first:

```bash
curl http://MUPIBOX:8090/api/health
curl http://MUPIBOX:8090/api/status
curl http://MUPIBOX:8090/api/system
```

Expected health response:

```json
{
  "status": "ok",
  "version": "0.1.0-dev"
}
```

If public functions work but Admin buttons are unavailable, verify `/api/admin/auth` and configure the Admin password in the Home Assistant integration when `protected` is `true`.
