# MuPiBox for Home Assistant

Home Assistant integration for **MuPiBox / MuPiBox-NG**.

**Author and maintainer:** Olaf Splitt  
**Website:** https://mupibox.de  
**MuPiBox-NG:** https://github.com/splitti/MuPiBox-NG  
**Home Assistant integration version:** 0.1.1

The Home Assistant integration is versioned independently from MuPiBox-NG.

## Features

- Local media player with play, pause, stop, previous/next, seek and volume
- Home Assistant media browser for local MuPiBox media
- Separate Spotify Connect media player with transport, seek and volume control
- TTS announcements through a Home Assistant notify entity
- Battery, Wi-Fi, connectivity and diagnostic sensors
- Library rescan and UI restart controls
- Reboot and power-off controls with optional MuPiBox Admin authentication
- MuPiBox display screenshot camera

Local playback and Spotify are exposed as separate media-player entities and have separate volume controls.

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
7. Go to **Settings → Devices & services → Add integration → MuPiBox**.

Updates are published from this repository. The Home Assistant integration uses its own release numbers and does not follow the MuPiBox-NG application version.

## Manual installation

Copy `custom_components/mupibox` to:

`<Home Assistant config>/custom_components/mupibox`

and restart Home Assistant.

## Configuration

The config flow asks for:

- MuPiBox host or IP address
- API port (default: `8090`)
- HTTPS on/off
- optional MuPiBox Admin password

The Admin password is only required for protected maintenance functions such as library rescan, UI restart, reboot, shutdown and display screenshots when Admin protection is enabled.

## API documentation

See [docs/API.md](docs/API.md) for the API mapping and examples used by the integration.

## Versioning

This project uses semantic versioning independently from MuPiBox-NG.

## HACS validation

The repository includes validation workflows for HACS and Home Assistant Hassfest.

## License

MIT License. See [LICENSE](LICENSE).
