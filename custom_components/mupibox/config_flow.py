"""Config flow for MuPiBox-NG."""

from __future__ import annotations

from typing import Any
import uuid

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .classic_contract import CLASSIC_GENERATION, discovery_generation
from .v1_api import MuPiBoxV1Client
from .v1_trust import probe_device_key, fetch_verified_ca, normalized_fingerprint
from .api import (
    MuPiBoxApiClient,
    MuPiBoxApiError,
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


def _txt_value(properties: dict[str, Any], key: str) -> str:
    value = properties.get(key, "")
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace").strip()
    return str(value).strip()


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
        self._v1_data: dict[str, Any] | None = None
        self._v1_expected_id = ""
        self._v1_name = ""
        self._v1_generation = ""
        self._v1_fingerprint = ""
        self._v1_cert_digest: bytes = b""
        self._v1_ca = ""
        self._v1_client_id = str(uuid.uuid4())
        self._v1_pairing_id = ""
        self._discovered_data: dict[str, Any] | None = None
        self._discovered_title = "MuPiBox-NG"
        self._discovered_box_id = ""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle setup initiated by the user."""
        errors: dict[str, str] = {}

        if user_input is not None and user_input.get("connection_type") == "secure_v1":
            host = str(user_input[CONF_HOST]).strip()
            port = int(user_input[CONF_PORT])
            self._v1_data = {
                CONF_HOST: host, CONF_PORT: port,
                CONF_USE_SSL: True, "protocol": "ha_v1",
            }
            self._v1_name = f"MuPiBox ({host})"
            try:
                self._v1_fingerprint, self._v1_cert_digest = await probe_device_key(host, port)
            except ValueError:
                errors["base"] = "cannot_connect"
            else:
                return await self.async_step_v1_trust()
        elif user_input is not None:
            user_input.pop("connection_type", None)
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
                vol.Optional("connection_type", default="legacy_ng"): vol.In(
                    ["legacy_ng", "secure_v1"]
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle MuPiBox mDNS/Zeroconf discovery."""
        if (_txt_value(discovery_info.properties, "transport").lower() == "https"
                and _txt_value(discovery_info.properties, "api_version") == "1"):
            return await self._async_v1_discovery(discovery_info)
        host = discovery_info.host.rstrip(".")
        port = int(discovery_info.port or DEFAULT_PORT)
        properties = discovery_info.properties
        if discovery_generation(properties) == CLASSIC_GENERATION:
            return self.async_abort(reason="classic_pairing_not_supported")
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

    async def _async_v1_discovery(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Start opt-in, pin-verified v1 flow without altering legacy NG."""
        host = discovery_info.host.rstrip(".")
        self._v1_expected_id = _txt_value(discovery_info.properties, "device_id")
        self._v1_generation = discovery_generation(discovery_info.properties)
        if not self._v1_expected_id or self._v1_generation not in {"ng", "classic"}:
            return self.async_abort(reason="invalid_discovery")
        await self.async_set_unique_id(self._v1_expected_id)
        existing = next(
            (entry for entry in self.hass.config_entries.async_entries(DOMAIN)
             if entry.unique_id == self._v1_expected_id),
            None,
        )
        if existing is not None:
            # Never change an existing legacy NG installation to the TLS API.
            # A paired v1 installation, however, must follow DHCP address changes.
            if existing.data.get("protocol") == "ha_v1":
                self._abort_if_unique_id_configured(
                    updates={
                        CONF_HOST: host,
                        CONF_PORT: int(discovery_info.port),
                        CONF_USE_SSL: True,
                    }
                )
            self._abort_if_unique_id_configured()
        self._v1_data = {
            CONF_HOST: host,
            CONF_PORT: int(discovery_info.port),
            CONF_USE_SSL: True,
            "protocol": "ha_v1",
        }
        self._v1_name = _discovery_name(discovery_info)
        try:
            self._v1_fingerprint, self._v1_cert_digest = await probe_device_key(
                host, int(discovery_info.port)
            )
        except ValueError:
            return self.async_abort(reason="cannot_connect")
        return await self.async_step_v1_trust()

    async def async_step_v1_trust(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Require user to type the SPKI fingerprint shown on the box."""
        if self._v1_data is None:
            return self.async_abort(reason="invalid_discovery")
        errors: dict[str, str] = {}
        if user_input is not None:
            if normalized_fingerprint(str(user_input["fingerprint"])) != self._v1_fingerprint:
                errors["base"] = "invalid_fingerprint"
            else:
                try:
                    self._v1_ca = await fetch_verified_ca(
                        async_get_clientsession(self.hass),
                        self._v1_data[CONF_HOST],
                        self._v1_data[CONF_PORT],
                        self._v1_cert_digest,
                    )
                except ValueError:
                    errors["base"] = "cannot_connect"
                else:
                    return await self.async_step_v1_start()
        return self.async_show_form(
            step_id="v1_trust",
            data_schema=vol.Schema({vol.Required("fingerprint"): str}),
            errors=errors,
            description_placeholders={"name": self._v1_name},
        )

    async def async_step_v1_start(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """User enables pairing in box Admin before requesting a code."""
        if self._v1_data is None or not self._v1_ca:
            return self.async_abort(reason="invalid_discovery")
        errors: dict[str, str] = {}
        if user_input is not None:
            client = MuPiBoxV1Client(
                async_get_clientsession(self.hass),
                self._v1_data[CONF_HOST],
                self._v1_data[CONF_PORT],
                self._v1_ca,
                "",
            )
            try:
                response = await client._v1(
                    "POST", "pair/start",
                    {
                        "client_name": "Home Assistant",
                        "client_id": self._v1_client_id,
                        "requested_scopes": ["read", "control"],
                    },
                )
            except (MuPiBoxApiError, MuPiBoxAuthenticationError, MuPiBoxCannotConnect):
                errors["base"] = "pairing_not_enabled"
            else:
                self._v1_pairing_id = str(response.get("pairing_id", ""))
                if self._v1_pairing_id:
                    return await self.async_step_v1_confirm()
                errors["base"] = "unknown"
        return self.async_show_form(
            step_id="v1_start",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders={"name": self._v1_name},
        )

    async def async_step_v1_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Exchange the single-use displayed code for a scoped token."""
        if self._v1_data is None or not self._v1_pairing_id:
            return self.async_abort(reason="invalid_discovery")
        errors: dict[str, str] = {}
        if user_input is not None:
            client = MuPiBoxV1Client(
                async_get_clientsession(self.hass),
                self._v1_data[CONF_HOST],
                self._v1_data[CONF_PORT],
                self._v1_ca,
                "",
            )
            code = str(user_input.get("code", "")).replace(" ", "")
            try:
                response = await client._v1("POST", "pair/confirm", {
                    "pairing_id": self._v1_pairing_id,
                    "client_id": self._v1_client_id,
                    "code": code,
                })
            except (MuPiBoxAuthenticationError, MuPiBoxApiError):
                errors["base"] = "invalid_auth"
            except MuPiBoxCannotConnect:
                errors["base"] = "cannot_connect"
            else:
                token = response.get("access_token")
                actual_id = str(response.get("device_id", ""))
                if ((self._v1_expected_id and actual_id != self._v1_expected_id)
                        or not actual_id or not isinstance(token, str) or not token):
                    return self.async_abort(reason="invalid_discovery")
                if any(
                    other.unique_id == actual_id
                    for other in self.hass.config_entries.async_entries(DOMAIN)
                ):
                    # No orphaned remote credentials when a manually entered box
                    # is already installed through the legacy NG integration.
                    try:
                        paired = MuPiBoxV1Client(
                            async_get_clientsession(self.hass),
                            self._v1_data[CONF_HOST],
                            self._v1_data[CONF_PORT],
                            self._v1_ca,
                            token,
                        )
                        await paired._v1(
                            "POST", "pair/revoke", {"client_id": self._v1_client_id}
                        )
                    except MuPiBoxApiError:
                        pass
                    return self.async_abort(reason="already_configured")
                await self.async_set_unique_id(actual_id, raise_on_progress=False)
                self._abort_if_unique_id_configured()
                data = dict(self._v1_data)
                data.update({
                    "access_token": token,
                    "ca_pem": self._v1_ca,
                    "generation": self._v1_generation,
                    "client_id": self._v1_client_id,
                })
                return self.async_create_entry(title=self._v1_name, data=data)
        return self.async_show_form(
            step_id="v1_confirm",
            data_schema=vol.Schema({vol.Required("code"): str}),
            errors=errors,
            description_placeholders={"name": self._v1_name},
        )
