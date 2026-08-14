"""Provider registry and auto-detection for BenchLM."""

from __future__ import annotations

import asyncio
import socket
from typing import Any, AsyncIterator, Dict, List, Optional, Type, Set

from benchlm.providers.base import (
    LLMProvider,
    ProviderType,
    HealthStatus,
    ProviderConnectionError,
)
from benchlm.providers.ollama import OllamaProvider
from benchlm.providers.llama_cpp import LlamaCppProvider
from benchlm.providers.lmstudio import LMStudioProvider
from benchlm.providers.vllm import VLLMProvider
from benchlm.providers.openai_compatible import OpenAICompatibleProvider
from benchlm.config import get_config


# Provider class mapping
PROVIDER_CLASSES: Dict[ProviderType, Type[LLMProvider]] = {
    ProviderType.OLLAMA: OllamaProvider,
    ProviderType.LLAMA_CPP: LlamaCppProvider,
    ProviderType.LMSTUDIO: LMStudioProvider,
    ProviderType.VLLM: VLLMProvider,
    ProviderType.OPENAI_COMPATIBLE: OpenAICompatibleProvider,
}


# Default ports for auto-detection
DEFAULT_PORTS: Dict[ProviderType, int] = {
    ProviderType.OLLAMA: 11434,
    ProviderType.LLAMA_CPP: 8080,
    ProviderType.LMSTUDIO: 1234,
    ProviderType.VLLM: 8000,
    ProviderType.OPENAI_COMPATIBLE: 8000,
}

# Default base URLs
DEFAULT_BASE_URLS: Dict[ProviderType, str] = {
    ProviderType.OLLAMA: "http://localhost:11434",
    ProviderType.LLAMA_CPP: "http://localhost:8080",
    ProviderType.LMSTUDIO: "http://localhost:1234/v1",
    ProviderType.VLLM: "http://localhost:8000/v1",
    ProviderType.OPENAI_COMPATIBLE: "http://localhost:8000/v1",
}


