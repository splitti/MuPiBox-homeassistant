"""Versioned MuPiBox Classic/NG API client; legacy API remains untouched."""

from __future__ import annotations

import asyncio
import functools
import ssl
import time
from typing import Any
from urllib.parse import urlsplit

from aiohttp import ClientError, ClientSession

from .api import (
    MuPiBoxApiClient,
    MuPiBoxApiError,
    MuPiBoxAuthenticationError,
    MuPiBoxCannotConnect,
)


class MuPiBoxV1Client(MuPiBoxApiClient):
    """V1 over per-device CA-verified HTTPS with a scoped bearer token."""

    def __init__(
        self,
        session: ClientSession,
        host: str,
        port: int,
        ca_pem: str,
        token: str,
    ) -> None:
        super().__init__(session, host, port, True)
        self._token = token
        self._ca_pem = ca_pem
        self._ssl_context: ssl.SSLContext | None = None
        self._state_cache: tuple[float, dict[str, Any]] | None = None
        self._state_lock = asyncio.Lock()

    async def _state(self) -> dict[str, Any]:
        """Return /state, shared by status, system, MuPiHAT and metrics.

        One coordinator refresh asks for all four within a moment; a short
        cache turns that into a single request to the box.
        """
        # The coordinator gathers status, system and MuPiHAT concurrently;
        # the lock lets the first caller fetch while the others wait for it.
        async with self._state_lock:
            now = time.monotonic()
            if self._state_cache and now - self._state_cache[0] < 2.0:
                return self._state_cache[1]
            raw = await self._v1("GET", "state")
            self._state_cache = (time.monotonic(), raw)
            return raw

    async def _context(self) -> ssl.SSLContext:
        """Build the pinned TLS context once, off the event loop.

        Loading the CA (load_verify_locations) blocks; Home Assistant warns
        about blocking calls inside the event loop.
        """
        if self._ssl_context is None:
            loop = asyncio.get_running_loop()
            self._ssl_context = await loop.run_in_executor(
                None, functools.partial(ssl.create_default_context, cadata=self._ca_pem)
            )
        return self._ssl_context

    async def _v1(
        self, method: str, path: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        url = f"{self.base_url}/api/ha/v1/{path.lstrip('/')}"
        headers = {"Authorization": f"Bearer {self._token}"}
        try:
            async with asyncio.timeout(12):
                async with self._session.request(
                    method,
                    url,
                    ssl=await self._context(),
                    json=data,
                    headers=headers,
                ) as response:
                    if response.content_type != "application/json":
                        raise MuPiBoxApiError("Invalid v1 response format")
                    payload = await response.json()
                    if not isinstance(payload, dict):
                        raise MuPiBoxApiError("Invalid v1 response")
                    if response.status in (401, 403):
                        raise MuPiBoxAuthenticationError(
                            str(payload.get("error", "unauthorized")), status=response.status
                        )
                    if response.status >= 400:
                        # Prefer the human-readable message (e.g. 409 "nothing
                        # loaded to play") over the machine error code.
                        raise MuPiBoxApiError(
                            str(payload.get("message") or payload.get("error", "api_error")),
                            status=response.status,
                        )
                    return payload
        except (TimeoutError, ClientError, OSError, ssl.SSLError) as error:
            raise MuPiBoxCannotConnect(f"MuPiBox v1 connection failed: {error}") from error

    async def async_get_health(self) -> dict[str, Any]:
        result = await self._v1("GET", "health")
        return {"status": "ok" if result.get("ok") else "error"}

    async def async_get_info(self) -> dict[str, Any]:
        raw = await self._v1("GET", "info")
        return {
            "box_id": raw.get("device_id"),
            "version": raw.get("software_version"),
            "generation": raw.get("generation"),
            "capabilities": raw.get("capabilities", []),
            "name": raw.get("name"),
            "web_url": raw.get("web_url"),
        }

    async def async_get_status(self) -> dict[str, Any]:
        raw = await self._state()
        playback = raw.get("playback", {})
        if not isinstance(playback, dict):
            raise MuPiBoxApiError("Invalid playback data")
        track = {
            "id": playback.get("media_id"),
            "title": playback.get("title"),
            "artist": playback.get("artist"),
            "provider": playback.get("provider", "local"),
        }
        state = {
            "idle": "stopped",
            "unavailable": "error",
        }.get(playback.get("state"), playback.get("state"))
        cover = None
        if playback.get("provider") == "spotify":
            candidate = str(playback.get("cover_url") or "")
            parsed = urlsplit(candidate)
            if parsed.scheme == "https" and parsed.hostname in {
                "i.scdn.co", "mosaic.scdn.co",
            }:
                cover = candidate
        return {
            "state": state,
            "queue": [track] if playback.get("title") else [],
            "index": 0 if playback.get("title") else -1,
            "folder": playback.get("album"),
            "duration": playback.get("duration"),
            "position": playback.get("position"),
            "volume": playback.get("volume"),
            "max_volume": 100,
            "cover": cover,
        }

    async def async_get_system(self) -> dict[str, Any]:
        raw = await self._state()
        device = raw.get("device", {})
        if not isinstance(device, dict):
            return {}
        signal = device.get("wifi_signal_dbm")
        battery = device.get("battery_percent")
        return {
            "wifi": {
                "connected": isinstance(signal, (int, float)),
                "signal_dbm": signal,
                "ipv4": device.get("ip_address"),
            },
            "battery": {
                "available": isinstance(battery, (int, float)),
                "percent": battery,
                "charging": device.get("charging"),
            },
            "power_state": device.get("power_state"),
        }

    async def async_get_spotify_status(self) -> dict[str, Any]:
        return {}

    async def async_get_mupihat_status(self) -> dict[str, Any]:
        """Map the optional MuPiHAT fields of /state to the legacy schema.

        Boxes without a MuPiHAT (or older firmware) send none of them; then
        the MuPiHAT entities stay unavailable instead of showing zeros.
        """
        raw = await self._state()
        device = raw.get("device", {})
        if not isinstance(device, dict) or "external_power" not in device:
            return {}
        battery = device.get("battery_percent")
        return {
            "hardware_available": True,
            "battery_present": isinstance(battery, (int, float)),
            "battery_percent": battery,
            "charging": device.get("charging"),
            "external_power": device.get("external_power"),
            "battery_voltage_mv": device.get("battery_voltage_mv"),
            "battery_current_ma": device.get("battery_current_ma"),
            "temperature_c": device.get("mupihat_temperature_c"),
        }

    async def async_get_provider_status(self) -> dict[str, Any]:
        return {}

    async def async_get_output_targets(self) -> dict[str, Any]:
        return await self._v1("GET", "outputs")

    async def async_select_output_target(self, target_id: str) -> dict[str, Any]:
        return await self._v1("POST", "outputs/select", {"target_id": target_id})

    async def async_show_message(self, message: str, *, title: str | None = None, duration_ms: int = 8000) -> dict[str, Any]:
        return await self._v1("POST", "message", {"message": message, "title": title or "", "duration_ms": duration_ms})

    async def async_speak(self, text: str, source_ref: str = "home-assistant") -> dict[str, Any]:
        del source_ref
        return await self._v1("POST", "speak", {"text": text})

    async def async_screenshot(self) -> bytes:
        import asyncio
        from aiohttp import ClientError
        try:
            async with asyncio.timeout(12):
                async with self._session.get(
                    f"{self.base_url}/api/ha/v1/screenshot",
                    ssl=await self._context(),
                    headers={"Authorization": f"Bearer {self._token}"},
                ) as response:
                    if response.status != 200 or response.content_type != "image/png":
                        raise MuPiBoxApiError("Screenshot unavailable", status=response.status)
                    image = await response.read()
                    if len(image) > 8 * 1024 * 1024:
                        raise MuPiBoxApiError("Screenshot too large")
                    return image
        except (TimeoutError, ClientError, OSError) as error:
            raise MuPiBoxCannotConnect(f"Screenshot failed: {error}") from error

    async def async_get_system_metrics(self) -> dict[str, Any]:
        raw = await self._state()
        metrics = raw.get("metrics", {})
        return metrics if isinstance(metrics, dict) else {}

    async def async_get_update(self) -> dict[str, Any]:
        return await self._v1("GET", "update")

    async def async_get_sleep_timer(self) -> dict[str, Any]:
        from .sleep_timer_contract import normalize_sleep_timer

        raw = await self._state()
        try:
            return normalize_sleep_timer(raw.get("sleep_timer"))
        except (ValueError, TypeError) as error:
            raise MuPiBoxApiError(f"Invalid sleep_timer state: {error}") from error

    async def async_set_sleep_timer(self, minutes: int) -> dict[str, Any]:
        from .sleep_timer_contract import MAX_SLEEP_TIMER_MINUTES

        if type(minutes) is not int or not 0 <= minutes <= MAX_SLEEP_TIMER_MINUTES:
            raise ValueError("Timer must be an integer from 0 to 720 minutes")
        result = await self._v1("POST", "sleep_timer", {"minutes": minutes})
        # A status refresh must not see stale data from the two-second cache.
        async with self._state_lock:
            self._state_cache = None
        return result

    async def async_power(self, action: str) -> dict[str, Any]:
        if action not in ("reboot", "poweroff"):
            raise ValueError("Invalid power action")
        return await self._v1("POST", "power", {"action": action})

    async def async_get_admin_auth(self) -> dict[str, Any]:
        return {"protected": False, "authenticated": False}

    async def async_get_library(self) -> list[dict[str, Any]]:
        return []

    async def async_command(self, action: str, **kwargs: Any) -> dict[str, Any]:
        command = "set_volume" if action == "volume" else action
        data: dict[str, Any] = {"command": command}
        if action == "volume":
            data["value"] = kwargs.get("value")
        if action == "seek":
            data["position"] = kwargs.get("value")
        return await self._v1("POST", "control", data)
