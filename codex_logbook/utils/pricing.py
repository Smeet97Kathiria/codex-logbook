import logging

"""
Pricing utilities for calculating Codex API costs.
Uses LiteLLM pricing data with local fallback.
"""


logger = logging.getLogger(__name__)

# Default pricing in USD per token (not per million)
# Local fallback values for common Codex models.
DEFAULT_CODEX_PRICING = {
    "gpt-5": {
        "input_cost_per_token": 1.25 / 1_000_000,
        "output_cost_per_token": 10.0 / 1_000_000,
        "cache_creation_cost_per_token": 1.25 / 1_000_000,
        "cache_read_cost_per_token": 0.125 / 1_000_000,
    },
    "gpt-5-mini": {
        "input_cost_per_token": 0.25 / 1_000_000,
        "output_cost_per_token": 2.0 / 1_000_000,
        "cache_creation_cost_per_token": 0.25 / 1_000_000,
        "cache_read_cost_per_token": 0.025 / 1_000_000,
    },
    "gpt-5-nano": {
        "input_cost_per_token": 0.05 / 1_000_000,
        "output_cost_per_token": 0.4 / 1_000_000,
        "cache_creation_cost_per_token": 0.05 / 1_000_000,
        "cache_read_cost_per_token": 0.005 / 1_000_000,
    },
}

# Cache for dynamic pricing
_dynamic_pricing_cache = None


def get_dynamic_pricing() -> dict[str, dict[str, float]]:
    """Get pricing from service or fallback to defaults."""
    global _dynamic_pricing_cache

    if _dynamic_pricing_cache is None:
        try:
            from ..services.pricing_service import PricingService

            service = PricingService()
            pricing_data = service.get_pricing()
            _dynamic_pricing_cache = pricing_data.get("pricing", DEFAULT_CODEX_PRICING)
        except Exception as e:
            logger.info(f"Error loading dynamic pricing: {e}")
            _dynamic_pricing_cache = DEFAULT_CODEX_PRICING

    return _dynamic_pricing_cache


def get_model_pricing(model_name: str) -> dict[str, float] | None:
    """
    Get pricing for a specific model.
    Returns pricing dict or None if model not found.
    """
    # Get dynamic pricing
    pricing_data = get_dynamic_pricing()

    # Direct match
    if model_name in pricing_data:
        return pricing_data[model_name]

    # Try to match by partial name (e.g., "gpt-5-mini" inside a dated model ID)
    for known_model, pricing in pricing_data.items():
        if model_name in known_model or known_model in model_name:
            return pricing

    # This is a reasonable default for unknown Codex models
    return pricing_data.get("gpt-5-mini") or DEFAULT_CODEX_PRICING.get("gpt-5-mini")


def calculate_cost(tokens: dict[str, int], model: str) -> dict[str, float]:
    """
    Calculate cost breakdown for given tokens and model.

    Args:
        tokens: Dict with keys 'input', 'output', 'cache_creation', 'cache_read'
        model: Model name string

    Returns:
        Dict with cost breakdown by token type and total
    """
    pricing = get_model_pricing(model)
    if not pricing:
        return {
            "input_cost": 0.0,
            "output_cost": 0.0,
            "cache_creation_cost": 0.0,
            "cache_read_cost": 0.0,
            "total_cost": 0.0,
        }

    costs = {
        "input_cost": tokens.get("input", 0) * pricing["input_cost_per_token"],
        "output_cost": tokens.get("output", 0) * pricing["output_cost_per_token"],
        "cache_creation_cost": tokens.get("cache_creation", 0) * pricing["cache_creation_cost_per_token"],
        "cache_read_cost": tokens.get("cache_read", 0) * pricing["cache_read_cost_per_token"],
    }

    costs["total_cost"] = sum(costs.values())
    return costs


def format_cost(cost: float) -> str:
    """Format cost for display."""
    if cost < 0.01:
        return f"${cost:.4f}"
    elif cost < 1:
        return f"${cost:.3f}"
    else:
        return f"${cost:.2f}"
