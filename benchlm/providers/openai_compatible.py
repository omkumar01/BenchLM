"""Generic OpenAI-compatible provider for BenchLM."""

from __future__ import annotations

import json
from datetime import datetime
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
    ProviderRateLimitError,
    ProviderValidationError,
)


class OpenAICompatibleProvider(LLMProvider):
    """Generic OpenAI-compatible provider for any OpenAI API-compatible endpoint."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000/v1",
        api_key: str = "",
        timeout: float = 300.0,
        organization: str = "",
        **kwargs
    ):
        # Ensure base_url ends with /v1
        if not base_url.endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"

        super().__init__(base_url, api_key, timeout, **kwargs)
        self.organization = organization

        # Standard OpenAI endpoints
        self._models_endpoint = "/models"
        self._completions_endpoint = "/completions"
        self._chat_endpoint = "/chat/completions"
        self._embeddings_endpoint = "/embeddings"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OPENAI_COMPATIBLE

    @property
    def default_model(self) -> str:
        return "gpt-3.5-turbo"

    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for OpenAI-compatible requests."""
        headers = super()._get_default_headers()
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        return headers

    async def _check_health(self) -> HealthStatus:
        """Check provider health via models endpoint."""
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
        """Load available models from OpenAI-compatible endpoint."""
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
        """Parse model info from OpenAI-compatible response."""
        model_id = data.get("id", "unknown")
        owned_by = data.get("owned_by", "unknown")

        return ModelInfo(
            name=model_id,
            provider=self.provider_type,
            provider_model_id=model_id,
            parameter_count=None,  # Not provided by standard API
            quantization=None,
            context_window=data.get("context_window", 4096),
            architecture="unknown",
            description=f"OpenAI-compatible model: {model_id}",
            capabilities=["completion", "chat"],
            metadata={
                "owned_by": owned_by,
                "permission": data.get("permission", []),
                "root": data.get("root", model_id),
                "created": data.get("created"),
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
        """Detect provider capabilities (generic OpenAI)."""
        return ProviderCapabilities(
            supports_streaming=True,
            supports_chat=True,
            supports_completion=True,
            supports_embeddings=True,
            supports_function_calling=False,  # Varies by provider
            supports_vision=False,  # Varies by provider
            max_context_length=4096,  # Varies by model
            max_batch_size=1,
            supports_concurrent_requests=True,
            custom_parameters={},
        )

    def _build_completion_payload(self, request: GenerationRequest) -> Dict[str, Any]:
        """Build payload for OpenAI completions endpoint."""
        config = request.config

        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "n": 1,
            "stream": config.stream,
            "stop": config.stop_sequences if config.stop_sequences else None,
            "frequency_penalty": config.frequency_penalty,
            "presence_penalty": config.presence_penalty,
            "seed": config.seed if config.seed != -1 else None,
            "user": request.metadata.get("user", ""),
        }

        # Add extra params
        for key, value in config.extra_params.items():
            payload[key] = value

        # Remove None values
        return {k: v for k, v in payload.items() if v is not None}

    def _build_chat_payload(self, request: ChatRequest) -> Dict[str, Any]:
        """Build payload for OpenAI chat completions endpoint."""
        config = request.config

        messages = []
        for msg in request.messages:
            message = {
                "role": msg.role,
                "content": msg.content,
            }
            if msg.name:
                message["name"] = msg.name
            if msg.tool_calls:
                message["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                message["tool_call_id"] = msg.tool_call_id
            messages.append(message)

        payload = {
            "model": request.model,
            "messages": messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "n": 1,
            "stream": config.stream,
            "stop": config.stop_sequences if config.stop_sequences else None,
            "frequency_penalty": config.frequency_penalty,
            "presence_penalty": config.presence_penalty,
            "seed": config.seed if config.seed != -1 else None,
            "user": request.metadata.get("user", ""),
        }

        # Add tools if provided
        if request.tools:
            payload["tools"] = request.tools
        if request.tool_choice:
            payload["tool_choice"] = request.tool_choice

        # Add extra params
        for key, value in config.extra_params.items():
            payload[key] = value

        # Remove None values
        return {k: v for k, v in payload.items() if v is not None}

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text completion (non-streaming)."""
        payload = self._build_completion_payload(request)
        payload["stream"] = False

        start_time = time.perf_counter()
        try:
            response = await self._client.post(self._completions_endpoint, json=payload)
            response.raise_for_status()
            data = response.json()

            elapsed = time.perf_counter() - start_time
            return self._parse_openai_completion(data, elapsed, request.model)

        except httpx.TimeoutException:
            raise ProviderTimeoutError("Generation timeout", self.provider_type)
        except httpx.HTTPStatusError as e:
            return self._handle_http_error(e, request.model)

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[TokenEvent]:
        """Generate text completion with streaming."""
        payload = self._build_completion_payload(request)
        payload["stream"] = True

        try:
            async with self._client.stream("POST", self._completions_endpoint, json=payload) as response:
                response.raise_for_status()

                token_index = 0
                first_token = True

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    # OpenAI streaming format: "data: {...}"
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: "
                        if data_str.strip() == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("text", "")
                            if delta:
                                yield TokenEvent(
                                    token_id=token_index,
                                    token_text=delta,
                                    timestamp=datetime.now(),
                                    is_first_token=first_token,
                                    is_last_token=choices[0].get("finish_reason") is not None,
                                )
                                token_index += 1
                                first_token = False

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
            return self._parse_openai_chat(data, elapsed, request.model)

        except httpx.TimeoutException:
            raise ProviderTimeoutError("Chat timeout", self.provider_type)
        except httpx.HTTPStatusError as e:
            return self._handle_http_error(e, request.model)

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

                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield TokenEvent(
                                    token_id=token_index,
                                    token_text=content,
                                    timestamp=datetime.now(),
                                    is_first_token=first_token,
                                    is_last_token=choices[0].get("finish_reason") is not None,
                                )
                                token_index += 1
                                first_token = False

        except httpx.TimeoutException:
            raise ProviderTimeoutError("Chat streaming timeout", self.provider_type)
        except httpx.HTTPStatusError as e:
            raise ProviderConnectionError(f"HTTP error: {e}", self.provider_type)

    def _parse_openai_completion(
        self,
        data: Dict[str, Any],
        elapsed: float,
        model: str
    ) -> GenerationResponse:
        """Parse OpenAI completion response."""
        choices = data.get("choices", [])
        text = choices[0].get("text", "") if choices else ""
        finish_reason = choices[0].get("finish_reason", "stop") if choices else "stop"

        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

        return GenerationResponse(
            text=text,
            model=model,
            provider=self.provider_type,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            finish_reason=finish_reason,
            created_at=time.time(),
            metadata={
                "elapsed_seconds": elapsed,
                "id": data.get("id"),
                "created": data.get("created"),
                "system_fingerprint": data.get("system_fingerprint"),
            },
        )

    def _parse_openai_chat(
        self,
        data: Dict[str, Any],
        elapsed: float,
        model: str
    ) -> GenerationResponse:
        """Parse OpenAI chat completion response."""
        choices = data.get("choices", [])
        message = choices[0].get("message", {}) if choices else {}
        text = message.get("content", "")
        finish_reason = choices[0].get("finish_reason", "stop") if choices else "stop"

        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

        return GenerationResponse(
            text=text,
            model=model,
            provider=self.provider_type,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            finish_reason=finish_reason,
            created_at=time.time(),
            metadata={
                "elapsed_seconds": elapsed,
                "id": data.get("id"),
                "created": data.get("created"),
                "system_fingerprint": data.get("system_fingerprint"),
                "tool_calls": message.get("tool_calls"),
            },
        )

    def _handle_http_error(self, error: httpx.HTTPStatusError, model: str) -> GenerationResponse:
        """Handle HTTP errors and return appropriate error response."""
        status_code = error.response.status_code

        try:
            error_data = error.response.json()
            error_message = error_data.get("error", {}).get("message", str(error))
        except Exception:
            error_message = str(error)

        if status_code == 401:
            raise ProviderConnectionError(f"Authentication failed: {error_message}", self.provider_type)
        elif status_code == 404:
            raise ProviderModelNotFoundError(f"Model not found: {model}", self.provider_type)
        elif status_code == 429:
            raise ProviderRateLimitError(f"Rate limited: {error_message}", self.provider_type)
        elif status_code == 400:
            raise ProviderValidationError(f"Invalid request: {error_message}", self.provider_type)
        else:
            raise ProviderConnectionError(f"HTTP {status_code}: {error_message}", self.provider_type, status_code)

    async def embeddings(
        self,
        texts: List[str],
        model: str = "text-embedding-ada-002"
    ) -> List[List[float]]:
        """Generate embeddings (if supported)."""
        payload = {
            "model": model,
            "input": texts,
        }

        try:
            response = await self._client.post(self._embeddings_endpoint, json=payload)
            response.raise_for_status()
            data = response.json()

            embeddings = []
            for item in data.get("data", []):
                embeddings.append(item.get("embedding", []))

            return embeddings
        except Exception as e:
            raise ProviderConnectionError(f"Embeddings failed: {e}", self.provider_type)