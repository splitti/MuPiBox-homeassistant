# MuPiBox dashboard templates

These examples are designed for the MuPiBox Home Assistant integration **0.3.3 or newer**.

## Dependencies

**Required**

- Home Assistant
- MuPiBox Home Assistant integration

**No additional HACS dashboard cards are required.** The templates use only built-in Home Assistant cards and the modern `sections` view.

**Optional features**

- The display screenshot card needs the MuPiBox `camera` entity. If Admin protection is enabled on the box, the Home Assistant integration needs the Admin password for this protected endpoint.
- Library rescan, UI restart, reboot and power-off buttons likewise require the Admin password when Admin protection is enabled.

The **Audio output** selector itself does not need an Admin password. Its choices are discovered dynamically from the box and can include the local MuPiBox output, paired Bluetooth devices, Sonos targets and Music Assistant targets.

## Before pasting a template

Home Assistant generates entity IDs from the device name and area, so entity IDs are intentionally **not assumed to be identical between boxes**.

Open **Settings → Devices & services → MuPiBox → your box** and copy the matching entity IDs. Replace the placeholders in the examples below.

| Placeholder | MuPiBox entity |
| --- | --- |
| `MUPIBOX_PLAYER` | Media player (`Player`) |
| `MUPIBOX_AUDIO_OUTPUT` | Select (`Audio output`) |
| `MUPIBOX_BATTERY` | Battery sensor |
| `MUPIBOX_WIFI_QUALITY` | Wi-Fi quality sensor |
| `MUPIBOX_NETWORK` | Network reachable binary sensor |
| `MUPIBOX_CHARGING` | Charging binary sensor |
| `MUPIBOX_TTS_ENABLED` | Voice output enabled binary sensor |
| `MUPIBOX_ACTIVE_PROVIDER` | Active provider sensor |
| `MUPIBOX_SPOTIFY` | Spotify status sensor |
| `MUPIBOX_MA` | Music Assistant status sensor |
| `MUPIBOX_JELLYFIN` | Jellyfin status sensor |
| `MUPIBOX_AUDIBLE` | Audible status sensor |
| `MUPIBOX_SENDSPIN` | Sendspin status sensor |
| `MUPIBOX_CPU` | CPU usage sensor |
| `MUPIBOX_RAM` | RAM usage sensor |
| `MUPIBOX_STORAGE` | Storage usage sensor |
| `MUPIBOX_CPU_TEMP` | CPU temperature sensor |
| `MUPIBOX_HAT_TEMP` | MuPiHAT temperature sensor |
| `MUPIBOX_BATTERY_VOLTAGE` | Battery voltage sensor |
| `MUPIBOX_EXTERNAL_POWER` | External power binary sensor |
| `MUPIBOX_CAMERA` | Display camera |
| `MUPIBOX_DISPLAY_NOTIFY` | Notify entity (`Show text on display` / `Text auf Display anzeigen`) |
| `MUPIBOX_RESCAN` | Rescan media library button |
| `MUPIBOX_RESTART_UI` | Restart interface button |
| `MUPIBOX_REBOOT` | Restart box button |
| `MUPIBOX_POWER_OFF` | Power off box button |

## Compact MuPiBox card

Use this inside an existing dashboard. It keeps playback, output routing and the most useful box status in one compact block.

```yaml
type: grid
columns: 1
square: false
cards:
  - type: heading
    heading: MuPiBox
    icon: mdi:music-box
    badges:
      - type: entity
        entity: MUPIBOX_BATTERY
        show_state: true
        color: state
      - type: entity
        entity: MUPIBOX_WIFI_QUALITY
        show_state: true
      - type: entity
        entity: MUPIBOX_ACTIVE_PROVIDER
        show_state: true
  - type: media-control
    entity: MUPIBOX_PLAYER
    name: Wiedergabe
  - type: tile
    entity: MUPIBOX_AUDIO_OUTPUT
    name: Audioausgabe
    icon: mdi:speaker-multiple
    features_position: inline
    features:
      - type: select-options
  - type: grid
    columns: 3
    square: false
    cards:
      - type: tile
        entity: MUPIBOX_BATTERY
        name: Akku
        icon: mdi:battery
      - type: tile
        entity: MUPIBOX_NETWORK
        name: Netzwerk
        icon: mdi:lan-connect
      - type: tile
        entity: MUPIBOX_TTS_ENABLED
        name: Sprachausgabe
        icon: mdi:text-to-speech
```

