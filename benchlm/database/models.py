"""Database models for BenchLM using SQLModel."""

import json
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Optional
from uuid import uuid4

from sqlmodel import Column, Field, Relationship, SQLModel, JSON
from sqlalchemy import DateTime, Enum, Index, Text, func


class ProviderType(str, PyEnum):
    """Supported LLM provider types."""

    OLLAMA = "ollama"
    LLAMA_CPP = "llama_cpp"
    LMSTUDIO = "lmstudio"
    VLLM = "vllm"
    TENSORRT_LLM = "tensorrt_llm"
    OPENAI_COMPATIBLE = "openai_compatible"


class BenchmarkStatus(str, PyEnum):
    """Benchmark run status."""

    PENDING = "pending"
    WARMUP = "warmup"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModelQuantization(str, PyEnum):
    """Model quantization types."""

    FP32 = "fp32"
    FP16 = "fp16"
    BF16 = "bf16"
    INT8 = "int8"
    INT4 = "int4"
    GPTQ = "gptq"
    AWQ = "awq"
    GGUF = "gguf"
    EXL2 = "exl2"
    UNKNOWN = "unknown"


class Model(SQLModel, table=True):
    """Model information table."""

    __tablename__ = "models"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(default_factory=lambda: str(uuid4()), unique=True, index=True)

    # Basic info
    name: str = Field(index=True)
    display_name: Optional[str] = None
    provider: ProviderType = Field(sa_column=Column(Enum(ProviderType), index=True))
    provider_model_id: Optional[str] = None  # Provider-specific model ID

    # Architecture
    architecture: Optional[str] = None
    parameter_count: Optional[str] = None  # e.g., "7B", "70B"
    quantization: ModelQuantization = Field(
        default=ModelQuantization.UNKNOWN,
        sa_column=Column(Enum(ModelQuantization)),
    )
    precision: Optional[str] = None

    # Context & tokenizer
    context_window: int = Field(default=4096)
    vocabulary_size: Optional[int] = None
    tokenizer: Optional[str] = None

    # Model file info
    model_size_bytes: Optional[int] = None
    model_path: Optional[str] = None
    model_hash: Optional[str] = None

    # Metadata
    description: Optional[str] = None
    license: Optional[str] = None
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    capabilities: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    # System prompt
    system_prompt: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )

    # Relationships
    benchmark_runs: list["BenchmarkRun"] = Relationship(back_populates="model")

    __table_args__ = (
        Index("ix_models_provider_name", "provider", "name"),
        Index("ix_models_arch_params", "architecture", "parameter_count"),
    )


class BenchmarkRun(SQLModel, table=True):
    """Benchmark run metadata."""

    __tablename__ = "benchmark_runs"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(default_factory=lambda: str(uuid4()), unique=True, index=True)

    # Model reference
    model_id: int = Field(foreign_key="models.id", index=True)
    model: Optional[Model] = Relationship(back_populates="benchmark_runs")

    # Benchmark configuration
    name: Optional[str] = None
    description: Optional[str] = None
    preset_name: Optional[str] = None

    # Generation parameters
    temperature: float = Field(default=0.7)
    top_p: float = Field(default=0.9)
    top_k: int = Field(default=40)
    seed: int = Field(default=-1)
    max_tokens: int = Field(default=2048)
    batch_size: int = Field(default=1)
    context_length: int = Field(default=4096)
    streaming: bool = Field(default=True)

    # Execution parameters
    concurrent_users: int = Field(default=1)
    iterations: int = Field(default=10)
    warmup_runs: int = Field(default=2)
    cooldown_seconds: int = Field(default=5)

    # Prompt configuration
    system_prompt: str = Field(default="")
    prompt_dataset: str = Field(default="builtin:general")
    custom_prompts: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    # Status & timing
    status: BenchmarkStatus = Field(
        default=BenchmarkStatus.PENDING,
        sa_column=Column(Enum(BenchmarkStatus), index=True),
    )
    started_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    completed_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    duration_seconds: Optional[float] = None

    # Hardware snapshot at run time
    hardware_info: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    # Overall scores
    overall_score: Optional[float] = None
    grade: Optional[str] = None
    latency_score: Optional[float] = None
    throughput_score: Optional[float] = None
    quality_score: Optional[float] = None
    reliability_score: Optional[float] = None
    memory_score: Optional[float] = None
    energy_score: Optional[float] = None
    context_score: Optional[float] = None

    # Error info
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None

    # Metadata
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    notes: Optional[str] = None

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )

    # Relationships
    prompts: list["Prompt"] = Relationship(back_populates="benchmark_run")
    token_events: list["TokenEvent"] = Relationship(back_populates="benchmark_run")
    hardware_samples: list["HardwareSample"] = Relationship(back_populates="benchmark_run")
    quality_scores: list["QualityScore"] = Relationship(back_populates="benchmark_run")
    statistical_summary: Optional["StatisticalSummary"] = Relationship(
        back_populates="benchmark_run"
    )

    __table_args__ = (
        Index("ix_benchmark_runs_model_status", "model_id", "status"),
        Index("ix_benchmark_runs_started", "started_at"),
    )


