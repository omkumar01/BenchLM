"""GPU monitoring for BenchLM (NVIDIA, AMD, Intel)."""

from __future__ import annotations

import asyncio
import subprocess
import time
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from benchlm.config import get_config


@dataclass
class GPUSample:
    """Single GPU sample."""

    timestamp: float
    gpu_index: int
    name: str
    utilization_percent: float
    memory_used_mb: int
    memory_total_mb: int
    memory_percent: float
    temperature_celsius: Optional[float] = None
    power_watts: Optional[float] = None
    power_limit_watts: Optional[float] = None
    fan_speed_percent: Optional[float] = None
    clock_mhz: Optional[int] = None
    memory_clock_mhz: Optional[int] = None
    encoder_util_percent: Optional[float] = None
    decoder_util_percent: Optional[float] = None
    voltage_mv: Optional[float] = None


@dataclass
class GPUInfo:
    """Static GPU information."""

    index: int
    name: str
    vendor: str
    driver_version: str
    vram_total_mb: int
    compute_capability: Optional[str] = None
    pcie_gen: Optional[int] = None
    pcie_width: Optional[int] = None


class GPUCollector:
    """GPU metrics collector supporting NVIDIA, AMD, and Intel."""

    def __init__(self):
        self._config = get_config().hardware
        self._gpu_infos: List[GPUInfo] = []
        self._last_samples: Dict[int, GPUSample] = {}
        self._sample_history: Dict[int, List[GPUSample]] = {}
        self._max_history = 10000

        # Backend availability
        self._pynvml_available = False
        self._rocm_smi_available = False
        self._intel_gpu_top_available = False
        self._nvidia_smi_available = False

    async def initialize(self):
        """Initialize GPU collector and detect available backends."""
        await self._detect_backends()
        await self._load_gpu_info()

    async def _detect_backends(self):
        """Detect available GPU monitoring backends."""
        # Check pynvml (NVIDIA)
        try:
            import pynvml
            pynvml.nvmlInit()
            self._pynvml_available = True
        except Exception:
            self._pynvml_available = False

        # Check nvidia-smi
        try:
            result = await asyncio.create_subprocess_exec(
                "nvidia-smi", "--version",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await result.wait()
            self._nvidia_smi_available = result.returncode == 0
        except Exception:
            self._nvidia_smi_available = False

        # Check rocm-smi (AMD)
        try:
            result = await asyncio.create_subprocess_exec(
                "rocm-smi", "--version",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await result.wait()
            self._rocm_smi_available = result.returncode == 0
        except Exception:
            self._rocm_smi_available = False

        # Check intel-gpu-top
        try:
            result = await asyncio.create_subprocess_exec(
                "intel-gpu-top", "--version",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await result.wait()
            self._intel_gpu_top_available = result.returncode == 0
        except Exception:
            self._intel_gpu_top_available = False

    async def _load_gpu_info(self):
        """Load static GPU information."""
        self._gpu_infos = []

        # Try NVIDIA first
        if self._pynvml_available:
            try:
                infos = await self._load_nvidia_info()
                self._gpu_infos.extend(infos)
            except Exception:
                pass

        # Try AMD if no NVIDIA
        if not self._gpu_infos and self._rocm_smi_available:
            try:
                infos = await self._load_amd_info()
                self._gpu_infos.extend(infos)
            except Exception:
                pass

        # Try Intel
        if not self._gpu_infos and self._intel_gpu_top_available:
            try:
                infos = await self._load_intel_info()
                self._gpu_infos.extend(infos)
            except Exception:
                pass

        # Initialize history for each GPU
        for info in self._gpu_infos:
            self._sample_history[info.index] = []

    async def _load_nvidia_info(self) -> List[GPUInfo]:
        """Load NVIDIA GPU info via pynvml."""
        import pynvml

        infos = []
        device_count = pynvml.nvmlDeviceGetCount()

        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle).decode("utf-8")
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            driver_version = pynvml.nvmlSystemGetDriverVersion().decode("utf-8")

            # Get compute capability
            try:
                major, minor = pynvml.nvmlDeviceGetCudaComputeCapability(handle)
                compute_cap = f"{major}.{minor}"
            except Exception:
                compute_cap = None

            # Get PCIe info
            try:
                pcie_info = pynvml.nvmlDeviceGetPcieThroughput(handle)
                pcie_gen = pcie_info.max_speed if pcie_info else None
                pcie_width = pcie_info.max_width if pcie_info else None
            except Exception:
                pcie_gen = None
                pcie_width = None

            infos.append(GPUInfo(
                index=i,
                name=name,
                vendor="NVIDIA",
                driver_version=driver_version,
                vram_total_mb=mem_info.total // (1024 * 1024),
                compute_capability=compute_cap,
                pcie_gen=pcie_gen,
                pcie_width=pcie_width,
            ))

        return infos

    async def _load_amd_info(self) -> List[GPUInfo]:
        """Load AMD GPU info via rocm-smi."""
        infos = []

        try:
            result = await asyncio.create_subprocess_exec(
                "rocm-smi", "--showproductname", "--showvram", "--showdriverversion", "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await result.communicate()

            if result.returncode == 0:
                import json
                data = json.loads(stdout.decode())

                for gpu_id, gpu_data in data.items():
                    if gpu_id.startswith("card"):
                        index = int(gpu_id.replace("card", ""))
                        name = gpu_data.get("Product Name", "AMD GPU")
                        vram_str = gpu_data.get("VRAM Total Memory (B)", "0")
                        vram_bytes = int(vram_str) if vram_str.isdigit() else 0
                        driver = gpu_data.get("Driver Version", "Unknown")

                        infos.append(GPUInfo(
                            index=index,
                            name=name,
                            vendor="AMD",
                            driver_version=driver,
                            vram_total_mb=vram_bytes // (1024 * 1024),
                        ))
        except Exception:
            pass

        return infos

    async def _load_intel_info(self) -> List[GPUInfo]:
        """Load Intel GPU info."""
        infos = []

        try:
            # Intel GPU info is limited via intel-gpu-top
            # Would need to parse output or use sysfs
            # For now, return empty
            pass
        except Exception:
            pass

        return infos

    async def sample(self) -> List[GPUSample]:
        """Take GPU samples from all available GPUs."""
        samples = []

        # Try NVIDIA via pynvml
        if self._pynvml_available:
            try:
                nvidia_samples = await self._sample_nvidia()
                samples.extend(nvidia_samples)
            except Exception:
                pass

        # Try AMD via rocm-smi
        if self._rocm_smi_available and not samples:
            try:
                amd_samples = await self._sample_amd()
                samples.extend(amd_samples)
            except Exception:
                pass

        # Try Intel
        if self._intel_gpu_top_available and not samples:
            try:
                intel_samples = await self._sample_intel()
                samples.extend(intel_samples)
            except Exception:
                pass

        # Update history
        for sample in samples:
            self._last_samples[sample.gpu_index] = sample
            self._sample_history[sample.gpu_index].append(sample)

            # Trim history
            if len(self._sample_history[sample.gpu_index]) > self._max_history:
                self._sample_history[sample.gpu_index] = \
                    self._sample_history[sample.gpu_index][-self._max_history:]

        return samples

    async def _sample_nvidia(self) -> List[GPUSample]:
        """Sample NVIDIA GPUs via pynvml."""
        import pynvml

        samples = []
        device_count = pynvml.nvmlDeviceGetCount()

        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)

            # Utilization
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)

            # Memory
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)

            # Temperature
            try:
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            except Exception:
                temp = None

            # Power
            try:
                power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # mW to W
            except Exception:
                power = None

            # Power limit
            try:
                power_limit = pynvml.nvmlDeviceGetEnforcedPowerLimit(handle) / 1000.0
            except Exception:
                power_limit = None

            # Fan speed
            try:
                fan = pynvml.nvmlDeviceGetFanSpeed(handle)
            except Exception:
                fan = None

            # Clocks
            try:
                clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
                mem_clock = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
            except Exception:
                clock = None
                mem_clock = None

            # Encoder/Decoder utilization
            try:
                encoder = pynvml.nvmlDeviceGetEncoderUtilization(handle)[0]
                decoder = pynvml.nvmlDeviceGetDecoderUtilization(handle)[0]
            except Exception:
                encoder = None
                decoder = None

            # Name
            name = pynvml.nvmlDeviceGetName(handle).decode("utf-8")

            samples.append(GPUSample(
                timestamp=time.time(),
                gpu_index=i,
                name=name,
                utilization_percent=util.gpu,
                memory_used_mb=mem_info.used // (1024 * 1024),
                memory_total_mb=mem_info.total // (1024 * 1024),
                memory_percent=(mem_info.used / mem_info.total) * 100 if mem_info.total > 0 else 0,
                temperature_celsius=temp,
                power_watts=power,
                power_limit_watts=power_limit,
                fan_speed_percent=fan,
                clock_mhz=clock,
                memory_clock_mhz=mem_clock,
                encoder_util_percent=encoder,
                decoder_util_percent=decoder,
            ))

        return samples

    async def _sample_amd(self) -> List[GPUSample]:
        """Sample AMD GPUs via rocm-smi."""
        samples = []

        try:
            result = await asyncio.create_subprocess_exec(
                "rocm-smi",
                "--showuse", "--showmemuse", "--showtemp", "--showpower",
                "--showfan", "--showclk", "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await result.communicate()

            if result.returncode == 0:
                import json
                data = json.loads(stdout.decode())

                for gpu_id, gpu_data in data.items():
                    if gpu_id.startswith("card"):
                        index = int(gpu_id.replace("card", ""))

                        # Parse utilization
                        use_str = gpu_data.get("GPU Use (%)", "0%")
                        util = float(use_str.replace("%", "")) if use_str else 0.0

                        # Memory
                        vram_used_str = gpu_data.get("VRAM Used Memory (B)", "0")
                        vram_total_str = gpu_data.get("VRAM Total Memory (B)", "0")
                        vram_used = int(vram_used_str) if vram_used_str.isdigit() else 0
                        vram_total = int(vram_total_str) if vram_total_str.isdigit() else 0

                        # Temperature
                        temp_str = gpu_data.get("Temperature (C)", "")
                        temp = float(temp_str) if temp_str else None

                        # Power
                        power_str = gpu_data.get("Average Power (W)", "")
                        power = float(power_str) if power_str else None

                        # Fan
                        fan_str = gpu_data.get("Fan Speed (%)", "")
                        fan = float(fan_str.replace("%", "")) if fan_str else None

                        # Clocks
                        sclk_str = gpu_data.get("SCLK (MHz)", "")
                        mclk_str = gpu_data.get("MCLK (MHz)", "")
                        clock = int(sclk_str) if sclk_str.isdigit() else None
                        mem_clock = int(mclk_str) if mclk_str.isdigit() else None

                        # Name
                        name = gpu_data.get("Product Name", "AMD GPU")

                        samples.append(GPUSample(
                            timestamp=time.time(),
                            gpu_index=index,
                            name=name,
                            utilization_percent=util,
                            memory_used_mb=vram_used // (1024 * 1024),
                            memory_total_mb=vram_total // (1024 * 1024),
                            memory_percent=(vram_used / vram_total) * 100 if vram_total > 0 else 0,
                            temperature_celsius=temp,
                            power_watts=power,
                            fan_speed_percent=fan,
                            clock_mhz=clock,
                            memory_clock_mhz=mem_clock,
                        ))
        except Exception:
            pass

        return samples

    async def _sample_intel(self) -> List[GPUSample]:
        """Sample Intel GPUs via intel-gpu-top."""
        samples = []

        try:
            # intel-gpu-top JSON output
            result = await asyncio.create_subprocess_exec(
                "intel-gpu-top", "-J", "-s", "1000",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await result.communicate()

            if result.returncode == 0:
                import json
                data = json.loads(stdout.decode())

                # Parse intel-gpu-top output (structure varies)
                # This is a simplified parser
                for engine_class, engines in data.items():
                    if isinstance(engines, list):
                        for engine in engines:
                            if isinstance(engine, dict) and "busy" in engine:
                                # Create sample
                                samples.append(GPUSample(
                                    timestamp=time.time(),
                                    gpu_index=0,  # Intel typically single GPU
                                    name="Intel GPU",
                                    utilization_percent=engine.get("busy", 0) * 100,
                                    memory_used_mb=0,
                                    memory_total_mb=0,
                                    memory_percent=0,
                                ))
        except Exception:
            pass

        return samples

    async def sample_nvidia_smi(self) -> List[GPUSample]:
        """Sample NVIDIA GPUs via nvidia-smi (fallback)."""
        samples = []

        try:
            result = await asyncio.create_subprocess_exec(
                "nvidia-smi",
                "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw,power.limit,fan.speed,clocks.gr,clocks.mem,utilization.encoder,utilization.decoder",
                "--format=csv,noheader,nounits",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await result.communicate()

            if result.returncode == 0:
                lines = stdout.decode().strip().split("\n")
                for line in lines:
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 11:
                        index = int(parts[0])
                        name = parts[1]
                        util = float(parts[2]) if parts[2] else 0.0
                        mem_used = int(float(parts[3])) if parts[3] else 0
                        mem_total = int(float(parts[4])) if parts[4] else 0
                        temp = float(parts[5]) if parts[5] else None
                        power = float(parts[6]) if parts[6] else None
                        power_limit = float(parts[7]) if parts[7] else None
                        fan = float(parts[8]) if parts[8] else None
                        clock = int(float(parts[9])) if parts[9] else None
                        mem_clock = int(float(parts[10])) if parts[10] else None
                        encoder = float(parts[11]) if len(parts) > 11 and parts[11] else None
                        decoder = float(parts[12]) if len(parts) > 12 and parts[12] else None

                        samples.append(GPUSample(
                            timestamp=time.time(),
                            gpu_index=index,
                            name=name,
                            utilization_percent=util,
                            memory_used_mb=mem_used,
                            memory_total_mb=mem_total,
                            memory_percent=(mem_used / mem_total) * 100 if mem_total > 0 else 0,
                            temperature_celsius=temp,
                            power_watts=power,
                            power_limit_watts=power_limit,
                            fan_speed_percent=fan,
                            clock_mhz=clock,
                            memory_clock_mhz=mem_clock,
                            encoder_util_percent=encoder,
                            decoder_util_percent=decoder,
                        ))
        except Exception:
            pass

        return samples

    def get_gpu_infos(self) -> List[GPUInfo]:
        """Get static GPU information."""
        return self._gpu_infos

    def get_last_samples(self) -> Dict[int, GPUSample]:
        """Get last samples for all GPUs."""
        return self._last_samples

    def get_history(self, gpu_index: int, count: int = 100) -> List[GPUSample]:
        """Get sample history for a GPU."""
        return self._sample_history.get(gpu_index, [])[-count:]

    def get_statistics(self, gpu_index: int) -> Dict[str, Any]:
        """Get GPU statistics from history."""
        history = self._sample_history.get(gpu_index, [])
        if not history:
            return {}

        recent = history[-1000:]

        return {
            "utilization": {
                "current": recent[-1].utilization_percent if recent else 0,
                "average": sum(s.utilization_percent for s in recent) / len(recent),
                "min": min(s.utilization_percent for s in recent),
                "max": max(s.utilization_percent for s in recent),
            },
            "memory": {
                "current_used_mb": recent[-1].memory_used_mb if recent else 0,
                "current_percent": recent[-1].memory_percent if recent else 0,
                "average_used_mb": sum(s.memory_used_mb for s in recent) / len(recent),
                "average_percent": sum(s.memory_percent for s in recent) / len(recent),
                "peak_used_mb": max(s.memory_used_mb for s in recent),
                "peak_percent": max(s.memory_percent for s in recent),
            },
            "temperature": {
                "current": recent[-1].temperature_celsius if recent and recent[-1].temperature_celsius else None,
                "average": sum(s.temperature_celsius for s in recent if s.temperature_celsius) / len([s for s in recent if s.temperature_celsius]) if any(s.temperature_celsius for s in recent) else None,
                "max": max(s.temperature_celsius for s in recent if s.temperature_celsius) if any(s.temperature_celsius for s in recent) else None,
            },
            "power": {
                "current": recent[-1].power_watts if recent and recent[-1].power_watts else None,
                "average": sum(s.power_watts for s in recent if s.power_watts) / len([s for s in recent if s.power_watts]) if any(s.power_watts for s in recent) else None,
                "max": max(s.power_watts for s in recent if s.power_watts) if any(s.power_watts for s in recent) else None,
            },
            "sample_count": len(recent),
        }

    async def close(self):
        """Clean up."""
        if self._pynvml_available:
            try:
                import pynvml
                pynvml.nvmlShutdown()
            except Exception:
                pass
        self._sample_history.clear()