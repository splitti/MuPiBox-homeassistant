"""Config flow for MuPiBox-NG."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

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


def _endpoint_unique_id(data: dict[str, Any]) -> str:
    """Return the legacy endpoint identity for older MuPiBox versions."""
    scheme = "https" if data.get(CONF_USE_SSL) else "http"
    return f"{scheme}://{str(data[CONF_HOST]).lower()}:{data[CONF_PORT]}"


def _discovery_name(discovery_info: ZeroconfServiceInfo) -> str:
    """Return the human-readable mDNS instance name."""
    suffix = "._mupibox._tcp.local."
    name = discovery_info.name
    if name.lower().endswith(suffix):
        name = name[: -len(suffix)]
    return name.rstrip(".") or "MuPiBox-NG"


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

    info = await api.async_get_info()
    auth = await api.async_get_admin_auth()
    if auth.get("protected") and data.get(CONF_ADMIN_PASSWORD):
        await api.async_login()

    return info


class MuPiBoxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a MuPiBox-NG config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._discovered_data: dict[str, Any] | None = None
        self._discovered_title = "MuPiBox-NG"
        self._discovered_box_id = ""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle setup initiated by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            user_input[CONF_HOST] = str(user_input[CONF_HOST]).strip()
            try:
                info = await _validate_input(self.hass, user_input)
            except MuPiBoxAuthenticationError:
                errors["base"] = "invalid_auth"
            except MuPiBoxCannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001 - config flows must convert unexpected errors
                errors["base"] = "unknown"
            else:
                unique_id = str(info.get("box_id", "")).strip() or _endpoint_unique_id(
                    user_input
                )
                await self.async_set_unique_id(unique_id, raise_on_progress=False)
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

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle MuPiBox mDNS/Zeroconf discovery."""
        host = discovery_info.host.rstrip(".")
        port = int(discovery_info.port or DEFAULT_PORT)
        properties = discovery_info.properties
        advertised_id = str(properties.get("id", "")).strip()

        if advertised_id:
            await self.async_set_unique_id(advertised_id)
            self._abort_if_unique_id_configured(
                updates={
                    CONF_HOST: host,
                    CONF_PORT: port,
                    CONF_USE_SSL: False,
                }
            )

        data: dict[str, Any] = {
            CONF_HOST: host,
            CONF_PORT: port,
            CONF_USE_SSL: False,
            CONF_ADMIN_PASSWORD: "",
        }
        try:
            info = await _validate_input(self.hass, data)
        except MuPiBoxCannotConnect:
            return self.async_abort(reason="cannot_connect")
        except Exception:  # noqa: BLE001 - discovery must fail closed
            return self.async_abort(reason="invalid_discovery")

        box_id = str(info.get("box_id", "")).strip()
        if not box_id or (advertised_id and advertised_id != box_id):
            return self.async_abort(reason="invalid_discovery")

        await self.async_set_unique_id(box_id)
        self._abort_if_unique_id_configured(
            updates={
                CONF_HOST: host,
                CONF_PORT: port,
                CONF_USE_SSL: False,
            }
        )

        self._discovered_data = data
        self._discovered_box_id = box_id
        self._discovered_title = _discovery_name(discovery_info)
        self.context.update(
            {
                "title_placeholders": {"name": self._discovered_title},
                "configuration_url": f"http://{host}:{port}",
            }
        )
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm a discovered MuPiBox and optionally add Admin credentials."""
        if self._discovered_data is None:
            return self.async_abort(reason="invalid_discovery")

        errors: dict[str, str] = {}
        if user_input is not None:
            data = dict(self._discovered_data)
            data[CONF_ADMIN_PASSWORD] = str(
                user_input.get(CONF_ADMIN_PASSWORD, "")
            ).strip()
            try:
                info = await _validate_input(self.hass, data)
            except MuPiBoxAuthenticationError:
                errors["base"] = "invalid_auth"
            except MuPiBoxCannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                box_id = str(info.get("box_id", "")).strip()
                if box_id != self._discovered_box_id:
                    return self.async_abort(reason="invalid_discovery")
                return self.async_create_entry(
                    title=self._discovered_title,
                    data=data,
                )

        return self.async_show_form(
            step_id="zeroconf_confirm",
            data_schema=vol.Schema(
                {vol.Optional(CONF_ADMIN_PASSWORD, default=""): str}
            ),
            errors=errors,
            description_placeholders={"name": self._discovered_title},
        )
