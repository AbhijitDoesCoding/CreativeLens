from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

class ModelContext(BaseModel):
    brand: Optional[str] = None
    product: Optional[str] = None
    offer: Optional[str] = None
    cta: Optional[str] = None
    summary: Optional[str] = None

    model_config = ConfigDict(extra="ignore")

class ModelRequest(BaseModel):
    image_path: Optional[str] = None
    frame_paths: Optional[List[str]] = None
    prompt: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="ignore")

    @property
    def media_type(self) -> str:
        if self.image_path:
            return "image"
        if self.frame_paths:
            return "video"
        return "unknown"

class ModelResponse(BaseModel):
    text: str = ""
    context: ModelContext = Field(default_factory=ModelContext)
    latency_ms: Optional[int] = None
    ttft_ms: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    estimated_cost_usd: Optional[float] = None
    raw_output: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="ignore")

class ModelAdapter(ABC):
    """
    Abstract base class for all AI vision/multimodal model adapters.
    Core inference code must only interact with this interface.
    """

    @abstractmethod
    def run(self, request: ModelRequest) -> ModelResponse:
        """
        Executes model inference on the provided media inputs and prompt.
        Must return a standardized ModelResponse.
        """
        pass

    def is_available(self) -> bool:
        """
        Checks whether the adapter is ready to execute (e.g. credentials, network, local server).
        Default is True.
        """
        return True
