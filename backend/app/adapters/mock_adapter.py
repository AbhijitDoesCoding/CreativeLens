import os
import time
from pathlib import Path
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

    def _detect_marketing_context(self, request: ModelRequest) -> Dict[str, str]:
        if self.fixed_context:
            return dict(self.fixed_context)

        # Determine target name from metadata or file paths
        meta = request.metadata or {}
        raw_name = (
            meta.get("original_filename")
            or meta.get("filename")
            or (Path(request.image_path).name if request.image_path else "")
            or (Path(request.frame_paths[0]).name if request.frame_paths else "")
        )
        stem = Path(raw_name).stem.lower().replace("-", " ").replace("_", " ")

        if "nike" in stem:
            brand = "Nike"
            product = "Air Max Pro"
            offer = "Free Express Shipping"
            cta = "Just Do It"
        elif "apple" in stem or "iphone" in stem:
            brand = "Apple"
            product = "iPhone 15 Pro"
            offer = "Trade in and Save"
            cta = "Buy Now"
        elif "samsung" in stem or "galaxy" in stem:
            brand = "Samsung"
            product = "Galaxy S24"
            offer = "Double Your Storage"
            cta = "Pre-Order"
        elif "coke" in stem or "coca" in stem:
            brand = "Coca-Cola"
            product = "Zero Sugar"
            offer = "Share an Ice Cold Coke"
            cta = "Open Happiness"
        else:
            brand = "Colgate"
            product = "Pure Gold SBW"
            offer = "20% Off Limited Time"
            cta = "Shop Now"

        if request.frame_paths:
            num_frames = len(request.frame_paths)
            summary = f"Video marketing narrative sampled across {num_frames} keyframes with strong brand visibility."
        else:
            summary = f"Image marketing creative showcasing brand promo with call to action."

        return {
            "brand": brand,
            "product": product,
            "offer": offer,
            "cta": cta,
            "summary": summary,
        }

    def run(self, request: ModelRequest) -> ModelResponse:
        start_time = time.perf_counter()

        if self.should_fail:
            raise RuntimeError(f"Mock model [{self.model_key}] simulated provider failure")

        if self.simulated_latency_ms > 0:
            # Small non-blocking sleep (max 20ms) so tests stay fast while simulating realistic passage of time
            time.sleep(min(self.simulated_latency_ms / 1000.0, 0.02))

        context_dict = self._detect_marketing_context(request)

        # Generate detected text based on media type & context
        if self.fixed_text:
            text = self.fixed_text
        elif request.image_path:
            text = f"Brand Campaign: {context_dict['brand']} {context_dict['product']}. {context_dict['offer']}."
        elif request.frame_paths:
            num_frames = len(request.frame_paths)
            text = f"Video Commercial: {context_dict['brand']} {context_dict['product']}. Sequence across {num_frames} frames. {context_dict['cta']}."
        else:
            text = f"{context_dict['brand']} {context_dict['product']} Creative Promo."

        # Token calculation heuristic
        input_tokens = len(text.split()) * 25 + (len(request.frame_paths or []) * 120 if request.frame_paths else 150)
        output_tokens = len(text.split()) * 4 + 40
        estimated_cost_usd = round((input_tokens * 0.0000005) + (output_tokens * 0.0000015), 6)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        total_latency_ms = max(self.simulated_latency_ms, elapsed_ms)

        return ModelResponse(
            text=text,
            context=ModelContext(**context_dict),
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
