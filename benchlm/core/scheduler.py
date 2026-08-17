"""Benchmark scheduler for BenchLM."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Set

from benchlm.providers.base import (
    LLMProvider,
    GenerationRequest,
    ChatRequest,
    GenerationResponse,
    TokenEvent,
    ChatMessage,
)
from benchlm.core.config import BenchmarkConfig, GenerationParameters, ExecutionParameters


class BenchmarkPhase(str, Enum):
    """Benchmark execution phase."""

    IDLE = "idle"
    INITIALIZING = "initializing"
    WARMUP = "warmup"
    RUNNING = "running"
    COOLDOWN = "cooldown"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class RequestType(str, Enum):
    """Type of request to execute."""

    GENERATE = "generate"
    CHAT = "chat"


@dataclass
class BenchmarkRequest:
    """A single benchmark request."""

    request_id: str
    prompt: str
    model: str
    request_type: RequestType = RequestType.GENERATE
    system_prompt: str = ""
    generation_config: Optional[GenerationParameters] = None
    chat_messages: Optional[List[ChatMessage]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Timing
    submitted_at: Optional[float] = None
    started_at: Optional[float] = None
    first_token_at: Optional[float] = None
    completed_at: Optional[float] = None

    # Results
    response: Optional[GenerationResponse] = None
    token_events: List[TokenEvent] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class BenchmarkResult:
    """Result of a completed benchmark request."""

    request_id: str
    prompt: str
    model: str

    # Latency (microseconds)
    ttft_us: Optional[int] = None  # Time to first token
    tpot_us: Optional[int] = None  # Time per output token
    e2e_latency_us: Optional[int] = None  # End-to-end latency

    # Token counts
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    # Throughput
    tokens_per_second: float = 0.0

    # Response
    response_text: str = ""
    finish_reason: str = "stop"

    # Error
    error: Optional[str] = None

    # Hardware snapshot at completion
    hardware_snapshot: Optional[Dict[str, Any]] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class RequestQueue:
    """Async request queue with concurrency control."""

    def __init__(self, max_concurrent: int = 1):
        self._max_concurrent = max_concurrent
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running: Set[str] = set()
        self._results: Dict[str, BenchmarkResult] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._completed_count = 0
        self._failed_count = 0

    async def put(self, request: BenchmarkRequest):
        """Add request to queue."""
        await self._queue.put(request)

    async def get(self) -> BenchmarkRequest:
        """Get next request from queue."""
        return await self._queue.get()

    async def mark_running(self, request_id: str):
        """Mark request as running."""
        self._running.add(request_id)

    async def mark_completed(self, request_id: str, result: BenchmarkResult):
        """Mark request as completed."""
        self._running.discard(request_id)
        self._results[request_id] = result
        self._completed_count += 1
        if result.error:
            self._failed_count += 1

    def get_running_count(self) -> int:
        return len(self._running)

    def get_completed_count(self) -> int:
        return self._completed_count

    def get_failed_count(self) -> int:
        return self._failed_count

    def get_results(self) -> List[BenchmarkResult]:
        return list(self._results.values())

    def is_empty(self) -> bool:
        return self._queue.empty() and len(self._running) == 0

    async def wait_completion(self, timeout: Optional[float] = None) -> bool:
        """Wait for all requests to complete."""
        start = time.time()
        while not self.is_empty():
            if timeout and (time.time() - start) > timeout:
                return False
            await asyncio.sleep(0.1)
        return True


class BenchmarkScheduler:
    """Schedules and executes benchmark requests with concurrency control."""

    def __init__(
        self,
        provider: LLMProvider,
        config: BenchmarkConfig,
        hardware_collector: Optional[Any] = None,
    ):
        self.provider = provider
        self.config = config
        self.hardware_collector = hardware_collector

        self._phase = BenchmarkPhase.IDLE
        self._phase_start_time: Optional[float] = None
        self._total_requests = 0
        self._completed_requests = 0
        self._failed_requests = 0

        # Queue and execution
        self._queue = RequestQueue(max_concurrent=config.execution.concurrent_users)
        self._execution_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None

        # Callbacks
        self._on_request_start: Optional[Callable[[BenchmarkRequest], Any]] = None
        self._on_request_complete: Optional[Callable[[BenchmarkResult], Any]] = None
        self._on_token: Optional[Callable[[TokenEvent], Any]] = None
        self._on_phase_change: Optional[Callable[[BenchmarkPhase], Any]] = None
        self._on_progress: Optional[Callable[[int, int], Any]] = None  # completed, total

        # State
        self._paused = False
        self._cancelled = False
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None

        # Token streaming
        self._token_streams: Dict[str, AsyncIterator[TokenEvent]] = {}

    @property
    def phase(self) -> BenchmarkPhase:
        return self._phase

    @property
    def progress(self) -> float:
        if self._total_requests == 0:
            return 0.0
        return self._completed_requests / self._total_requests

    @property
    def is_running(self) -> bool:
        return self._phase in (BenchmarkPhase.WARMUP, BenchmarkPhase.RUNNING)

    @property
    def elapsed_seconds(self) -> Optional[float]:
        if self._start_time is None:
            return None
        end = self._end_time or time.time()
        return end - self._start_time

    def set_callbacks(
        self,
        on_request_start: Optional[Callable[[BenchmarkRequest], Any]] = None,
        on_request_complete: Optional[Callable[[BenchmarkResult], Any]] = None,
        on_token: Optional[Callable[[TokenEvent], Any]] = None,
        on_phase_change: Optional[Callable[[BenchmarkPhase], Any]] = None,
        on_progress: Optional[Callable[[int, int], Any]] = None,
    ):
        """Set callback functions."""
        self._on_request_start = on_request_start
        self._on_request_complete = on_request_complete
        self._on_token = on_token
        self._on_phase_change = on_phase_change
        self._on_progress = on_progress

    def _set_phase(self, phase: BenchmarkPhase):
        """Change benchmark phase."""
        if self._phase != phase:
            self._phase = phase
            self._phase_start_time = time.time()
            if self._on_phase_change:
                try:
                    self._on_phase_change(phase)
                except Exception:
                    pass

    async def prepare_requests(self, prompts: List[str]) -> List[BenchmarkRequest]:
        """Prepare benchmark requests from prompts."""
        requests = []
        gen_config = self.config.generation

        for i, prompt in enumerate(prompts):
            request = BenchmarkRequest(
                request_id=str(uuid.uuid4()),
                prompt=prompt,
                model=self.config.model_names[0] if self.config.model_names else "default",
                request_type=RequestType.GENERATE,
                system_prompt=self.config.prompts.system_prompt,
                generation_config=gen_config,
                metadata={
                    "prompt_index": i,
                    "iteration": i // len(prompts) + 1,
                },
            )
            requests.append(request)

        return requests

    async def run_benchmark(
        self,
        prompts: List[str],
    ) -> List[BenchmarkResult]:
        """Run complete benchmark with all phases."""
        self._cancelled = False
        self._paused = False
        self._start_time = time.time()
        self._total_requests = 0
        self._completed_requests = 0
        self._failed_requests = 0

        try:
            # Phase 1: Initialize
            self._set_phase(BenchmarkPhase.INITIALIZING)
            requests = await self.prepare_requests(prompts)

            # Replicate requests for iterations
            all_requests = []
            for iteration in range(self.config.execution.iterations):
                for req in requests:
                    new_req = BenchmarkRequest(
                        request_id=str(uuid.uuid4()),
                        prompt=req.prompt,
                        model=req.model,
                        request_type=req.request_type,
                        system_prompt=req.system_prompt,
                        generation_config=req.generation_config,
                        chat_messages=req.chat_messages,
                        metadata={**req.metadata, "iteration": iteration + 1},
                    )
                    all_requests.append(new_req)

            self._total_requests = len(all_requests)

            # Phase 2: Warmup
            if self.config.execution.warmup_runs > 0:
                self._set_phase(BenchmarkPhase.WARMUP)
                warmup_requests = all_requests[:self.config.execution.warmup_runs]
                await self._execute_requests(warmup_requests, is_warmup=True)

                # Cooldown after warmup
                if self.config.execution.cooldown_seconds > 0:
                    await asyncio.sleep(self.config.execution.cooldown_seconds)

            # Phase 3: Main benchmark
            if not self._cancelled:
                self._set_phase(BenchmarkPhase.RUNNING)
                main_requests = all_requests[self.config.execution.warmup_runs:]
                await self._execute_requests(main_requests, is_warmup=False)

            # Phase 4: Cooldown
            if not self._cancelled and self.config.execution.cooldown_seconds > 0:
                self._set_phase(BenchmarkPhase.COOLDOWN)
                await asyncio.sleep(self.config.execution.cooldown_seconds)

            # Complete
            self._end_time = time.time()
            if self._cancelled:
                self._set_phase(BenchmarkPhase.CANCELLED)
            elif self._failed_requests > 0 and self._completed_requests == 0:
                self._set_phase(BenchmarkPhase.FAILED)
            else:
                self._set_phase(BenchmarkPhase.COMPLETED)

            return self._queue.get_results()

        except Exception as e:
            self._set_phase(BenchmarkPhase.FAILED)
            self._end_time = time.time()
            raise

    async def _execute_requests(
        self,
        requests: List[BenchmarkRequest],
        is_warmup: bool = False,
    ):
        """Execute a batch of requests."""
        # Start workers
        workers = [
            asyncio.create_task(self._worker(f"worker-{i}"))
            for i in range(self.config.execution.concurrent_users)
        ]

        # Enqueue requests
        for req in requests:
            if self._cancelled:
                break
            while self._paused:
                await asyncio.sleep(0.1)
            await self._queue.put(req)

        # Wait for completion
        await self._queue.wait_completion()

        # Stop workers
        for worker in workers:
            worker.cancel()
        await asyncio.gather(*workers, return_exceptions=True)

    async def _worker(self, worker_id: str):
        """Worker coroutine to process requests."""
        while self.is_running or not self._queue.is_empty():
            if self._cancelled:
                break

            while self._paused:
                await asyncio.sleep(0.1)

            try:
                request = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            await self._process_request(request, worker_id, is_warmup=False)

    async def _process_request(
        self,
        request: BenchmarkRequest,
        worker_id: str,
        is_warmup: bool = False,
    ):
        """Process a single benchmark request."""
        request.submitted_at = time.time()

        # Notify start
        if self._on_request_start:
            try:
                self._on_request_start(request)
            except Exception:
                pass

        await self._queue.mark_running(request.request_id)

        try:
            # Execute request
            if request.request_type == RequestType.CHAT:
                result = await self._execute_chat(request)
            else:
                result = await self._execute_generate(request)

            request.completed_at = time.time()
            request.response = result

            # Create benchmark result
            benchmark_result = self._create_result(request, result)

            await self._queue.mark_completed(request.request_id, benchmark_result)
            self._completed_requests += 1

            # Notify completion
            if self._on_request_complete:
                try:
                    self._on_request_complete(benchmark_result)
                except Exception:
                    pass

            # Progress callback
            if self._on_progress:
                try:
                    self._on_progress(self._completed_requests, self._total_requests)
                except Exception:
                    pass

        except Exception as e:
            # Handle error
            error_result = BenchmarkResult(
                request_id=request.request_id,
                prompt=request.prompt,
                model=request.model,
                error=str(e),
            )
            await self._queue.mark_completed(request.request_id, error_result)
            self._failed_requests += 1

    async def _execute_generate(self, request: BenchmarkRequest) -> GenerationResponse:
        """Execute generation request with streaming."""
        gen_request = GenerationRequest(
            prompt=request.prompt,
            model=request.model,
            config=request.generation_config or self.config.generation,
            system_prompt=request.system_prompt,
            request_id=request.request_id,
        )

        if request.generation_config and request.generation_config.stream:
            # Streaming execution
            return await self._execute_generate_streaming(gen_request, request)
        else:
            # Non-streaming
            return await self.provider.generate(gen_request)

    async def _execute_generate_streaming(
        self,
        gen_request: GenerationRequest,
        benchmark_request: BenchmarkRequest,
    ) -> GenerationResponse:
        """Execute streaming generation and collect token events."""
        token_events = []
        accumulated_text = ""
        first_token_time = None
        start_time = time.time()

        async for token_event in self.provider.generate_stream(gen_request):
            current_time = time.time()

            if first_token_time is None:
                first_token_time = current_time
                benchmark_request.first_token_at = first_token_time

            token_events.append(token_event)
            accumulated_text += token_event.token_text

            # Notify token callback
            if self._on_token:
                try:
                    self._on_token(token_event)
                except Exception:
                    pass

        end_time = time.time()

        # Build response
        prompt_tokens = self.provider._count_tokens(gen_request.prompt)
        completion_tokens = len(token_events)

        return GenerationResponse(
            text=accumulated_text,
            model=gen_request.model,
            provider=self.provider.provider_type,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            finish_reason="stop",
            token_events=token_events,
            metadata={
                "start_time": start_time,
                "end_time": end_time,
                "first_token_time": first_token_time,
            },
        )

    async def _execute_chat(self, request: BenchmarkRequest) -> GenerationResponse:
        """Execute chat request."""
        messages = request.chat_messages or [
            ChatMessage(role="system", content=request.system_prompt) if request.system_prompt else None,
            ChatMessage(role="user", content=request.prompt),
        ]
        messages = [m for m in messages if m is not None]

        chat_request = ChatRequest(
            messages=messages,
            model=request.model,
            config=request.generation_config or self.config.generation,
            request_id=request.request_id,
        )

        if request.generation_config and request.generation_config.stream:
            return await self._execute_chat_streaming(chat_request, request)
        else:
            return await self.provider.chat(chat_request)

    async def _execute_chat_streaming(
        self,
        chat_request: ChatRequest,
        benchmark_request: BenchmarkRequest,
    ) -> GenerationResponse:
        """Execute streaming chat."""
        token_events = []
        accumulated_text = ""
        first_token_time = None
        start_time = time.time()

        async for token_event in self.provider.chat_stream(chat_request):
            current_time = time.time()

            if first_token_time is None:
                first_token_time = current_time
                benchmark_request.first_token_at = first_token_time

            token_events.append(token_event)
            accumulated_text += token_event.token_text

            if self._on_token:
                try:
                    self._on_token(token_event)
                except Exception:
                    pass

        end_time = time.time()

        prompt_tokens = sum(self.provider._count_tokens(m.content) for m in chat_request.messages)
        completion_tokens = len(token_events)

        return GenerationResponse(
            text=accumulated_text,
            model=chat_request.model,
            provider=self.provider.provider_type,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            finish_reason="stop",
            token_events=token_events,
            metadata={
                "start_time": start_time,
                "end_time": end_time,
                "first_token_time": first_token_time,
            },
        )

    def _create_result(self, request: BenchmarkRequest, response: GenerationResponse) -> BenchmarkResult:
        """Create benchmark result from request and response."""
        # Calculate latencies
        ttft_us = None
        tpot_us = None
        e2e_latency_us = None

        if request.first_token_at and request.submitted_at:
            ttft_us = int((request.first_token_at - request.submitted_at) * 1_000_000)

        if request.completed_at and request.submitted_at:
            e2e_latency_us = int((request.completed_at - request.submitted_at) * 1_000_000)

        if response.completion_tokens > 0 and request.first_token_at and request.completed_at:
            decode_time = request.completed_at - request.first_token_at
            tpot_us = int((decode_time / response.completion_tokens) * 1_000_000)

        # Calculate throughput
        tps = 0.0
        if request.completed_at and request.first_token_at:
            decode_time = request.completed_at - request.first_token_at
            if decode_time > 0:
                tps = response.completion_tokens / decode_time

        # Hardware snapshot
        hw_snapshot = None
        if self.hardware_collector:
            try:
                hw_snapshot = self.hardware_collector.get_statistics()
            except Exception:
                pass

        return BenchmarkResult(
            request_id=request.request_id,
            prompt=request.prompt,
            model=request.model,
            ttft_us=ttft_us,
            tpot_us=tpot_us,
            e2e_latency_us=e2e_latency_us,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
            tokens_per_second=tps,
            response_text=response.text,
            finish_reason=response.finish_reason,
            hardware_snapshot=hw_snapshot,
            metadata=request.metadata,
        )

    def pause(self):
        """Pause benchmark execution."""
        self._paused = True

    def resume(self):
        """Resume benchmark execution."""
        self._paused = False

    def cancel(self):
        """Cancel benchmark execution."""
        self._cancelled = True

    def get_results(self) -> List[BenchmarkResult]:
        """Get all benchmark results."""
        return self._queue.get_results()

    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return {
            "phase": self._phase.value,
            "progress": self.progress,
            "total_requests": self._total_requests,
            "completed": self._completed_requests,
            "failed": self._failed_requests,
            "running": self._queue.get_running_count(),
            "elapsed_seconds": self.elapsed_seconds,
            "phase_elapsed": time.time() - self._phase_start_time if self._phase_start_time else 0,
        }