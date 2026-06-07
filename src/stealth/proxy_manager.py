"""
Proxy manager abstraction layer.

Defaults to NO PROXY (zero cost). Designed as a plug-in point
so a proxy provider can be integrated later by simply setting
the PROXY_URL environment variable — no code changes required.

Supported formats (for future use):
  - Direct: http://user:pass@host:port
  - ScraperAPI: http://api.scraperapi.com?api_key=XXX&url=
  - Bright Data: http://user:pass@brd.superproxy.io:port
"""

import os


class ProxyManager:
    """Lightweight proxy abstraction.

    Currently operates in passthrough mode (no proxy).
    When PROXY_URL is set, requests are routed through the proxy.
    """

    def __init__(self):
        self._proxy_url = os.environ.get("PROXY_URL")
        if self._proxy_url:
            print(f"[ProxyManager] Proxy configured: {self._mask_url(self._proxy_url)}")
        else:
            print("[ProxyManager] No proxy configured. Running in direct mode.")

    def get_proxy(self) -> dict | None:
        """Return proxy dict for requests/curl-cffi, or None for direct mode."""
        if not self._proxy_url:
            return None
        return {
            "http": self._proxy_url,
            "https": self._proxy_url,
        }

    @property
    def is_active(self) -> bool:
        """Check if a proxy is configured."""
        return self._proxy_url is not None

    @staticmethod
    def _mask_url(url: str) -> str:
        """Mask credentials in proxy URL for safe logging."""
        if "@" in url:
            # http://user:pass@host:port -> http://***@host:port
            prefix, suffix = url.rsplit("@", 1)
            return prefix.split("://")[0] + "://***@" + suffix
        return url
