import time
from typing import Any, Dict, Optional
from app.adapters.base import ModelAdapter, ModelContext, ModelRequest, ModelResponse

class MockModelAdapter(ModelAdapter):
    """
    Deterministic fake model adapter for testing and local demonstration.
    Provides predictable OCR text extraction and contextual understanding.
    """

    def __init__(
        self,
        model_key: str = "mock-vision-v1",
        simulated_latency_ms: int = 120,
        should_fail: bool = False,
        fixed_text: Optional[str] = None,
        fixed_context: Optional[Dict[str, Any]] = None,
    ):
        self.model_key = model_key
        self.simulated_latency_ms = simulated_latency_ms
        self.should_fail = should_fail
        self.fixed_text = fixed_text
        self.fixed_context = fixed_context

    def run(self, request: ModelRequest) -> ModelResponse:
        start_time = time.perf_counter()

        if self.should_fail:
            raise RuntimeError(f"Mock model [{self.model_key}] simulated provider failure")

        # Determine media type and generate contextual mock text
        if request.image_path:
            text = self.fixed_text or "Brand Campaign: Pure Gold Colgate SBW. 20% Off Limited Time."
            summary = "Image marketing creative showcasing brand promo with call to action."
        elif request.frame_paths:
            num_frames = len(request.frame_paths)
            text = self.fixed_text or f"Video Commercial: Pure Gold Colgate SBW. Sequence across {num_frames} frames. Shop Now."
            summary = f"Video marketing narrative sampled across {num_frames} keyframes with strong brand visibility."
        else:
            text = self.fixed_text or "General marketing creative copy."
            summary = "Marketing creative with text overlay."

        context_data = self.fixed_context or {
            "brand": "Colgate",
            "product": "Pure Gold SBW",
            "offer": "20% Off",
            "cta": "Shop Now",
            "summary": summary,
        }

        # Token calculation heuristic
        input_tokens = len(text.split()) * 25 + (len(request.frame_paths or []) * 120 if request.frame_paths else 150)
        output_tokens = len(text.split()) * 4 + 40
        estimated_cost_usd = round((input_tokens * 0.0000005) + (output_tokens * 0.0000015), 6)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        total_latency_ms = max(self.simulated_latency_ms, elapsed_ms)

        return ModelResponse(
            text=text,
            context=ModelContext(**context_data),
            latency_ms=total_latency_ms,
            ttft_ms=int(total_latency_ms * 0.4),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=estimated_cost_usd,
            raw_output={
                "model_key": self.model_key,
                "provider": "mock",
                "simulated": True,
                "input_type": request.media_type,
            },
        )