class Prompt(SQLModel, table=True):
    """Prompt used in benchmark."""

    __tablename__ = "prompts"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(default_factory=lambda: str(uuid4()), unique=True)

    benchmark_run_id: int = Field(foreign_key="benchmark_runs.id", index=True)
    benchmark_run: Optional[BenchmarkRun] = Relationship(back_populates="prompts")

    # Prompt content
    prompt_text: str = Field(sa_column=Column(Text))
    prompt_tokens: int = Field(default=0)
    expected_output: Optional[str] = Field(default=None, sa_column=Column(Text))

    # Metadata
    dataset_name: Optional[str] = None
    dataset_index: Optional[int] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )


class TokenEvent(SQLModel, table=True):
    """Individual token generation event for detailed analysis."""

    __tablename__ = "token_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(default_factory=lambda: str(uuid4()), unique=True)

    benchmark_run_id: int = Field(foreign_key="benchmark_runs.id", index=True)
    benchmark_run: Optional[BenchmarkRun] = Relationship(back_populates="token_events")

    # Prompt reference
    prompt_id: Optional[int] = Field(default=None, foreign_key="prompts.id", index=True)

    # Timing (microseconds since run start)
    timestamp_us: int = Field(index=True)
    relative_timestamp_us: int = Field(index=True)

    # Token info
    token_id: int
    token_text: str
    is_special: bool = False

    # Latency metrics
    ttft_us: Optional[int] = None  # Time to first token
    tpot_us: Optional[int] = None  # Time per output token
    inter_token_latency_us: Optional[int] = None

    # Position
    token_index: int = 0
    is_first_token: bool = False
    is_last_token: bool = False

    # Streaming info
    chunk_index: Optional[int] = None
    chunk_size: Optional[int] = None

    __table_args__ = (
        Index("ix_token_events_run_timestamp", "benchmark_run_id", "timestamp_us"),
        Index("ix_token_events_run_prompt", "benchmark_run_id", "prompt_id"),
    )


class HardwareSample(SQLModel, table=True):
    """Hardware metrics sample during benchmark."""

    __tablename__ = "hardware_samples"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(default_factory=lambda: str(uuid4()), unique=True)

    benchmark_run_id: int = Field(foreign_key="benchmark_runs.id", index=True)
    benchmark_run: Optional[BenchmarkRun] = Relationship(back_populates="hardware_samples")

    # Timestamp (microseconds since run start)
    timestamp_us: int = Field(index=True)

    # CPU
    cpu_percent: Optional[float] = None
    cpu_percent_per_core: list[float] = Field(default_factory=list, sa_column=Column(JSON))
    cpu_freq_mhz: Optional[float] = None
    cpu_temp_celsius: Optional[float] = None
    cpu_power_watts: Optional[float] = None

    # GPU
    gpu_percent: Optional[float] = None
    gpu_memory_used_mb: Optional[int] = None
    gpu_memory_total_mb: Optional[int] = None
    gpu_temp_celsius: Optional[float] = None
    gpu_power_watts: Optional[float] = None
    gpu_fan_percent: Optional[float] = None
    gpu_clock_mhz: Optional[int] = None
    gpu_memory_clock_mhz: Optional[int] = None

    # Memory
    ram_used_mb: Optional[int] = None
    ram_total_mb: Optional[int] = None
    ram_percent: Optional[float] = None
    swap_used_mb: Optional[int] = None
    swap_total_mb: Optional[int] = None

    # Disk I/O
    disk_read_mb_s: Optional[float] = None
    disk_write_mb_s: Optional[float] = None

    # Network I/O
    net_sent_mb_s: Optional[float] = None
    net_recv_mb_s: Optional[float] = None

    # Battery
    battery_percent: Optional[float] = None
    battery_power_watts: Optional[float] = None
    battery_charging: Optional[bool] = None

    __table_args__ = (
        Index("ix_hardware_samples_run_time", "benchmark_run_id", "timestamp_us"),
    )


