"""Providers package for BenchLM."""

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
    ProviderError,
    ProviderConnectionError,
    ProviderTimeoutError,
    ProviderModelNotFoundError,
    ProviderRateLimitError,
    ProviderValidationError,
)
from benchlm.providers.ollama import OllamaProvider
from benchlm.providers.llama_cpp import LlamaCppProvider
from benchlm.providers.lmstudio import LMStudioProvider
from benchlm.providers.vllm import VLLMProvider
from benchlm.providers.openai_compatible import OpenAICompatibleProvider
from benchlm.providers.registry import (
    ProviderRegistry,
    get_provider_registry,
    set_provider_registry,
    initialize_providers,
    close_providers,
    PROVIDER_CLASSES,
    DEFAULT_PORTS,
    DEFAULT_BASE_URLS,
)

__all__ = [
    # Base
    "LLMProvider",
    "ModelInfo",
    "ProviderCapabilities",
    "ProviderType",
    "GenerationConfig",
    "GenerationRequest",
    "GenerationResponse",
    "ChatMessage",
    "ChatRequest",
    "TokenEvent",
    "HealthStatus",
    # Errors
    "ProviderError",
    "ProviderConnectionError",
    "ProviderTimeoutError",
    "ProviderModelNotFoundError",
    "ProviderRateLimitError",
    "ProviderValidationError",
    # Providers
    "OllamaProvider",
    "LlamaCppProvider",
    "LMStudioProvider",
    "VLLMProvider",
    "OpenAICompatibleProvider",
    # Registry
    "ProviderRegistry",
    "get_provider_registry",
    "set_provider_registry",
    "initialize_providers",
    "close_providers",
    # Constants
    "PROVIDER_CLASSES",
    "DEFAULT_PORTS",
    "DEFAULT_BASE_URLS",
]