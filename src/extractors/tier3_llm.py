"""
Tier 3: AI Self-Healing Extraction via LLM Fallback.

Triggered when both Tier 1 (HTTP) and Tier 2 (browser) fail.
Sends truncated page content to a free LLM provider and requests
structured JSON extraction matching the ScrapedProduct Pydantic schema.

Supported free providers (auto-detected from API key):
  - Groq (key starts with "gsk_")
  - OpenRouter (key starts with "sk-or-")
  - HuggingFace Inference API (key starts with "hf_")
  - Generic OpenAI-compatible endpoint

Cost: $0 on free tiers. Latency: ~3-8s.
"""

import json
import os
import time
from datetime import UTC, datetime
from urllib.parse import urlparse

from src.extractors.base import BaseExtractor
from src.models import ScrapedProduct, SiteConfig

try:
    from openai import OpenAI

    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


# Provider configurations (all free tiers)
PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.1-8b-instant",
        "key_prefix": "gsk_",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "meta-llama/llama-3-8b-instruct:free",
        "key_prefix": "sk-or-",
    },
    "huggingface": {
        "base_url": "https://api-inference.huggingface.co/v1",
        "model": "meta-llama/Meta-Llama-3-8B-Instruct",
        "key_prefix": "hf_",
    },
}

SYSTEM_PROMPT = (
    "You are a specialized e-commerce data extractor. "
    "You receive raw webpage text and must extract product information. "
    "Output ONLY valid JSON containing EXACTLY two keys: "
    "'product_name' (string) and 'price_current' (integer, the selling price "
    "in the local currency). Do not include any markdown formatting, "
    "code blocks, or extra text. Just raw JSON."
)


class Tier3LlmExtractor(BaseExtractor):
    """AI self-healing extraction using free LLM providers.

    This tier is the safety net for when sites redesign their layouts,
    use unusual markup, or employ anti-scraping measures that break
    traditional parsing. The LLM reads the raw page text and extracts
    structured data.

    Provider auto-detection priority:
    1. GROQ_API_KEY (fastest free inference)
    2. OPENROUTER_API_KEY (widest model selection)
    3. HF_API_KEY / HUGGINGFACE_API_KEY (HuggingFace Inference API)
    """

    tier_name = "tier3_llm"

    def extract(
        self,
        url: str,
        site_config: SiteConfig | None = None,
        page_text: str | None = None,
        **kwargs,
    ) -> ScrapedProduct | None:
        domain = urlparse(url).netloc.replace("www.", "")

        if not self.can_attempt(domain):
            print(f"  [Tier3] Circuit open for {domain}, skipping.")
            return None

        if not HAS_OPENAI:
            print("  [Tier3] openai package not installed. Skipping LLM tier.")
            return None

        # Resolve API key and provider
        api_key, provider_config = self._resolve_provider()
        if not api_key:
            print("  [Tier3] No LLM API key found. Set GROQ_API_KEY, OPENROUTER_API_KEY, or HF_API_KEY.")
            return None

        start_ms = time.monotonic_ns()

        try:
            # If we don't have pre-fetched page text, fetch it ourselves
            if not page_text:
                page_text = self._fetch_page_text(url)
                if not page_text:
                    self.circuit_breaker.record_failure(domain)
                    return None

            # Context compaction: truncate to 15k chars per context_compaction.md
            truncated_text = page_text[:15000]

            client = OpenAI(
                base_url=provider_config["base_url"],
                api_key=api_key,
            )

            # Build request — use JSON mode if supported
            request_kwargs = {
                "model": provider_config["model"],
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"Extract the product name and current selling price "
                            f"from this webpage text:\n\n{truncated_text}"
                        ),
                    },
                ],
                "temperature": 0.0,
            }

            # JSON mode not universally supported; try it but don't require it
            try:
                request_kwargs["response_format"] = {"type": "json_object"}
                res = client.chat.completions.create(**request_kwargs)
            except Exception:
                del request_kwargs["response_format"]
                res = client.chat.completions.create(**request_kwargs)

            content = res.choices[0].message.content.strip()

            # Strip markdown code blocks if the LLM wraps its response
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            extracted = json.loads(content)
            price_current = int(extracted.get("price_current", 0))
            product_name = extracted.get("product_name", "")

            if price_current <= 0 or not product_name:
                print(f"  [Tier3] LLM returned invalid data: {extracted}")
                self.circuit_breaker.record_failure(domain)
                return None

            latency_ms = int((time.monotonic_ns() - start_ms) / 1_000_000)
            self.circuit_breaker.record_success(domain)

            print(f"  [Tier3] AI recovered: {product_name} @ Rs.{price_current}")

            return ScrapedProduct(
                product_name=product_name,
                vendor_name=domain,
                vendor_url=url,
                price_current=price_current,
                scraped_at_utc=datetime.now(UTC),
                extraction_tier=self.tier_name,
                extraction_latency_ms=latency_ms,
            )

        except Exception as e:
            print(f"  [Tier3] LLM extraction failed: {e}")
            self.circuit_breaker.record_failure(domain)
            return None

    def _resolve_provider(self) -> tuple[str | None, dict | None]:
        """Auto-detect the LLM provider from available API keys.

        Priority: Groq (fastest) → OpenRouter → HuggingFace
        """
        # Check each provider in priority order
        for provider_name, config in PROVIDERS.items():
            # Check multiple env var naming conventions
            key_names = {
                "groq": ["GROQ_API_KEY"],
                "openrouter": ["OPENROUTER_API_KEY"],
                "huggingface": ["HF_API_KEY", "HUGGINGFACE_API_KEY", "HF_TOKEN"],
            }
            for key_name in key_names.get(provider_name, []):
                api_key = os.environ.get(key_name)
                if api_key:
                    print(f"  [Tier3] Using provider: {provider_name}")
                    return api_key, config

        # Fallback: check for a generic OPENAI_API_KEY
        generic_key = os.environ.get("OPENAI_API_KEY")
        if generic_key:
            # Detect provider from key prefix
            for config in PROVIDERS.values():
                if generic_key.startswith(config["key_prefix"]):
                    return generic_key, config
            # Default to OpenAI-compatible
            return generic_key, {
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4o-mini",
            }

        return None, None

    @staticmethod
    def _fetch_page_text(url: str) -> str | None:
        """Fetch raw page text for LLM consumption."""
        try:
            from curl_cffi import requests as cffi_requests

            from src.stealth.fingerprints import get_stealth_headers

            response = cffi_requests.get(url, headers=get_stealth_headers(), timeout=15, impersonate="chrome")
        except ImportError:
            import requests

            response = requests.get(url, timeout=15)

        if response.status_code != 200:
            return None

        from bs4 import BeautifulSoup

        soup = BeautifulSoup(response.text, "html.parser")
        body = soup.body
        if body:
            return body.get_text(separator=" ", strip=True)
        return response.text
