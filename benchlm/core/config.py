"""Benchmark configuration models for BenchLM."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class BenchmarkPreset(str, Enum):
    """Built-in benchmark presets."""

    QUICK = "quick"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    LOAD_TEST = "load_test"
    QUALITY_FOCUS = "quality_focus"
    CUSTOM = "custom"


class PromptDataset(str, Enum):
    """Available prompt datasets."""

    BUILTIN_GENERAL = "builtin:general"
    BUILTIN_CODING = "builtin:coding"
    BUILTIN_REASONING = "builtin:reasoning"
    BUILTIN_CREATIVE = "builtin:creative"
    BUILTIN_ANALYSIS = "builtin:analysis"
    BUILTIN_MMLU = "builtin:mmlu"
    BUILTIN_HUMANEVAL = "builtin:humaneval"
    BUILTIN_GSM8K = "builtin:gsm8k"
    CUSTOM = "custom"


@dataclass
class GenerationParameters:
    """LLM generation parameters."""

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
class ExecutionParameters:
    """Benchmark execution parameters."""

    iterations: int = 10
    warmup_runs: int = 2
    cooldown_seconds: float = 5.0
    concurrent_users: int = 1
    batch_size: int = 1
    context_length: int = 4096


@dataclass
class PromptConfiguration:
    """Prompt configuration for benchmark."""

    dataset: PromptDataset = PromptDataset.BUILTIN_GENERAL
    system_prompt: str = ""
    custom_prompts: List[str] = field(default_factory=list)
    shuffle_prompts: bool = True
    max_prompts: Optional[int] = None


@dataclass
class QualityBenchmarkConfig:
    """Quality benchmark configuration."""

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

    pass_at_k: List[int] = field(default_factory=lambda: [1, 5, 10])
    humaneval_k: List[int] = field(default_factory=lambda: [1, 5, 10])
    mbpp_k: List[int] = field(default_factory=lambda: [1, 5, 10])

    needle_context_lengths: List[int] = field(default_factory=lambda: [
        1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072
    ])
    needle_depths: List[float] = field(default_factory=lambda: [
        0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0
    ])


@dataclass
class MonitoringConfig:
    """Hardware monitoring configuration."""

    cpu_monitoring: bool = True
    gpu_monitoring: bool = True
    memory_monitoring: bool = True
    disk_monitoring: bool = True
    battery_monitoring: bool = True
    temperature_monitoring: bool = True
    power_monitoring: bool = True
    poll_interval_ms: int = 250
    temperature_poll_interval_ms: int = 500
    power_poll_interval_ms: int = 500
    tps_update_per_token: bool = True


@dataclass
class ExportConfig:
    """Export configuration."""

    formats: List[str] = field(default_factory=lambda: ["csv", "json", "html", "pdf", "sqlite"])
    include_charts: bool = True
    include_raw_data: bool = False
    output_directory: str = "~/BenchLM_Exports"
    auto_export: bool = True


@dataclass
class BenchmarkConfig:
    """Complete benchmark configuration."""

    # Metadata
    name: str = ""
    description: str = ""
    preset: BenchmarkPreset = BenchmarkPreset.STANDARD
    tags: List[str] = field(default_factory=list)

    # Model selection
    model_names: List[str] = field(default_factory=list)
    provider: str = "ollama"

    # Core parameters
    generation: GenerationParameters = field(default_factory=GenerationParameters)
    execution: ExecutionParameters = field(default_factory=ExecutionParameters)
    prompts: PromptConfiguration = field(default_factory=PromptConfiguration)

    # Quality benchmarks
    quality: QualityBenchmarkConfig = field(default_factory=QualityBenchmarkConfig)

    # Monitoring
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    # Export
    export: ExportConfig = field(default_factory=ExportConfig)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    uuid: str = field(default_factory=lambda: str(uuid4()))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "preset": self.preset.value,
            "tags": self.tags,
            "model_names": self.model_names,
            "provider": self.provider,
            "generation": self.generation.__dict__,
            "execution": self.execution.__dict__,
            "prompts": {
                "dataset": self.prompts.dataset.value,
                "system_prompt": self.prompts.system_prompt,
                "custom_prompts": self.prompts.custom_prompts,
                "shuffle_prompts": self.prompts.shuffle_prompts,
                "max_prompts": self.prompts.max_prompts,
            },
            "quality": self.quality.__dict__,
            "monitoring": self.monitoring.__dict__,
            "export": self.export.__dict__,
            "uuid": self.uuid,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BenchmarkConfig":
        """Create from dictionary."""
        config = cls()

        # Simple fields
        for field_name in ["name", "description", "tags", "model_names", "provider"]:
            if field_name in data:
                setattr(config, field_name, data[field_name])

        if "preset" in data:
            config.preset = BenchmarkPreset(data["preset"])

        # Nested configs
        if "generation" in data:
            config.generation = GenerationParameters(**data["generation"])
        if "execution" in data:
            config.execution = ExecutionParameters(**data["execution"])
        if "prompts" in data:
            prompts_data = data["prompts"]
            if "dataset" in prompts_data:
                prompts_data["dataset"] = PromptDataset(prompts_data["dataset"])
            config.prompts = PromptConfiguration(**prompts_data)
        if "quality" in data:
            config.quality = QualityBenchmarkConfig(**data["quality"])
        if "monitoring" in data:
            config.monitoring = MonitoringConfig(**data["monitoring"])
        if "export" in data:
            config.export = ExportConfig(**data["export"])

        return config

    @classmethod
    def from_preset(cls, preset: BenchmarkPreset) -> "BenchmarkConfig":
        """Create config from preset."""
        presets = {
            BenchmarkPreset.QUICK: {
                "name": "Quick Test",
                "preset": BenchmarkPreset.QUICK,
                "execution": ExecutionParameters(iterations=3, warmup_runs=1, concurrent_users=1),
                "quality": QualityBenchmarkConfig(mmlu=False, humaneval=False, gsm8k=False, needle=False),
            },
            BenchmarkPreset.STANDARD: {
                "name": "Standard",
                "preset": BenchmarkPreset.STANDARD,
                "execution": ExecutionParameters(iterations=10, warmup_runs=2, concurrent_users=1),
                "quality": QualityBenchmarkConfig(),
            },
            BenchmarkPreset.COMPREHENSIVE: {
                "name": "Comprehensive",
                "preset": BenchmarkPreset.COMPREHENSIVE,
                "execution": ExecutionParameters(iterations=20, warmup_runs=3, concurrent_users=1),
                "quality": QualityBenchmarkConfig(mmlu_pro=True, gpqa=True, math=True, mbpp=True),
            },
            BenchmarkPreset.LOAD_TEST: {
                "name": "Load Test",
                "preset": BenchmarkPreset.LOAD_TEST,
                "execution": ExecutionParameters(iterations=10, warmup_runs=2, concurrent_users=10, batch_size=4),
                "quality": QualityBenchmarkConfig(mmlu=False, humaneval=False, gsm8k=False, needle=False),
            },
            BenchmarkPreset.QUALITY_FOCUS: {
                "name": "Quality Focus",
                "preset": BenchmarkPreset.QUALITY_FOCUS,
                "execution": ExecutionParameters(iterations=5, warmup_runs=2, concurrent_users=1),
                "quality": QualityBenchmarkConfig(
                    mmlu=True, mmlu_pro=True, gpqa=True, math=True,
                    humaneval=True, mbpp=True, needle=True,
                    instruction_following=True, reliability=True,
                ),
            },
        }

        if preset in presets:
            return cls(**presets[preset])
        return cls()


# Pydantic models for API serialization
class GenerationParametersModel(BaseModel):
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    top_k: int = Field(default=40, ge=0)
    seed: int = Field(default=-1)
    max_tokens: int = Field(default=2048, ge=1, le=131072)
    stop_sequences: List[str] = Field(default_factory=list)
    stream: bool = True
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    repeat_penalty: float = Field(default=1.0, ge=0.0, le=2.0)
    mirostat: int = Field(default=0, ge=0, le=2)
    mirostat_tau: float = Field(default=5.0, ge=0.1, le=10.0)
    mirostat_eta: float = Field(default=0.1, ge=0.01, le=1.0)
    extra_params: Dict[str, Any] = Field(default_factory=dict)


class ExecutionParametersModel(BaseModel):
    iterations: int = Field(default=10, ge=1, le=1000)
    warmup_runs: int = Field(default=2, ge=0, le=100)
    cooldown_seconds: float = Field(default=5.0, ge=0.0, le=300.0)
    concurrent_users: int = Field(default=1, ge=1, le=100)
    batch_size: int = Field(default=1, ge=1, le=32)
    context_length: int = Field(default=4096, ge=512, le=131072)


class PromptConfigurationModel(BaseModel):
    dataset: str = Field(default="builtin:general")
    system_prompt: str = ""
    custom_prompts: List[str] = Field(default_factory=list)
    shuffle_prompts: bool = True
    max_prompts: Optional[int] = None


class QualityBenchmarkConfigModel(BaseModel):
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

    pass_at_k: List[int] = Field(default_factory=lambda: [1, 5, 10])
    humaneval_k: List[int] = Field(default_factory=lambda: [1, 5, 10])
    mbpp_k: List[int] = Field(default_factory=lambda: [1, 5, 10])

    needle_context_lengths: List[int] = Field(default_factory=lambda: [
        1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072
    ])
    needle_depths: List[float] = Field(default_factory=lambda: [
        0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0
    ])


class MonitoringConfigModel(BaseModel):
    cpu_monitoring: bool = True
    gpu_monitoring: bool = True
    memory_monitoring: bool = True
    disk_monitoring: bool = True
    battery_monitoring: bool = True
    temperature_monitoring: bool = True
    power_monitoring: bool = True
    poll_interval_ms: int = Field(default=250, ge=50, le=5000)
    temperature_poll_interval_ms: int = Field(default=500, ge=100, le=10000)
    power_poll_interval_ms: int = Field(default=500, ge=100, le=10000)
    tps_update_per_token: bool = True


class ExportConfigModel(BaseModel):
    formats: List[str] = Field(default_factory=lambda: ["csv", "json", "html", "pdf", "sqlite"])
    include_charts: bool = True
    include_raw_data: bool = False
    output_directory: str = "~/BenchLM_Exports"
    auto_export: bool = True


class BenchmarkConfigModel(BaseModel):
    name: str = ""
    description: str = ""
    preset: str = "standard"
    tags: List[str] = Field(default_factory=list)
    model_names: List[str] = Field(default_factory=list)
    provider: str = "ollama"
    generation: GenerationParametersModel = Field(default_factory=GenerationParametersModel)
    execution: ExecutionParametersModel = Field(default_factory=ExecutionParametersModel)
    prompts: PromptConfigurationModel = Field(default_factory=PromptConfigurationModel)
    quality: QualityBenchmarkConfigModel = Field(default_factory=QualityBenchmarkConfigModel)
    monitoring: MonitoringConfigModel = Field(default_factory=MonitoringConfigModel)
    export: ExportConfigModel = Field(default_factory=ExportConfigModel)