# MuPiBox for Home Assistant

Home Assistant integration for **MuPiBox / MuPiBox-NG**.

**Author and maintainer:** Olaf Splitt  
**Website:** https://mupibox.de  
**MuPiBox-NG:** https://github.com/splitti/MuPiBox-NG  
**Home Assistant integration version:** 0.4.0

The Home Assistant integration is versioned independently from MuPiBox-NG.

## Features

- One provider-neutral MuPiBox media player for local media, radio, podcasts, ARD Sounds, Audible and Spotify
- Automatic routing of play/pause/next/previous/seek/volume to the currently active playback backend
- Home Assistant media browser for the MuPiBox local library plus direct `spotify:` URI playback
- Display messages on the MuPiBox touch screen through a Home Assistant notify entity
- TTS announcements through a separate notify entity
- Live MuPiHAT battery percentage, voltage, current, charging/external-power and temperature diagnostics
- Wi-Fi/network diagnostics including signal, quality, interface and IP address
- CPU, RAM, storage and CPU-temperature diagnostics
- Selectable audio output for local playback, Bluetooth, Sonos and Music Assistant targets currently available to the box
- Optional playback-engine diagnostic (`mpv`), disabled by default because it is only useful for troubleshooting
- Active playback-provider sensor and provider status for Spotify, Music Assistant, Jellyfin, Audible and Sendspin
- Library rescan and UI restart controls
- Reboot and power-off controls with optional MuPiBox Admin authentication
- MuPiBox display screenshot camera

The integration exposes the physical MuPiBox as **one media player**. Spotify is no longer represented as a second speaker entity; the box itself decides which backend is active and Home Assistant follows that state.

## Requirements

- A MuPiBox-NG installation exposing its local HTTP API
- Default API port: `8090`
- Home Assistant 2026.3 or newer is recommended for local custom-integration branding

## Installation with HACS

Until this repository is included in the default HACS catalog:

1. Open **HACS → Integrations**.
2. Open the menu and select **Custom repositories**.
3. Add `https://github.com/splitti/MuPiBox-homeassistant`.
4. Select category **Integration**.
5. Install **MuPiBox**.
6. Restart Home Assistant.
7. MuPiBox devices advertising `_mupibox._tcp.local.` appear automatically under **Settings → Devices & services → Discovered**. Select **Configure** to add one.
8. Manual setup through **Add integration → MuPiBox** remains available as a fallback.

Updates are published from this repository. The Home Assistant integration uses its own release numbers and does not follow the MuPiBox-NG application version.

## Manual installation

Copy `custom_components/mupibox` to:

`<Home Assistant config>/custom_components/mupibox`

and restart Home Assistant.

## Configuration

For automatically discovered boxes, the config flow already knows the host and API port and only asks for confirmation plus an optional Admin password.

Manual setup asks for:

- MuPiBox host or IP address
- API port (default: `8090`)
- HTTPS on/off
- optional MuPiBox Admin password

MuPiBox-NG 0.1.0-dev builds with discovery support advertise a persistent `box_id`. Home Assistant uses that identity instead of the IP address, so DHCP address changes do not create a second device.

The Admin password is only required for protected maintenance functions such as library rescan, UI restart, reboot, shutdown and display screenshots when Admin protection is enabled.

## Dashboard template

A compact, dependency-free two-view MuPiBox dashboard template is included in the repository. It uses only native Home Assistant cards and supports playback, selectable audio output routing, provider status, display preview, quick actions and a separate diagnostics view.

See [docs/DASHBOARD.md](docs/DASHBOARD.md) for requirements, entity mapping and installation, and [docs/dashboard-template.yaml](docs/dashboard-template.yaml) for the ready-to-copy template.

## Dashboard templates

Ready-to-use Home Assistant dashboard examples are available in [docs/DASHBOARD.md](docs/DASHBOARD.md):

- a compact MuPiBox card for an existing dashboard
- a full responsive Player + Diagnostics dashboard
- direct Audio output selection for available local, Bluetooth, Sonos and Music Assistant targets

The templates use **only built-in Home Assistant cards**. No Mushroom, Button Card, Card Mod, Mini Graph Card or ApexCharts dependency is required. Entity IDs are mapped explicitly so the examples can be adapted to any MuPiBox without assuming a particular box/area name.

## API documentation

See [docs/API.md](docs/API.md) for the API mapping and examples used by the integration.

## Versioning

This project uses semantic versioning independently from MuPiBox-NG.

## HACS validation

The repository includes validation workflows for HACS and Home Assistant Hassfest.

## License

MIT License. See [LICENSE](LICENSE).


## Secure API v1 (0.4.0, opt-in)

Existing NG installations stay on the legacy HTTP API with their saved admin
sessions, device and entity IDs and dashboards. No automatic migration or
re-pairing is performed. API v1 supports both MuPiBox Classic and NG if the
corresponding box firmware implements the shared contract.

For a new API v1 connection, Home Assistant discovers the HTTPS Zeroconf
advertisement (or use manual mode secure_v1, port 8443). In NG Admin -> Smart
Home, click "Home Assistant sicher koppeln" to show the SPKI fingerprint on
the physical box. Enter and verify the fingerprint in the Home Assistant setup
dialog. Return to NG Admin and allow pairing again immediately before
requesting the six-digit code in Home Assistant. Enter the code shown on the
box (valid for 300 seconds). The box grants only read/control by default.

V1 currently exposes a provider-neutral media player plus battery, Wi-Fi,
provider and software-version sensors where supported. Existing legacy NG
entities, including notifications and maintenance controls, remain unchanged.

See docs/classic-api-contract.md for the full protocol, wire schemas,
security requirements and acceptance tests.
