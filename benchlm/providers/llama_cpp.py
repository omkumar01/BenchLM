"""llama.cpp provider implementation for BenchLM."""

from __future__ import annotations

import asyncio
import json
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


class LlamaCppProvider(LLMProvider):
    """llama.cpp HTTP server provider implementation."""

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        api_key: str = "",
        timeout: float = 300.0,
        n_ctx: int = 4096,
        n_predict: int = -1,
        n_gpu_layers: int = -1,
        **kwargs
    ):
        super().__init__(base_url, api_key, timeout, **kwargs)
        self.default_n_ctx = n_ctx
        self.default_n_predict = n_predict
        self.default_n_gpu_layers = n_gpu_layers

        # llama.cpp endpoints
        self._completion_endpoint = "/completion"
        self._chat_endpoint = "/chat"
        self._models_endpoint = "/models"
        self._health_endpoint = "/health"
        self._slots_endpoint = "/slots"
        self._props_endpoint = "/props"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.LLAMA_CPP

    @property
    def default_model(self) -> str:
        return "default"

    async def _check_health(self) -> HealthStatus:
        """Check llama.cpp server health."""
        start = time.perf_counter()
        try:
            response = await self._client.get(self._health_endpoint)
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
                    metadata=data,
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
        """Load available models from llama.cpp."""
        try:
            response = await self._client.get(self._models_endpoint)
            response.raise_for_status()
            data = response.json()

            models = []
            # llama.cpp typically returns a single model or model info
            if isinstance(data, dict):
                if "models" in data:
                    model_list = data["models"]
                else:
                    model_list = [data]

                for model_data in model_list:
                    model_info = self._parse_model_info(model_data)
                    models.append(model_info)

            self._models_cache = models
            return models
        except Exception:
            # If /models endpoint doesn't exist, create a default model entry
            default_model = ModelInfo(
                name="default",
                provider=self.provider_type,
                provider_model_id="default",
                context_window=self.default_n_ctx,
                description="llama.cpp default model",
                capabilities=["completion", "chat"],
            )
            self._models_cache = [default_model]
            return self._models_cache

    def _parse_model_info(self, data: Dict[str, Any]) -> ModelInfo:
        """Parse model info from llama.cpp response."""
        name = data.get("name", data.get("model", "default"))
        n_params = data.get("n_params", 0)
        n_ctx = data.get("n_ctx", self.default_n_ctx)
        quantization = data.get("quantization", "")

        param_count = None
        if n_params > 0:
            if n_params >= 1e9:
                param_count = f"{n_params / 1e9:.1f}B"
            elif n_params >= 1e6:
                param_count = f"{n_params / 1e6:.1f}M"

        return ModelInfo(
            name=name,
            provider=self.provider_type,
            provider_model_id=name,
            parameter_count=param_count,
            quantization=quantization or None,
            context_window=n_ctx,
            architecture=data.get("architecture", "llama"),
            description=f"llama.cpp model: {name}",
            capabilities=["completion", "chat"],
            metadata=data,
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

        # Try to get from props endpoint
        try:
            response = await self._client.get(self._props_endpoint)
            if response.status_code == 200:
                data = response.json()
                return self._parse_model_info({"name": model_name, **data})
        except Exception:
            pass

        return None

    async def _detect_capabilities(self) -> ProviderCapabilities:
        """Detect llama.cpp capabilities."""
        return ProviderCapabilities(
            supports_streaming=True,
            supports_chat=True,
            supports_completion=True,
            supports_embeddings=False,
            supports_function_calling=False,
            supports_vision=False,
            max_context_length=self.default_n_ctx,
            max_batch_size=1,
            supports_concurrent_requests=True,
            custom_parameters={
                "n_ctx": "Context window size",
                "n_predict": "Max tokens to predict",
                "n_gpu_layers": "GPU layers to offload",
                "temperature": "Sampling temperature",
                "top_p": "Top-p sampling",
                "top_k": "Top-k sampling",
                "repeat_penalty": "Repetition penalty",
            },
        )

    def _build_completion_payload(self, request: GenerationRequest) -> Dict[str, Any]:
        """Build payload for /completion."""
        config = request.config

        payload = {
            "prompt": request.prompt,
            "stream": config.stream,
            "n_predict": config.max_tokens if config.max_tokens > 0 else self.default_n_predict,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "top_k": config.top_k,
            "repeat_penalty": config.repeat_penalty,
            "frequency_penalty": config.frequency_penalty,
            "presence_penalty": config.presence_penalty,
            "seed": config.seed if config.seed != -1 else None,
            "stop": config.stop_sequences,
            "mirostat": config.mirostat,
            "mirostat_tau": config.mirostat_tau,
            "mirostat_eta": config.mirostat_eta,
        }

        # Add system prompt if provided
        if request.system_prompt:
            payload["system_prompt"] = request.system_prompt

        # Add extra params
        for key, value in config.extra_params.items():
            payload[key] = value

        # Remove None values
        return {k: v for k, v in payload.items() if v is not None}

    def _build_chat_payload(self, request: ChatRequest) -> Dict[str, Any]:
        """Build payload for /chat."""
        config = request.config

        messages = []
        for msg in request.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })

        payload = {
            "messages": messages,
            "stream": config.stream,
            "n_predict": config.max_tokens if config.max_tokens > 0 else self.default_n_predict,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "top_k": config.top_k,
            "repeat_penalty": config.repeat_penalty,
            "seed": config.seed if config.seed != -1 else None,
            "stop": config.stop_sequences,
        }

        # Add extra params
        for key, value in config.extra_params.items():
            payload[key] = value

        return {k: v for k, v in payload.items() if v is not None}

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text completion (non-streaming)."""
        payload = self._build_completion_payload(request)
        payload["stream"] = False

        start_time = time.perf_counter()
        try:
            response = await self._client.post(self._completion_endpoint, json=payload)
            response.raise_for_status()
            data = response.json()

            elapsed = time.perf_counter() - start_time

            text = data.get("content", "")
            # llama.cpp doesn't always return token counts
            prompt_tokens = data.get("tokens_predicted", 0)
            completion_tokens = data.get("tokens_evaluated", 0)

            return GenerationResponse(
                text=text,
                model=request.model,
                provider=self.provider_type,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                finish_reason=data.get("stop_type", "stop"),
                created_at=time.time(),
                metadata={
                    "elapsed_seconds": elapsed,
                    "tokens_per_second": data.get("tps", 0),
                },
            )
        except httpx.TimeoutException:
            raise ProviderTimeoutError("Generation timeout", self.provider_type)
        except httpx.HTTPStatusError as e:
            raise ProviderConnectionError(f"HTTP error: {e}", self.provider_type)

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[TokenEvent]:
        """Generate text completion with streaming."""
        payload = self._build_completion_payload(request)
        payload["stream"] = True

        try:
            async with self._client.stream("POST", self._completion_endpoint, json=payload) as response:
                response.raise_for_status()

                token_index = 0
                first_token = True

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # llama.cpp streaming format
                    token_text = chunk.get("content", "")
                    if token_text:
                        yield TokenEvent(
                            token_id=token_index,
                            token_text=token_text,
                            is_first_token=first_token,
                            is_last_token=chunk.get("stop", False),
                        )
                        token_index += 1
                        first_token = False

                    if chunk.get("stop", False):
                        break

        except httpx.TimeoutException:
            raise ProviderTimeoutError("Streaming generation timeout", self.provider_type)
        except httpx.HTTPStatusError as e:
            raise ProviderConnectionError(f"HTTP error: {e}", self.provider_type)

    async def chat(self, request: ChatRequest) -> GenerationResponse:
        """Generate chat completion (non-streaming)."""
        payload = self._build_chat_payload(request)
        payload["stream"] = False

        start_time = time.perf_counter()
        try:
            response = await self._client.post(self._chat_endpoint, json=payload)
            response.raise_for_status()
            data = response.json()

            elapsed = time.perf_counter() - start_time

            # Chat response format
            text = data.get("content", "") or data.get("message", {}).get("content", "")

            return GenerationResponse(
                text=text,
                model=request.model,
                provider=self.provider_type,
                prompt_tokens=0,  # Not provided by llama.cpp
                completion_tokens=0,
                total_tokens=0,
                finish_reason=data.get("stop_type", "stop"),
                created_at=time.time(),
                metadata={
                    "elapsed_seconds": elapsed,
                },
            )
        except httpx.TimeoutException:
            raise ProviderTimeoutError("Chat timeout", self.provider_type)
        except httpx.HTTPStatusError as e:
            raise ProviderConnectionError(f"HTTP error: {e}", self.provider_type)

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[TokenEvent]:
        """Generate chat completion with streaming."""
        payload = self._build_chat_payload(request)
        payload["stream"] = True

        try:
            async with self._client.stream("POST", self._chat_endpoint, json=payload) as response:
                response.raise_for_status()

                token_index = 0
                first_token = True

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    token_text = chunk.get("content", "") or chunk.get("message", {}).get("content", "")
                    if token_text:
                        yield TokenEvent(
                            token_id=token_index,
                            token_text=token_text,
                            is_first_token=first_token,
                            is_last_token=chunk.get("stop", False),
                        )
                        token_index += 1
                        first_token = False

                    if chunk.get("stop", False):
                        break

        except httpx.TimeoutException:
            raise ProviderTimeoutError("Chat streaming timeout", self.provider_type)
        except httpx.HTTPStatusError as e:
            raise ProviderConnectionError(f"HTTP error: {e}", self.provider_type)

    async def get_slots(self) -> Dict[str, Any]:
        """Get server slots information."""
        try:
            response = await self._client.get(self._slots_endpoint)
            response.raise_for_status()
            return response.json()
        except Exception:
            return {}

    async def get_properties(self) -> Dict[str, Any]:
        """Get server properties."""
        try:
            response = await self._client.get(self._props_endpoint)
            response.raise_for_status()
            return response.json()
        except Exception:
            return {}

    async def slot_action(self, slot_id: int, action: str) -> bool:
        """Perform action on a slot (release, etc.)."""
        try:
            response = await self._client.post(
                f"{self._slots_endpoint}/{slot_id}",
                json={"action": action},
            )
            response.raise_for_status()
            return True
        except Exception:
            return False