## Full MuPiBox dashboard

The full template uses two views: **Player** for everyday use and **Diagnostics** for hardware/system details. It stays responsive on phone, tablet and desktop by using Home Assistant's native sections layout.

```yaml
views:
  - title: MuPiBox
    path: player
    icon: mdi:music-box
    type: sections
    max_columns: 3
    sections:
      - type: grid
        column_span: 2
        cards:
          - type: heading
            heading: MuPiBox
            icon: mdi:music-box
            badges:
              - type: entity
                entity: MUPIBOX_BATTERY
                show_state: true
                color: state
              - type: entity
                entity: MUPIBOX_WIFI_QUALITY
                show_state: true
              - type: entity
                entity: MUPIBOX_ACTIVE_PROVIDER
                show_state: true
          - type: media-control
            entity: MUPIBOX_PLAYER
            name: Wiedergabe
            grid_options:
              columns: full
              rows: 4
          - type: tile
            entity: MUPIBOX_AUDIO_OUTPUT
            name: Audioausgabe
            icon: mdi:speaker-multiple
            features_position: inline
            features:
              - type: select-options
            grid_options:
              columns: full
              rows: 2
      - type: grid
        cards:
          - type: heading
            heading: Status
            icon: mdi:heart-pulse
          - type: tile
            entity: MUPIBOX_BATTERY
            name: Akku
            icon: mdi:battery
            features:
              - type: bar-gauge
                min: 0
                max: 100
            grid_options:
              columns: 6
              rows: 2
          - type: tile
            entity: MUPIBOX_CHARGING
            name: Lädt
            icon: mdi:battery-charging
            grid_options:
              columns: 6
              rows: 2
          - type: tile
            entity: MUPIBOX_NETWORK
            name: Netzwerk
            icon: mdi:lan-connect
            grid_options:
              columns: 6
              rows: 2
          - type: tile
            entity: MUPIBOX_TTS_ENABLED
            name: Sprachausgabe
            icon: mdi:text-to-speech
            grid_options:
              columns: 6
              rows: 2
          - type: tile
            entity: MUPIBOX_WIFI_QUALITY
            name: WLAN
            icon: mdi:wifi
            features:
              - type: bar-gauge
                min: 0
                max: 100
            grid_options:
              columns: full
              rows: 2
      - type: grid
        cards:
          - type: heading
            heading: Dienste
            icon: mdi:connection
          - type: tile
            entity: MUPIBOX_SPOTIFY
            name: Spotify
            icon: mdi:spotify
            grid_options: {columns: 6, rows: 2}
          - type: tile
            entity: MUPIBOX_MA
            name: Music Assistant
            icon: mdi:music-circle
            grid_options: {columns: 6, rows: 2}
          - type: tile
            entity: MUPIBOX_JELLYFIN
            name: Jellyfin
            icon: mdi:jellyfish
            grid_options: {columns: 6, rows: 2}
          - type: tile
            entity: MUPIBOX_AUDIBLE
            name: Audible
            icon: mdi:book-music
            grid_options: {columns: 6, rows: 2}
          - type: tile
            entity: MUPIBOX_SENDSPIN
            name: Sendspin
            icon: mdi:cast-audio
            grid_options: {columns: full, rows: 2}
      - type: grid
        cards:
          - type: heading
            heading: Schnellaktionen
            icon: mdi:gesture-tap-button
          - type: tile
            entity: MUPIBOX_RESCAN
            name: Medien neu einlesen
            icon: mdi:database-refresh
            tap_action:
              action: perform-action
              perform_action: button.press
              target: {entity_id: MUPIBOX_RESCAN}
            grid_options: {columns: 6, rows: 2}
          - type: tile
            entity: MUPIBOX_RESTART_UI
            name: Oberfläche neu starten
            icon: mdi:monitor-shimmer
            tap_action:
              action: perform-action
              perform_action: button.press
              target: {entity_id: MUPIBOX_RESTART_UI}
              confirmation:
                text: MuPiBox-Oberfläche neu starten?
            grid_options: {columns: 6, rows: 2}
          - type: tile
            entity: MUPIBOX_REBOOT
            name: Box neu starten
            icon: mdi:restart
            tap_action:
              action: perform-action
              perform_action: button.press
              target: {entity_id: MUPIBOX_REBOOT}
              confirmation:
                text: MuPiBox wirklich neu starten?
            grid_options: {columns: 6, rows: 2}
          - type: tile
            entity: MUPIBOX_POWER_OFF
            name: Box ausschalten
            icon: mdi:power
            tap_action:
              action: perform-action
              perform_action: button.press
              target: {entity_id: MUPIBOX_POWER_OFF}
              confirmation:
                text: MuPiBox wirklich ausschalten?
            grid_options: {columns: 6, rows: 2}

  - title: Diagnose
    path: diagnose
    icon: mdi:chart-box-outline
    type: sections
    max_columns: 3
    sections:
      - type: grid
        column_span: 2
        cards:
          - type: heading
            heading: Leistung
            icon: mdi:speedometer
          - type: history-graph
            title: Auslastung · letzte 6 Stunden
            hours_to_show: 6
            entities:
              - entity: MUPIBOX_CPU
                name: CPU
              - entity: MUPIBOX_RAM
                name: RAM
              - entity: MUPIBOX_STORAGE
                name: Speicher
            grid_options: {columns: full, rows: 5}
          - type: history-graph
            title: Temperaturen · letzte 6 Stunden
            hours_to_show: 6
            entities:
              - entity: MUPIBOX_CPU_TEMP
                name: CPU
              - entity: MUPIBOX_HAT_TEMP
                name: MuPiHAT
            grid_options: {columns: full, rows: 5}
      - type: grid
        cards:
          - type: heading
            heading: Hardware
            icon: mdi:raspberry-pi
          - type: tile
            entity: MUPIBOX_BATTERY
            name: Akku
            icon: mdi:battery
            features:
              - type: bar-gauge
                min: 0
                max: 100
            grid_options: {columns: full, rows: 2}
          - type: tile
            entity: MUPIBOX_BATTERY_VOLTAGE
            name: Akkuspannung
            icon: mdi:sine-wave
            grid_options: {columns: 6, rows: 2}
          - type: tile
            entity: MUPIBOX_EXTERNAL_POWER
            name: Netzteil
            icon: mdi:power-plug
            grid_options: {columns: 6, rows: 2}
          - type: tile
            entity: MUPIBOX_CPU_TEMP
            name: CPU-Temperatur
            icon: mdi:thermometer
            grid_options: {columns: 6, rows: 2}
          - type: tile
            entity: MUPIBOX_HAT_TEMP
            name: MuPiHAT
            icon: mdi:thermometer-lines
            grid_options: {columns: 6, rows: 2}
      - type: grid
        cards:
          - type: heading
            heading: Display
            icon: mdi:monitor-eye
          - type: picture-entity
            entity: MUPIBOX_CAMERA
            name: Live-Screenshot
            show_state: false
            show_name: true
            camera_view: auto
            grid_options: {columns: full, rows: 5}
```

