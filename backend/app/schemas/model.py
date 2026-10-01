from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ModelBase(BaseModel):
    name: str
    provider: str
    model_key: str
    model_type: Optional[str] = "multimodal"
    enabled: Optional[bool] = False
    configuration_json: Optional[Dict[str, Any]] = None
    pricing_json: Optional[Dict[str, Any]] = None

class ModelCreate(ModelBase):
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if v is None:
            raise ValueError("Model name is required")
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Model name cannot be blank")
        return trimmed

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        if v is None:
            raise ValueError("Provider is required")
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Provider cannot be blank")
        return trimmed

    @field_validator("model_key")
    @classmethod
    def validate_model_key(cls, v: str) -> str:
        if v is None:
            raise ValueError("Model key is required")
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Model key cannot be blank")
        return trimmed

class ModelUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    model_key: Optional[str] = None
    model_type: Optional[str] = None
    enabled: Optional[bool] = None
    configuration_json: Optional[Dict[str, Any]] = None
    pricing_json: Optional[Dict[str, Any]] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Model name cannot be blank")
            return trimmed
        return v

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Provider cannot be blank")
            return trimmed
        return v

    @field_validator("model_key")
    @classmethod
    def validate_model_key(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Model key cannot be blank")
            return trimmed
        return v

class ModelResponse(ModelBase):
    id: str
    name: str
    provider: str
    model_key: str
    model_type: str
    enabled: bool
    configuration_json: Optional[Dict[str, Any]] = None
    pricing_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
