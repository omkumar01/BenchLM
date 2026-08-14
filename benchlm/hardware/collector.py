"""Unified hardware collector for BenchLM."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Set
from collections import defaultdict
from datetime import datetime

from benchlm.hardware.cpu import CPUCollector, CPUSample, CPUInfo
from benchlm.hardware.gpu import GPUCollector, GPUSample, GPUInfo
from benchlm.hardware.memory import MemoryCollector, MemorySample, MemoryInfo
from benchlm.hardware.disk import DiskCollector, DiskSample, DiskInfo
from benchlm.hardware.battery import BatteryCollector, BatterySample, BatteryInfo
from benchlm.hardware.temperature import TemperatureCollector, TemperatureSample, TemperatureInfo
from benchlm.config import get_config


@dataclass
class HardwareSnapshot:
    """Unified hardware snapshot at a point in time."""

    timestamp: float
    timestamp_iso: str
    cpu: Optional[CPUSample] = None
    gpus: List[GPUSample] = field(default_factory=list)
    memory: Optional[MemorySample] = None
    disk: Optional[DiskSample] = None
    battery: Optional[BatterySample] = None
    temperature: Optional[TemperatureSample] = None

    # Benchmark context
    benchmark_run_id: Optional[int] = None
    benchmark_phase: str = "idle"  # idle, warmup, running, cooldown
    tokens_generated: int = 0
    current_tps: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "timestamp": self.timestamp,
            "timestamp_iso": self.timestamp_iso,
            "cpu": self.cpu.__dict__ if self.cpu else None,
            "gpus": [gpu.__dict__ for gpu in self.gpus],
            "memory": self.memory.__dict__ if self.memory else None,
            "disk": self.disk.__dict__ if self.disk else None,
            "battery": self.battery.__dict__ if self.battery else None,
            "temperature": self.temperature.__dict__ if self.temperature else None,
            "benchmark_run_id": self.benchmark_run_id,
            "benchmark_phase": self.benchmark_phase,
            "tokens_generated": self.tokens_generated,
            "current_tps": self.current_tps,
        }


class RingBuffer:
    """Thread-safe ring buffer for hardware samples."""

    def __init__(self, max_size: int = 100000):
        self._max_size = max_size
        self._buffer: List[HardwareSnapshot] = []
        self._index = 0
        self._full = False
        self._lock = asyncio.Lock()

    async def append(self, item: HardwareSnapshot):
        """Add item to buffer."""
        async with self._lock:
            if len(self._buffer) < self._max_size:
                self._buffer.append(item)
            else:
                self._buffer[self._index] = item
                self._index = (self._index + 1) % self._max_size
                self._full = True

    async def get_recent(self, count: int) -> List[HardwareSnapshot]:
        """Get most recent items."""
        async with self._lock:
            if not self._buffer:
                return []

            if self._full:
                # Buffer is full, items are in order from _index
                result = self._buffer[self._index:] + self._buffer[:self._index]
            else:
                result = self._buffer[:]

            return result[-count:]

    async def get_all(self) -> List[HardwareSnapshot]:
        """Get all items in chronological order."""
        async with self._lock:
            if self._full:
                return self._buffer[self._index:] + self._buffer[:self._index]
            return self._buffer[:]

    async def clear(self):
        """Clear buffer."""
        async with self._lock:
            self._buffer.clear()
            self._index = 0
            self._full = False

    def __len__(self) -> int:
        return len(self._buffer)


class HardwareCollector:
    """Unified hardware metrics collector with configurable polling."""

    def __init__(self):
        self._config = get_config().hardware
        self._ui_config = get_config().ui

        # Sub-collectors
        self._cpu = CPUCollector()
        self._gpu = GPUCollector()
        self._memory = MemoryCollector()
        self._disk = DiskCollector()
        self._battery = BatteryCollector()
        self._temperature = TemperatureCollector()

        # State
        self._running = False
        self._poll_task: Optional[asyncio.Task] = None
        self._snapshot_buffer = RingBuffer(self._config.sample_history_size)

        # Callbacks
        self._callbacks: Set[Callable[[HardwareSnapshot], Any]] = set()

        # Benchmark context
        self._benchmark_run_id: Optional[int] = None
        self._benchmark_phase: str = "idle"
        self._tokens_generated: int = 0
        self._current_tps: float = 0.0

        # Last samples for quick access
        self._last_snapshot: Optional[HardwareSnapshot] = None

    async def initialize(self):
        """Initialize all sub-collectors."""
        await asyncio.gather(
            self._cpu.initialize(),
            self._gpu.initialize(),
            self._memory.initialize(),
            self._disk.initialize(),
            self._battery.initialize(),
            self._temperature.initialize(),
        )

    def register_callback(self, callback: Callable[[HardwareSnapshot], Any]):
        """Register a callback for hardware updates."""
        self._callbacks.add(callback)

    def unregister_callback(self, callback: Callable[[HardwareSnapshot], Any]):
        """Unregister a callback."""
        self._callbacks.discard(callback)

    def set_benchmark_context(
        self,
        run_id: Optional[int] = None,
        phase: str = "idle",
        tokens: int = 0,
        tps: float = 0.0,
    ):
        """Set benchmark context for snapshots."""
        self._benchmark_run_id = run_id
        self._benchmark_phase = phase
        self._tokens_generated = tokens
        self._current_tps = tps

    async def start_polling(self):
        """Start hardware polling loop."""
        if self._running:
            return

        self._running = True
        self._poll_task = asyncio.create_task(self._polling_loop())

    async def stop_polling(self):
        """Stop hardware polling loop."""
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass

    async def _polling_loop(self):
        """Main polling loop."""
        hw_interval = self._ui_config.hardware_poll_interval / 1000.0
        temp_interval = self._ui_config.temperature_poll_interval / 1000.0
        power_interval = self._ui_config.power_poll_interval / 1000.0

        last_temp = 0.0
        last_power = 0.0

        while self._running:
            start = time.perf_counter()

            try:
                await self._collect_snapshot(
                    collect_temp=(time.time() - last_temp) >= temp_interval,
                    collect_power=(time.time() - last_power) >= power_interval,
                )

                if (time.time() - last_temp) >= temp_interval:
                    last_temp = time.time()
                if (time.time() - last_power) >= power_interval:
                    last_power = time.time()

            except Exception as e:
                # Log error but continue polling
                print(f"Hardware polling error: {e}")

            # Sleep to maintain interval
            elapsed = time.perf_counter() - start
            sleep_time = max(0, hw_interval - elapsed)
            await asyncio.sleep(sleep_time)

    async def _collect_snapshot(
        self,
        collect_temp: bool = True,
        collect_power: bool = True,
    ) -> HardwareSnapshot:
        """Collect a single hardware snapshot."""
        timestamp = time.time()
        timestamp_iso = datetime.fromtimestamp(timestamp).isoformat()

        # Collect all metrics concurrently
        cpu_task = self._cpu.sample()
        gpu_task = self._gpu.sample()
        memory_task = self._memory.sample()
        disk_task = self._disk.sample()
        battery_task = self._battery.sample()

        # Wait for core metrics
        cpu_sample, gpu_samples, memory_sample, disk_sample, battery_sample = await asyncio.gather(
            cpu_task, gpu_task, memory_task, disk_task, battery_task,
            return_exceptions=True,
        )

        # Handle exceptions
        if isinstance(cpu_sample, Exception):
            cpu_sample = None
        if isinstance(gpu_samples, Exception):
            gpu_samples = []
        if isinstance(memory_sample, Exception):
            memory_sample = None
        if isinstance(disk_sample, Exception):
            disk_sample = None
        if isinstance(battery_sample, Exception):
            battery_sample = None

        # Collect temperature if needed
        temp_sample = None
        if collect_temp:
            try:
                temp_sample = await self._temperature.sample()
            except Exception:
                pass

        # Create snapshot
        snapshot = HardwareSnapshot(
            timestamp=timestamp,
            timestamp_iso=timestamp_iso,
            cpu=cpu_sample,
            gpus=gpu_samples,
            memory=memory_sample,
            disk=disk_sample,
            battery=battery_sample,
            temperature=temp_sample,
            benchmark_run_id=self._benchmark_run_id,
            benchmark_phase=self._benchmark_phase,
            tokens_generated=self._tokens_generated,
            current_tps=self._current_tps,
        )

        # Store and notify
        await self._snapshot_buffer.append(snapshot)
        self._last_snapshot = snapshot

        # Notify callbacks
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(snapshot)
                else:
                    callback(snapshot)
            except Exception:
                pass

        return snapshot

    async def get_snapshot(self) -> Optional[HardwareSnapshot]:
        """Get the latest snapshot."""
        return self._last_snapshot

    async def get_recent(self, count: int = 100) -> List[HardwareSnapshot]:
        """Get recent snapshots."""
        return await self._snapshot_buffer.get_recent(count)

    async def get_all(self) -> List[HardwareSnapshot]:
        """Get all snapshots."""
        return await self._snapshot_buffer.get_all()

    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregated statistics from all collectors."""
        return {
            "cpu": self._cpu.get_statistics(),
            "gpu": {str(i): self._gpu.get_statistics(i) for i in range(len(self._gpu.get_gpu_infos()))},
            "memory": self._memory.get_statistics(),
            "disk": self._disk.get_statistics(),
            "battery": self._battery.get_statistics(),
            "temperature": self._temperature.get_statistics(),
        }

    def get_static_info(self) -> Dict[str, Any]:
        """Get static hardware information."""
        return {
            "cpu": self._cpu.get_cpu_info().__dict__ if self._cpu.get_cpu_info() else None,
            "gpus": [info.__dict__ for info in self._gpu.get_gpu_infos()],
            "memory": self._memory.get_memory_info().__dict__ if self._memory.get_memory_info() else None,
            "disks": [info.__dict__ for info in self._disk.get_disk_infos()],
            "battery": self._battery.get_battery_info().__dict__ if self._battery.get_battery_info() else None,
            "temperature_sensors": self._temperature.get_temperature_info().__dict__ if self._temperature.get_temperature_info() else None,
        }

    def is_running(self) -> bool:
        """Check if collector is running."""
        return self._running

    async def close(self):
        """Stop polling and clean up."""
        await self.stop_polling()
        await asyncio.gather(
            self._cpu.close(),
            self._gpu.close(),
            self._memory.close(),
            self._disk.close(),
            self._battery.close(),
            self._temperature.close(),
        )
        await self._snapshot_buffer.clear()


# Global collector instance
_collector: Optional[HardwareCollector] = None


def get_hardware_collector() -> HardwareCollector:
    """Get the global hardware collector."""
    global _collector
    if _collector is None:
        _collector = HardwareCollector()
    return _collector


async def initialize_hardware_collector() -> HardwareCollector:
    """Initialize and start hardware collector."""
    collector = get_hardware_collector()
    await collector.initialize()
    await collector.start_polling()
    return collector


async def close_hardware_collector():
    """Close hardware collector."""
    global _collector
    if _collector:
        await _collector.close()
        _collector = None