## Optional: direct message composer

Home Assistant `notify` entities are action targets and therefore do not have a persistent state. Home Assistant can show their state as `unknown`; this is expected and does not mean the MuPiBox is unavailable.

For a convenient text box directly on a dashboard, create one native **Text helper** and one native **Script**. This adds no HACS card dependency.

1. Create **Settings → Devices & services → Helpers → Create helper → Text**. Name it `MuPiBox Message` (or `MuPiBox Nachricht`).
2. Create a script that calls `notify.send_message` and targets `MUPIBOX_DISPLAY_NOTIFY`. Use the Text helper's state as the message.
3. Add the following native card to the dashboard:

```yaml
type: entities
entities:
  - entity: input_text.mupibox_message
    name: Text
  - entity: script.mupibox_send_message
    name: Show on display
    icon: mdi:send
```

Example script action (replace the two entity IDs with yours):

```yaml
action: notify.send_message
target:
  entity_id: MUPIBOX_DISPLAY_NOTIFY
data:
  title: Home Assistant
  message: "{{ states('input_text.mupibox_message') }}"
```

The MuPiBox displays this as a transient overlay without interrupting playback. For spoken output, target the separate **Speak announcement** / **Sprachnachricht ausgeben** notify entity instead.

### Notes

- Remove cards for providers you do not use.
- The Audio output dropdown only shows targets that the MuPiBox currently considers selectable and available. A paired Bluetooth device can therefore appear/disappear depending on reachability.
- Provider status sensors deliberately expose only safe status/configuration information and never credentials.
- `Playback engine` is a low-level diagnostic and is disabled by default; it is intentionally not part of these templates.
- The dashboard does not require Card Mod, Mushroom, Button Card, Mini Graph Card or ApexCharts.
