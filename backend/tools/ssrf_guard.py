"""SSRF Guard for validating target URLs against internal, private, and reserved network ranges."""
import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple


BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),          # Current network
    ipaddress.ip_network("10.0.0.0/8"),         # RFC 1918 Private
    ipaddress.ip_network("100.64.0.0/10"),      # Shared Address Space (CGNAT)
    ipaddress.ip_network("127.0.0.0/8"),        # Loopback
    ipaddress.ip_network("169.254.0.0/16"),     # Link-Local (Cloud metadata e.g. 169.254.169.254)
    ipaddress.ip_network("172.16.0.0/12"),      # RFC 1918 Private
    ipaddress.ip_network("192.0.0.0/24"),       # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),       # TEST-NET-1
    ipaddress.ip_network("192.168.0.0/16"),     # RFC 1918 Private
    ipaddress.ip_network("198.18.0.0/15"),      # Network benchmark tests
    ipaddress.ip_network("198.51.100.0/24"),    # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),     # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),        # Multicast
    ipaddress.ip_network("240.0.0.0/4"),        # Reserved
    ipaddress.ip_network("255.255.255.255/32"), # Broadcast
    # IPv6 ranges
    ipaddress.ip_network("::1/128"),            # IPv6 Loopback
    ipaddress.ip_network("fc00::/7"),           # IPv6 Unique Local Address
    ipaddress.ip_network("fe80::/10"),          # IPv6 Link-Local
]


class SSRFValidationError(ValueError):
    """Raised when a URL resolves to a prohibited or private network address."""
    pass


def validate_url_safe(url: str) -> Tuple[bool, str]:
    """
    Validate that a URL uses safe protocols (http/https) and does not resolve
    to localhost, link-local, private RFC 1918, or cloud metadata endpoints.
    Returns (is_safe, reason_or_normalized_url).
    """
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string"

    url = url.strip()
    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Malformed URL: {e}"

    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Prohibited URL scheme '{parsed.scheme}'. Only http and https are allowed."

    hostname = parsed.hostname
    if not hostname:
        return False, "URL contains no hostname"

    # Check for direct localhost aliases
    if hostname.lower() in ("localhost", "localhost.localdomain", "broadcasthost"):
        return False, "Access to localhost is prohibited."

    # Resolve hostname to IP addresses
    try:
        # getaddrinfo resolves both IPv4 and IPv6
        addr_info = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False, f"Failed to resolve DNS for hostname '{hostname}'"
    except Exception as e:
        return False, f"DNS resolution error: {e}"

    if not addr_info:
        return False, f"No IP addresses resolved for hostname '{hostname}'"

    for entry in addr_info:
        ip_str = entry[4][0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            return False, f"Invalid IP address format: {ip_str}"

        # Check against blocked network ranges
        for blocked in BLOCKED_NETWORKS:
            if ip_obj in blocked:
                return False, f"Target IP {ip_str} falls within blocked network range {blocked} (SSRF protection)"

        # Check is_private, is_loopback, is_link_local, is_reserved
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved:
            return False, f"Target IP {ip_str} is private, loopback, or reserved"

    return True, url
