"""Ollama provider implementation for BenchLM."""

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


class OllamaProvider(LLMProvider):
    """Ollama provider implementation."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        api_key: str = "",
        timeout: float = 300.0,
        keep_alive: str = "5m",
        **kwargs
    ):
        super().__init__(base_url, api_key, timeout, **kwargs)
        self.keep_alive = keep_alive
        self._models_endpoint = "/api/tags"
        self._generate_endpoint = "/api/generate"
        self._chat_endpoint = "/api/chat"
        self._show_endpoint = "/api/show"
        self._version_endpoint = "/api/version"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OLLAMA

    @property
    def default_model(self) -> str:
        return "llama3.1:8b"

    async def _check_health(self) -> HealthStatus:
        """Check Ollama health."""
        start = time.perf_counter()
        try:
            response = await self._client.get(self._version_endpoint)
            response.raise_for_status()
            latency_ms = (time.perf_counter() - start) * 1000

            version_data = response.json()
            models = await self.list_models()

            # Get GPU memory info if available
            gpu_memory_used = None
            gpu_memory_total = None
            try:
                ps_response = await self._client.get("/api/ps")
                if ps_response.status_code == 200:
                    ps_data = ps_response.json()
                    # Ollama doesn't directly expose GPU memory in /api/ps
                    # but we can get model info
            except Exception:
                pass

            self._healthy = True
            return HealthStatus(
                healthy=True,
                provider=self.provider_type,
                endpoint=self.base_url,
                latency_ms=latency_ms,
                models_count=len(models),
                gpu_memory_used=gpu_memory_used,
                gpu_memory_total=gpu_memory_total,
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
        """Load available models from Ollama."""
        try:
            response = await self._client.get(self._models_endpoint)
            response.raise_for_status()
            data = response.json()

            models = []
            for model_data in data.get("models", []):
                model_info = self._parse_model_info(model_data)
                models.append(model_info)

            self._models_cache = models
            return models
        except Exception as e:
            raise ProviderConnectionError(f"Failed to load models: {e}", self.provider_type)

    def _parse_model_info(self, data: Dict[str, Any]) -> ModelInfo:
        """Parse model info from Ollama response."""
        name = data.get("name", "")
        size = data.get("size", 0)
        digest = data.get("digest", "")
        modified = data.get("modified_at", "")
        details = data.get("details", {})

        # Parse parameter count from name or details
        param_count = details.get("parameter_size", "")
        if not param_count and ":" in name:
            param_part = name.split(":")[-1]
            if param_part.endswith("b") or param_part.endswith("B"):
                param_count = param_part.upper()

        # Determine quantization
        quantization = details.get("quantization_level", "")
        if not quantization and ":" in name:
            quant_part = name.split(":")[-1]
            if "q" in quant_part.lower() or "fp" in quant_part.lower():
                quantization = quant_part.upper()

        return ModelInfo(
            name=name,
            provider=self.provider_type,
            provider_model_id=name,
            size_bytes=size if size > 0 else None,
            parameter_count=param_count or None,
            quantization=quantization or None,
            context_window=details.get("context_length", 4096),
            architecture=details.get("architecture", ""),
            family=details.get("family", ""),
            description=f"Ollama model: {name}",
            capabilities=["completion", "chat"],
            metadata={
                "digest": digest,
                "modified_at": modified,
                "details": details,
            },
        )

    async def list_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """List available models."""
        if force_refresh or not self._models_cache:
            await self._load_models()
        return self._models_cache

    async def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get detailed model information."""
        # Check cache first
        for model in self._models_cache:
            if model.name == model_name:
                return model

        # Fetch from /api/show
        try:
            response = await self._client.post(
                self._show_endpoint,
                json={"name": model_name},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()

            # Merge with cached info
            model_info = self._parse_model_info({"name": model_name, "details": data})
            return model_info
        except Exception:
            return None

    async def _detect_capabilities(self) -> ProviderCapabilities:
        """Detect Ollama capabilities."""
        caps = ProviderCapabilities(
            supports_streaming=True,
            supports_chat=True,
            supports_completion=True,
            supports_embeddings=False,  # Ollama has /api/embed but different
            supports_function_calling=False,
            supports_vision=False,
            max_context_length=131072,  # Varies by model
            max_batch_size=1,
            supports_concurrent_requests=True,
        )

        # Try to get version for more accurate capabilities
        try:
            response = await self._client.get(self._version_endpoint)
            if response.status_code == 200:
                version = response.json().get("version", "")
                caps.metadata["version"] = version
        except Exception:
            pass

        return caps

    def _build_generate_payload(self, request: GenerationRequest) -> Dict[str, Any]:
        """Build payload for /api/generate."""
        config = request.config
        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "system": request.system_prompt,
            "stream": config.stream,
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": config.temperature,
                "top_p": config.top_p,
                "top_k": config.top_k,
                "seed": config.seed if config.seed != -1 else None,
                "num_predict": config.max_tokens,
                "stop": config.stop_sequences,
                "repeat_penalty": config.repeat_penalty,
                "frequency_penalty": config.frequency_penalty,
                "presence_penalty": config.presence_penalty,
                "mirostat": config.mirostat,
                "mirostat_tau": config.mirostat_tau,
                "mirostat_eta": config.mirostat_eta,
            },
        }

        # Add images if provided
        if request.images:
            payload["images"] = request.images

        # Add extra params
        for key, value in config.extra_params.items():
            payload["options"][key] = value

        # Remove None values
        payload["options"] = {k: v for k, v in payload["options"].items() if v is not None}

        return payload

    def _build_chat_payload(self, request: ChatRequest) -> Dict[str, Any]:
        """Build payload for /api/chat."""
        config = request.config
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]

        payload = {
            "model": request.model,
            "messages": messages,
            "stream": config.stream,
            "keep_alive": self.keep_alive,
            "options": {
                "temperature": config.temperature,
                "top_p": config.top_p,
                "top_k": config.top_k,
                "seed": config.seed if config.seed != -1 else None,
                "num_predict": config.max_tokens,
                "stop": config.stop_sequences,
                "repeat_penalty": config.repeat_penalty,
            },
        }

        payload["options"] = {k: v for k, v in payload["options"].items() if v is not None}
        return payload

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text completion (non-streaming)."""
        payload = self._build_generate_payload(request)
        payload["stream"] = False

        start_time = time.perf_counter()
        try:
            response = await self._client.post(self._generate_endpoint, json=payload)
            response.raise_for_status()
            data = response.json()

            elapsed = time.perf_counter() - start_time

            # Parse response
            text = data.get("response", "")
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)

            return GenerationResponse(
                text=text,
                model=request.model,
                provider=self.provider_type,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                finish_reason=data.get("done_reason", "stop"),
                created_at=time.time(),
                metadata={
                    "elapsed_seconds": elapsed,
                    "eval_duration_ns": data.get("eval_duration", 0),
                    "prompt_eval_duration_ns": data.get("prompt_eval_duration", 0),
                },
            )
        except httpx.TimeoutException:
            raise ProviderTimeoutError("Generation timeout", self.provider_type)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ProviderModelNotFoundError(f"Model not found: {request.model}", self.provider_type)
            raise ProviderConnectionError(f"HTTP error: {e}", self.provider_type)

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[TokenEvent]:
        """Generate text completion with streaming."""
        payload = self._build_generate_payload(request)
        payload["stream"] = True

        try:
            async with self._client.stream("POST", self._generate_endpoint, json=payload) as response:
                response.raise_for_status()

                token_index = 0
                first_token = True
                accumulated_text = ""

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Extract token
                    token_text = chunk.get("response", "")
                    if token_text:
                        accumulated_text += token_text
                        yield TokenEvent(
                            token_id=token_index,
                            token_text=token_text,
                            is_first_token=first_token,
                            is_last_token=chunk.get("done", False),
                        )
                        token_index += 1
                        first_token = False

                    if chunk.get("done", False):
                        break

        except httpx.TimeoutException:
            raise ProviderTimeoutError("Streaming generation timeout", self.provider_type)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ProviderModelNotFoundError(f"Model not found: {request.model}", self.provider_type)
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

            message = data.get("message", {})
            text = message.get("content", "")
            prompt_tokens = data.get("prompt_eval_count", 0)
            completion_tokens = data.get("eval_count", 0)

            return GenerationResponse(
                text=text,
                model=request.model,
                provider=self.provider_type,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                finish_reason=data.get("done_reason", "stop"),
                created_at=time.time(),
                metadata={
                    "elapsed_seconds": elapsed,
                    "eval_duration_ns": data.get("eval_duration", 0),
                    "prompt_eval_duration_ns": data.get("prompt_eval_duration", 0),
                },
            )
        except httpx.TimeoutException:
            raise ProviderTimeoutError("Chat timeout", self.provider_type)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ProviderModelNotFoundError(f"Model not found: {request.model}", self.provider_type)
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

                    message = chunk.get("message", {})
                    token_text = message.get("content", "")

                    if token_text:
                        yield TokenEvent(
                            token_id=token_index,
                            token_text=token_text,
                            is_first_token=first_token,
                            is_last_token=chunk.get("done", False),
                        )
                        token_index += 1
                        first_token = False

                    if chunk.get("done", False):
                        break

        except httpx.TimeoutException:
            raise ProviderTimeoutError("Chat streaming timeout", self.provider_type)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ProviderModelNotFoundError(f"Model not found: {request.model}", self.provider_type)
            raise ProviderConnectionError(f"HTTP error: {e}", self.provider_type)

    async def pull_model(self, model_name: str, stream: bool = True) -> AsyncIterator[Dict[str, Any]]:
        """Pull a model from Ollama registry."""
        async with self._client.stream(
            "POST",
            "/api/pull",
            json={"name": model_name, "stream": stream},
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.strip():
                    yield json.loads(line)

    async def delete_model(self, model_name: str) -> bool:
        """Delete a model from Ollama."""
        try:
            response = await self._client.delete("/api/delete", json={"name": model_name})
            response.raise_for_status()
            # Invalidate cache
            self._models_cache = [m for m in self._models_cache if m.name != model_name]
            return True
        except Exception:
            return False

    async def copy_model(self, source: str, destination: str) -> bool:
        """Copy a model."""
        try:
            response = await self._client.post(
                "/api/copy",
                json={"source": source, "destination": destination},
            )
            response.raise_for_status()
            await self._load_models()
            return True
        except Exception:
            return False