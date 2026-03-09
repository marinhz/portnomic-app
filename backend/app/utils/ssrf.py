"""SSRF protection: validate URLs to block private IPs and localhost."""

import ipaddress
from urllib.parse import urlparse


def _is_private_host(host: str) -> bool:
    """Return True if host is localhost or a private/internal IP."""
    if not host:
        return True
    host_lower = host.lower()
    if host_lower in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        return True
    # Strip brackets for IPv6
    host_clean = host.strip("[]")
    try:
        ip = ipaddress.ip_address(host_clean)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or host_clean.startswith("169.254.")  # AWS/GCP metadata
        )
    except ValueError:
        # Not an IP; could be a hostname. localhost already checked.
        return False


def validate_llm_base_url(url: str | None) -> None:
    """Validate base_url for LLM API. Raises ValueError if SSRF risk (private IP, localhost)."""
    if not url or not url.strip():
        return
    parsed = urlparse(url.strip())
    host = parsed.hostname
    if not host:
        raise ValueError("Invalid LLM base_url: no host")
    if _is_private_host(host):
        raise ValueError(
            f"LLM base_url cannot target private/localhost addresses: {host}"
        )
    if parsed.scheme not in ("http", "https"):
        raise ValueError("LLM base_url must use http or https")
