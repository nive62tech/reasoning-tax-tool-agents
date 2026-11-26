"""Central configuration. Edit here or override with environment variables."""
import json
import os

# ---- Conditions -----------------------------------------------------------
# Default design: SAME model, thinking OFF vs ON. This isolates the effect of
# reasoning and keeps "general capability" identical. To compare two different
# models instead (e.g. a reasoning model vs a fast model), set BASELINE_MODEL
# and REASONING_MODEL to different model IDs.
BASELINE_MODEL = os.getenv("BASELINE_MODEL", "claude-sonnet-5-5")
REASONING_MODEL = os.getenv("REASONING_MODEL", "claude-sonnet-5-5")

THINKING_BUDGET = int(os.getenv("THINKING_BUDGET", "8000"))
# If your chosen model uses a different thinking parameter shape, override the
# whole object with THINKING_JSON, e.g. '{"type":"adaptive"}'.
_thinking_override = os.getenv("THINKING_JSON")
THINKING_PARAM = (
    json.loads(_thinking_override)
    if _thinking_override
    else {"type": "enabled", "budget_tokens": THINKING_BUDGET}
)

CONDITIONS = {
    "baseline": {"model": BASELINE_MODEL, "thinking": None},
    "reasoning": {"model": REASONING_MODEL, "thinking": THINKING_PARAM},
}

# ---- Run limits -----------------------------------------------------------
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "16000"))  # must exceed thinking budget
MAX_TURNS = int(os.getenv("MAX_TURNS", "15"))       # model<->tool round trips per task

# Optional sampling temperature for the baseline only. Leave unset (None) so both
# conditions use the API default; extended thinking requires the default anyway.
_t = os.getenv("BASELINE_TEMPERATURE")
BASELINE_TEMPERATURE = float(_t) if _t else None

# ---- Prices (USD per million tokens) --------------------------------------
# PLACEHOLDERS: set these to your provider's current price for the model.
# Thinking tokens are billed as output tokens, and are already inside output_tokens.
PRICE_IN_PER_MTOK = float(os.getenv("PRICE_IN_PER_MTOK", "3.0"))
PRICE_OUT_PER_MTOK = float(os.getenv("PRICE_OUT_PER_MTOK", "15.0"))


# ===========================================================================
# Provider selection + Gemini settings
# ===========================================================================
PROVIDER = os.getenv("PROVIDER", "anthropic")   # "anthropic" or "gemini" (CLI --provider overrides)

# Gemini: SAME model in both conditions, only the thinking setting differs.
# Default is gemini-3.6-flash (free tier; supports MINIMAL..HIGH thinking levels).
# NOTE: gemini-3.8-flash does NOT support MINIMAL (lowest is LOW), so it cannot give a near-"off" baseline.
# Format of the thinking spec: "level:<minimal|low|medium|high>" or "budget:<int>" (budget: older 2.5 models only;
# never mix level and budget in one request).
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
GEMINI_BASELINE_THINKING = os.getenv("GEMINI_BASELINE_THINKING", "level:minimal")
GEMINI_REASONING_THINKING = os.getenv("GEMINI_REASONING_THINKING", "level:high")
GEMINI_MAX_OUTPUT_TOKENS = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "16000"))
GEMINI_RPM = float(os.getenv("GEMINI_RPM", "8"))  # client-side pacing; stay under your free-tier requests/minute

# List-price-equivalent defaults used only for the cost columns (the free tier itself costs $0).
# Verify against https://ai.google.dev/gemini-api/docs/pricing -- introductory prices end Dec 31, 2026.
GEMINI_PRICE_IN_PER_MTOK = float(os.getenv("GEMINI_PRICE_IN_PER_MTOK", "0.75"))
GEMINI_PRICE_OUT_PER_MTOK = float(os.getenv("GEMINI_PRICE_OUT_PER_MTOK", "3.75"))


def get_conditions(provider):
    if provider == "gemini":
        return {
            "baseline": {"model": GEMINI_MODEL, "thinking": GEMINI_BASELINE_THINKING},
            "reasoning": {"model": GEMINI_MODEL, "thinking": GEMINI_REASONING_THINKING},
        }
    return CONDITIONS


def get_prices(provider):
    if provider == "gemini":
        return GEMINI_PRICE_IN_PER_MTOK, GEMINI_PRICE_OUT_PER_MTOK
    return PRICE_IN_PER_MTOK, PRICE_OUT_PER_MTOK
