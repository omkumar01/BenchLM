"""Battery monitoring for BenchLM."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import psutil

from benchlm.config import get_config


@dataclass
class BatterySample:
    """Single battery sample."""

    timestamp: float
    percent: float
    power_watts: Optional[float] = None
    charging: bool = False
    plugged_in: bool = False
    time_remaining_seconds: Optional[float] = None
    capacity_full_mwh: Optional[float] = None
    capacity_design_mwh: Optional[float] = None
    voltage_v: Optional[float] = None
    current_ma: Optional[float] = None
    temperature_celsius: Optional[float] = None
    status: str = "unknown"  # charging, discharging, full, unknown


@dataclass
class BatteryInfo:
    """Static battery information."""

    present: bool
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    serial_number: Optional[str] = None
    chemistry: Optional[str] = None
    design_capacity_mwh: Optional[float] = None
    full_capacity_mwh: Optional[float] = None
    voltage_v: Optional[float] = None


class BatteryCollector:
    """Battery metrics collector using psutil."""

    def __init__(self):
        self._config = get_config().hardware
        self._battery_info: Optional[BatteryInfo] = None
        self._last_sample: Optional[BatterySample] = None
        self._sample_history: List[BatterySample] = []
        self._max_history = 10000
        self._has_battery = False

    async def initialize(self):
        """Initialize battery collector."""
        self._has_battery = psutil.sensors_battery() is not None
        if self._has_battery:
            self._battery_info = await self._get_battery_info()

    async def _get_battery_info(self) -> BatteryInfo:
        """Get static battery information."""
        # psutil doesn't provide detailed battery info
        # This would require platform-specific code (WMI on Windows, sysfs on Linux)
        return BatteryInfo(present=True)

    async def sample(self) -> Optional[BatterySample]:
        """Take a single battery sample."""
        if not self._has_battery:
            return None

        loop = asyncio.get_event_loop()

        def _collect():
            return psutil.sensors_battery()

        battery = await loop.run_in_executor(None, _collect)

        if battery is None:
            return None

        sample = BatterySample(
            timestamp=time.time(),
            percent=battery.percent,
            power_watts=None,  # Not provided by psutil
            charging=battery.power_plugged,
            plugged_in=battery.power_plugged,
            time_remaining_seconds=battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None,
            status="charging" if battery.power_plugged else "discharging",
        )

        self._last_sample = sample
        self._sample_history.append(sample)

        if len(self._sample_history) > self._max_history:
            self._sample_history = self._sample_history[-self._max_history:]

        return sample

    def has_battery(self) -> bool:
        """Check if battery is present."""
        return self._has_battery

    def get_battery_info(self) -> Optional[BatteryInfo]:
        """Get static battery info."""
        return self._battery_info

    def get_last_sample(self) -> Optional[BatterySample]:
        """Get last sample."""
        return self._last_sample

    def get_history(self, count: int = 100) -> List[BatterySample]:
        """Get sample history."""
        return self._sample_history[-count:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get battery statistics."""
        if not self._sample_history:
            return {}

        samples = self._sample_history[-1000:]

        percents = [s.percent for s in samples]

        return {
            "current_percent": percents[-1] if percents else 0,
            "average_percent": sum(percents) / len(percents) if percents else 0,
            "min_percent": min(percents) if percents else 0,
            "max_percent": max(percents) if percents else 0,
            "charging": samples[-1].charging if samples else False,
            "plugged_in": samples[-1].plugged_in if samples else False,
            "time_remaining_hours": samples[-1].time_remaining_seconds / 3600 if samples and samples[-1].time_remaining_seconds else None,
            "sample_count": len(samples),
        }

    async def close(self):
        """Clean up."""
        self._sample_history.clear()