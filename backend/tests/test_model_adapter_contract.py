import pytest
from app.adapters.base import (
    ModelAdapter,
    ModelContext,
    ModelRequest,
    ModelResponse,
)
from app.adapters.mock_adapter import MockModelAdapter
from app.adapters.registry import (
    AdapterNotFoundError,
    get_adapter,
    register_adapter,
)

def test_model_adapter_is_abstract():
    """Verify ModelAdapter cannot be instantiated without implementing run()."""
    with pytest.raises(TypeError):
        ModelAdapter()

def test_model_response_structure():
    """Verify ModelResponse structure and field defaults."""
    resp = ModelResponse(
        text="Extracted Campaign Text",
        context=ModelContext(
            brand="Colgate",
            product="Total",
            offer="Save 15%",
            cta="Buy Now",
            summary="Colgate promotional banner",
        ),
        latency_ms=1250,
        ttft_ms=450,
        input_tokens=1000,
        output_tokens=120,
        estimated_cost_usd=0.002,
        raw_output={"provider_id": "test-123"},
    )

    data = resp.model_dump()
    assert data["text"] == "Extracted Campaign Text"
    assert data["context"]["brand"] == "Colgate"
    assert data["context"]["product"] == "Total"
    assert data["context"]["offer"] == "Save 15%"
    assert data["context"]["cta"] == "Buy Now"
    assert data["context"]["summary"] == "Colgate promotional banner"
    assert data["latency_ms"] == 1250
    assert data["ttft_ms"] == 450
    assert data["input_tokens"] == 1000
    assert data["output_tokens"] == 120
    assert data["estimated_cost_usd"] == 0.002
    assert data["raw_output"]["provider_id"] == "test-123"

def test_model_response_nullable_fields():
    """Ensure models that do not expose token usage or TTFT can return nulls gracefully."""
    resp = ModelResponse(
        text="Simple local model output",
        context=ModelContext(summary="Local inference"),
    )
    assert resp.latency_ms is None
    assert resp.ttft_ms is None
    assert resp.input_tokens is None
    assert resp.output_tokens is None
    assert resp.estimated_cost_usd is None
    assert resp.raw_output is None
    assert resp.context.brand is None

def test_mock_adapter_image_run():
    """Verify MockModelAdapter processes an image request."""
    adapter = MockModelAdapter(model_key="mock-vision-v1", simulated_latency_ms=50)
    req = ModelRequest(image_path="/path/to/test_image.png")

    resp = adapter.run(req)
    assert isinstance(resp, ModelResponse)
    assert "Colgate" in resp.text
    assert resp.context.brand == "Colgate"
    assert resp.latency_ms >= 50
    assert resp.input_tokens > 0
    assert resp.output_tokens > 0
    assert resp.estimated_cost_usd > 0
    assert resp.raw_output["input_type"] == "image"

def test_mock_adapter_video_frames_run():
    """Verify MockModelAdapter processes video frame inputs."""
    adapter = MockModelAdapter(model_key="mock-vision-v1")
    req = ModelRequest(
        frame_paths=[
            "/path/to/frame_000001.jpg",
            "/path/to/frame_000002.jpg",
            "/path/to/frame_000003.jpg",
        ]
    )

    resp = adapter.run(req)
    assert "3 frames" in resp.text
    assert "3 keyframes" in resp.context.summary
    assert resp.raw_output["input_type"] == "video"

def test_mock_adapter_simulated_failure():
    """Verify MockModelAdapter can simulate failure when configured."""
    adapter = MockModelAdapter(model_key="failing-model", should_fail=True)
    req = ModelRequest(image_path="/path/to/image.png")

    with pytest.raises(RuntimeError) as exc:
        adapter.run(req)
    assert "simulated provider failure" in str(exc.value)

def test_adapter_registry():
    """Verify registering and retrieving adapters from registry."""
    # Built-in mock provider
    adapter = get_adapter("mock", "mock-vision-v1")
    assert isinstance(adapter, MockModelAdapter)

    # Case insensitive
    adapter_upper = get_adapter("MOCK", "mock-vision-v1")
    assert isinstance(adapter_upper, MockModelAdapter)

    # Unknown provider
    with pytest.raises(AdapterNotFoundError):
        get_adapter("unknown_provider_xyz", "model-key")

    # Custom provider registration
    class CustomTestAdapter(ModelAdapter):
        def run(self, request: ModelRequest) -> ModelResponse:
            return ModelResponse(text="custom adapter response")

    register_adapter("custom_ai", lambda key, cfg: CustomTestAdapter())
    custom = get_adapter("custom_ai", "custom-model")
    assert isinstance(custom, CustomTestAdapter)
    out = custom.run(ModelRequest())
    assert out.text == "custom adapter response"
