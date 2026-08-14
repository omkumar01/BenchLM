"""Disk I/O monitoring for BenchLM."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import psutil

from benchlm.config import get_config


@dataclass
class DiskSample:
    """Single disk I/O sample."""

    timestamp: float
    read_bytes_per_sec: float
    write_bytes_per_sec: float
    read_count_per_sec: float
    write_count_per_sec: float
    read_time_ms: float
    write_time_ms: float
    busy_time_ms: float
    # Per-disk
    disks: Dict[str, Dict[str, float]] = None


@dataclass
class DiskInfo:
    """Static disk information."""

    device: str
    mountpoint: str
    fstype: str
    total_gb: float
    used_gb: float
    free_gb: float
    percent: float


class DiskCollector:
    """Disk I/O metrics collector using psutil."""

    def __init__(self):
        self._config = get_config().hardware
        self._disk_infos: List[DiskInfo] = []
        self._last_io_counters = None
        self._last_time = 0.0
        self._last_sample: Optional[DiskSample] = None
        self._sample_history: List[DiskSample] = []
        self._max_history = 10000

    async def initialize(self):
        """Initialize disk collector."""
        self._disk_infos = await self._get_disk_info()
        # Get initial counters
        self._last_io_counters = psutil.disk_io_counters(perdisk=True)
        self._last_time = time.time()

    async def _get_disk_info(self) -> List[DiskInfo]:
        """Get static disk information."""
        infos = []
        partitions = psutil.disk_partitions(all=False)

        for part in partitions:
            try:
                usage = psutil.disk_usage(part.mountpoint)
                infos.append(DiskInfo(
                    device=part.device,
                    mountpoint=part.mountpoint,
                    fstype=part.fstype,
                    total_gb=usage.total / (1024**3),
                    used_gb=usage.used / (1024**3),
                    free_gb=usage.free / (1024**3),
                    percent=usage.percent,
                ))
            except Exception:
                continue

        return infos

    async def sample(self) -> DiskSample:
        """Take a single disk I/O sample."""
        loop = asyncio.get_event_loop()

        def _collect():
            return psutil.disk_io_counters(perdisk=True)

        io_counters = await loop.run_in_executor(None, _collect)
        current_time = time.time()

        sample = DiskSample(
            timestamp=current_time,
            read_bytes_per_sec=0,
            write_bytes_per_sec=0,
            read_count_per_sec=0,
            write_count_per_sec=0,
            read_time_ms=0,
            write_time_ms=0,
            busy_time_ms=0,
            disks={},
        )

        if self._last_io_counters and io_counters:
            dt = current_time - self._last_time
            if dt > 0:
                total_read_bytes = 0
                total_write_bytes = 0
                total_read_count = 0
                total_write_count = 0
                total_read_time = 0
                total_write_time = 0
                total_busy_time = 0

                for disk_name, counters in io_counters.items():
                    last_counters = self._last_io_counters.get(disk_name)
                    if not last_counters:
                        continue

                    read_bytes = (counters.read_bytes - last_counters.read_bytes) / dt
                    write_bytes = (counters.write_bytes - last_counters.write_bytes) / dt
                    read_count = (counters.read_count - last_counters.read_count) / dt
                    write_count = (counters.write_count - last_counters.write_count) / dt
                    read_time = (counters.read_time - last_counters.read_time) / dt
                    write_time = (counters.write_time - last_counters.write_time) / dt

                    # Busy time (if available)
                    busy_time = 0
                    if hasattr(counters, 'busy_time') and hasattr(last_counters, 'busy_time'):
                        busy_time = (counters.busy_time - last_counters.busy_time) / dt

                    total_read_bytes += read_bytes
                    total_write_bytes += write_bytes
                    total_read_count += read_count
                    total_write_count += write_count
                    total_read_time += read_time
                    total_write_time += write_time
                    total_busy_time += busy_time

                    sample.disks[disk_name] = {
                        "read_bytes_per_sec": read_bytes,
                        "write_bytes_per_sec": write_bytes,
                        "read_count_per_sec": read_count,
                        "write_count_per_sec": write_count,
                        "read_time_ms_per_sec": read_time,
                        "write_time_ms_per_sec": write_time,
                        "busy_time_ms_per_sec": busy_time,
                    }

                sample.read_bytes_per_sec = total_read_bytes
                sample.write_bytes_per_sec = total_write_bytes
                sample.read_count_per_sec = total_read_count
                sample.write_count_per_sec = total_write_count
                sample.read_time_ms = total_read_time
                sample.write_time_ms = total_write_time
                sample.busy_time_ms = total_busy_time

        self._last_io_counters = io_counters
        self._last_time = current_time
        self._last_sample = sample
        self._sample_history.append(sample)

        if len(self._sample_history) > self._max_history:
            self._sample_history = self._sample_history[-self._max_history:]

        return sample

    def get_disk_infos(self) -> List[DiskInfo]:
        """Get static disk info."""
        return self._disk_infos

    def get_last_sample(self) -> Optional[DiskSample]:
        """Get last sample."""
        return self._last_sample

    def get_history(self, count: int = 100) -> List[DiskSample]:
        """Get sample history."""
        return self._sample_history[-count:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get disk statistics."""
        if not self._sample_history:
            return {}

        samples = self._sample_history[-1000:]

        read_bytes = [s.read_bytes_per_sec for s in samples]
        write_bytes = [s.write_bytes_per_sec for s in samples]
        read_counts = [s.read_count_per_sec for s in samples]
        write_counts = [s.write_count_per_sec for s in samples]

        return {
            "read": {
                "current_mb_s": read_bytes[-1] / (1024**2) if read_bytes else 0,
                "average_mb_s": sum(read_bytes) / len(read_bytes) / (1024**2) if read_bytes else 0,
                "peak_mb_s": max(read_bytes) / (1024**2) if read_bytes else 0,
                "current_iops": read_counts[-1] if read_counts else 0,
                "average_iops": sum(read_counts) / len(read_counts) if read_counts else 0,
            },
            "write": {
                "current_mb_s": write_bytes[-1] / (1024**2) if write_bytes else 0,
                "average_mb_s": sum(write_bytes) / len(write_bytes) / (1024**2) if write_bytes else 0,
                "peak_mb_s": max(write_bytes) / (1024**2) if write_bytes else 0,
                "current_iops": write_counts[-1] if write_counts else 0,
                "average_iops": sum(write_counts) / len(write_counts) if write_counts else 0,
            },
            "disks": {
                disk: {
                    "read_mb_s": sum(s.disks.get(disk, {}).get("read_bytes_per_sec", 0) for s in samples[-100:]) / 100 / (1024**2),
                    "write_mb_s": sum(s.disks.get(disk, {}).get("write_bytes_per_sec", 0) for s in samples[-100:]) / 100 / (1024**2),
                }
                for disk in self._sample_history[-1].disks.keys() if self._sample_history
            },
            "sample_count": len(samples),
        }

    async def close(self):
        """Clean up."""
        self._sample_history.clear()