class QualityScore(SQLModel, table=True):
    """Quality benchmark scores."""

    __tablename__ = "quality_scores"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(default_factory=lambda: str(uuid4()), unique=True)

    benchmark_run_id: int = Field(foreign_key="benchmark_runs.id", index=True)
    benchmark_run: Optional[BenchmarkRun] = Relationship(back_populates="quality_scores")

    # Benchmark identifier
    benchmark_name: str = Field(index=True)  # mmlu, humaneval, gsm8k, etc.
    task_name: Optional[str] = None  # Specific task within benchmark

    # Scores
    accuracy: Optional[float] = None
    exact_match: Optional[float] = None
    f1_score: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    bleu: Optional[float] = None
    rouge1: Optional[float] = None
    rouge2: Optional[float] = None
    rouge_l: Optional[float] = None
    bert_score: Optional[float] = None
    perplexity: Optional[float] = None

    # Pass@k
    pass_at_1: Optional[float] = None
    pass_at_5: Optional[float] = None
    pass_at_10: Optional[float] = None

    # Needle in Haystack
    retrieval_precision: Optional[float] = None
    retrieval_recall: Optional[float] = None
    context_retention: Optional[float] = None

    # Instruction Following
    json_validity: Optional[float] = None
    xml_validity: Optional[float] = None
    schema_compliance: Optional[float] = None
    tool_call_accuracy: Optional[float] = None
    format_adherence: Optional[float] = None

    # Reliability
    hallucination_rate: Optional[float] = None
    factuality_score: Optional[float] = None
    consistency_score: Optional[float] = None
    determinism_score: Optional[float] = None
    error_rate: Optional[float] = None

    # Safety
    toxicity_score: Optional[float] = None
    refusal_correctness: Optional[float] = None

    # Agent metrics
    task_success_rate: Optional[float] = None
    plan_quality: Optional[float] = None
    tool_precision: Optional[float] = None
    tool_recall: Optional[float] = None
    avg_tool_calls: Optional[float] = None

    # Metadata
    num_samples: int = Field(default=0)
    details: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )

    __table_args__ = (
        Index("ix_quality_scores_run_benchmark", "benchmark_run_id", "benchmark_name"),
    )


class StatisticalSummary(SQLModel, table=True):
    """Pre-computed statistical summaries for fast dashboard queries."""

    __tablename__ = "statistical_summaries"

    id: Optional[int] = Field(default=None, primary_key=True)

    benchmark_run_id: int = Field(
        foreign_key="benchmark_runs.id", unique=True, index=True
    )
    benchmark_run: Optional[BenchmarkRun] = Relationship(
        back_populates="statistical_summary"
    )

    # Latency statistics (microseconds)
    ttft_mean: Optional[float] = None
    ttft_median: Optional[float] = None
    ttft_std: Optional[float] = None
    ttft_min: Optional[float] = None
    ttft_max: Optional[float] = None
    ttft_p50: Optional[float] = None
    ttft_p90: Optional[float] = None
    ttft_p95: Optional[float] = None
    ttft_p99: Optional[float] = None
    ttft_ci_lower: Optional[float] = None
    ttft_ci_upper: Optional[float] = None

    tpot_mean: Optional[float] = None
    tpot_median: Optional[float] = None
    tpot_std: Optional[float] = None
    tpot_p50: Optional[float] = None
    tpot_p90: Optional[float] = None
    tpot_p95: Optional[float] = None
    tpot_p99: Optional[float] = None

    e2e_latency_mean: Optional[float] = None
    e2e_latency_p50: Optional[float] = None
    e2e_latency_p90: Optional[float] = None
    e2e_latency_p95: Optional[float] = None
    e2e_latency_p99: Optional[float] = None

    # Throughput
    output_tps_mean: Optional[float] = None
    output_tps_median: Optional[float] = None
    output_tps_std: Optional[float] = None
    output_tps_max: Optional[float] = None
    input_tps_mean: Optional[float] = None
    total_tps_mean: Optional[float] = None
    rps_mean: Optional[float] = None

    # Memory
    peak_vram_mb: Optional[int] = None
    avg_vram_mb: Optional[float] = None
    peak_ram_mb: Optional[int] = None
    avg_ram_mb: Optional[float] = None

    # Utilization
    avg_gpu_percent: Optional[float] = None
    avg_cpu_percent: Optional[float] = None
    peak_gpu_percent: Optional[float] = None
    peak_cpu_percent: Optional[float] = None

    # Thermal
    peak_gpu_temp_celsius: Optional[float] = None
    avg_gpu_temp_celsius: Optional[float] = None
    peak_cpu_temp_celsius: Optional[float] = None
    avg_cpu_temp_celsius: Optional[float] = None

    # Power
    avg_gpu_power_watts: Optional[float] = None
    avg_cpu_power_watts: Optional[float] = None
    energy_per_token_joules: Optional[float] = None
    performance_per_watt: Optional[float] = None

    # Quality aggregate
    overall_quality_score: Optional[float] = None

    # Reliability
    success_rate: Optional[float] = None
    timeout_rate: Optional[float] = None
    oom_rate: Optional[float] = None
    error_rate: Optional[float] = None

    # Computed at
    computed_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )


class ComparisonSet(SQLModel, table=True):
    """Named comparison sets for multi-model comparison."""

    __tablename__ = "comparison_sets"

    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(default_factory=lambda: str(uuid4()), unique=True)

    name: str = Field(index=True)
    description: Optional[str] = None

    # Model references (JSON array of benchmark_run_ids)
    benchmark_run_ids: list[int] = Field(default_factory=list, sa_column=Column(JSON))

    # Comparison configuration
    metrics_to_compare: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )


# Type aliases for common queries
ModelId = int
BenchmarkRunId = int