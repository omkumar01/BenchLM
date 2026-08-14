"""Pytest configuration and fixtures for BenchLM tests."""

import pytest
import asyncio
from pathlib import Path
from typing import AsyncGenerator

from benchlm.config import Config, reset_config, get_config
from benchlm.database.repository import get_repository, init_database, close_database


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_config_fixture():
    """Reset config before each test."""
    reset_config()
    yield
    reset_config()


@pytest.fixture
def test_config(tmp_path) -> Config:
    """Create a test configuration."""
    config = Config()
    config.app.data_dir = str(tmp_path / "data")
    config.app.log_level = "DEBUG"
    config.database.path = str(tmp_path / "test.db")
    config.ui.hardware_poll_interval = 100
    config.ui.temperature_poll_interval = 200
    return config


@pytest.fixture
async def test_db(test_config):
    """Create a test database."""
    # Override the global config
    import benchlm.config
    benchlm.config._config = test_config

    repo = get_repository()
    await repo.init_db()
    yield repo
    await repo.close()


@pytest.fixture
def sample_benchmark_config():
    """Create a sample benchmark configuration."""
    from benchlm.core.config import BenchmarkConfig, BenchmarkPreset

    config = BenchmarkConfig.from_preset(BenchmarkPreset.STANDARD)
    config.name = "Test Benchmark"
    config.model_names = ["test-model"]
    config.provider = "ollama"
    config.generation.temperature = 0.7
    config.generation.max_tokens = 1024
    config.execution.iterations = 3
    config.execution.warmup_runs = 1
    return config


# Async fixtures for database tests
@pytest.fixture
async def db_session(test_db):
    """Get a database session."""
    async with test_db.session() as session:
        yield session


# Mock fixtures
@pytest.fixture
def mock_provider():
    """Create a mock LLM provider."""
    from unittest.mock import AsyncMock, MagicMock
    from benchlm.providers.base import (
        LLMProvider, ProviderType, ModelInfo, GenerationResponse, TokenEvent
    )

    provider = AsyncMock(spec=LLMProvider)
    provider.provider_type = ProviderType.OLLAMA
    provider.base_url = "http://localhost:11434"

    # Mock methods
    provider.initialize = AsyncMock()
    provider.close = AsyncMock()
    provider.list_models = AsyncMock(return_value=[
        ModelInfo(
            name="test-model",
            provider=ProviderType.OLLAMA,
            provider_model_id="test-model",
            parameter_count="7B",
            quantization="Q4_K_M",
            context_window=4096,
        )
    ])
    provider.get_model_info = AsyncMock(return_value=ModelInfo(
        name="test-model",
        provider=ProviderType.OLLAMA,
        provider_model_id="test-model",
        parameter_count="7B",
        quantization="Q4_K_M",
        context_window=4096,
    ))
    provider.generate = AsyncMock(return_value=GenerationResponse(
        text="Test response",
        model="test-model",
        provider=ProviderType.OLLAMA,
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
    ))
    provider.generate_stream = AsyncMock()
    provider.chat = AsyncMock(return_value=GenerationResponse(
        text="Test chat response",
        model="test-model",
        provider=ProviderType.OLLAMA,
        prompt_tokens=15,
        completion_tokens=25,
        total_tokens=40,
    ))
    provider.chat_stream = AsyncMock()
    provider.health_check = AsyncMock()
    provider.is_healthy = MagicMock(return_value=True)

    return provider


# Test data fixtures
@pytest.fixture
def sample_latency_data():
    """Sample latency data for testing."""
    return [100000, 120000, 110000, 130000, 115000, 125000, 105000, 118000] * 10


@pytest.fixture
def sample_throughput_data():
    """Sample throughput data for testing."""
    return [80, 85, 82, 88, 83, 87, 84, 86, 89, 81] * 10


@pytest.fixture
def sample_model_data():
    """Sample model comparison data."""
    return {
        "ModelA": [80, 82, 81, 83, 84],
        "ModelB": [90, 92, 89, 91, 93],
        "ModelC": [70, 72, 71, 73, 69],
    }


# Markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "hardware: marks tests requiring hardware access")
    config.addinivalue_line("markers", "network: marks tests requiring network access")


# Collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Mark tests in test_statistics.py as unit tests
        if "test_statistics" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        # Mark tests in test_config.py as unit tests
        if "test_config" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        # Mark tests in test_scorer.py as unit tests
        if "test_scorer" in str(item.fspath):
            item.add_marker(pytest.mark.unit)