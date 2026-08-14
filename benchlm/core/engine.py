"""Benchmark engine orchestrator for BenchLM."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from benchlm.core.config import BenchmarkConfig
from benchlm.core.scheduler import BenchmarkScheduler, BenchmarkPhase, BenchmarkResult
from benchlm.core.metrics import MetricsCollector, BenchmarkMetrics
from benchlm.core.statistics import StatisticsEngine
from benchlm.core.scorer import ScoringEngine, BenchmarkScore, EloRatingSystem
from benchlm.providers.base import LLMProvider, GenerationRequest
from benchlm.providers.registry import get_provider_registry
from benchlm.hardware.collector import HardwareCollector, HardwareSnapshot
from benchlm.database.repository import get_repository
from benchlm.database.models import BenchmarkRun, BenchmarkStatus, Model
from benchlm.config import get_config


@dataclass
class BenchmarkExecution:
    """Represents a benchmark execution."""

    run_id: str
    benchmark_id: str
    config: BenchmarkConfig
    model_name: str
    provider_name: str

    # State
    phase: BenchmarkPhase = BenchmarkPhase.IDLE
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Progress
    total_requests: int = 0
    completed_requests: int = 0
    failed_requests: int = 0

    # Results
    results: List[BenchmarkResult] = field(default_factory=list)
    metrics: Optional[BenchmarkMetrics] = None
    score: Optional[BenchmarkScore] = None

    # Error
    error: Optional[str] = None

    # Callbacks
    callbacks: Dict[str, List[Callable]] = field(default_factory=lambda: {
        "on_phase_change": [],
        "on_progress": [],
        "on_request_complete": [],
        "on_token": [],
        "on_error": [],
        "on_complete": [],
    })


class BenchmarkEngine:
    """Main benchmark orchestration engine."""

    def __init__(self):
        self._config = get_config()
        self._repository = get_repository()
        self._provider_registry = get_provider_registry()
        self._hardware_collector: Optional[HardwareCollector] = None
        self._statistics_engine = StatisticsEngine()
        self._scoring_engine = ScoringEngine()
        self._elo_system = EloRatingSystem()

        # Active executions
        self._executions: Dict[str, BenchmarkExecution] = {}
        self._current_execution: Optional[str] = None

    async def initialize(self):
        """Initialize the benchmark engine."""
        # Initialize hardware collector
        self._hardware_collector = HardwareCollector()
        await self._hardware_collector.initialize()

        # Initialize database
        await self._repository.init_db()

        # Initialize providers
        from benchlm.providers.registry import initialize_providers
        await initialize_providers(self._config)

    async def run_benchmark(
        self,
        config: BenchmarkConfig,
        model_name: str,
        provider_name: str = "ollama",
    ) -> BenchmarkExecution:
        """Run a complete benchmark."""
        execution = await self._create_execution(config, model_name, provider_name)

        try:
            # Get provider
            provider = self._get_provider(provider_name)
            if not provider:
                raise ValueError(f"Provider not found: {provider_name}")

            # Initialize provider
            await provider.initialize()

            # Get model info
            model_info = await provider.get_model_info(model_name)
            if not model_info:
                raise ValueError(f"Model not found: {model_name}")

            # Prepare prompts
            prompts = await self._prepare_prompts(config)

            # Create database run record
            db_run = await self._create_db_run(execution, model_info)

            # Set hardware collector benchmark context
            self._hardware_collector.set_benchmark_context(
                run_id=db_run.id,
                phase="warmup",
            )

            # Initialize metrics collector
            metrics_collector = MetricsCollector()
            metrics_collector.initialize(
                run_id=execution.run_id,
                model_name=model_name,
                provider=provider_name,
                config=config,
                hardware_collector=self._hardware_collector,
            )

            # Register metrics callbacks
            metrics_collector.register_callback(self._on_metrics_update)

            # Create scheduler
            scheduler = BenchmarkScheduler(provider, config, self._hardware_collector)
            scheduler.set_callbacks(
                on_phase_change=self._on_phase_change(execution),
                on_progress=self._on_progress(execution),
                on_request_complete=self._on_request_complete(execution, metrics_collector),
                on_token=self._on_token(execution),
            )

            # Update execution state
            execution.phase = BenchmarkPhase.INITIALIZING
            execution.started_at = datetime.utcnow()

            # Start hardware collection
            await metrics_collector.start_collection()
            self._hardware_collector.set_benchmark_context(
                run_id=db_run.id,
                phase="running",
            )

            # Run benchmark
            execution.phase = BenchmarkPhase.RUNNING
            results = await scheduler.run_benchmark(prompts)

            # Store results
            execution.results = results
            execution.total_requests = len(results)
            execution.completed_requests = sum(1 for r in results if not r.error)
            execution.failed_requests = sum(1 for r in results if r.error)

            # Finalize metrics
            await metrics_collector.stop_collection()
            metrics_collector.finalize()
            execution.metrics = metrics_collector.get_metrics()

            # Compute score
            if execution.metrics:
                execution.score = self._scoring_engine.compute_score(execution.metrics)

            # Update database
            await self._finalize_db_run(db_run, execution)

            # Update Elo rating
            self._update_elo_rating(model_name, provider_name, execution.score.overall_score if execution.score else 0)

            # Mark complete
            execution.phase = BenchmarkPhase.COMPLETED
            execution.completed_at = datetime.utcnow()

            # Notify completion
            self._notify_callbacks(execution, "on_complete")

            return execution

        except Exception as e:
            execution.phase = BenchmarkPhase.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()
            self._notify_callbacks(execution, "on_error", e)
            raise

        finally:
            # Cleanup
            self._hardware_collector.set_benchmark_context(phase="idle")
            if execution.run_id in self._executions:
                del self._executions[execution.run_id]

    async def _create_execution(
        self,
        config: BenchmarkConfig,
        model_name: str,
        provider_name: str,
    ) -> BenchmarkExecution:
        """Create a new benchmark execution."""
        execution = BenchmarkExecution(
            run_id=str(uuid.uuid4()),
            benchmark_id=config.uuid,
            config=config,
            model_name=model_name,
            provider_name=provider_name,
        )
        self._executions[execution.run_id] = execution
        self._current_execution = execution.run_id
        return execution

    def _get_provider(self, provider_name: str) -> Optional[LLMProvider]:
        """Get provider by name."""
        # Try direct lookup
        provider = self._provider_registry.get_provider(provider_name)
        if provider:
            return provider

        # Try by type
        from benchlm.providers.base import ProviderType
        try:
            ptype = ProviderType(provider_name)
            return self._provider_registry.get_provider_by_type(ptype)
        except ValueError:
            pass

        return None

    async def _prepare_prompts(self, config: BenchmarkConfig) -> List[str]:
        """Prepare prompts from dataset or custom prompts."""
        prompts = []

        if config.prompts.custom_prompts:
            prompts = config.prompts.custom_prompts.copy()
        else:
            # Load from built-in dataset
            prompts = await self._load_builtin_dataset(config.prompts.dataset.value)

        # Apply max prompts limit
        if config.prompts.max_prompts and len(prompts) > config.prompts.max_prompts:
            prompts = prompts[:config.prompts.max_prompts]

        # Shuffle if configured
        if config.prompts.shuffle_prompts:
            import random
            random.shuffle(prompts)

        return prompts

    async def _load_builtin_dataset(self, dataset_id: str) -> List[str]:
        """Load prompts from built-in dataset."""
        # This would load from the datasets package
        # For now, return some default prompts
        default_prompts = [
            "Explain quantum computing in simple terms.",
            "Write a Python function to calculate fibonacci numbers.",
            "What are the key differences between REST and GraphQL?",
            "Describe the process of photosynthesis.",
            "How does a neural network learn?",
            "What is the capital of France?",
            "Write a haiku about programming.",
            "Explain the concept of recursion with an example.",
            "What are the benefits of containerization?",
            "Describe how DNS works.",
        ]

        # Filter by dataset type
        if "coding" in dataset_id:
            return [p for p in default_prompts if any(kw in p.lower() for kw in ["python", "function", "code", "programming"])]
        elif "reasoning" in dataset_id:
            return [p for p in default_prompts if any(kw in p.lower() for kw in ["explain", "describe", "concept", "how"])]
        elif "creative" in dataset_id:
            return [p for p in default_prompts if any(kw in p.lower() for kw in ["write", "haiku", "story", "poem"])]

        return default_prompts

    async def _create_db_run(self, execution: BenchmarkExecution, model_info: Any) -> BenchmarkRun:
        """Create database record for benchmark run."""
        db_run = BenchmarkRun(
            model_id=1,  # Would need to look up actual model ID
            name=execution.config.name,
            description=execution.config.description,
            preset_name=execution.config.preset.value,
            temperature=execution.config.generation.temperature,
            top_p=execution.config.generation.top_p,
            top_k=execution.config.generation.top_k,
            seed=execution.config.generation.seed,
            max_tokens=execution.config.generation.max_tokens,
            batch_size=execution.config.execution.batch_size,
            context_length=execution.config.execution.context_length,
            streaming=execution.config.generation.stream,
            concurrent_users=execution.config.execution.concurrent_users,
            iterations=execution.config.execution.iterations,
            warmup_runs=execution.config.execution.warmup_runs,
            cooldown_seconds=int(execution.config.execution.cooldown_seconds),
            system_prompt=execution.config.prompts.system_prompt,
            prompt_dataset=execution.config.prompts.dataset.value,
            custom_prompts=execution.config.prompts.custom_prompts,
            status=BenchmarkStatus.RUNNING,
            started_at=datetime.utcnow(),
            hardware_info=self._hardware_collector.get_static_info() if self._hardware_collector else {},
        )
        return await self._repository.create_benchmark_run(db_run)

    async def _finalize_db_run(self, db_run: BenchmarkRun, execution: BenchmarkExecution):
        """Finalize database record with results."""
        if execution.metrics:
            db_run.status = BenchmarkStatus.COMPLETED
            db_run.completed_at = execution.completed_at
            db_run.duration_seconds = execution.metrics.duration_seconds

            # Overall scores
            if execution.score:
                db_run.overall_score = execution.score.overall_score
                db_run.grade = execution.score.grade
                db_run.latency_score = execution.score.category_scores[0].raw_score
                db_run.throughput_score = execution.score.category_scores[1].raw_score
                db_run.quality_score = execution.score.category_scores[2].raw_score
                db_run.reliability_score = execution.score.category_scores[3].raw_score
                db_run.memory_score = execution.score.category_scores[4].raw_score
                db_run.energy_score = execution.score.category_scores[5].raw_score
                db_run.context_score = execution.score.category_scores[6].raw_score
        else:
            db_run.status = BenchmarkStatus.FAILED
            db_run.error_message = execution.error

        await self._repository.update_benchmark_run(db_run)

    def _update_elo_rating(self, model_name: str, provider_name: str, score: float):
        """Update Elo rating based on benchmark score."""
        # Convert score to win probability against average
        # This is a simplified approach
        model_key = f"{provider_name}:{model_name}"
        current_rating = self._elo_system.get_rating(model_key)

        # Expected score based on rating difference from 1500
        expected = 1 / (1 + 10 ** ((1500 - current_rating) / 400))
        actual = score / 1000  # Normalize to 0-1

        # Update rating
        k_factor = 32
        new_rating = current_rating + k_factor * (actual - expected)
        self._elo_system.set_rating(model_key, new_rating)

    def _on_phase_change(self, execution: BenchmarkExecution):
        def callback(phase: BenchmarkPhase):
            execution.phase = phase
            if self._hardware_collector:
                self._hardware_collector.set_benchmark_context(phase=phase.value)
            self._notify_callbacks(execution, "on_phase_change", phase)
        return callback

    def _on_progress(self, execution: BenchmarkExecution):
        def callback(completed: int, total: int):
            execution.completed_requests = completed
            execution.total_requests = total
            self._notify_callbacks(execution, "on_progress", completed, total)
        return callback

    def _on_request_complete(
        self,
        execution: BenchmarkExecution,
        metrics_collector: MetricsCollector
    ):
        def callback(result: BenchmarkResult):
            execution.results.append(result)
            if result.error:
                execution.failed_requests += 1
            else:
                execution.completed_requests += 1
            metrics_collector.record_result(result)
            self._notify_callbacks(execution, "on_request_complete", result)
        return callback

    def _on_token(self, execution: BenchmarkExecution):
        def callback(token_event):
            # Update TPS in hardware collector
            self._hardware_collector.set_benchmark_context(tokens=execution.completed_requests)
            self._notify_callbacks(execution, "on_token", token_event)
        return callback

    def _on_metrics_update(self, metrics: BenchmarkMetrics):
        """Callback for metrics updates."""
        if self._current_execution and self._current_execution in self._executions:
            execution = self._executions[self._current_execution]
            execution.metrics = metrics

    def _notify_callbacks(self, execution: BenchmarkExecution, event: str, *args):
        """Notify all callbacks for an event."""
        for callback in execution.callbacks.get(event, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(*args))
                else:
                    callback(*args)
            except Exception:
                pass

    def register_callback(
        self,
        execution_id: str,
        event: str,
        callback: Callable,
    ):
        """Register a callback for an execution event."""
        if execution_id in self._executions:
            self._executions[execution_id].callbacks[event].append(callback)

    def get_execution(self, execution_id: str) -> Optional[BenchmarkExecution]:
        """Get execution by ID."""
        return self._executions.get(execution_id)

    def get_current_execution(self) -> Optional[BenchmarkExecution]:
        """Get currently running execution."""
        if self._current_execution:
            return self._executions.get(self._current_execution)
        return None

    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution."""
        if execution_id in self._executions:
            execution = self._executions[execution_id]
            # Would need to signal scheduler to cancel
            execution.phase = BenchmarkPhase.CANCELLED
            return True
        return False

    async def close(self):
        """Close the engine and all resources."""
        # Cancel all running executions
        for execution in self._executions.values():
            if execution.phase in (BenchmarkPhase.RUNNING, BenchmarkPhase.WARMUP):
                execution.phase = BenchmarkPhase.CANCELLED

        # Close hardware collector
        if self._hardware_collector:
            await self._hardware_collector.close()

        # Close providers
        from benchlm.providers.registry import close_providers
        await close_providers()

        # Close database
        await self._repository.close()


# Global engine instance
_engine: Optional[BenchmarkEngine] = None


def get_benchmark_engine() -> BenchmarkEngine:
    """Get the global benchmark engine."""
    global _engine
    if _engine is None:
        _engine = BenchmarkEngine()
    return _engine


async def initialize_benchmark_engine() -> BenchmarkEngine:
    """Initialize the benchmark engine."""
    engine = get_benchmark_engine()
    await engine.initialize()
    return engine


async def close_benchmark_engine():
    """Close the benchmark engine."""
    global _engine
    if _engine:
        await _engine.close()
        _engine = None