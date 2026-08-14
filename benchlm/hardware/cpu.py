"""CPU monitoring for BenchLM."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

import psutil

from benchlm.config import get_config


@dataclass
class CPUSample:
    """Single CPU sample."""

    timestamp: float
    total_percent: float
    per_core_percent: List[float]
    frequency_mhz: Optional[float] = None
    temperature_celsius: Optional[float] = None
    power_watts: Optional[float] = None
    load_average: Optional[List[float]] = None  # 1, 5, 15 min


@dataclass
class CPUInfo:
    """Static CPU information."""

    physical_cores: int
    logical_cores: int
    max_frequency_mhz: float
    min_frequency_mhz: float
    architecture: str
    vendor: str
    model_name: str
    cache_sizes: Dict[str, int] = field(default_factory=dict)


class CPUCollector:
    """CPU metrics collector using psutil."""

    def __init__(self):
        self._config = get_config().hardware
        self._cpu_info: Optional[CPUInfo] = None
        self._last_sample: Optional[CPUSample] = None
        self._sample_history: List[CPUSample] = []
        self._max_history = 10000

    async def initialize(self):
        """Initialize CPU collector."""
        self._cpu_info = await self._get_cpu_info()

    def _get_cpu_info(self) -> CPUInfo:
        """Get static CPU information."""
        cpu_freq = psutil.cpu_freq()
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_count_physical = psutil.cpu_count(logical=False)

        # Get detailed CPU info on Linux
        vendor = "Unknown"
        model_name = "Unknown"
        architecture = "Unknown"

        try:
            import platform
            architecture = platform.machine()

            # Try to read from /proc/cpuinfo on Linux
            if hasattr(psutil, "cpu_info"):
                info = psutil.cpu_info()
                vendor = info.get("vendor_id_raw", "Unknown")
                model_name = info.get("brand_raw", "Unknown")
        except Exception:
            pass

        return CPUInfo(
            physical_cores=cpu_count_physical or 1,
            logical_cores=cpu_count_logical or 1,
            max_frequency_mhz=cpu_freq.max if cpu_freq else 0.0,
            min_frequency_mhz=cpu_freq.min if cpu_freq else 0.0,
            architecture=architecture,
            vendor=vendor,
            model_name=model_name,
        )

    async def sample(self) -> CPUSample:
        """Take a single CPU sample."""
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()

        def _collect():
            # CPU percent (interval=None for non-blocking)
            total_percent = psutil.cpu_percent(interval=None)
            per_core = psutil.cpu_percent(interval=None, percpu=True)

            # Frequency
            freq = psutil.cpu_freq()
            frequency = freq.current if freq else None

            # Load average (Unix only)
            load_avg = None
            try:
                load_avg = list(psutil.getloadavg())
            except Exception:
                pass

            return total_percent, per_core, frequency, load_avg

        total_percent, per_core, frequency, load_avg = await loop.run_in_executor(None, _collect)

        # Temperature (platform specific)
        temperature = await self._get_temperature()
        power = await self._get_power()

        sample = CPUSample(
            timestamp=time.time(),
            total_percent=total_percent,
            per_core_percent=per_core,
            frequency_mhz=frequency,
            temperature_celsius=temperature,
            power_watts=power,
            load_average=load_avg,
        )

        self._last_sample = sample
        self._sample_history.append(sample)

        # Trim history
        if len(self._sample_history) > self._max_history:
            self._sample_history = self._sample_history[-self._max_history:]

        return sample

    async def _get_temperature(self) -> Optional[float]:
        """Get CPU temperature."""
        try:
            # psutil sensors_temperatures (Linux)
            temps = psutil.sensors_temperatures()
            if not temps:
                return None

            # Look for CPU package temperature
            for name, entries in temps.items():
                name_lower = name.lower()
                if any(keyword in name_lower for keyword in ["cpu", "core", "package", "k10temp", "coretemp"]):
                    for entry in entries:
                        if entry.current > 0:
                            return entry.current

            # Fallback: return first available temperature
            for entries in temps.values():
                for entry in entries:
                    if entry.current > 0:
                        return entry.current

        except Exception:
            pass

        return None

    async def _get_power(self) -> Optional[float]:
        """Get CPU power consumption (RAPL on Linux)."""
        try:
            # Try to read from RAPL interface
            import os
            rapl_paths = [
                "/sys/class/powercap/intel-rapl:0/energy_uj",
                "/sys/class/powercap/intel-rapl:0/intel-rapl:0:0/energy_uj",
            ]

            for path in rapl_paths:
                if os.path.exists(path):
                    with open(path, "r") as f:
                        energy_uj = int(f.read().strip())
                    # This is cumulative, would need previous reading for power
                    # For now, return None - would need continuous monitoring
                    return None
        except Exception:
            pass

        return None

    def get_cpu_info(self) -> Optional[CPUInfo]:
        """Get static CPU info."""
        return self._cpu_info

    def get_last_sample(self) -> Optional[CPUSample]:
        """Get last sample."""
        return self._last_sample

    def get_history(self, count: int = 100) -> List[CPUSample]:
        """Get sample history."""
        return self._sample_history[-count:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get CPU statistics from history."""
        if not self._sample_history:
            return {}

        samples = self._sample_history[-1000:]  # Last 1000 samples

        total_percents = [s.total_percent for s in samples]
        per_core = list(zip(*[s.per_core_percent for s in samples])) if samples[0].per_core_percent else []

        return {
            "total": {
                "current": total_percents[-1] if total_percents else 0,
                "average": sum(total_percents) / len(total_percents) if total_percents else 0,
                "min": min(total_percents) if total_percents else 0,
                "max": max(total_percents) if total_percents else 0,
            },
            "per_core": [
                {
                    "current": core[-1] if core else 0,
                    "average": sum(core) / len(core) if core else 0,
                    "min": min(core) if core else 0,
                    "max": max(core) if core else 0,
                }
                for core in per_core
            ],
            "sample_count": len(samples),
        }

    async def close(self):
        """Clean up."""
        self._sample_history.clear()