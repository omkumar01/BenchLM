"""Base provider interface for BenchLM LLM providers."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator, Optional, List, Dict
from enum import Enum

import httpx


class ProviderType(str, Enum):
    """Supported LLM provider types."""

    OLLAMA = "ollama"
    LLAMA_CPP = "llama_cpp"
    LMSTUDIO = "lmstudio"
    VLLM = "vllm"
    TENSORRT_LLM = "tensorrt_llm"
    OPENAI_COMPATIBLE = "openai_compatible"


@dataclass
class ModelInfo:
    """Information about a model."""

    name: str
    provider: ProviderType
    provider_model_id: str
    size_bytes: Optional[int] = None
    parameter_count: Optional[str] = None  # e.g., "7B", "70B"
    quantization: Optional[str] = None
    context_window: int = 4096
    architecture: Optional[str] = None
    family: Optional[str] = None
    description: Optional[str] = None
    license: Optional[str] = None
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderCapabilities:
    """Capabilities of a provider."""

    supports_streaming: bool = True
    supports_chat: bool = True
    supports_completion: bool = True
    supports_embeddings: bool = False
    supports_function_calling: bool = False
    supports_vision: bool = False
    max_context_length: int = 4096
    max_batch_size: int = 1
    supports_concurrent_requests: bool = True
    custom_parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationConfig:
    """Configuration for text generation."""

    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    seed: int = -1  # -1 = random
    max_tokens: int = 2048
    stop_sequences: List[str] = field(default_factory=list)
    stream: bool = True
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    repeat_penalty: float = 1.0
    mirostat: int = 0
    mirostat_tau: float = 5.0
    mirostat_eta: float = 0.1
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationRequest:
    """Request for text generation."""

    prompt: str
    model: str
    config: GenerationConfig = field(default_factory=GenerationConfig)
    system_prompt: str = ""
    images: List[str] = field(default_factory=list)  # Base64 encoded
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatMessage:
    """Chat message."""

    role: str  # system, user, assistant, tool
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None


@dataclass
class ChatRequest:
    """Request for chat completion."""

    messages: List[ChatMessage]
    model: str
    config: GenerationConfig = field(default_factory=GenerationConfig)
    tools: Optional[List[Dict]] = None
    tool_choice: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TokenEvent:
    """Individual token generation event."""

    token_id: int
    token_text: str
    timestamp: datetime
    is_first_token: bool = False
    is_last_token: bool = False
    logprob: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResponse:
    """Response from text generation."""

    text: str
    model: str
    provider: ProviderType
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    finish_reason: str = "stop"
    token_events: List[TokenEvent] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class HealthStatus:
    """Provider health status."""

    healthy: bool
    provider: ProviderType
    endpoint: str
    latency_ms: Optional[float] = None
    models_count: int = 0
    gpu_memory_used: Optional[int] = None
    gpu_memory_total: Optional[int] = None
    error: Optional[str] = None
    checked_at: datetime = field(default_factory=datetime.utcnow)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        timeout: float = 300.0,
        **kwargs
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._models_cache: List[ModelInfo] = []
        self._capabilities: Optional[ProviderCapabilities] = None
        self._healthy = False

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Return the provider type."""
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Return default model name."""
        pass

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def initialize(self):
        """Initialize the provider connection."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
            headers=self._get_default_headers(),
        )
        await self._check_health()
        await self._load_models()

    async def close(self):
        """Close the provider connection."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for requests."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @abstractmethod
    async def _check_health(self) -> HealthStatus:
        """Check provider health."""
        pass

    @abstractmethod
    async def _load_models(self) -> List[ModelInfo]:
        """Load available models."""
        pass

    @abstractmethod
    async def list_models(self, force_refresh: bool = False) -> List[ModelInfo]:
        """List available models."""
        pass

    @abstractmethod
    async def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get detailed model information."""
        pass

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text completion."""
        pass

    @abstractmethod
    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[TokenEvent]:
        """Generate text completion with streaming."""
        pass

    @abstractmethod
    async def chat(self, request: ChatRequest) -> GenerationResponse:
        """Generate chat completion."""
        pass

    @abstractmethod
    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[TokenEvent]:
        """Generate chat completion with streaming."""
        pass

    async def get_capabilities(self) -> ProviderCapabilities:
        """Get provider capabilities."""
        if self._capabilities is None:
            self._capabilities = await self._detect_capabilities()
        return self._capabilities

    @abstractmethod
    async def _detect_capabilities(self) -> ProviderCapabilities:
        """Detect provider capabilities."""
        pass

    async def health_check(self) -> HealthStatus:
        """Perform health check."""
        return await self._check_health()

    def is_healthy(self) -> bool:
        """Check if provider is healthy."""
        return self._healthy

    def _create_token_event(
        self,
        token_id: int,
        token_text: str,
        is_first: bool = False,
        is_last: bool = False,
        logprob: Optional[float] = None,
    ) -> TokenEvent:
        """Create a token event."""
        return TokenEvent(
            token_id=token_id,
            token_text=token_text,
            timestamp=datetime.utcnow(),
            is_first_token=is_first,
            is_last_token=is_last,
            logprob=logprob,
        )

    def _parse_token_events(self, chunks: List[Dict], is_chat: bool = True) -> List[TokenEvent]:
        """Parse token events from streaming chunks."""
        events = []
        token_index = 0
        first_token = True

        for chunk in chunks:
            if is_chat:
                choices = chunk.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        events.append(self._create_token_event(
                            token_id=token_index,
                            token_text=content,
                            is_first=first_token,
                        ))
                        token_index += 1
                        first_token = False

                    if choices[0].get("finish_reason"):
                        if events:
                            events[-1].is_last_token = True
            else:
                # Completion format
                choices = chunk.get("choices", [])
                if choices:
                    text = choices[0].get("text", "")
                    if text:
                        events.append(self._create_token_event(
                            token_id=token_index,
                            token_text=text,
                            is_first=first_token,
                        ))
                        token_index += 1
                        first_token = False

                    if choices[0].get("finish_reason"):
                        if events:
                            events[-1].is_last_token = True

        return events

    def _count_tokens(self, text: str) -> int:
        """Rough token count estimation (4 chars ≈ 1 token)."""
        return max(1, len(text) // 4)


class ProviderError(Exception):
    """Base provider error."""

    def __init__(self, message: str, provider: ProviderType, status_code: Optional[int] = None):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code


class ProviderConnectionError(ProviderError):
    """Provider connection error."""
    pass


class ProviderTimeoutError(ProviderError):
    """Provider timeout error."""
    pass


class ProviderModelNotFoundError(ProviderError):
    """Model not found error."""
    pass


class ProviderRateLimitError(ProviderError):
    """Rate limit error."""
    pass


class ProviderValidationError(ProviderError):
    """Request validation error."""
    pass