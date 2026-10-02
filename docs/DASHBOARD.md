# MuPiBox Home Assistant dashboard

This repository includes a compact two-view Home Assistant dashboard template for MuPiBox-NG:

- **Control** — current media, cover, playback, output routing, battery/Wi-Fi, provider state, display preview and quick maintenance actions.
- **Diagnostics** — CPU/RAM/storage, temperatures, MuPiHAT power data, network and software information.

## Dependencies

### Required

- Home Assistant **2026.9 or newer** (recommended/tested layout target)
- MuPiBox Home Assistant integration **0.3.3 or newer**
- A MuPiBox-NG build exposing the current Home Assistant, MuPiHAT, provider and output-target APIs

### Additional HACS cards

**None.** The reference dashboard deliberately uses only Home Assistant built-in cards and the modern Sections layout. Mushroom, card-mod, button-card, ApexCharts and other custom frontend cards are **not required**.

This keeps the template portable, theme-aware and less likely to break after Home Assistant frontend updates.

## Install the template

1. Add/configure your MuPiBox integration first and make sure its entities are available.
2. Create an empty dashboard in Home Assistant.
3. Open **Edit dashboard → Raw configuration editor**.
4. Copy `docs/dashboard-template.yaml` into the editor.
5. Replace every `REPLACE_*` entity ID with the matching entity from your own MuPiBox device.

Do not edit Home Assistant `.storage` files directly.

## Entity mapping

Use the entity names on the MuPiBox device page to find the IDs for your installation. Home Assistant entity IDs can contain the device name and/or area name, so they are intentionally not hard-coded in the published template.

| Placeholder | MuPiBox entity name |
|---|---|
| `REPLACE_PLAYER` | Player |
| `REPLACE_AUDIO_OUTPUT` | Audio output / Audioausgabe |
| `REPLACE_BATTERY` | Battery |
| `REPLACE_WIFI_SIGNAL` | Wi-Fi signal |
| `REPLACE_WIFI_QUALITY` | Wi-Fi quality |
| `REPLACE_CHARGING` | Charging |
| `REPLACE_NETWORK` | Network reachable |
| `REPLACE_TTS_ENABLED` | Voice output enabled |
| `REPLACE_ACTIVE_PROVIDER` | Active provider |
| `REPLACE_TTS_PROVIDER` | TTS provider |
| `REPLACE_SPOTIFY_STATUS` | Spotify status |
| `REPLACE_MA_STATUS` | Music Assistant status |
| `REPLACE_JELLYFIN_STATUS` | Jellyfin status |
| `REPLACE_AUDIBLE_STATUS` | Audible status |
| `REPLACE_SENDSPIN_STATUS` | Sendspin status |
| `REPLACE_DISPLAY` | Display camera |
| `REPLACE_RESCAN` | Rescan media library |
| `REPLACE_RESTART_UI` | Restart interface |
| `REPLACE_REBOOT` | Restart box |
| `REPLACE_POWEROFF` | Power off box |
| `REPLACE_CPU_USAGE` | CPU usage |
| `REPLACE_CPU_TEMP` | CPU temperature |
| `REPLACE_RAM_USAGE` | RAM usage |
| `REPLACE_STORAGE_USAGE` | Storage usage |
| `REPLACE_BATTERY_VOLTAGE` | Battery voltage |
| `REPLACE_BATTERY_CURRENT` | Battery current |
| `REPLACE_MUPIHAT_TEMP` | MuPiHAT temperature |
| `REPLACE_EXTERNAL_POWER` | External power |
| `REPLACE_MUPIHAT_AVAILABLE` | MuPiHAT available |
| `REPLACE_VERSION` | Version |

## Audio output routing

Integration 0.3.3+ exposes **Audio output** as a Home Assistant `select` entity instead of a read-only sensor. The options are populated dynamically from currently selectable MuPiBox output targets. Depending on the box this can include:

- the MuPiBox itself
- paired/available Bluetooth devices
- Sonos targets
- Music Assistant players

The dashboard uses the native `select-options` tile feature so routing can be changed directly without opening the device page.

## Display messages and TTS

The integration also exposes two notify entities:

- **Display message** — transient text on the MuPiBox touch display
- **TTS announcement** — spoken message via the TTS provider configured on the box

They are intentionally not wired to a fixed-message dashboard button in the base template, because the message text should be supplied by an automation, script, or user input rather than hard-coded. This keeps the reference dashboard dependency-free. A separate optional message-composer example can be built with native Home Assistant helpers if desired.
