"""LM Studio provider implementation for BenchLM (OpenAI-compatible)."""

from __future__ import annotations

import time
from typing import Any, AsyncIterator, List, Optional, Dict

import httpx

from benchlm.providers.base import (
    LLMProvider,
    ModelInfo,
    ProviderCapabilities,
    ProviderType,
    GenerationConfig,
    GenerationRequest,
    GenerationResponse,
    ChatMessage,
    ChatRequest,
    TokenEvent,
    HealthStatus,
    ProviderConnectionError,
    ProviderTimeoutError,
    ProviderModelNotFoundError,
)
from benchlm.providers.openai_compatible import OpenAICompatibleProvider


class LMStudioProvider(OpenAICompatibleProvider):
    """LM Studio provider - OpenAI-compatible with LM Studio specific features."""

    def __init__(
        self,
        base_url: str = "http://localhost:1234",
        api_key: str = "lm-studio",
        timeout: float = 300.0,
        **kwargs
    ):
        # LM Studio uses OpenAI-compatible API at /v1
        if not base_url.endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"

        super().__init__(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            **kwargs
        )

        # LM Studio specific endpoints
        self._models_endpoint = "/models"
        self._completions_endpoint = "/completions"
        self._chat_endpoint = "/chat/completions"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.LMSTUDIO

    @property
    def default_model(self) -> str:
        return "local-model"

    async def _check_health(self) -> HealthStatus:
        """Check LM Studio health."""
        start = time.perf_counter()
        try:
            response = await self._client.get(self._models_endpoint)
            latency_ms = (time.perf_counter() - start) * 1000

            if response.status_code == 200:
                data = response.json()
                models = await self.list_models()

                # Get loaded model info
                loaded_model = None
                for model in data.get("data", []):
                    if model.get("type") == "llm":
                        loaded_model = model.get("id")
                        break

                self._healthy = True
                return HealthStatus(
                    healthy=True,
                    provider=self.provider_type,
                    endpoint=self.base_url,
                    latency_ms=latency_ms,
                    models_count=len(models),
                    metadata={"loaded_model": loaded_model},
                )
            else:
                self._healthy = False
                return HealthStatus(
                    healthy=False,
                    provider=self.provider_type,
                    endpoint=self.base_url,
                    error=f"Health check failed: {response.status_code}",
                    latency_ms=latency_ms,
                )
        except httpx.ConnectError as e:
            self._healthy = False
            return HealthStatus(
                healthy=False,
                provider=self.provider_type,
                endpoint=self.base_url,
                error=f"Connection failed: {e}",
            )
        except httpx.TimeoutException as e:
            self._healthy = False
            return HealthStatus(
                healthy=False,
                provider=self.provider_type,
                endpoint=self.base_url,
                error=f"Timeout: {e}",
            )
        except Exception as e:
            self._healthy = False
            return HealthStatus(
                healthy=False,
                provider=self.provider_type,
                endpoint=self.base_url,
                error=str(e),
            )

    async def _load_models(self) -> List[ModelInfo]:
        """Load available models from LM Studio."""
        try:
            response = await self._client.get(self._models_endpoint)
            response.raise_for_status()
            data = response.json()

            models = []
            for model_data in data.get("data", []):
                model_info = self._parse_model_info(model_data)
                models.append(model_info)

            self._models_cache = models
            return models
        except Exception as e:
            raise ProviderConnectionError(f"Failed to load models: {e}", self.provider_type)

    def _parse_model_info(self, data: Dict[str, Any]) -> ModelInfo:
        """Parse model info from LM Studio response."""
        model_id = data.get("id", "unknown")
        owned_by = data.get("owned_by", "local")

        # LM Studio model IDs often contain quantization info
        # e.g., "qwen2.5-7b-instruct-q4_k_m"
        quantization = None
        param_count = None

        # Try to extract quantization from model ID
        parts = model_id.lower().split("-")
        for part in parts:
            if part.startswith("q") and any(c.isdigit() for c in part):
                quantization = part.upper()
            if part.endswith("b") and part[:-1].replace(".", "").isdigit():
                param_count = part.upper()

        return ModelInfo(
            name=model_id,
            provider=self.provider_type,
            provider_model_id=model_id,
            parameter_count=param_count,
            quantization=quantization,
            context_window=data.get("context_length", 4096),
            architecture="auto",
            description=f"LM Studio model: {model_id}",
            capabilities=["completion", "chat"],
            metadata={
                "owned_by": owned_by,
                "type": data.get("type", "llm"),
            },
        )

    async def list_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """List available models."""
        if force_refresh or not self._models_cache:
            await self._load_models()
        return self._models_cache

    async def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get detailed model information."""
        for model in self._models_cache:
            if model.name == model_name:
                return model

        # Try to get specific model info
        try:
            response = await self._client.get(f"{self._models_endpoint}/{model_name}")
            if response.status_code == 200:
                data = response.json()
                return self._parse_model_info(data)
        except Exception:
            pass

        return None

    async def _detect_capabilities(self) -> ProviderCapabilities:
        """Detect LM Studio capabilities."""
        return ProviderCapabilities(
            supports_streaming=True,
            supports_chat=True,
            supports_completion=True,
            supports_embeddings=True,  # LM Studio supports embeddings
            supports_function_calling=False,  # Depends on model
            supports_vision=False,  # Depends on model
            max_context_length=32768,  # Varies by model
            max_batch_size=1,
            supports_concurrent_requests=True,
            custom_parameters={
                "temperature": "Sampling temperature",
                "top_p": "Top-p sampling",
                "max_tokens": "Maximum tokens to generate",
                "stop": "Stop sequences",
                "presence_penalty": "Presence penalty",
                "frequency_penalty": "Frequency penalty",
            },
        )

    # Override base methods to handle LM Studio specifics if needed
    # Most functionality inherited from OpenAICompatibleProvider

    async def get_loaded_model(self) -> Optional[str]:
        """Get currently loaded model in LM Studio."""
        try:
            response = await self._client.get(self._models_endpoint)
            if response.status_code == 200:
                data = response.json()
                for model in data.get("data", []):
                    if model.get("type") == "llm":
                        return model.get("id")
        except Exception:
            pass
        return None

    async def load_model(self, model_name: str, **kwargs) -> bool:
        """Load a model in LM Studio (if supported by API)."""
        # LM Studio doesn't have a standard API for loading models
        # This would need to be done via the UI or CLI
        return False

    async def unload_model(self) -> bool:
        """Unload current model."""
        # Not supported via API
        return False