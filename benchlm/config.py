"""Configuration management for BenchLM using Pydantic Settings."""

from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Application-level configuration."""

    model_config = SettingsConfigDict(env_prefix="BENCHLM_APP_", extra="ignore")

    name: str = "BenchLM"
    version: str = "0.1.0"
    debug: bool = False
    data_dir: str = "~/.benchlm"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    theme: Literal["dark", "light", "system"] = "dark"
    accent_color: str = "#6366F1"
    language: str = "en"

    @field_validator("data_dir")
    @classmethod
    def expand_data_dir(cls, v: str) -> str:
        return str(Path(v).expanduser())


class UIConfig(BaseSettings):
    """UI configuration."""

    model_config = SettingsConfigDict(env_prefix="BENCHLM_UI_", extra="ignore")

    hardware_poll_interval: int = 250
    temperature_poll_interval: int = 500
    power_poll_interval: int = 500
    tps_update_per_token: bool = True

    sidebar_width: int = 280
    card_border_radius: int = 16
    glassmorphism_enabled: bool = True
    animations_enabled: bool = True
    compact_mode: bool = False

    table_virtualization_threshold: int = 1000
    chart_lazy_load: bool = True

    mobile_optimization: bool = False
    touch_friendly: bool = True


class BenchmarkConfig(BaseSettings):
    """Benchmark execution configuration."""

    model_config = SettingsConfigDict(env_prefix="BENCHLM_BENCHMARK_", extra="ignore")

    default_preset: str = "standard"
    default_provider: Literal["ollama", "llama_cpp", "lmstudio", "vllm", "openai_compatible"] = "ollama"

    ollama_host: str = "http://localhost:11434"
    llama_cpp_host: str = "http://localhost:8080"
    lmstudio_host: str = "http://localhost:1234"
    vllm_host: str = "http://localhost:8000"

    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    seed: int = -1
    max_tokens: int = 2048
    batch_size: int = 1
    context_length: int = 4096
    streaming: bool = True

    concurrent_users: int = 1
    iterations: int = 10
    warmup_runs: int = 2
    cooldown_seconds: int = 5

    system_prompt: str = ""
    prompt_dataset: str = "builtin:general"


class HardwareConfig(BaseSettings):
    """Hardware monitoring configuration."""

    model_config = SettingsConfigDict(env_prefix="BENCHLM_HARDWARE_", extra="ignore")

    cpu_backend: Literal["auto", "psutil"] = "auto"
    gpu_backend: Literal["auto", "pynvml", "rocm-smi", "intel-gpu-top"] = "auto"
    memory_backend: Literal["auto", "psutil"] = "auto"

    nvidia_gpu_index: int = 0
    pynvml_enabled: bool = True

    rocm_smi_path: str = "rocm-smi"
    intel_gpu_top_path: str = "intel-gpu-top"

    sample_history_size: int = 100000


class DatabaseConfig(BaseSettings):
    """Database configuration."""

    model_config = SettingsConfigDict(env_prefix="BENCHLM_DATABASE_", extra="ignore")

    path: str = "~/.benchlm/benchlm.db"
    pool_size: int = 5
    max_overflow: int = 10
    echo: bool = False
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    backup_retention_days: int = 30

    @field_validator("path")
    @classmethod
    def expand_path(cls, v: str) -> str:
        return str(Path(v).expanduser())


class ExportsConfig(BaseSettings):
    """Export configuration."""

    model_config = SettingsConfigDict(env_prefix="BENCHLM_EXPORTS_", extra="ignore")

    default_directory: str = "~/BenchLM_Exports"
    formats: list[str] = ["csv", "json", "html", "pdf", "sqlite"]
    pdf_engine: Literal["reportlab", "weasyprint"] = "reportlab"
    include_charts_in_pdf: bool = True
    include_raw_data: bool = False

    @field_validator("default_directory")
    @classmethod
    def expand_dir(cls, v: str) -> str:
        return str(Path(v).expanduser())


class ScoringWeights(BaseSettings):
    """Scoring weight configuration."""

    model_config = SettingsConfigDict(env_prefix="BENCHLM_SCORING_WEIGHTS_", extra="ignore")

    latency: int = 20
    throughput: int = 20
    quality: int = 25
    reliability: int = 15
    memory: int = 10
    energy: int = 5
    context: int = 5

    def total(self) -> int:
        return (
            self.latency
            + self.throughput
            + self.quality
            + self.reliability
            + self.memory
            + self.energy
            + self.context
        )


class ScoringGrades(BaseSettings):
    """Scoring grade thresholds."""

    model_config = SettingsConfigDict(env_prefix="BENCHLM_SCORING_GRADES_", extra="ignore")

    s_plus: int = 950
    s: int = 900
    a: int = 800
    b: int = 700
    c: int = 600


class ScoringConfig(BaseSettings):
    """Scoring configuration."""

    model_config = SettingsConfigDict(env_prefix="BENCHLM_SCORING_", extra="ignore")

    weights: ScoringWeights = Field(default_factory=ScoringWeights)
    grades: ScoringGrades = Field(default_factory=ScoringGrades)


class ProviderConfig(BaseSettings):
    """Provider-specific configuration."""

    model_config = SettingsConfigDict(env_prefix="BENCHLM_PROVIDER_", extra="ignore")

    ollama_timeout: int = 300
    ollama_keep_alive: str = "5m"
    ollama_num_ctx: int = 4096
    ollama_num_predict: int = -1

    llama_cpp_timeout: int = 300
    llama_cpp_n_ctx: int = 4096
    llama_cpp_n_predict: int = -1
    llama_cpp_n_gpu_layers: int = -1

    lmstudio_timeout: int = 300

    vllm_timeout: int = 300
    vllm_max_model_len: int = 4096

    openai_compatible_timeout: int = 300
    openai_compatible_api_key: str = ""


class QualityBenchmarksConfig(BaseSettings):
    """Quality benchmark configuration."""

    model_config = SettingsConfigDict(env_prefix="BENCHLM_QUALITY_", extra="ignore")

    mmlu: bool = True
    mmlu_pro: bool = False
    gpqa: bool = False
    gsm8k: bool = True
    math: bool = False
    arc_easy: bool = True
    arc_challenge: bool = True
    hellaswag: bool = True
    truthfulqa: bool = False
    big_bench: bool = False
    agieval: bool = False
    humaneval: bool = True
    mbpp: bool = True
    swe_bench: bool = False
    repobench: bool = False
    needle: bool = True
    instruction_following: bool = True
    reliability: bool = True
    safety: bool = False
    agent: bool = False

    pass_at_k: list[int] = [1, 5, 10]
    humaneval_k: list[int] = [1, 5, 10]
    mbpp_k: list[int] = [1, 5, 10]

    needle_context_lengths: list[int] = [
        1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072
    ]
    needle_depths: list[float] = [
        0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0
    ]

    dataset_cache_dir: str = "~/.benchlm/datasets"

    @field_validator("dataset_cache_dir")
    @classmethod
    def expand_cache_dir(cls, v: str) -> str:
        return str(Path(v).expanduser())


class LoggingConfig(BaseSettings):
    """Logging configuration."""

    model_config = SettingsConfigDict(env_prefix="BENCHLM_LOGGING_", extra="ignore")

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    format: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )
    rotation: str = "10 MB"
    retention: str = "30 days"
    compression: str = "zip"
    file_path: str = "~/.benchlm/logs/benchlm.log"

    @field_validator("file_path")
    @classmethod
    def expand_log_path(cls, v: str) -> str:
        return str(Path(v).expanduser())


class Config(BaseSettings):
    """Main configuration class aggregating all sub-configs."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app: AppConfig = Field(default_factory=AppConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    benchmark: BenchmarkConfig = Field(default_factory=BenchmarkConfig)
    hardware: HardwareConfig = Field(default_factory=HardwareConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    exports: ExportsConfig = Field(default_factory=ExportsConfig)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    providers: ProviderConfig = Field(default_factory=ProviderConfig)
    quality_benchmarks: QualityBenchmarksConfig = Field(
        default_factory=QualityBenchmarksConfig
    )
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Config":
        """Load configuration from YAML file."""
        import yaml

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)

    def to_yaml(self, path: str | Path) -> None:
        """Save configuration to YAML file."""
        import yaml

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, sort_keys=False)


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        config_path = Path("config.yaml")
        if config_path.exists():
            _config = Config.from_yaml(config_path)
        else:
            _config = Config()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config


def reset_config() -> None:
    """Reset the global configuration."""
    global _config
    _config = None