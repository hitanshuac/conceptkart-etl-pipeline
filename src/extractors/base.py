"""
Base extractor with circuit breaker pattern.

All extraction tiers inherit from this ABC. The circuit breaker
prevents repeated calls to a tier that is consistently failing
for a specific domain (e.g., Tier 1 keeps getting 403'd on amazon.in).
"""

import time
from abc import ABC, abstractmethod
from collections import defaultdict

from src.models import ScrapedProduct


class CircuitBreaker:
    """Per-domain, per-tier circuit breaker.

    After `failure_threshold` consecutive failures for a (domain, tier)
    pair, the circuit opens and the tier is bypassed for `recovery_timeout`
    seconds before being retried.
    """

    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 600):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        # {domain: {"failures": int, "last_failure": float, "open": bool}}
        self._states: dict[str, dict] = defaultdict(lambda: {"failures": 0, "last_failure": 0.0, "open": False})

    def is_open(self, domain: str) -> bool:
        """Check if the circuit is open (tier should be skipped) for a domain."""
        state = self._states[domain]
        if not state["open"]:
            return False
        # Check if recovery timeout has elapsed
        if time.time() - state["last_failure"] > self.recovery_timeout:
            state["open"] = False
            state["failures"] = 0
            return False
        return True

    def record_success(self, domain: str) -> None:
        """Reset the circuit on a successful extraction."""
        self._states[domain] = {"failures": 0, "last_failure": 0.0, "open": False}

    def record_failure(self, domain: str) -> None:
        """Record a failure. Opens the circuit after threshold is hit."""
        state = self._states[domain]
        state["failures"] += 1
        state["last_failure"] = time.time()
        if state["failures"] >= self.failure_threshold:
            state["open"] = True


class BaseExtractor(ABC):
    """Abstract base class for all extraction tiers."""

    tier_name: str = "base"

    def __init__(self):
        self.circuit_breaker = CircuitBreaker()

    @abstractmethod
    def extract(self, url: str, **kwargs) -> ScrapedProduct | None:
        """Attempt to extract product data from the given URL.

        Returns ScrapedProduct on success, None on failure.
        Implementations must NOT raise exceptions — they should catch
        internally and return None to allow the cascade to continue.
        """
        ...

    def can_attempt(self, domain: str) -> bool:
        """Check if this tier should be attempted for the given domain."""
        return not self.circuit_breaker.is_open(domain)
