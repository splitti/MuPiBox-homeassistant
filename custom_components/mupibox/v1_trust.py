"""First-contact device identity verification for API-v1 pairing."""

from __future__ import annotations

import asyncio
import hashlib
import ssl

from aiohttp import ClientSession, Fingerprint
from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from yarl import URL


def normalized_fingerprint(value: str) -> str:
    """Allow pasted hex values with spaces/colons; never auto-accept them."""
    return value.lower().replace(":", "").replace(" ", "").strip()


async def probe_device_key(host: str, port: int) -> tuple[str, bytes]:
    """Inspect TLS certificate without sending application credentials."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    try:
        async with asyncio.timeout(8):
            reader, writer = await asyncio.open_connection(
                host, port, ssl=context, server_hostname=host
            )
            del reader
            ssl_object = writer.get_extra_info("ssl_object")
            certificate = ssl_object.getpeercert(binary_form=True)
            writer.close()
            await writer.wait_closed()
        if not certificate:
            raise ValueError("No TLS server certificate")
        leaf = x509.load_der_x509_certificate(certificate)
        spki = leaf.public_key().public_bytes(
            Encoding.DER, PublicFormat.SubjectPublicKeyInfo
        )
        return hashlib.sha256(spki).hexdigest(), hashlib.sha256(certificate).digest()
    except (OSError, TimeoutError, ssl.SSLError) as error:
        raise ValueError(f"Cannot inspect MuPiBox TLS identity: {error}") from error


async def fetch_verified_ca(
    session: ClientSession, host: str, port: int, leaf_digest: bytes
) -> str:
    """Download CA using pinned leaf cert, then verify CA/hostname as a chain."""
    url = str(URL.build(scheme="https", host=host, port=port)) + "/api/ha/v1/tls/ca"
    try:
        async with asyncio.timeout(10):
            async with session.get(url, ssl=Fingerprint(leaf_digest)) as response:
                response.raise_for_status()
                data = await response.read()
        if len(data) > 32768:
            raise ValueError("CA certificate too large")
        ca = data.decode("ascii")
        context = ssl.create_default_context(cadata=ca)
        async with asyncio.timeout(8):
            reader, writer = await asyncio.open_connection(
                host, port, ssl=context, server_hostname=host
            )
            del reader
            writer.close()
            await writer.wait_closed()
        return ca
    except (OSError, TimeoutError, ssl.SSLError, UnicodeError) as error:
        raise ValueError(f"Cannot verify MuPiBox CA: {error}") from error
