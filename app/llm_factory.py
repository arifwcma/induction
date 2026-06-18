"""Provider-aware LLM construction.

The bot can run on OpenAI or Anthropic depending on the LLM_PROVIDER setting.
This module is the single place that knows how to build a chat LLM for either
provider, including the per-attempt variation we use to make verifier retries a
genuinely different draft rather than an identical one:

  - OpenAI    : vary the deterministic ``seed`` (temperature stays 0).
  - Anthropic : Anthropic has no seed parameter, so vary ``temperature`` instead.
"""

from app.config import get_settings

FIXED_SEED = 7

# Opus 4.8 ships in llama-index-llms-anthropic only on `main`; the pinned PyPI
# release (0.11.4) does not know its context window yet, so register it. The
# value only gates client-side context-size bookkeeping; the model id we send to
# the API is what actually matters.
_OPUS_48_CONTEXT_WINDOW = 1_000_000


def _ensure_anthropic_model_registered(model: str) -> None:
    """Teach the pinned integration about Opus 4.8.

    The pinned PyPI build (0.11.4) only knows up to Opus 4.7, so for 4.8 we
    register (a) its context window and (b) that it is a no-temperature model
    (Opus 4.8 rejects the ``temperature`` parameter; it uses adaptive thinking).
    """
    from llama_index.llms.anthropic import base as anthropic_base
    from llama_index.llms.anthropic import utils as anthropic_utils

    if model not in anthropic_utils.CLAUDE_MODELS:
        anthropic_utils.CLAUDE_MODELS[model] = _OPUS_48_CONTEXT_WINDOW

    no_temp = anthropic_base.ANTHROPIC_NO_TEMP_MODELS
    if model not in no_temp:
        anthropic_base.ANTHROPIC_NO_TEMP_MODELS = (*no_temp, model)


def _resolve_provider_and_model(settings, fast: bool) -> tuple[str, str]:
    """Pick (provider, model) for the requested lane.

    The bot uses two lanes:
      - answer lane (``fast=False``): the strongest model (e.g. Opus 4.8) for the
        user-facing answer, where judgment matters most.
      - fast lane (``fast=True``): a cheap, deterministic model for the mechanical
        sub-steps (condense, query rewrite, applicability, verification). Keeping
        these on a seedable model restores reproducible retrieval and cuts latency
        and cost without touching answer quality.
    """
    if fast:
        provider = (settings.fast_llm_provider or "openai").lower()
        model = settings.fast_chat_model
        return provider, model

    provider = (settings.llm_provider or "openai").lower()
    model = settings.anthropic_chat_model if provider == "anthropic" else settings.openai_chat_model
    return provider, model


def make_llm(*, fast: bool = False, max_tokens: int | None = None, attempt: int = 0):
    """Build a chat LLM for the requested lane (see ``_resolve_provider_and_model``).

    ``attempt`` > 0 produces a different draft on retry. For OpenAI we vary the
    deterministic ``seed``; Opus 4.8 rejects ``temperature`` (it uses adaptive
    thinking), so its retry variation comes from the model's own sampling.
    """
    settings = get_settings()
    provider, model = _resolve_provider_and_model(settings, fast)

    if provider == "anthropic":
        from llama_index.llms.anthropic import Anthropic

        _ensure_anthropic_model_registered(model)
        return Anthropic(
            model=model,
            api_key=settings.anthropic_api_key,
            max_tokens=max_tokens or 2048,
        )

    from llama_index.llms.openai import OpenAI

    extra: dict = {"seed": FIXED_SEED + attempt * 101}
    # GPT-5 models are reasoning models: keep effort minimal so the mechanical
    # fast-lane steps (condense, query rewrite, applicability, verify) stay cheap
    # and low-latency rather than burning reasoning tokens on yes/no judgements.
    if model.startswith("gpt-5"):
        extra["reasoning_effort"] = "minimal"
    kwargs: dict = {
        "model": model,
        "api_key": settings.openai_api_key,
        "temperature": 0,
        "additional_kwargs": extra,
    }
    if max_tokens is not None:
        # Reasoning models bill reasoning tokens against the output budget, so a
        # tiny cap can yield an empty completion; keep some headroom.
        kwargs["max_tokens"] = max(max_tokens, 256) if model.startswith("gpt-5") else max_tokens
    return OpenAI(**kwargs)