class ProviderRegistry:
    """Registry for managing LLM providers."""

    def __init__(self):
        self._providers: Dict[str, LLMProvider] = {}
        self._provider_configs: Dict[str, Dict[str, Any]] = {}
        self._health_cache: Dict[str, HealthStatus] = {}
        self._auto_detected: bool = False

    def register_provider(
        self,
        name: str,
        provider_type: ProviderType,
        base_url: str,
        api_key: str = "",
        **kwargs
    ) -> LLMProvider:
        """Register a new provider."""
        provider_class = PROVIDER_CLASSES.get(provider_type)
        if not provider_class:
            raise ValueError(f"Unknown provider type: {provider_type}")

        provider = provider_class(
            base_url=base_url,
            api_key=api_key,
            **kwargs
        )

        self._providers[name] = provider
        self._provider_configs[name] = {
            "type": provider_type,
            "base_url": base_url,
            "api_key": api_key,
            **kwargs
        }

        return provider

    def get_provider(self, name: str) -> Optional[LLMProvider]:
        """Get a provider by name."""
        return self._providers.get(name)

    def get_provider_by_type(self, provider_type: ProviderType) -> Optional[LLMProvider]:
        """Get first provider of a specific type."""
        for provider in self._providers.values():
            if provider.provider_type == provider_type:
                return provider
        return None

    def list_providers(self) -> List[Dict[str, Any]]:
        """List all registered providers."""
        return [
            {
                "name": name,
                "type": config["type"].value,
                "base_url": config["base_url"],
                "healthy": self._health_cache.get(name, HealthStatus(
                    healthy=False,
                    provider=config["type"],
                    endpoint=config["base_url"],
                )).healthy,
            }
            for name, config in self._provider_configs.items()
        ]

    def unregister_provider(self, name: str) -> bool:
        """Unregister a provider."""
        if name in self._providers:
            del self._providers[name]
            del self._provider_configs[name]
            self._health_cache.pop(name, None)
            return True
        return False

    async def initialize_all(self) -> Dict[str, HealthStatus]:
        """Initialize all registered providers."""
        results = {}
        for name, provider in self._providers.items():
            try:
                await provider.initialize()
                health = await provider.health_check()
                self._health_cache[name] = health
                results[name] = health
            except Exception as e:
                health = HealthStatus(
                    healthy=False,
                    provider=provider.provider_type,
                    endpoint=provider.base_url,
                    error=str(e),
                )
                self._health_cache[name] = health
                results[name] = health
        return results

    async def close_all(self):
        """Close all providers."""
        for provider in self._providers.values():
            await provider.close()
        self._providers.clear()
        self._health_cache.clear()

    async def health_check_all(self) -> Dict[str, HealthStatus]:
        """Check health of all providers."""
        results = {}
        for name, provider in self._providers.items():
            try:
                health = await provider.health_check()
                self._health_cache[name] = health
                results[name] = health
            except Exception as e:
                health = HealthStatus(
                    healthy=False,
                    provider=provider.provider_type,
                    endpoint=provider.base_url,
                    error=str(e),
                )
                self._health_cache[name] = health
                results[name] = health
        return results

    def get_health(self, name: str) -> Optional[HealthStatus]:
        """Get cached health status."""
        return self._health_cache.get(name)

    def get_all_healthy(self) -> List[LLMProvider]:
        """Get all healthy providers."""
        return [
            provider for name, provider in self._providers.items()
            if self._health_cache.get(name, HealthStatus(
                healthy=False,
                provider=provider.provider_type,
                endpoint=provider.base_url,
            )).healthy
        ]

    async def auto_detect(
        self,
        providers: Optional[List[ProviderType]] = None,
        hosts: Optional[List[str]] = None,
        ports: Optional[List[int]] = None,
        timeout: float = 2.0,
    ) -> List[Dict[str, Any]]:
        """
        Auto-detect running LLM providers on local network.

        Args:
            providers: Provider types to scan for (default: all)
            hosts: Hosts to scan (default: localhost)
            ports: Ports to scan (default: standard ports)
            timeout: Connection timeout per host:port

        Returns:
            List of detected providers with health info
        """
        if providers is None:
            providers = list(PROVIDER_CLASSES.keys())

        if hosts is None:
            hosts = ["localhost", "127.0.0.1"]

        detected = []

        for provider_type in providers:
            default_port = DEFAULT_PORTS.get(provider_type, 8000)
            scan_ports = ports or [default_port]

            for host in hosts:
                for port in scan_ports:
                    base_url = f"http://{host}:{port}"
                    if provider_type in (ProviderType.LMSTUDIO, ProviderType.VLLM, ProviderType.OPENAI_COMPATIBLE):
                        base_url += "/v1"

                    try:
                        # Quick connection test
                        provider_class = PROVIDER_CLASSES[provider_type]
                        provider = provider_class(base_url=base_url, timeout=timeout)

                        health = await provider.health_check()
                        await provider.close()

                        if health.healthy:
                            detected.append({
                                "provider_type": provider_type.value,
                                "base_url": base_url,
                                "host": host,
                                "port": port,
                                "health": health,
                            })

                            # Register if not already registered
                            name = f"{provider_type.value}_{host}_{port}"
                            if name not in self._providers:
                                self.register_provider(name, provider_type, base_url)

                    except Exception:
                        # Ignore connection failures during scanning
                        continue

        self._auto_detected = True
        return detected

    async def scan_localhost(
        self,
        timeout: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """Quick scan of localhost for common LLM servers."""
        return await self.auto_detect(
            hosts=["localhost", "127.0.0.1"],
            timeout=timeout,
        )

    def create_provider_from_config(self, name: str, config: Dict[str, Any]) -> LLMProvider:
        """Create provider from configuration dictionary."""
        provider_type = ProviderType(config.get("type", "ollama"))
        base_url = config.get("base_url", DEFAULT_BASE_URLS.get(provider_type, "http://localhost:8000"))
        api_key = config.get("api_key", "")

        kwargs = {k: v for k, v in config.items() if k not in ("type", "base_url", "api_key")}

        return self.register_provider(name, provider_type, base_url, api_key, **kwargs)

    def load_from_config(self, config: Any) -> None:
        """Load providers from BenchLM configuration."""
        cfg = config.benchmark if hasattr(config, 'benchmark') else config

        # Register default providers from config
        provider_configs = [
            ("ollama", ProviderType.OLLAMA, getattr(cfg, 'ollama_host', 'http://localhost:11434')),
            ("llama_cpp", ProviderType.LLAMA_CPP, getattr(cfg, 'llama_cpp_host', 'http://localhost:8080')),
            ("lmstudio", ProviderType.LMSTUDIO, getattr(cfg, 'lmstudio_host', 'http://localhost:1234')),
            ("vllm", ProviderType.VLLM, getattr(cfg, 'vllm_host', 'http://localhost:8000')),
        ]

        for name, ptype, url in provider_configs:
            if name not in self._providers:
                self.register_provider(name, ptype, url)

    def get_default_provider(self) -> Optional[LLMProvider]:
        """Get the default provider based on configuration."""
        config = get_config()
        default_type = config.benchmark.default_provider

        # Try to get by type
        provider = self.get_provider_by_type(default_type)
        if provider:
            return provider

        # Fallback to first healthy provider
        healthy = self.get_all_healthy()
        if healthy:
            return healthy[0]

        # Fallback to first registered
        if self._providers:
            return next(iter(self._providers.values()))

        return None


# Global registry instance
_registry: Optional[ProviderRegistry] = None


def get_provider_registry() -> ProviderRegistry:
    """Get the global provider registry."""
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry


def set_provider_registry(registry: ProviderRegistry) -> None:
    """Set the global provider registry."""
    global _registry
    _registry = registry


async def initialize_providers(config: Any = None) -> ProviderRegistry:
    """Initialize provider registry with configuration."""
    registry = get_provider_registry()

    if config:
        registry.load_from_config(config)

    await registry.initialize_all()
    return registry


async def close_providers() -> None:
    """Close all providers in registry."""
    registry = get_provider_registry()
    await registry.close_all()
    global _registry
    _registry = None