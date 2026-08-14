"""Dependency Injection container for BenchLM."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, Generic

T = TypeVar("T")


class ServiceDescriptor(Generic[T]):
    """Describes a service registration."""

    def __init__(
        self,
        implementation: type[T] | Callable[..., T] | T,
        *,
        singleton: bool = True,
        factory: bool = False,
    ):
        self.implementation = implementation
        self.singleton = singleton
        self.factory = factory
        self._instance: T | None = None


class DIContainer:
    """Simple dependency injection container with singleton support."""

    def __init__(self):
        self._services: dict[type, ServiceDescriptor] = {}
        self._resolving: set[type] = set()

    def register(
        self,
        interface: type[T],
        implementation: type[T] | Callable[..., T] | T,
        *,
        singleton: bool = True,
        factory: bool = False,
    ) -> None:
        """Register a service implementation."""
        self._services[interface] = ServiceDescriptor(
            implementation, singleton=singleton, factory=factory
        )

    def register_instance(self, interface: type[T], instance: T) -> None:
        """Register an existing instance as a singleton."""
        descriptor = ServiceDescriptor(instance, singleton=True)
        descriptor._instance = instance
        self._services[interface] = descriptor

    def unregister(self, interface: type) -> None:
        """Unregister a service."""
        self._services.pop(interface, None)

    def resolve(self, interface: type[T]) -> T:
        """Resolve a service instance."""
        if interface not in self._services:
            raise KeyError(f"Service not registered: {interface}")

        if interface in self._resolving:
            raise RuntimeError(f"Circular dependency detected for: {interface}")

        descriptor = self._services[interface]
        self._resolving.add(interface)

        try:
            if descriptor._instance is not None:
                return descriptor._instance

            if descriptor.factory:
                # Factory: call the implementation each time
                instance = descriptor.implementation()
            elif callable(descriptor.implementation) and not isinstance(
                descriptor.implementation, type
            ):
                # Callable (factory function)
                instance = descriptor.implementation()
            else:
                # Class: instantiate with dependency injection
                instance = self._instantiate(descriptor.implementation)

            if descriptor.singleton:
                descriptor._instance = instance

            return instance
        finally:
            self._resolving.discard(interface)

    def _instantiate(self, cls: type[T]) -> T:
        """Instantiate a class with injected dependencies."""
        import inspect

        signature = inspect.signature(cls.__init__)
        kwargs = {}

        for param_name, param in signature.parameters.items():
            if param_name == "self":
                continue

            # Try to resolve by type annotation
            if param.annotation != inspect.Parameter.empty:
                try:
                    kwargs[param_name] = self.resolve(param.annotation)
                    continue
                except KeyError:
                    pass

            # Use default if available
            if param.default != inspect.Parameter.empty:
                kwargs[param_name] = param.default
            else:
                raise ValueError(
                    f"Cannot resolve dependency '{param_name}' for {cls.__name__}"
                )

        return cls(**kwargs)

    def is_registered(self, interface: type) -> bool:
        """Check if a service is registered."""
        return interface in self._services

    def clear(self) -> None:
        """Clear all registrations."""
        self._services.clear()


# Global container instance
_container: DIContainer | None = None


def get_container() -> DIContainer:
    """Get the global DI container."""
    global _container
    if _container is None:
        _container = DIContainer()
    return _container


def set_container(container: DIContainer) -> None:
    """Set the global DI container."""
    global _container
    _container = container


def configure_container() -> DIContainer:
    """Configure and return the DI container with all services."""
    container = get_container()

    # Import here to avoid circular imports
    from benchlm.config import get_config
    from benchlm.logging_config import setup_logging

    # Register config as singleton
    config = get_config()
    container.register_instance(type(config), config)

    # Setup logging
    setup_logging(config.logging)

    # Register core services (will be implemented in later phases)
    # container.register(IBenchmarkEngine, BenchmarkEngine)
    # container.register(IHardwareCollector, HardwareCollector)
    # container.register(IProviderRegistry, ProviderRegistry)
    # container.register(IDatabaseRepository, DatabaseRepository)

    return container


def reset_container() -> None:
    """Reset the global container."""
    global _container
    if _container:
        _container.clear()
    _container = None