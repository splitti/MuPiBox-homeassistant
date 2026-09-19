"""Config flow for MuPiBox-NG."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    MuPiBoxApiClient,
    MuPiBoxAuthenticationError,
    MuPiBoxCannotConnect,
)
from .const import (
    CONF_ADMIN_PASSWORD,
    CONF_USE_SSL,
    DEFAULT_PORT,
    DEFAULT_USE_SSL,
    DOMAIN,
)


async def _validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    api = MuPiBoxApiClient(
        async_get_clientsession(hass),
        data[CONF_HOST],
        data[CONF_PORT],
        data.get(CONF_USE_SSL, False),
        data.get(CONF_ADMIN_PASSWORD, ""),
    )
    health = await api.async_get_health()
    if health.get("status") != "ok":
        raise MuPiBoxCannotConnect("MuPiBox health endpoint did not return status=ok")

    auth = await api.async_get_admin_auth()
    if auth.get("protected") and data.get(CONF_ADMIN_PASSWORD):
        await api.async_login()

    return health


class MuPiBoxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a MuPiBox-NG config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle setup initiated by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_HOST] = str(user_input[CONF_HOST]).strip()
            try:
                await _validate_input(self.hass, user_input)
            except MuPiBoxAuthenticationError:
                errors["base"] = "invalid_auth"
            except MuPiBoxCannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001 - config flows must convert unexpected errors
                errors["base"] = "unknown"
            else:
                scheme = "https" if user_input.get(CONF_USE_SSL) else "http"
                unique_id = (
                    f"{scheme}://{user_input[CONF_HOST].lower()}:{user_input[CONF_PORT]}"
                )
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"MuPiBox-NG ({user_input[CONF_HOST]})",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
                vol.Required(CONF_USE_SSL, default=DEFAULT_USE_SSL): bool,
                vol.Optional(CONF_ADMIN_PASSWORD, default=""): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
