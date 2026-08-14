"""Unit tests for BenchLM providers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from benchlm.providers.base import (
    LLMProvider, ProviderType, ModelInfo, ProviderCapabilities,
    GenerationConfig, GenerationRequest, ChatRequest,
    GenerationResponse, TokenEvent, ChatMessage, HealthStatus,
    ProviderError, ProviderConnectionError, ProviderTimeoutError,
    ProviderModelNotFoundError, ProviderRateLimitError, ProviderValidationError,
)
from benchlm.providers.ollama import OllamaProvider
from benchlm.providers.llama_cpp import LlamaCppProvider
from benchlm.providers.lmstudio import LMStudioProvider
from benchlm.providers.vllm import VLLMProvider
from benchlm.providers.openai_compatible import OpenAICompatibleProvider
from benchlm.providers.registry import ProviderRegistry, get_provider_registry


class TestBaseModels:
    """Tests for base provider models."""

    def test_generation_config_defaults(self):
        config = GenerationConfig()
        assert config.temperature == 0.7
        assert config.top_p == 0.9
        assert config.top_k == 40
        assert config.seed == -1
        assert config.max_tokens == 2048
        assert config.stream is True

    def test_generation_request(self):
        request = GenerationRequest(
            prompt="Test prompt",
            model="test-model",
            config=GenerationConfig(temperature=0.5),
        )
        assert request.prompt == "Test prompt"
        assert request.model == "test-model"
        assert request.config.temperature == 0.5

    def test_chat_message(self):
        msg = ChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_generation_response(self):
        response = GenerationResponse(
            text="Test response",
            model="test-model",
            provider=ProviderType.OLLAMA,
            prompt_tokens=10,
            completion_tokens=20,
        )
        assert response.total_tokens == 30
        assert response.finish_reason == "stop"

    def test_token_event(self):
        event = TokenEvent(
            token_id=1,
            token_text="hello",
            is_first_token=True,
        )
        assert event.token_id == 1
        assert event.is_first_token is True
        assert event.is_last_token is False

    def test_health_status(self):
        status = HealthStatus(
            healthy=True,
            provider=ProviderType.OLLAMA,
            endpoint="http://localhost:11434",
            latency_ms=50.0,
            models_count=3,
        )
        assert status.healthy is True
        assert status.provider == ProviderType.OLLAMA

    def test_provider_errors(self):
        # Base error
        err = ProviderError("Test error", ProviderType.OLLAMA, 500)
        assert str(err) == "Test error"
        assert err.provider == ProviderType.OLLAMA
        assert err.status_code == 500

        # Connection error
        conn_err = ProviderConnectionError("Connection failed", ProviderType.OLLAMA)
        assert isinstance(conn_err, ProviderError)

        # Timeout error
        timeout_err = ProviderTimeoutError("Timeout", ProviderType.OLLAMA)
        assert isinstance(timeout_err, ProviderError)

        # Model not found
        not_found = ProviderModelNotFoundError("Model not found", ProviderType.OLLAMA)
        assert isinstance(not_found, ProviderError)

        # Rate limit
        rate_err = ProviderRateLimitError("Rate limited", ProviderType.OLLAMA)
        assert isinstance(rate_err, ProviderError)

        # Validation error
        val_err = ProviderValidationError("Invalid request", ProviderType.OLLAMA)
        assert isinstance(val_err, ProviderError)


class TestProviderCapabilities:
    """Tests for ProviderCapabilities."""

    def test_default_capabilities(self):
        caps = ProviderCapabilities()
        assert caps.supports_streaming is True
        assert caps.supports_chat is True
        assert caps.supports_completion is True
        assert caps.supports_embeddings is False
        assert caps.max_context_length == 4096


class TestProviderRegistry:
    """Tests for ProviderRegistry."""

    def test_singleton(self):
        registry1 = get_provider_registry()
        registry2 = get_provider_registry()
        assert registry1 is registry2

    def test_register_provider(self):
        registry = ProviderRegistry()
        provider = registry.register_provider(
            "test_ollama",
            ProviderType.OLLAMA,
            "http://localhost:11434",
        )
        assert provider is not None
        assert provider.provider_type == ProviderType.OLLAMA

    def test_get_provider(self):
        registry = ProviderRegistry()
        registry.register_provider("test_ollama", ProviderType.OLLAMA, "http://localhost:11434")

        provider = registry.get_provider("test_ollama")
        assert provider is not None

        provider = registry.get_provider("nonexistent")
        assert provider is None

    def test_get_provider_by_type(self):
        registry = ProviderRegistry()
        registry.register_provider("test_ollama", ProviderType.OLLAMA, "http://localhost:11434")
        registry.register_provider("test_llama", ProviderType.LLAMA_CPP, "http://localhost:8080")

        ollama = registry.get_provider_by_type(ProviderType.OLLAMA)
        assert ollama is not None
        assert ollama.provider_type == ProviderType.OLLAMA

    def test_list_providers(self):
        registry = ProviderRegistry()
        registry.register_provider("test_ollama", ProviderType.OLLAMA, "http://localhost:11434")
        registry.register_provider("test_llama", ProviderType.LLAMA_CPP, "http://localhost:8080")

        providers = registry.list_providers()
        assert len(providers) == 2

    def test_unregister_provider(self):
        registry = ProviderRegistry()
        registry.register_provider("test_ollama", ProviderType.OLLAMA, "http://localhost:11434")

        result = registry.unregister_provider("test_ollama")
        assert result is True

        result = registry.unregister_provider("nonexistent")
        assert result is False

    def test_create_provider_from_config(self):
        registry = ProviderRegistry()
        config = {
            "type": "ollama",
            "base_url": "http://localhost:11434",
            "keep_alive": "10m",
        }

        provider = registry.create_provider_from_config("my_ollama", config)
        assert provider is not None
        assert provider.provider_type == ProviderType.OLLAMA


class TestOllamaProvider:
    """Tests for OllamaProvider (with mocked HTTP)."""

    @pytest.fixture
    def provider(self):
        return OllamaProvider(base_url="http://localhost:11434")

    def test_provider_properties(self, provider):
        assert provider.provider_type == ProviderType.OLLAMA
        assert provider.default_model == "llama3.1:8b"
        assert provider.keep_alive == "5m"

    def test_parse_model_info(self, provider):
        data = {
            "name": "qwen3:8b",
            "size": 4_700_000_000,
            "digest": "abc123",
            "details": {
                "parameter_size": "8B",
                "quantization_level": "Q4_K_M",
                "context_length": 32768,
                "architecture": "qwen",
                "family": "qwen",
            }
        }

        model = provider._parse_model_info(data)

        assert model.name == "qwen3:8b"
        assert model.provider == ProviderType.OLLAMA
        assert model.parameter_count == "8B"
        assert model.quantization == "Q4_K_M"
        assert model.context_window == 32768
        assert model.architecture == "qwen"

    def test_build_generate_payload(self, provider):
        request = GenerationRequest(
            prompt="Hello",
            model="test-model",
            config=GenerationConfig(
                temperature=0.8,
                top_p=0.95,
                max_tokens=512,
                stream=True,
            ),
            system_prompt="Be helpful",
        )

        payload = provider._build_generate_payload(request)

        assert payload["model"] == "test-model"
        assert payload["prompt"] == "Hello"
        assert payload["system"] == "Be helpful"
        assert payload["stream"] is True
        assert payload["options"]["temperature"] == 0.8
        assert payload["options"]["top_p"] == 0.95
        assert payload["options"]["num_predict"] == 512
        assert payload["keep_alive"] == "5m"

    def test_build_chat_payload(self, provider):
        request = ChatRequest(
            messages=[
                ChatMessage(role="system", content="You are helpful"),
                ChatMessage(role="user", content="Hello"),
            ],
            model="test-model",
            config=GenerationConfig(temperature=0.7),
        )

        payload = provider._build_chat_payload(request)

        assert payload["model"] == "test-model"
        assert len(payload["messages"]) == 2
        assert payload["messages"][0]["role"] == "system"
        assert payload["messages"][1]["role"] == "user"
        assert payload["options"]["temperature"] == 0.7


class TestLlamaCppProvider:
    """Tests for LlamaCppProvider."""

    def test_provider_properties(self):
        provider = LlamaCppProvider(base_url="http://localhost:8080")
        assert provider.provider_type == ProviderType.LLAMA_CPP
        assert provider.default_model == "default"
        assert provider.default_n_ctx == 4096

    def test_parse_model_info(self):
        provider = LlamaCppProvider(base_url="http://localhost:8080")

        data = {
            "name": "llama-3-8b",
            "n_params": 8_000_000_000,
            "n_ctx": 8192,
            "quantization": "Q4_K_M",
            "architecture": "llama",
        }

        model = provider._parse_model_info(data)

        assert model.name == "llama-3-8b"
        assert model.provider == ProviderType.LLAMA_CPP
        assert model.parameter_count == "8.0B"
        assert model.quantization == "Q4_K_M"
        assert model.context_window == 8192


class TestLMStudioProvider:
    """Tests for LMStudioProvider."""

    def test_provider_properties(self):
        provider = LMStudioProvider(base_url="http://localhost:1234")
        assert provider.provider_type == ProviderType.LMSTUDIO
        assert provider.default_model == "local-model"
        assert provider.base_url == "http://localhost:1234/v1"

    def test_parse_model_info(self):
        provider = LMStudioProvider(base_url="http://localhost:1234")

        data = {
            "id": "qwen2.5-7b-instruct-q4_k_m",
            "owned_by": "local",
            "context_length": 8192,
        }

        model = provider._parse_model_info(data)

        assert model.name == "qwen2.5-7b-instruct-q4_k_m"
        assert model.provider == ProviderType.LMSTUDIO
        assert model.parameter_count == "7B"
        assert model.quantization == "Q4_K_M"
        assert model.context_window == 8192


class TestVLLMProvider:
    """Tests for VLLMProvider."""

    def test_provider_properties(self):
        provider = VLLMProvider(base_url="http://localhost:8000")
        assert provider.provider_type == ProviderType.VLLM
        assert provider.default_model == "default"
        assert provider.base_url == "http://localhost:8000/v1"

    def test_parse_model_info(self):
        provider = VLLMProvider(base_url="http://localhost:8000")

        data = {
            "id": "meta-llama/Llama-3-8b-instruct-gptq",
            "owned_by": "vllm",
            "max_model_len": 8192,
            "architecture": "llama",
        }

        model = provider._parse_model_info(data)

        assert model.name == "meta-llama/Llama-3-8b-instruct-gptq"
        assert model.provider == ProviderType.VLLM
        assert model.parameter_count == "8B"
        assert model.context_window == 8192


class TestOpenAICompatibleProvider:
    """Tests for OpenAICompatibleProvider."""

    def test_provider_properties(self):
        provider = OpenAICompatibleProvider(
            base_url="http://localhost:8000",
            api_key="test-key",
            organization="test-org",
        )
        assert provider.provider_type == ProviderType.OPENAI_COMPATIBLE
        assert provider.default_model == "gpt-3.5-turbo"
        assert provider.base_url == "http://localhost:8000/v1"
        assert provider.organization == "test-org"

    def test_headers(self):
        provider = OpenAICompatibleProvider(
            base_url="http://localhost:8000",
            api_key="test-key",
            organization="test-org",
        )
        headers = provider._get_default_headers()

        assert headers["Authorization"] == "Bearer test-key"
        assert headers["OpenAI-Organization"] == "test-org"
        assert headers["Content-Type"] == "application/json"

    def test_parse_model_info(self):
        provider = OpenAICompatibleProvider(base_url="http://localhost:8000")

        data = {
            "id": "gpt-4",
            "owned_by": "openai",
            "context_window": 8192,
            "permission": [],
            "root": "gpt-4",
            "created": 1234567890,
        }

        model = provider._parse_model_info(data)

        assert model.name == "gpt-4"
        assert model.provider == ProviderType.OPENAI_COMPATIBLE
        assert model.context_window == 8192

    def test_build_completion_payload(self):
        provider = OpenAICompatibleProvider(base_url="http://localhost:8000")

        request = GenerationRequest(
            prompt="Test prompt",
            model="gpt-3.5-turbo",
            config=GenerationConfig(
                temperature=0.5,
                max_tokens=100,
                stop_sequences=["\n"],
            ),
        )

        payload = provider._build_completion_payload(request)

        assert payload["model"] == "gpt-3.5-turbo"
        assert payload["prompt"] == "Test prompt"
        assert payload["temperature"] == 0.5
        assert payload["max_tokens"] == 100
        assert payload["stop"] == ["\n"]
        assert payload["stream"] is True

    def test_build_chat_payload(self):
        provider = OpenAICompatibleProvider(base_url="http://localhost:8000")

        request = ChatRequest(
            messages=[
                ChatMessage(role="system", content="Be helpful"),
                ChatMessage(role="user", content="Hello"),
            ],
            model="gpt-3.5-turbo",
            config=GenerationConfig(temperature=0.7),
        )

        payload = provider._build_chat_payload(request)

        assert payload["model"] == "gpt-3.5-turbo"
        assert len(payload["messages"]) == 2
        assert payload["temperature"] == 0.7


class TestProviderFactory:
    """Tests for provider factory/registry."""

    def test_provider_classes_mapping(self):
        from benchlm.providers.registry import PROVIDER_CLASSES

        assert ProviderType.OLLAMA in PROVIDER_CLASSES
        assert ProviderType.LLAMA_CPP in PROVIDER_CLASSES
        assert ProviderType.LMSTUDIO in PROVIDER_CLASSES
        assert ProviderType.VLLM in PROVIDER_CLASSES
        assert ProviderType.OPENAI_COMPATIBLE in PROVIDER_CLASSES

    def test_default_ports(self):
        from benchlm.providers.registry import DEFAULT_PORTS

        assert DEFAULT_PORTS[ProviderType.OLLAMA] == 11434
        assert DEFAULT_PORTS[ProviderType.LLAMA_CPP] == 8080
        assert DEFAULT_PORTS[ProviderType.LMSTUDIO] == 1234
        assert DEFAULT_PORTS[ProviderType.VLLM] == 8000

    def test_default_base_urls(self):
        from benchlm.providers.registry import DEFAULT_BASE_URLS

        assert DEFAULT_BASE_URLS[ProviderType.OLLAMA] == "http://localhost:11434"
        assert DEFAULT_BASE_URLS[ProviderType.LLAMA_CPP] == "http://localhost:8080"
        assert DEFAULT_BASE_URLS[ProviderType.LMSTUDIO] == "http://localhost:1234/v1"
        assert DEFAULT_BASE_URLS[ProviderType.VLLM] == "http://localhost:8000/v1"