"""Metrics collector for BenchLM - collects and aggregates benchmark metrics."""

from __future__ import annotations

import asyncio
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from statistics import mean, median, stdev

from benchlm.core.scheduler import BenchmarkResult, BenchmarkPhase
from benchlm.hardware.collector import HardwareSnapshot


@dataclass
class LatencyMetrics:
    """Latency metrics for a benchmark run."""

    # Time to First Token (microseconds)
    ttft_samples: List[int] = field(default_factory=list)
    ttft_mean: float = 0.0
    ttft_median: float = 0.0
    ttft_stdev: float = 0.0
    ttft_min: int = 0
    ttft_max: int = 0
    ttft_p50: float = 0.0
    ttft_p90: float = 0.0
    ttft_p95: float = 0.0
    ttft_p99: float = 0.0
    ttft_ci_lower: float = 0.0
    ttft_ci_upper: float = 0.0

    # Time Per Output Token (microseconds)
    tpot_samples: List[int] = field(default_factory=list)
    tpot_mean: float = 0.0
    tpot_median: float = 0.0
    tpot_stdev: float = 0.0
    tpot_p50: float = 0.0
    tpot_p90: float = 0.0
    tpot_p95: float = 0.0
    tpot_p99: float = 0.0

    # End-to-end latency (microseconds)
    e2e_samples: List[int] = field(default_factory=list)
    e2e_mean: float = 0.0
    e2e_p50: float = 0.0
    e2e_p90: float = 0.0
    e2e_p95: float = 0.0
    e2e_p99: float = 0.0

    # Inter-token latency (microseconds)
    inter_token_samples: List[int] = field(default_factory=list)
    inter_token_mean: float = 0.0
    inter_token_jitter: float = 0.0  # Std dev of inter-token latency

    def compute_percentiles(self):
        """Compute all percentiles from samples."""
        for attr_name in ['ttft_samples', 'tpot_samples', 'e2e_samples', 'inter_token_samples']:
            samples = getattr(self, attr_name)
            if not samples:
                continue

            sorted_samples = sorted(samples)
            n = len(sorted_samples)

            prefix = attr_name.replace('_samples', '')

            # Mean, median, stdev
            setattr(self, f'{prefix}_mean', mean(samples))
            setattr(self, f'{prefix}_median', median(samples))
            setattr(self, f'{prefix}_stdev', stdev(samples) if n > 1 else 0.0)
            setattr(self, f'{prefix}_min', min(samples))
            setattr(self, f'{prefix}_max', max(samples))

            # Percentiles
            for p in [50, 90, 95, 99]:
                idx = int(n * p / 100)
                if idx >= n:
                    idx = n - 1
                setattr(self, f'{prefix}_p{p}', sorted_samples[idx])

            # Jitter for inter-token
            if attr_name == 'inter_token_samples' and n > 1:
                self.inter_token_jitter = stdev(samples)


@dataclass
class ThroughputMetrics:
    """Throughput metrics for a benchmark run."""

    # Tokens per second
    tps_samples: List[float] = field(default_factory=list)
    output_tps_mean: float = 0.0
    output_tps_median: float = 0.0
    output_tps_stdev: float = 0.0
    output_tps_min: float = 0.0
    output_tps_max: float = 0.0

    # Prompt tokens per second
    prompt_tps_samples: List[float] = field(default_factory=list)
    prompt_tps_mean: float = 0.0

    # Total tokens per second
    total_tps_samples: List[float] = field(default_factory=list)
    total_tps_mean: float = 0.0

    # Requests per second
    rps_samples: List[float] = field(default_factory=list)
    rps_mean: float = 0.0

    # Queries per minute
    qpm_samples: List[float] = field(default_factory=list)
    qpm_mean: float = 0.0

    # Batch efficiency
    batch_efficiency_samples: List[float] = field(default_factory=list)
    batch_efficiency_mean: float = 0.0

    def compute_all(self):
        """Compute all throughput metrics."""
        metrics_map = {
            'tps_samples': ('output_tps', True),
            'prompt_tps_samples': ('prompt_tps', True),
            'total_tps_samples': ('total_tps', True),
            'rps_samples': ('rps', True),
            'qpm_samples': ('qpm', True),
            'batch_efficiency_samples': ('batch_efficiency', True),
        }

        for samples_attr, (prefix, compute_stats) in metrics_map.items():
            samples = getattr(self, samples_attr)
            if not samples:
                continue

            if compute_stats:
                setattr(self, f'{prefix}_mean', mean(samples))
                setattr(self, f'{prefix}_median', median(samples))
                setattr(self, f'{prefix}_stdev', stdev(samples) if len(samples) > 1 else 0.0)
                setattr(self, f'{prefix}_min', min(samples))
                setattr(self, f'{prefix}_max', max(samples))


