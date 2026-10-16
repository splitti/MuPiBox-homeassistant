# Classic sleep timer — implementation guide

This is the **Classic developer implementation checklist for after 5.0.11**;
the presence of this document does **not** mean Classic already ships the API.
The normative API contract and TLS/pairing rules are in
[classic-api-contract.md](classic-api-contract.md), power-off sleep timer section.

## Existing Classic implementation

| File | Purpose |
|---|---|
| `scripts/mupibox/sleep_timer.sh` | Local seconds countdown, `/tmp/.time2sleep`, fade-out over final 20s, player stop, volume restoration, poweroff |
| `src/backend-api/src/eltern/routes.ts` | Parent app GET /api/app/sleeptimer, POST /api/app/sleeptimer/start and /stop (session + CSRF, not v1 auth) |
| `AdminInterface/www/parental.php` | Admin timer |
| `scripts/telegram/telegram_receiver.py` | Telegram `/sleep` starts countdown script directly |

WARNING: the temporary countdown file can outlive the running process,
so file presence alone must not mean `active:true`. Telegram can currently
launch a second countdown without explicitly canceling the old one.
Both issues must be fixed before advertising this new capability.

## API to implement

1. GET /api/ha/v1/info (read): append `sleep_timer` to `capabilities`
   only when all endpoints work in this build.
2. POST /api/ha/v1/sleep_timer (power): strict Content-Type application/json,
   body `{"minutes":30}`; integer 1–720 starts/replaces, 0 cancels.
   Use TLS + existing v1 Bearer scope authorization. Never accept the admin
   session as authorization. Respond 200 after the timer operation persists:

       {"success":true,"sleep_timer":{"active":true,
         "ends_at":"2026-10-17T00:45:00+02:00","remaining_s":1800}}

   On stop:

       {"success":true,"sleep_timer":{"active":false,
         "ends_at":null,"remaining_s":0}}

3. GET /api/ha/v1/state (read): add top-level `sleep_timer` (same
   schema, NO new endpoint needed). Set timezone-aware RFC-3339
   `ends_at`, integer `remaining_s` rounded up, and inactive
   `{"active":false,"ends_at":null,"remaining_s":0}`. Reflect app/Telegram
   actions immediately. The end timestamp describes start of shutdown
   sequence, not instantaneous physical power-off.

## Single-timer service

- Centralize ownership: App, Admin, Telegram and HA must all call one
  timer manager/service. Do not let each client spawn its own process.
- Persist an absolute deadline with time zone, verify actual process
  state and recover after backend restart. Clear completed countdowns
  so power-off does not repeat on next boot.
- Serialize start/replace/stop. Make the old timer irrevocably canceled
  before acknowledging replacement. Avoid broad `pkill -f` and duplicate
  `nohup` instances. If system shutdown has already been scheduled
  irrevocably, never claim an effective cancellation.
- Reuse `sleep_timer.sh`'s existing 20-second fade-out, player stop,
  restoration of volume and regular shutdown. Cancel/replacement during
  fade must restore the original volume.
- Only pass validated integer seconds as arguments to `spawn` / `execFile`,
  not interpolated shell strings. Reject unknown JSON fields.
- Older Classic local UI supports up to 1440 minutes; the common
  Home Assistant v1 contract intentionally limits requests to 720.

## Errors (same for Classic and NG)

| Situation | HTTP and error code |
|---|---|
| Plain HTTP | 426 `https_required` |
| Unpaired/invalid Bearer | 401 `unauthorized` |
| Token without power scope | 403 `insufficient_scope` |
| Invalid JSON, content type, unknown fields | 400 `invalid_request` |
| Missing/null/text/float/negative/>720 minutes | 400 `invalid_value` or 400 `invalid_request` for type failures |
| Unavailable timer manager or persistence | 503 `temporarily_unavailable` |
| Successful start/replacement/stop | 200 with `success:true` and `sleep_timer` |

## Acceptance checklist

- [ ] Feature is NOT advertised on older/unimplemented Classic firmware.
- [ ] Start 30 min; /state shows 1800 seconds approximately and RFC-3339 timestamp.
- [ ] Replace with 45 min; original 30-min countdown cannot power off later.
- [ ] Stop 0 twice; both calls succeed and restored original volume.
- [ ] Telegram/App/Admin/HA all see the same countdown, whichever client changes it.
- [ ] Read-only token can read, but cannot start/replace/stop (403).
- [ ] HTTP, unauthenticated, invalid numbers, unknown fields are rejected without mutation.
- [ ] Backend restart and overdue deadline resume safely; completed timer does not fire after next boot.
- [ ] HA disconnect does not stop local timer.
- [ ] Expiry triggers fade, playback stop and full box shutdown.
- [ ] Old Classic/NG devices without capability show no HA timer entities.

HA integration references: `custom_components/mupibox/v1_api.py`,
`number.py`, `sensor.py`, `coordinator.py`, and
`tests/test_sleep_timer_contract.py`. Never fork the HA integration
for Classic; both generations use the same v1 contract.
