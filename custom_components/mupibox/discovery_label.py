"""Readable labels for untrusted MuPiBox Zeroconf discovery hints.

Device identity and pairing are verified separately using HTTPS and device ID.
"""

from __future__ import annotations

from typing import Any, Mapping

SERVICE_SUFFIX = "._mupibox._tcp.local."
_GENERIC = frozenset({
    "mupibox", "mupibox ng", "mupibox-ng", "mupibox classic",
    "mupibox ng secure", "mupibox classic secure",
})
_INSTANCE_PREFIXES = (
    "MuPiBox Classic Secure ", "MuPiBox NG Secure ",
    "MuPiBox Classic ", "MuPiBox NG ", "MuPiBox ",
)


def _clean(value: Any) -> str:
    """Decode TXT bytes; suppress control characters and long labels."""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    if value is None:
        return ""
    return " ".join("".join(ch for ch in str(value) if ch.isprintable()).split())[:80].strip()


def _instance_name(instance: str) -> str:
    name = _clean(instance)
    if name.lower().endswith(SERVICE_SUFFIX):
        name = name[:-len(SERVICE_SUFFIX)]
    for prefix in _INSTANCE_PREFIXES:
        if name.casefold().startswith(prefix.casefold()):
            name = name[len(prefix):]
            break
    return name


def discovery_title(
    properties: Mapping[str, Any], generation: str, instance: str, host: str
) -> str:
    """Distinguish boxes by generation, preferred friendly name and hostname."""
    device_type = "Classic" if generation == "classic" else "NG"
    endpoint = _clean(host).rstrip(".")
    name = ""
    for key in ("name", "friendly_name", "box_name"):
        candidate = _clean(properties.get(key))
        if candidate and candidate.casefold() not in _GENERIC:
            name = candidate
            break
    if not name:
        candidate = _instance_name(instance)
        if candidate and candidate.casefold() not in _GENERIC:
            name = candidate
    if not name:
        name = endpoint or "Unbekannte Box"
    host_short = endpoint.split(".", 1)[0].casefold()
    same_host = name.casefold() in {endpoint.casefold(), host_short}
    location = f"{name} ({endpoint})" if endpoint and not same_host else name
    return f"MuPiBox {device_type} – {location}"