@dataclass
class ResourceMetrics:
    """Resource utilization metrics."""

    # VRAM (MB)
    vram_samples: List[int] = field(default_factory=list)
    peak_vram_mb: int = 0
    avg_vram_mb: float = 0.0

    # RAM (MB)
    ram_samples: List[int] = field(default_factory=list)
    peak_ram_mb: int = 0
    avg_ram_mb: float = 0.0

    # GPU utilization (%)
    gpu_util_samples: List[float] = field(default_factory=list)
    avg_gpu_util: float = 0.0
    peak_gpu_util: float = 0.0

    # CPU utilization (%)
    cpu_util_samples: List[float] = field(default_factory=list)
    avg_cpu_util: float = 0.0
    peak_cpu_util: float = 0.0

    # Memory bandwidth (GB/s)
    memory_bandwidth_samples: List[float] = field(default_factory=list)
    avg_memory_bandwidth: float = 0.0

    # PCIe utilization (%)
    pcie_util_samples: List[float] = field(default_factory=list)
    avg_pcie_util: float = 0.0

    # Disk I/O (MB/s)
    disk_read_samples: List[float] = field(default_factory=list)
    disk_write_samples: List[float] = field(default_factory=list)
    avg_disk_read_mb_s: float = 0.0
    avg_disk_write_mb_s: float = 0.0

    # Network I/O (MB/s)
    net_sent_samples: List[float] = field(default_factory=list)
    net_recv_samples: List[float] = field(default_factory=list)

    def compute_all(self):
        """Compute all resource metrics."""
        metric_groups = [
            ('vram_samples', 'peak_vram_mb', 'avg_vram_mb', True, True),
            ('ram_samples', 'peak_ram_mb', 'avg_ram_mb', True, True),
            ('gpu_util_samples', 'peak_gpu_util', 'avg_gpu_util', True, True),
            ('cpu_util_samples', 'peak_cpu_util', 'avg_cpu_util', True, True),
            ('memory_bandwidth_samples', None, 'avg_memory_bandwidth', False, True),
            ('pcie_util_samples', None, 'avg_pcie_util', False, True),
            ('disk_read_samples', None, 'avg_disk_read_mb_s', False, True),
            ('disk_write_samples', None, 'avg_disk_write_mb_s', False, True),
        ]

        for samples_attr, peak_attr, avg_attr, has_peak, has_avg in metric_groups:
            samples = getattr(self, samples_attr)
            if not samples:
                continue

            if has_peak and peak_attr:
                setattr(self, peak_attr, max(samples))
            if has_avg and avg_attr:
                setattr(self, avg_attr, mean(samples))


