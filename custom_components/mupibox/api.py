"""Async HTTP client for the MuPiBox-NG API."""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import Any

from aiohttp import ClientError, ClientSession
from yarl import URL


class MuPiBoxApiError(Exception):
    """Base exception raised by the MuPiBox API client."""

    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class MuPiBoxCannotConnect(MuPiBoxApiError):
    """Raised when MuPiBox cannot be reached."""


class MuPiBoxAuthenticationError(MuPiBoxApiError):
    """Raised when an admin API needs valid credentials."""


class MuPiBoxApiClient:
    """Small async client around the public MuPiBox-NG HTTP API."""

    def __init__(
        self,
        session: ClientSession,
        host: str,
        port: int,
        use_ssl: bool = False,
        admin_password: str = "",
    ) -> None:
        self._session = session
        self._host = host.strip().strip("[]")
        self._port = int(port)
        self._use_ssl = bool(use_ssl)
        self._admin_password = admin_password
        self._admin_cookie: str | None = None

    @property
    def base_url(self) -> str:
        """Return the configured base URL."""
        scheme = "https" if self._use_ssl else "http"
        return str(URL.build(scheme=scheme, host=self._host, port=self._port))

    @property
    def has_admin_password(self) -> bool:
        """Return whether the config entry contains an admin password."""
        return bool(self._admin_password)

    def absolute_url(self, path_or_url: str | None) -> str | None:
        """Turn a MuPiBox relative URL into an absolute URL."""
        if not path_or_url:
            return None
        value = str(path_or_url)
        if value.startswith("http://") or value.startswith("https://"):
            return value
        if not value.startswith("/"):
            value = f"/{value}"
        return f"{self.base_url}{value}"

    async def _response_payload(self, response: Any) -> Any:
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            try:
                return await response.json(content_type=None)
            except (ValueError, ClientError):
                pass
        try:
            return await response.text()
        except ClientError:
            return ""

    @staticmethod
    def _error_message(payload: Any, fallback: str) -> str:
        if isinstance(payload, dict):
            error = payload.get("error")
            if error:
                return str(error)
        if isinstance(payload, str) and payload.strip():
            return payload.strip()
        return fallback

    async def _raw_request(
        self,
        method: str,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        include_admin_cookie: bool = False,
        timeout: float = 10,
    ) -> tuple[int, Any, Any]:
        headers: dict[str, str] = {}
        if include_admin_cookie and self._admin_cookie:
            headers["Cookie"] = f"mupibox_admin_session={self._admin_cookie}"

        try:
            async with asyncio.timeout(timeout):
                response = await self._session.request(
                    method,
                    self.absolute_url(path),
                    json=json_data,
                    headers=headers,
                )
                payload = await self._response_payload(response)
                return response.status, payload, response
        except (TimeoutError, ClientError, OSError) as err:
            raise MuPiBoxCannotConnect(f"Cannot connect to MuPiBox-NG: {err}") from err

    async def async_get_admin_auth(self) -> dict[str, Any]:
        """Return the current admin protection state."""
        status, payload, _ = await self._raw_request(
            "GET", "/api/admin/auth", include_admin_cookie=True
        )
        if status != HTTPStatus.OK:
            raise MuPiBoxApiError(
                self._error_message(payload, "Could not read admin authentication state"),
                status=status,
            )
        return payload if isinstance(payload, dict) else {}

    async def async_login(self) -> None:
        """Create a MuPiBox admin session and store its cookie in memory."""
        if not self._admin_password:
            raise MuPiBoxAuthenticationError(
                "MuPiBox admin authentication is enabled, but no admin password was configured",
                status=HTTPStatus.UNAUTHORIZED,
            )

        status, payload, response = await self._raw_request(
            "POST",
            "/api/admin/login",
            json_data={"password": self._admin_password},
        )
        if status != HTTPStatus.OK:
            raise MuPiBoxAuthenticationError(
                self._error_message(payload, "MuPiBox admin login failed"),
                status=status,
            )

        cookie = response.cookies.get("mupibox_admin_session")
        if cookie is None or not cookie.value:
            raise MuPiBoxAuthenticationError("MuPiBox login returned no admin session cookie")
        self._admin_cookie = cookie.value

    async def async_ensure_admin_session(self) -> None:
        """Authenticate only when the box actually protects admin routes."""
        auth = await self.async_get_admin_auth()
        if not bool(auth.get("protected")):
            return
        if bool(auth.get("authenticated")) and self._admin_cookie:
            return
        await self.async_login()

    async def async_request_json(
        self,
        method: str,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        admin: bool = False,
        timeout: float = 10,
    ) -> dict[str, Any] | list[Any]:
        """Execute an API request and return JSON data."""
        if admin:
            await self.async_ensure_admin_session()

        status, payload, _ = await self._raw_request(
            method,
            path,
            json_data=json_data,
            include_admin_cookie=admin,
            timeout=timeout,
        )

        if admin and status == HTTPStatus.UNAUTHORIZED:
            self._admin_cookie = None
            await self.async_ensure_admin_session()
            status, payload, _ = await self._raw_request(
                method,
                path,
                json_data=json_data,
                include_admin_cookie=True,
                timeout=timeout,
            )

        if status < 200 or status >= 300:
            message = self._error_message(payload, f"MuPiBox API returned HTTP {status}")
            if status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
                raise MuPiBoxAuthenticationError(message, status=status)
            raise MuPiBoxApiError(message, status=status)

        if isinstance(payload, (dict, list)):
            return payload
        raise MuPiBoxApiError(f"MuPiBox API returned non-JSON data for {path}")

    async def async_get_health(self) -> dict[str, Any]:
        return await self.async_request_json("GET", "/api/health")  # type: ignore[return-value]

    async def async_get_info(self) -> dict[str, Any]:
        return await self.async_request_json("GET", "/api/info")  # type: ignore[return-value]

    async def async_get_status(self) -> dict[str, Any]:
        return await self.async_request_json("GET", "/api/status")  # type: ignore[return-value]

    async def async_get_system(self) -> dict[str, Any]:
        return await self.async_request_json("GET", "/api/system")  # type: ignore[return-value]

    async def async_get_library(self) -> list[dict[str, Any]]:
        result = await self.async_request_json("GET", "/api/library")
        return result if isinstance(result, list) else []

    async def async_get_spotify_status(self) -> dict[str, Any]:
        try:
            result = await self.async_request_json("GET", "/api/spotify/status")
        except MuPiBoxApiError as err:
            if err.status == HTTPStatus.NOT_FOUND:
                return {}
            raise
        return result if isinstance(result, dict) else {}

    async def async_command(self, action: str, **kwargs: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {"action": action}
        payload.update(kwargs)
        result = await self.async_request_json("POST", "/api/command", json_data=payload)
        return result if isinstance(result, dict) else {}

    async def async_spotify_command(self, action: str, value: int | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"action": action}
        if value is not None:
            payload["value"] = int(value)
        result = await self.async_request_json("POST", "/api/spotify/command", json_data=payload)
        return result if isinstance(result, dict) else {}

    async def async_speak(self, text: str, source_ref: str = "home-assistant") -> dict[str, Any]:
        result = await self.async_request_json(
            "POST",
            "/api/speak",
            json_data={
                "source_type": "home-assistant",
                "source_ref": source_ref,
                "text": text,
            },
            timeout=25,
        )
        return result if isinstance(result, dict) else {}

    async def async_admin_get_bytes(self, path: str, timeout: float = 15) -> bytes:
        """Fetch binary data from a protected Admin endpoint."""
        await self.async_ensure_admin_session()

        async def _fetch() -> tuple[int, bytes]:
            headers: dict[str, str] = {}
            if self._admin_cookie:
                headers["Cookie"] = f"mupibox_admin_session={self._admin_cookie}"
            try:
                async with asyncio.timeout(timeout):
                    response = await self._session.get(
                        self.absolute_url(path), headers=headers
                    )
                    body = await response.read()
                    return response.status, body
            except (TimeoutError, ClientError, OSError) as err:
                raise MuPiBoxCannotConnect(
                    f"Cannot connect to MuPiBox-NG: {err}"
                ) from err

        status, body = await _fetch()
        if status == HTTPStatus.UNAUTHORIZED:
            self._admin_cookie = None
            await self.async_ensure_admin_session()
            status, body = await _fetch()
        if status < 200 or status >= 300:
            message = body.decode("utf-8", errors="replace").strip()
            if status in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
                raise MuPiBoxAuthenticationError(
                    message or f"MuPiBox API returned HTTP {status}", status=status
                )
            raise MuPiBoxApiError(
                message or f"MuPiBox API returned HTTP {status}", status=status
            )
        return body

    async def async_admin_post(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        result = await self.async_request_json(
            "POST", path, json_data=payload or {}, admin=True, timeout=15
        )
        return result if isinstance(result, dict) else {}
