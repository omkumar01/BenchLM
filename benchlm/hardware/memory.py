"""Memory monitoring for BenchLM."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import psutil

from benchlm.config import get_config


@dataclass
class MemorySample:
    """Single memory sample."""

    timestamp: float
    # RAM
    ram_total_mb: int
    ram_used_mb: int
    ram_available_mb: int
    ram_percent: float
    ram_free_mb: int
    ram_cached_mb: int
    ram_buffers_mb: int
    # Swap
    swap_total_mb: int
    swap_used_mb: int
    swap_free_mb: int
    swap_percent: float
    # Virtual memory (process)
    process_rss_mb: float
    process_vms_mb: float
    process_percent: float


@dataclass
class MemoryInfo:
    """Static memory information."""

    ram_total_mb: int
    swap_total_mb: int
    page_size_kb: int


class MemoryCollector:
    """Memory metrics collector using psutil."""

    def __init__(self):
        self._config = get_config().hardware
        self._memory_info: Optional[MemoryInfo] = None
        self._last_sample: Optional[MemorySample] = None
        self._sample_history: List[MemorySample] = []
        self._max_history = 10000
        self._process = psutil.Process()

    async def initialize(self):
        """Initialize memory collector."""
        self._memory_info = await self._get_memory_info()

    async def _get_memory_info(self) -> MemoryInfo:
        """Get static memory information."""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return MemoryInfo(
            ram_total_mb=mem.total // (1024 * 1024),
            swap_total_mb=swap.total // (1024 * 1024),
            page_size_kb=psutil.virtual_memory().pagesize // 1024 if hasattr(psutil.virtual_memory(), 'pagesize') else 4,
        )

    async def sample(self) -> MemorySample:
        """Take a single memory sample."""
        loop = asyncio.get_event_loop()

        def _collect():
            # System memory
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Process memory
            process_mem = self._process.memory_info()
            process_percent = self._process.memory_percent()

            return mem, swap, process_mem, process_percent

        mem, swap, process_mem, process_percent = await loop.run_in_executor(None, _collect)

        sample = MemorySample(
            timestamp=time.time(),
            ram_total_mb=mem.total // (1024 * 1024),
            ram_used_mb=mem.used // (1024 * 1024),
            ram_available_mb=mem.available // (1024 * 1024),
            ram_percent=mem.percent,
            ram_free_mb=mem.free // (1024 * 1024),
            ram_cached_mb=getattr(mem, 'cached', 0) // (1024 * 1024),
            ram_buffers_mb=getattr(mem, 'buffers', 0) // (1024 * 1024),
            swap_total_mb=swap.total // (1024 * 1024),
            swap_used_mb=swap.used // (1024 * 1024),
            swap_free_mb=swap.free // (1024 * 1024),
            swap_percent=swap.percent,
            process_rss_mb=process_mem.rss / (1024 * 1024),
            process_vms_mb=process_mem.vms / (1024 * 1024),
            process_percent=process_percent,
        )

        self._last_sample = sample
        self._sample_history.append(sample)

        if len(self._sample_history) > self._max_history:
            self._sample_history = self._sample_history[-self._max_history:]

        return sample

    def get_memory_info(self) -> Optional[MemoryInfo]:
        """Get static memory info."""
        return self._memory_info

    def get_last_sample(self) -> Optional[MemorySample]:
        """Get last sample."""
        return self._last_sample

    def get_history(self, count: int = 100) -> List[MemorySample]:
        """Get sample history."""
        return self._sample_history[-count:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get memory statistics."""
        if not self._sample_history:
            return {}

        samples = self._sample_history[-1000:]

        ram_percents = [s.ram_percent for s in samples]
        ram_used = [s.ram_used_mb for s in samples]
        swap_percents = [s.swap_percent for s in samples]
        process_rss = [s.process_rss_mb for s in samples]

        return {
            "ram": {
                "total_mb": samples[-1].ram_total_mb,
                "current_used_mb": ram_used[-1],
                "current_percent": ram_percents[-1],
                "average_used_mb": sum(ram_used) / len(ram_used),
                "average_percent": sum(ram_percents) / len(ram_percents),
                "peak_used_mb": max(ram_used),
                "peak_percent": max(ram_percents),
                "available_mb": samples[-1].ram_available_mb,
            },
            "swap": {
                "total_mb": samples[-1].swap_total_mb,
                "current_used_mb": samples[-1].swap_used_mb,
                "current_percent": swap_percents[-1],
                "average_percent": sum(swap_percents) / len(swap_percents),
                "peak_percent": max(swap_percents),
            },
            "process": {
                "current_rss_mb": process_rss[-1],
                "average_rss_mb": sum(process_rss) / len(process_rss),
                "peak_rss_mb": max(process_rss),
                "current_percent": samples[-1].process_percent,
            },
            "sample_count": len(samples),
        }

    async def close(self):
        """Clean up."""
        self._sample_history.clear()