@dataclass
class ThermalMetrics:
    """Thermal and power metrics."""

    # GPU temperatures (°C)
    gpu_temp_samples: List[float] = field(default_factory=list)
    peak_gpu_temp: float = 0.0
    avg_gpu_temp: float = 0.0

    # CPU temperatures (°C)
    cpu_temp_samples: List[float] = field(default_factory=list)
    peak_cpu_temp: float = 0.0
    avg_cpu_temp: float = 0.0

    # Power (Watts)
    gpu_power_samples: List[float] = field(default_factory=list)
    avg_gpu_power: float = 0.0
    peak_gpu_power: float = 0.0

    cpu_power_samples: List[float] = field(default_factory=list)
    avg_cpu_power: float = 0.0
    peak_cpu_power: float = 0.0

    # Energy
    energy_per_token_samples: List[float] = field(default_factory=list)
    avg_energy_per_token: float = 0.0  # Joules per token

    # Performance per Watt
    perf_per_watt_samples: List[float] = field(default_factory=list)
    avg_perf_per_watt: float = 0.0  # Tokens per Joule

    # Thermal throttling events
    throttling_events: int = 0
    throttling_timeline: List[Dict[str, Any]] = field(default_factory=list)

    def compute_all(self):
        """Compute all thermal metrics."""
        metric_groups = [
            ('gpu_temp_samples', 'peak_gpu_temp', 'avg_gpu_temp', True, True),
            ('cpu_temp_samples', 'peak_cpu_temp', 'avg_cpu_temp', True, True),
            ('gpu_power_samples', 'peak_gpu_power', 'avg_gpu_power', True, True),
            ('cpu_power_samples', 'peak_cpu_power', 'avg_cpu_power', True, True),
            ('energy_per_token_samples', None, 'avg_energy_per_token', False, True),
            ('perf_per_watt_samples', None, 'avg_perf_per_watt', False, True),
        ]

        for samples_attr, peak_attr, avg_attr, has_peak, has_avg in metric_groups:
            samples = getattr(self, samples_attr)
            if not samples:
                continue

            if has_peak and peak_attr:
                setattr(self, peak_attr, max(samples))
            if has_avg and avg_attr:
                setattr(self, avg_attr, mean(samples))


@dataclass
class QualityMetrics:
    """Quality benchmark metrics."""

    # Accuracy metrics
    accuracy: Optional[float] = None
    exact_match: Optional[float] = None
    f1_score: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None

    # NLP metrics
    bleu: Optional[float] = None
    rouge1: Optional[float] = None
    rouge2: Optional[float] = None
    rouge_l: Optional[float] = None
    bert_score: Optional[float] = None

    # Perplexity
    perplexity: Optional[float] = None
    log_loss: Optional[float] = None

    # Calibration
    calibration_error: Optional[float] = None

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

    # Agent
    task_success_rate: Optional[float] = None
    plan_quality: Optional[float] = None
    tool_precision: Optional[float] = None
    tool_recall: Optional[float] = None
    avg_tool_calls: Optional[float] = None


