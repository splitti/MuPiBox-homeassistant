# Changelog

## 0.2.0

- Add automatic MuPiBox discovery through mDNS/Zeroconf (`_mupibox._tcp.local.`).
- Use the persistent MuPiBox `box_id` as the stable identity for new setups.
- Update stored host and port automatically when discovery sees an existing box at a new address.
- Migrate existing URL-based config/entity/device identities to `box_id` without changing Home Assistant entity IDs or user customizations.
- Add a discovery confirmation flow with optional Admin credentials.

## 0.1.1

- Release workflow now waits for successful HACS and hassfest validation before publishing.
- Publication metadata and branding prepared for HACS default repository submission.

## 0.1.0

Initial standalone Home Assistant integration for MuPiBox.

- Local MuPiBox media player
- Spotify Connect media player
- Separate local and Spotify volume controls
- Local media browser
- TTS announcement notify entity
- Battery, Wi-Fi and connectivity sensors
- Diagnostic entities
- Library rescan, UI restart, reboot and power-off buttons
- Display screenshot camera
- Config flow with optional MuPiBox Admin authentication
