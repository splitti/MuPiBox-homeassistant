"""Constants for the MuPiBox-NG integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "mupibox"

CONF_USE_SSL = "use_ssl"
CONF_ADMIN_PASSWORD = "admin_password"

DEFAULT_PORT = 8090
DEFAULT_USE_SSL = False

UPDATE_INTERVAL = timedelta(seconds=5)
LIBRARY_UPDATE_INTERVAL_SECONDS = 60
INFO_UPDATE_INTERVAL_SECONDS = 300
AUTH_UPDATE_INTERVAL_SECONDS = 60

PLATFORMS = ["media_player", "sensor", "binary_sensor", "button", "notify", "camera"]