@dataclass
class ReliabilityMetrics:
    """Reliability metrics."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    oom_requests: int = 0

    success_rate: float = 0.0
    failure_rate: float = 0.0
    timeout_rate: float = 0.0
    oom_rate: float = 0.0

    # Error categories
    error_categories: Dict[str, int] = field(default_factory=dict)

    # Variance
    latency_variance: float = 0.0
    throughput_variance: float = 0.0

    # Stability score (0-100)
    stability_score: float = 0.0


@dataclass
class BenchmarkMetrics:
    """Complete benchmark metrics."""

    run_id: str
    model_name: str
    provider: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Configuration
    iterations: int = 0
    warmup_runs: int = 0
    concurrent_users: int = 1
    batch_size: int = 1

    # Metrics categories
    latency: LatencyMetrics = field(default_factory=LatencyMetrics)
    throughput: ThroughputMetrics = field(default_factory=ThroughputMetrics)
    resources: ResourceMetrics = field(default_factory=ResourceMetrics)
    thermal: ThermalMetrics = field(default_factory=ThermalMetrics)
    quality: QualityMetrics = field(default_factory=QualityMetrics)
    reliability: ReliabilityMetrics = field(default_factory=ReliabilityMetrics)

    # Overall scores (0-100 each)
    latency_score: float = 0.0
    throughput_score: float = 0.0
    quality_score: float = 0.0
    reliability_score: float = 0.0
    memory_score: float = 0.0
    energy_score: float = 0.0
    context_score: float = 0.0
    overall_score: float = 0.0
    grade: str = "D"

    # Raw samples for detailed analysis
    raw_token_events: List[Dict[str, Any]] = field(default_factory=list)
    raw_hardware_samples: List[Dict[str, Any]] = field(default_factory=list)

    def compute_all(self):
        """Compute all derived metrics."""
        self.latency.compute_percentiles()
        self.throughput.compute_all()
        self.resources.compute_all()
        self.thermal.compute_all()

        # Compute reliability
        rel = self.reliability
        if rel.total_requests > 0:
            rel.success_rate = rel.successful_requests / rel.total_requests
            rel.failure_rate = rel.failed_requests / rel.total_requests
            rel.timeout_rate = rel.timeout_requests / rel.total_requests
            rel.oom_rate = rel.oom_requests / rel.total_requests

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "run_id": self.run_id,
            "model_name": self.model_name,
            "provider": self.provider,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "iterations": self.iterations,
            "warmup_runs": self.warmup_runs,
            "concurrent_users": self.concurrent_users,
            "batch_size": self.batch_size,
            "latency": self.latency.__dict__,
            "throughput": self.throughput.__dict__,
            "resources": self.resources.__dict__,
            "thermal": self.thermal.__dict__,
            "quality": {k: v for k, v in self.quality.__dict__.items() if v is not None},
            "reliability": self.reliability.__dict__,
            "scores": {
                "latency": self.latency_score,
                "throughput": self.throughput_score,
                "quality": self.quality_score,
                "reliability": self.reliability_score,
                "memory": self.memory_score,
                "energy": self.energy_score,
                "context": self.context_score,
                "overall": self.overall_score,
            },
            "grade": self.grade,
        }


class MetricsCollector:
    """Collects and aggregates metrics during benchmark execution."""

    def __init__(self):
        self._metrics: Optional[BenchmarkMetrics] = None
        self._hardware_collector = None
        self._collection_task: Optional[asyncio.Task] = None
        self._running = False
        self._callbacks: List[Callable[[BenchmarkMetrics], Any]] = []

    def initialize(
        self,
        run_id: str,
        model_name: str,
        provider: str,
        config: Any,
        hardware_collector: Any = None,
    ):
        """Initialize metrics collection for a benchmark run."""
        self._metrics = BenchmarkMetrics(
            run_id=run_id,
            model_name=model_name,
            provider=provider,
            started_at=datetime.utcnow(),
            iterations=config.execution.iterations,
            warmup_runs=config.execution.warmup_runs,
            concurrent_users=config.execution.concurrent_users,
            batch_size=config.execution.batch_size,
        )
        self._hardware_collector = hardware_collector

    def register_callback(self, callback: Callable[[BenchmarkMetrics], Any]):
        """Register a callback for metrics updates."""
        self._callbacks.append(callback)

    def record_result(self, result: BenchmarkResult):
        """Record a benchmark result."""
        if not self._metrics:
            return

        m = self._metrics

        # Latency
        if result.ttft_us is not None:
            m.latency.ttft_samples.append(result.ttft_us)
        if result.tpot_us is not None:
            m.latency.tpot_samples.append(result.tpot_us)
        if result.e2e_latency_us is not None:
            m.latency.e2e_samples.append(result.e2e_latency_us)

        # Throughput
        if result.tokens_per_second > 0:
            m.throughput.tps_samples.append(result.tokens_per_second)

        # Token counts
        m.throughput.prompt_tps_samples.append(result.prompt_tokens)
        m.throughput.total_tps_samples.append(result.total_tokens)

        # Hardware snapshot
        if result.hardware_snapshot:
            hw = result.hardware_snapshot
            if 'gpu' in hw:
                for gpu_idx, gpu_data in hw['gpu'].items():
                    if 'utilization' in gpu_data:
                        m.resources.gpu_util_samples.append(gpu_data['utilization'].get('current', 0))
                    if 'memory' in gpu_data:
                        m.resources.vram_samples.append(gpu_data['memory'].get('current_used_mb', 0))
            if 'cpu' in hw and 'total' in hw['cpu']:
                m.resources.cpu_util_samples.append(hw['cpu']['total'].get('current', 0))
            if 'memory' in hw and 'ram' in hw['memory']:
                m.resources.ram_samples.append(hw['memory']['ram'].get('current_used_mb', 0))
            if 'thermal' in hw:
                thermal = hw['thermal']
                if 'gpu_core' in thermal:
                    m.thermal.gpu_temp_samples.append(thermal['gpu_core'].get('current', 0))
                if 'cpu_package' in thermal:
                    m.thermal.cpu_temp_samples.append(thermal['cpu_package'].get('current', 0))

        # Reliability
        m.reliability.total_requests += 1
        if result.error:
            m.reliability.failed_requests += 1
            if "timeout" in result.error.lower():
                m.reliability.timeout_requests += 1
            elif "oom" in result.error.lower() or "memory" in result.error.lower():
                m.reliability.oom_requests += 1

            # Categorize error
            category = result.error.split(":")[0] if ":" in result.error else "other"
            m.reliability.error_categories[category] = m.reliability.error_categories.get(category, 0) + 1
        else:
            m.reliability.successful_requests += 1

        # Store raw token events
        if hasattr(result, 'token_events') and result.token_events:
            for event in result.token_events:
                self._metrics.raw_token_events.append({
                    "token_id": event.token_id,
                    "token_text": event.token_text,
                    "timestamp": event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else str(event.timestamp),
                    "is_first": event.is_first_token,
                    "is_last": event.is_last_token,
                })

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(self._metrics)
            except Exception:
                pass

    def record_hardware_snapshot(self, snapshot: HardwareSnapshot):
        """Record a hardware snapshot."""
        if not self._metrics:
            return

        m = self._metrics

        # CPU
        if snapshot.cpu:
            m.resources.cpu_util_samples.append(snapshot.cpu.total_percent)

        # GPU
        for gpu in snapshot.gpus:
            m.resources.gpu_util_samples.append(gpu.utilization_percent)
            m.resources.vram_samples.append(gpu.memory_used_mb)
            if gpu.temperature_celsius:
                m.thermal.gpu_temp_samples.append(gpu.temperature_celsius)
            if gpu.power_watts:
                m.thermal.gpu_power_samples.append(gpu.power_watts)

        # Memory
        if snapshot.memory:
            m.resources.ram_samples.append(snapshot.memory.ram_used_mb)

        # Temperature
        if snapshot.temperature:
            if snapshot.temperature.cpu_package_celsius:
                m.thermal.cpu_temp_samples.append(snapshot.temperature.cpu_package_celsius)
            if snapshot.temperature.gpu_core_celsius:
                m.thermal.gpu_temp_samples.append(snapshot.temperature.gpu_core_celsius)

        # Store raw hardware sample
        self._metrics.raw_hardware_samples.append(snapshot.to_dict())

    async def start_collection(self):
        """Start continuous hardware collection."""
        self._running = True
        self._collection_task = asyncio.create_task(self._collection_loop())

    async def stop_collection(self):
        """Stop hardware collection."""
        self._running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass

    async def _collection_loop(self):
        """Background collection loop."""
        while self._running:
            if self._hardware_collector:
                try:
                    snapshot = await self._hardware_collector.get_snapshot()
                    if snapshot:
                        self.record_hardware_snapshot(snapshot)
                except Exception:
                    pass
            await asyncio.sleep(0.25)  # 250ms

    def finalize(self):
        """Finalize metrics collection."""
        if self._metrics:
            self._metrics.completed_at = datetime.utcnow()
            self._metrics.duration_seconds = (
                self._metrics.completed_at - self._metrics.started_at
            ).total_seconds()
            self._metrics.compute_all()

    def get_metrics(self) -> Optional[BenchmarkMetrics]:
        """Get current metrics."""
        return self._metrics

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        if not self._metrics:
            return {}

        m = self._metrics
        return {
            "run_id": m.run_id,
            "model": m.model_name,
            "provider": m.provider,
            "duration": m.duration_seconds,
            "requests": m.reliability.total_requests,
            "success_rate": m.reliability.success_rate,
            "ttft_p50": m.latency.ttft_p50,
            "ttft_p99": m.latency.ttft_p99,
            "tps_mean": m.throughput.output_tps_mean,
            "peak_vram": m.resources.peak_vram_mb,
            "peak_gpu_temp": m.thermal.peak_gpu_temp,
            "overall_score": m.overall_score,
            "grade": m.grade,
        }