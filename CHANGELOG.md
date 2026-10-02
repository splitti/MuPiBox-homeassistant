# Changelog

## 0.3.0

- Replace the separate Local Player and Spotify Connect entities with one provider-neutral MuPiBox media player while preserving the existing local-player registry identity.
- Remove the obsolete separate Spotify media-player registry entry during setup.
- Read battery percentage and charging state from the current MuPiHAT telemetry endpoint, with fallback for older boxes.
- Add MuPiHAT voltage, current, temperature, hardware and external-power diagnostics.
- Add CPU, RAM, storage and CPU-temperature diagnostics from the current MuPiBox system metrics API.
- Add an active-provider sensor and provider status sensors for Spotify, Music Assistant, Jellyfin, Audible and Sendspin.
- Add a display-message notify entity in addition to the existing TTS announcement entity.
- Keep provider/metrics endpoints optional so older MuPiBox builds continue to load with reduced diagnostics.

## 0.2.1

- Replace the legacy Home Assistant branding with the current MuPiBox-NG icon used by the box UI.

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
