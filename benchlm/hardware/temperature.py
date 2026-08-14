"""Temperature monitoring for BenchLM."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import psutil

from benchlm.config import get_config


@dataclass
class TemperatureSample:
    """Single temperature sample."""

    timestamp: float
    # CPU temperatures
    cpu_package_celsius: Optional[float] = None
    cpu_core_celsius: List[float] = None
    # GPU temperatures (from GPU collector)
    gpu_core_celsius: Optional[float] = None
    gpu_hotspot_celsius: Optional[float] = None
    gpu_vram_celsius: Optional[float] = None
    # Other
    motherboard_celsius: Optional[float] = None
    nvme_celsius: Optional[float] = None
    # All sensors
    all_sensors: Dict[str, float] = None


@dataclass
class TemperatureInfo:
    """Static temperature sensor information."""

    sensors: List[Dict[str, Any]] = None


class TemperatureCollector:
    """Temperature metrics collector using psutil."""

    def __init__(self):
        self._config = get_config().hardware
        self._temp_info: Optional[TemperatureInfo] = None
        self._last_sample: Optional[TemperatureSample] = None
        self._sample_history: List[TemperatureSample] = []
        self._max_history = 10000

    async def initialize(self):
        """Initialize temperature collector."""
        self._temp_info = await self._get_temperature_info()

    async def _get_temperature_info(self) -> TemperatureInfo:
        """Get available temperature sensors."""
        sensors = []
        try:
            temps = psutil.sensors_temperatures()
            for name, entries in temps.items():
                for entry in entries:
                    sensors.append({
                        "name": f"{name}_{entry.label or 'unknown'}",
                        "source": name,
                        "label": entry.label,
                        "critical": entry.critical,
                        "high": entry.high,
                    })
        except Exception:
            pass

        return TemperatureInfo(sensors=sensors)

    async def sample(self) -> TemperatureSample:
        """Take a single temperature sample."""
        loop = asyncio.get_event_loop()

        def _collect():
            return psutil.sensors_temperatures()

        temps = await loop.run_in_executor(None, _collect)

        sample = TemperatureSample(
            timestamp=time.time(),
            cpu_core_celsius=[],
            all_sensors={},
        )

        if temps:
            for name, entries in temps.items():
                for entry in entries:
                    key = f"{name}_{entry.label or 'unknown'}"
                    sample.all_sensors[key] = entry.current

                    # Categorize temperatures
                    name_lower = name.lower()
                    label_lower = (entry.label or "").lower()

                    if any(kw in name_lower for kw in ["cpu", "core", "package", "k10temp", "coretemp"]):
                        if "package" in label_lower or "pkg" in label_lower:
                            sample.cpu_package_celsius = entry.current
                        else:
                            sample.cpu_core_celsius.append(entry.current)
                    elif any(kw in name_lower for kw in ["gpu", "nvidia", "amdgpu", "radeon"]):
                        if "hotspot" in label_lower or "junction" in label_lower:
                            sample.gpu_hotspot_celsius = entry.current
                        elif "vram" in label_lower or "memory" in label_lower:
                            sample.gpu_vram_celsius = entry.current
                        else:
                            sample.gpu_core_celsius = entry.current
                    elif "nvme" in name_lower:
                        sample.nvme_celsius = entry.current
                    elif any(kw in name_lower for kw in ["motherboard", "acpi", "sys", "board"]):
                        sample.motherboard_celsius = entry.current

        self._last_sample = sample
        self._sample_history.append(sample)

        if len(self._sample_history) > self._max_history:
            self._sample_history = self._sample_history[-self._max_history:]

        return sample

    def get_temperature_info(self) -> Optional[TemperatureInfo]:
        """Get static temperature info."""
        return self._temp_info

    def get_last_sample(self) -> Optional[TemperatureSample]:
        """Get last sample."""
        return self._last_sample

    def get_history(self, count: int = 100) -> List[TemperatureSample]:
        """Get sample history."""
        return self._sample_history[-count:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get temperature statistics."""
        if not self._sample_history:
            return {}

        samples = self._sample_history[-1000:]

        # Collect all sensor readings
        sensor_data: Dict[str, List[float]] = {}
        for s in samples:
            if s.all_sensors:
                for name, temp in s.all_sensors.items():
                    if name not in sensor_data:
                        sensor_data[name] = []
                    sensor_data[name].append(temp)

        result = {"sensors": {}}
        for name, values in sensor_data.items():
            result["sensors"][name] = {
                "current": values[-1],
                "average": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
            }

        # CPU package
        cpu_pkg = [s.cpu_package_celsius for s in samples if s.cpu_package_celsius]
        if cpu_pkg:
            result["cpu_package"] = {
                "current": cpu_pkg[-1],
                "average": sum(cpu_pkg) / len(cpu_pkg),
                "min": min(cpu_pkg),
                "max": max(cpu_pkg),
            }

        # GPU core
        gpu_core = [s.gpu_core_celsius for s in samples if s.gpu_core_celsius]
        if gpu_core:
            result["gpu_core"] = {
                "current": gpu_core[-1],
                "average": sum(gpu_core) / len(gpu_core),
                "min": min(gpu_core),
                "max": max(gpu_core),
            }

        return result

    async def close(self):
        """Clean up."""
        self._sample_history.clear()