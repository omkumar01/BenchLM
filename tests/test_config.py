"""Unit tests for BenchLM configuration."""

import pytest
from pathlib import Path
from benchlm.config import (
    Config, AppConfig, UIConfig, BenchmarkConfig,
    DatabaseConfig, ExportsConfig, ScoringConfig,
    get_config, set_config, reset_config,
)


class TestAppConfig:
    """Tests for AppConfig."""

    def test_default_values(self):
        config = AppConfig()
        assert config.name == "BenchLM"
        assert config.version == "0.1.0"
        assert config.debug is False
        assert config.theme == "dark"
        assert config.accent_color == "#6366F1"

    def test_data_dir_expansion(self):
        config = AppConfig(data_dir="~/test_dir")
        assert str(Path.home() / "test_dir") in config.data_dir


class TestUIConfig:
    """Tests for UIConfig."""

    def test_default_values(self):
        config = UIConfig()
        assert config.hardware_poll_interval == 250
        assert config.temperature_poll_interval == 500
        assert config.glassmorphism_enabled is True
        assert config.animations_enabled is True


class TestBenchmarkConfig:
    """Tests for BenchmarkConfig."""

    def test_default_values(self):
        config = BenchmarkConfig()
        assert config.default_provider == "ollama"
        assert config.temperature == 0.7
        assert config.top_p == 0.9
        assert config.max_tokens == 2048
        assert config.iterations == 10
        assert config.warmup_runs == 2


class TestDatabaseConfig:
    """Tests for DatabaseConfig."""

    def test_path_expansion(self):
        config = DatabaseConfig(path="~/test.db")
        assert str(Path.home() / "test.db") in config.path


class TestScoringConfig:
    """Tests for ScoringConfig."""

    def test_weights_total(self):
        config = ScoringConfig()
        weights = config.weights
        total = weights.latency + weights.throughput + weights.quality + \
                weights.reliability + weights.memory + weights.energy + weights.context
        assert total == 100

    def test_grade_thresholds(self):
        config = ScoringConfig()
        grades = config.grades
        assert grades.s_plus == 950
        assert grades.s == 900
        assert grades.a == 800
        assert grades.b == 700
        assert grades.c == 600


class TestMainConfig:
    """Tests for main Config class."""

    def test_singleton_behavior(self):
        reset_config()
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_from_yaml(self, tmp_path):
        yaml_file = tmp_path / "test_config.yaml"
        yaml_content = """
app:
  name: "TestBenchLM"
  theme: "light"
  accent_color: "#FF0000"
benchmark:
  temperature: 0.5
  iterations: 5
"""
        yaml_file.write_text(yaml_content)

        config = Config.from_yaml(yaml_file)
        assert config.app.name == "TestBenchLM"
        assert config.app.theme == "light"
        assert config.app.accent_color == "#FF0000"
        assert config.benchmark.temperature == 0.5
        assert config.benchmark.iterations == 5

    def test_to_yaml(self, tmp_path):
        config = Config()
        config.app.name = "YAMLTest"
        config.benchmark.temperature = 0.8

        output_file = tmp_path / "output.yaml"
        config.to_yaml(output_file)

        assert output_file.exists()
        content = output_file.read_text()
        assert "YAMLTest" in content
        assert "temperature: 0.8" in content

    def test_reset(self):
        reset_config()
        config1 = get_config()
        config1.app.name = "Modified"
        reset_config()
        config2 = get_config()
        assert config1 is not config2
        assert config2.app.name == "BenchLM"


class TestConfigIntegration:
    """Integration tests for configuration."""

    def test_yaml_roundtrip(self, tmp_path):
        """Test saving and loading config from YAML."""
        config = Config()
        config.app.name = "RoundtripTest"
        config.app.theme = "light"
        config.benchmark.temperature = 0.9
        config.benchmark.iterations = 15
        config.ui.hardware_poll_interval = 100

        yaml_file = tmp_path / "roundtrip.yaml"
        config.to_yaml(yaml_file)

        loaded = Config.from_yaml(yaml_file)
        assert loaded.app.name == "RoundtripTest"
        assert loaded.app.theme == "light"
        assert loaded.benchmark.temperature == 0.9
        assert loaded.benchmark.iterations == 15
        assert loaded.ui.hardware_poll_interval == 100