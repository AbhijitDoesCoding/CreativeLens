from typing import Any, Callable, Dict, Optional
from app.adapters.base import ModelAdapter
from app.adapters.mock_adapter import MockModelAdapter

_ADAPTER_REGISTRY: Dict[str, Callable[[str, Optional[Dict[str, Any]]], ModelAdapter]] = {}

class AdapterNotFoundError(KeyError):
    """Raised when no adapter is registered for a given provider/model."""
    pass

def register_adapter(
    provider: str,
    factory: Callable[[str, Optional[Dict[str, Any]]], ModelAdapter],
) -> None:
    """Register an adapter factory function for a provider."""
    _ADAPTER_REGISTRY[provider.lower()] = factory

def get_adapter(
    provider: str,
    model_key: str,
    configuration: Optional[Dict[str, Any]] = None,
) -> ModelAdapter:
    """
    Resolve and instantiate the appropriate ModelAdapter for a provider and model_key.
    """
    key = provider.lower()
    factory = _ADAPTER_REGISTRY.get(key)
    if not factory:
        raise AdapterNotFoundError(
            f"No adapter registered for provider '{provider}'. Registered providers: {list(_ADAPTER_REGISTRY.keys())}"
        )
    return factory(model_key, configuration)

# Register default mock / test provider
def _mock_factory(model_key: str, configuration: Optional[Dict[str, Any]] = None) -> ModelAdapter:
    cfg = configuration or {}
    sim_latency = cfg.get("simulated_latency_ms", 100)
    should_fail = cfg.get("should_fail", False)
    return MockModelAdapter(
        model_key=model_key,
        simulated_latency_ms=sim_latency,
        should_fail=should_fail,
    )

register_adapter("mock", _mock_factory)
register_adapter("test", _mock_factory)
register_adapter("example_provider", _mock_factory)
