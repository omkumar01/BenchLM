"""Hardware monitoring package for BenchLM."""

from benchlm.hardware.collector import (
    HardwareCollector,
    HardwareSnapshot,
    RingBuffer,
    get_hardware_collector,
    initialize_hardware_collector,
    close_hardware_collector,
)
from benchlm.hardware.cpu import CPUCollector, CPUSample, CPUInfo
from benchlm.hardware.gpu import GPUCollector, GPUSample, GPUInfo
from benchlm.hardware.memory import MemoryCollector, MemorySample, MemoryInfo
from benchlm.hardware.disk import DiskCollector, DiskSample, DiskInfo
from benchlm.hardware.battery import BatteryCollector, BatterySample, BatteryInfo
from benchlm.hardware.temperature import TemperatureCollector, TemperatureSample, TemperatureInfo

__all__ = [
    # Collector
    "HardwareCollector",
    "HardwareSnapshot",
    "RingBuffer",
    "get_hardware_collector",
    "initialize_hardware_collector",
    "close_hardware_collector",
    # CPU
    "CPUCollector",
    "CPUSample",
    "CPUInfo",
    # GPU
    "GPUCollector",
    "GPUSample",
    "GPUInfo",
    # Memory
    "MemoryCollector",
    "MemorySample",
    "MemoryInfo",
    # Disk
    "DiskCollector",
    "DiskSample",
    "DiskInfo",
    # Battery
    "BatteryCollector",
    "BatterySample",
    "BatteryInfo",
    # Temperature
    "TemperatureCollector",
    "TemperatureSample",
    "TemperatureInfo",
]