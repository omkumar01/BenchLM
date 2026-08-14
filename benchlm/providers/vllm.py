"""vLLM provider implementation for BenchLM (OpenAI-compatible)."""

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


class VLLMProvider(OpenAICompatibleProvider):
    """vLLM provider - OpenAI-compatible with vLLM specific features."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: str = "",
        timeout: float = 300.0,
        **kwargs
    ):
        # vLLM uses OpenAI-compatible API at /v1
        if not base_url.endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"

        super().__init__(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout,
            **kwargs
        )

        # vLLM specific endpoints
        self._models_endpoint = "/models"
        self._completions_endpoint = "/completions"
        self._chat_endpoint = "/chat/completions"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.VLLM

    @property
    def default_model(self) -> str:
        return "default"

    async def _check_health(self) -> HealthStatus:
        """Check vLLM health."""
        start = time.perf_counter()
        try:
            response = await self._client.get(self._models_endpoint)
            latency_ms = (time.perf_counter() - start) * 1000

            if response.status_code == 200:
                data = response.json()
                models = await self.list_models()

                self._healthy = True
                return HealthStatus(
                    healthy=True,
                    provider=self.provider_type,
                    endpoint=self.base_url,
                    latency_ms=latency_ms,
                    models_count=len(models),
                    metadata={},
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
        """Load available models from vLLM."""
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
        """Parse model info from vLLM response."""
        model_id = data.get("id", "unknown")
        owned_by = data.get("owned_by", "vllm")

        # vLLM model IDs typically include the full path
        # Extract parameter count if present
        param_count = None
        quantization = None

        parts = model_id.lower().split("-")
        for part in parts:
            if part.endswith("b") and part[:-1].replace(".", "").isdigit():
                param_count = part.upper()
            if any(q in part for q in ["gptq", "awq", "fp8", "int4", "int8"]):
                quantization = part.upper()

        return ModelInfo(
            name=model_id,
            provider=self.provider_type,
            provider_model_id=model_id,
            parameter_count=param_count,
            quantization=quantization,
            context_window=data.get("max_model_len", 4096),
            architecture=data.get("architecture", "auto"),
            description=f"vLLM model: {model_id}",
            capabilities=["completion", "chat"],
            metadata={
                "owned_by": owned_by,
                "permission": data.get("permission", []),
                "root": data.get("root", model_id),
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
        return None

    async def _detect_capabilities(self) -> ProviderCapabilities:
        """Detect vLLM capabilities."""
        return ProviderCapabilities(
            supports_streaming=True,
            supports_chat=True,
            supports_completion=True,
            supports_embeddings=True,
            supports_function_calling=True,  # vLLM supports function calling
            supports_vision=False,  # Depends on model
            max_context_length=32768,  # Configurable
            max_batch_size=32,  # vLLM supports batching
            supports_concurrent_requests=True,
            custom_parameters={
                "temperature": "Sampling temperature",
                "top_p": "Top-p sampling",
                "top_k": "Top-k sampling",
                "max_tokens": "Maximum tokens to generate",
                "stop": "Stop sequences",
                "presence_penalty": "Presence penalty",
                "frequency_penalty": "Frequency penalty",
                "min_p": "Min-p sampling",
                "repetition_penalty": "Repetition penalty",
                "ignore_eos": "Ignore EOS token",
                "skip_special_tokens": "Skip special tokens",
                "spaces_between_special_tokens": "Spaces between special tokens",
            },
        )

    async def get_metrics(self) -> Dict[str, Any]:
        """Get vLLM Prometheus metrics."""
        try:
            response = await self._client.get("/metrics")
            if response.status_code == 200:
                return {"metrics": response.text}
        except Exception:
            pass
        return {}

    # Override to handle vLLM specific response formats
    def _parse_openai_completion(self, data: Dict[str, Any]) -> GenerationResponse:
        """Parse vLLM completion response (extends OpenAI format)."""
        response = super()._parse_openai_completion(data)

        # vLLM specific fields
        response.metadata.update({
            "vllm_tps": data.get("usage", {}).get("completion_tokens", 0) / max(
                data.get("usage", {}).get("completion_time", 0.001), 0.001
            ),
        })

        return response

    def _parse_openai_chat(self, data: Dict[str, Any]) -> GenerationResponse:
        """Parse vLLM chat response (extends OpenAI format)."""
        response = super()._parse_openai_chat(data)

        # vLLM specific fields
        response.metadata.update({
            "vllm_prompt_logprobs": data.get("prompt_logprobs"),
            "vllm_finish_reason": data.get("choices", [{}])[0].get("finish_reason"),
        })

        return response