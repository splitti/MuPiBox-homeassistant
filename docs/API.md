# Home Assistant / HACS integration

MuPiBox exposes a local HTTP API on port `8090` by default. The Home Assistant custom integration in `custom_components/mupibox` maps the stable player/status endpoints to native Home Assistant devices and entities.

The integration uses **local polling**. Player, system and Spotify state are polled every 5 seconds. The local library is refreshed at most once per minute and static information such as the software version less frequently.

## Installation

### HACS

Install the integration from this repository with HACS:

1. Open **HACS → Integrations**.
2. Open the menu and choose **Custom repositories**.
3. Add `https://github.com/splitti/MuPiBox` as category **Integration**.
4. Install **MuPiBox**.
5. Restart Home Assistant.
6. Open **Settings → Devices & services → Add integration → MuPiBox**.
7. Enter the MuPiBox hostname/IP and port. The default API port is `8090`.
8. Enter the MuPiBox admin password only if protected maintenance controls should be available in Home Assistant.

For development before a HACS-visible release, copy `custom_components/mupibox` into `<HA config>/custom_components/mupibox` and restart Home Assistant.

## Home Assistant entities

One Home Assistant device is created per configured MuPiBox.

| Entity | Purpose | MuPiBox API |
| --- | --- | --- |
| `media_player` Local Player | Local files: play/pause/stop, previous/next, seek, volume, media browser | `GET /api/status`, `GET /api/library`, `POST /api/command` |
| `media_player` Spotify Connect | Spotify Connect status and transport/volume control | `GET /api/spotify/status`, `POST /api/spotify/command` |
| `notify` Announcements | Local Piper TTS announcement on the box | `POST /api/speak` |\n| `camera` Display | Current display screenshot on demand | `GET /api/admin/screenshot` |
| Battery sensor | MuPiHAT/system battery percentage when available | `GET /api/system` |
| Wi-Fi signal/quality | RSSI, quality and interface | `GET /api/system` |
| Version / audio backend | Diagnostics | `GET /api/info`, `GET /api/status` |
| Network/Wi-Fi/Spotify/TTS binary sensors | Connectivity and feature state | `GET /api/system`, `/api/spotify/status`, `/api/info` |
| Rescan library button | Re-read local media | `POST /api/admin/library/rescan` |
| Restart UI button | Trigger the native UI restart generation | `POST /api/admin/ui/restart` |
| Reboot / Power off buttons | Schedule operating-system reboot or shutdown | `POST /api/admin/system/power` |

If an admin password is enabled on the MuPiBox but not stored in the Home Assistant config entry, normal playback, status and TTS remain available; protected maintenance buttons are unavailable.

## TTS from Home Assistant

The integration creates a **Notify entity**. Use the normal Home Assistant `notify.send_message` action and target the MuPiBox Announcements entity.

Example automation action:

```yaml
action: notify.send_message
target:
  entity_id: notify.mupibox_ng_announcements
data:
  message: "Essen ist fertig."
```

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
| GET | `/api/info` | Version, simulation flag, audio backend, TTS/power/display/theme summary |
| GET | `/api/system` | Network, Wi-Fi RSSI/quality and battery state |
| GET | `/api/ui-state` | UI restart generation |
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
