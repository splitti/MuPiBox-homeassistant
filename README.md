# MuPiBox for Home Assistant

Official HACS custom integration for **MuPiBox Classic and MuPiBox NG**.

**Maintainer:** Olaf Splitt ([@splitti](https://github.com/splitti))  
**Website:** https://mupibox.de  
**Project documentation:** https://docs.mupibox.de  
**Integration version in `manifest.json`:** **0.5.3** (19 October 2026)  
**Repository:** https://github.com/splitti/MuPiBox-homeassistant

The integration has its **own version numbers**, independently of the MuPiBox Classic and NG firmware versions. The installed HACS version is determined by the latest published release; the version above is the version currently declared in the main branch.

> **Official HACS catalog:** [The addition was approved and merged on 19 October 2026](https://github.com/hacs/default/pull/11101). Adding a custom repository is no longer necessary once your HACS catalog has refreshed.

## Compatibility: Classic and NG

Both generations use the same secure Home Assistant integration, provided the installed firmware implements the **MuPiBox HTTPS Home Assistant API v1** contract. A firmware's branding or the presence of older HTTP endpoints alone is **not** proof of API v1 compatibility.

- **MuPiBox NG:** supports secure API v1 onboarding and the features described below, subject to firmware capabilities.
- **MuPiBox Classic:** is recognized separately (generation `classic`). A Classic firmware implementing the shared API v1 contract can be paired and controlled in the same way. Available entities follow the capabilities and data provided by that box.
- **Existing legacy NG entries:** continue to work without automatic migration. New installations **cannot** be configured with legacy HTTP/admin-password onboarding.
- Device names and generations are displayed during discovery (for example, **MuPiBox Classic – Kinderzimmer** and **MuPiBox NG – Wohnzimmer**) so multiple boxes can be distinguished.
- One Home Assistant device and one provider-neutral media player are created per paired MuPiBox; no extra Spotify speaker is created.

The [versioned Classic/NG API contract](docs/classic-api-contract.md) defines requirements for firmware developers; it does not guarantee that every Classic build has all endpoints.

## Install from HACS

1. Open **HACS** in Home Assistant and search for **MuPiBox**.
2. Select the integration and choose **Download**.
3. Restart Home Assistant.
4. Ensure **Smart Home / automatic discovery** is enabled on the MuPiBox. Open **Settings → Devices & services** in Home Assistant and select the discovered box. Alternatively, choose **Add integration → MuPiBox** and enter its hostname/IP and **HTTPS port 8443**.
5. On the MuPiBox, open **Admin → Smart Home → Home Assistant sicher koppeln** (equivalent label on Classic). Enable local pairing approval.
6. Compare the **64-character SHA-256 SPKI fingerprint** displayed in the box's Admin interface with the fingerprint requested by Home Assistant. Copy/paste or enter it only after confirming it matches. This checks the box's TLS identity independently from mDNS.
7. Choose any additional permissions (`notify` for display messages/TTS and/or `power` for reboot, shutdown and the optional power-off timer), approve pairing locally and enter the **six-digit code shown on the box** in Home Assistant. The code is valid for up to five minutes.

**No MuPiBox Admin password is required for a new secure API v1 pairing.** HACS only installs/updates the integration; secure pairing takes place through Home Assistant.

If the integration does not appear immediately in HACS, refresh HACS's catalog and try again. Older instructions describing HACS **Custom repositories** are only a fallback, not the normal installation path.

## Features in secure API v1 (0.5.3)

| Feature | Availability |
| --- | --- |
| Play, pause, stop, next/previous, seek, volume; currently playing title and provider | Included with `read` / `control`, if the box exposes playback |
| Battery percentage, charging, MuPiHAT current/voltage/temperature | When supported and reported by the box; absent hardware is not shown as zero |
| Wi-Fi connectivity/signal, network status, CPU/RAM/storage, CPU temperature | Diagnostics where the box reports values |
| Operating state (playing, in use, idle, display off, standby), software version | Where firmware supplies these fields |
| Select the audio output (local/Bluetooth/other targets) | Based on currently available/selectable outputs supplied by the box |
| View a display screenshot as a camera entity | `read` permission; requires the screenshot endpoint |
| Check update availability | Diagnostic binary sensor via secure `/update` endpoint |
| Display a message or make a TTS announcement | Additional **`notify`** permission |
| Reboot or shut down the box | Additional **`power`** permission |
| Power-off timer (0–720 minutes; `0` cancels) and “Power off at” sensor | Only when firmware advertises `sleep_timer`. Setting requires `power`; reading the end timestamp requires `read` |

The power-off timer shuts down the **whole device**, not just playback. It is distinct from parental-control playback limits. See [Classic sleep-timer firmware notes](docs/CLASSIC_SLEEP_TIMER.md).

**Not yet mapped over secure API v1:** legacy HTTP library browsing, library-rescan button, UI-restart button and detailed individual provider-status sensors. Do not assume these controls exist in a newly paired Classic/NG device just because they appear in an older dashboard.

### Extend permissions later (without losing entities)

Open **Settings → Devices & services → MuPiBox → Configure**, choose notifications/TTS and/or power, approve a fresh pairing on the box and enter the new six-digit code. The integration updates the existing configuration entry, preserving its device identity and Home Assistant entity registry IDs. Existing tokens are **not silently given additional permissions**.

## Existing legacy HTTP installations

Previously configured NG connections remain supported to avoid breaking automations. Their earlier features can include media browsing, direct `spotify:` URIs, per-provider status, library rescan and UI restart, along with screenshots, notifications, output routing and protected Admin actions. They may use local HTTP port `8090` and an optional Admin password.

**Do not use legacy HTTP for new Home Assistant onboarding.** To change an older entry to API v1, first back up your entity IDs, dashboards and automations; removing and re-adding it may require updating references.

## Dashboard examples and API reference

- [Dashboard templates](docs/DASHBOARD.md) — built-in Home Assistant cards, a feature-availability matrix and optional timer controls
- [Home Assistant API guide](docs/API.md) — secure v1 pairing, permissions and legacy API reference
- [Shared Classic/NG API v1 contract](docs/classic-api-contract.md) — protocol and security requirements
- [Classic sleep-timer implementation guide](docs/CLASSIC_SLEEP_TIMER.md) — developer reference

## Manual installation (optional)

Download a released version and copy `custom_components/mupibox` to `<Home Assistant config>/custom_components/mupibox`, then restart Home Assistant. **HACS installation is recommended** for updates.

## Validation, support and license

The repository includes HACS and Hassfest validation workflows. Report problems and firmware incompatibilities in [GitHub Issues](https://github.com/splitti/MuPiBox-homeassistant/issues), including integration version, box generation, box firmware version and the unsupported capability (without fingerprints, pairing codes or tokens).

MIT License — see [LICENSE](LICENSE).
