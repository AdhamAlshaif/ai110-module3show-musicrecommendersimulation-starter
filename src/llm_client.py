"""
LLM client — the "brain" behind the recommender.

Everything that talks to a language model goes through this one module, so the
rest of the code never imports a vendor SDK directly. That keeps the provider
*swappable*: today it's Anthropic's Claude, but adding Gemini or Groq later is
just another branch in `LLMClient._complete_*` — no caller has to change.

Config comes from `.env` (loaded via python-dotenv):
  - ANTHROPIC_API_KEY : your Claude API key (required for the "anthropic" provider)
  - LLM_MODEL         : model id, e.g. claude-haiku-4-5-20251001 (cheap) or claude-opus-4-8

Cost note: defaults to Haiku 4.5 and a small max_tokens to protect a small budget.
Identical (system, prompt, model) calls are cached in-process so repeated runs
during development don't re-bill.

Quick smoke test:  python -m src.llm_client
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv

# Load .env once, when this module is first imported.
load_dotenv()

DEFAULT_MODEL = os.getenv("LLM_MODEL", "claude-haiku-4-5-20251001")
DEFAULT_MAX_TOKENS = 1024


class LLMError(RuntimeError):
    """Raised when the LLM call can't be made (missing key, API failure, etc.)."""


class LLMClient:
    """
    A thin, provider-agnostic wrapper around a chat LLM.

    Usage:
        llm = LLMClient()
        text = llm.complete("Say hello in five words.")

    The public surface is deliberately tiny — `complete()` takes a prompt (and an
    optional system instruction) and returns plain text. Swapping providers or
    models never changes this signature.
    """

    def __init__(
        self,
        provider: str = "anthropic",
        model: Optional[str] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = 0.2,
    ) -> None:
        self.provider = provider
        self.model = model or DEFAULT_MODEL
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._client = None  # lazily created on first call

    # --- public API ---------------------------------------------------------

    def complete(self, prompt: str, system: Optional[str] = None) -> str:
        """
        Send `prompt` to the model and return its text reply.

        `system` is an optional instruction that sets the model's role/behavior.
        Results are cached per (provider, model, temperature, system, prompt) so
        repeated identical calls during a dev session don't re-bill.
        """
        return _cached_complete(
            provider=self.provider,
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system or "",
            prompt=prompt,
            _client_factory=self._get_client,
        )

    # --- providers ----------------------------------------------------------

    def _get_client(self):
        """Create (once) and return the underlying vendor client."""
        if self._client is not None:
            return self._client

        if self.provider == "anthropic":
            self._client = self._make_anthropic_client()
        else:
            raise LLMError(
                f"Unknown provider '{self.provider}'. "
                "Supported today: 'anthropic'. (Gemini/Groq can be added here.)"
            )
        return self._client

    @staticmethod
    def _make_anthropic_client():
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key."
            )
        try:
            from anthropic import Anthropic
        except ImportError as err:  # pragma: no cover
            raise LLMError("The 'anthropic' package is not installed. Run: pip install anthropic") from err
        return Anthropic(api_key=api_key)


def _complete_anthropic(client, model, max_tokens, temperature, system, prompt) -> str:
    """One Claude Messages API call -> the assistant's text."""
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system
    try:
        msg = client.messages.create(**kwargs)
    except Exception as err:  # surface a clean error to callers
        raise LLMError(f"Anthropic API call failed: {err}") from err

    # Concatenate any text blocks in the response.
    parts = [block.text for block in msg.content if getattr(block, "type", None) == "text"]
    return "".join(parts).strip()


@lru_cache(maxsize=256)
def _cached_complete(provider, model, max_tokens, temperature, system, prompt, _client_factory) -> str:
    """
    Memoized completion. The cache key is every argument *except* the client
    factory's identity, which is stable per LLMClient instance. Keeping this a
    module-level function (not a method) lets lru_cache work cleanly.
    """
    client = _client_factory()
    if provider == "anthropic":
        return _complete_anthropic(client, model, max_tokens, temperature, system, prompt)
    raise LLMError(f"Unknown provider '{provider}'.")


if __name__ == "__main__":
    # Phase 1 smoke test: prove we can reach Claude and get text back.
    print(f"Provider: anthropic | Model: {DEFAULT_MODEL}")
    print("Sending a tiny test prompt to Claude...\n")
    llm = LLMClient(max_tokens=60)
    try:
        reply = llm.complete(
            "In one short sentence, introduce yourself as the brain of a music "
            "recommender called VibeCheck.",
            system="You are a concise, friendly music recommendation assistant.",
        )
        print("Claude replied:")
        print(f"  {reply}")
        print("\nPhase 1 OK - the LLM client works.")
    except LLMError as err:
        print(f"Phase 1 FAILED: {err}")
        raise SystemExit(1)
