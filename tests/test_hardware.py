"""Unit tests for BenchLM hardware monitoring."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from benchlm.hardware.cpu import CPUCollector, CPUSample, CPUInfo
from benchlm.hardware.memory import MemoryCollector, MemorySample, MemoryInfo
from benchlm.hardware.disk import DiskCollector, DiskSample, DiskInfo
from benchlm.hardware.battery import BatteryCollector, BatterySample, BatteryInfo
from benchlm.hardware.temperature import TemperatureCollector, TemperatureSample, TemperatureInfo
from benchlm.hardware.collector import HardwareCollector, HardwareSnapshot, RingBuffer


class TestCPUCollector:
    """Tests for CPUCollector."""

    @pytest.mark.asyncio
    async def test_initialize(self):
        collector = CPUCollector()
        await collector.initialize()

        assert collector._cpu_info is not None
        assert isinstance(collector._cpu_info, CPUInfo)
        assert collector._cpu_info.physical_cores > 0
        assert collector._cpu_info.logical_cores > 0

    @pytest.mark.asyncio
    async def test_sample(self):
        collector = CPUCollector()
        await collector.initialize()

        sample = await collector.sample()

        assert isinstance(sample, CPUSample)
        assert sample.timestamp > 0
        assert 0 <= sample.total_percent <= 100
        assert len(sample.per_core_percent) == collector._cpu_info.logical_cores
        assert all(0 <= p <= 100 for p in sample.per_core_percent)

    @pytest.mark.asyncio
    async def test_get_statistics(self):
        collector = CPUCollector()
        await collector.initialize()

        # Generate some samples
        for _ in range(5):
            await collector.sample()

        stats = collector.get_statistics()

        assert "total" in stats
        assert "per_core" in stats
        assert "sample_count" in stats
        assert stats["sample_count"] == 5
        assert "current" in stats["total"]
        assert "average" in stats["total"]
        assert "min" in stats["total"]
        assert "max" in stats["total"]


class TestMemoryCollector:
    """Tests for MemoryCollector."""

    @pytest.mark.asyncio
    async def test_initialize(self):
        collector = MemoryCollector()
        await collector.initialize()

        assert collector._memory_info is not None
        assert isinstance(collector._memory_info, MemoryInfo)
        assert collector._memory_info.ram_total_mb > 0

    @pytest.mark.asyncio
    async def test_sample(self):
        collector = MemoryCollector()
        await collector.initialize()

        sample = await collector.sample()

        assert isinstance(sample, MemorySample)
        assert sample.timestamp > 0
        assert sample.ram_total_mb > 0
        assert sample.ram_used_mb >= 0
        assert 0 <= sample.ram_percent <= 100
        assert sample.process_rss_mb >= 0

    @pytest.mark.asyncio
    async def test_get_statistics(self):
        collector = MemoryCollector()
        await collector.initialize()

        for _ in range(5):
            await collector.sample()

        stats = collector.get_statistics()

        assert "ram" in stats
        assert "swap" in stats
        assert "process" in stats
        assert stats["ram"]["total_mb"] > 0


class TestDiskCollector:
    """Tests for DiskCollector."""

    @pytest.mark.asyncio
    async def test_initialize(self):
        collector = DiskCollector()
        await collector.initialize()

        assert collector._disk_infos is not None
        assert len(collector._disk_infos) > 0
        for info in collector._disk_infos:
            assert isinstance(info, DiskInfo)
            assert info.total_gb > 0

    @pytest.mark.asyncio
    async def test_sample(self):
        collector = DiskCollector()
        await collector.initialize()

        sample = await collector.sample()

        assert isinstance(sample, DiskSample)
        assert sample.timestamp > 0
        assert sample.read_bytes_per_sec >= 0
        assert sample.write_bytes_per_sec >= 0


class TestBatteryCollector:
    """Tests for BatteryCollector."""

    @pytest.mark.asyncio
    async def test_initialize(self):
        collector = BatteryCollector()
        await collector.initialize()

        # Battery may or may not be present
        assert isinstance(collector._has_battery, bool)
        if collector._has_battery:
            assert collector._battery_info is not None
            assert isinstance(collector._battery_info, BatteryInfo)

    @pytest.mark.asyncio
    async def test_sample(self):
        collector = BatteryCollector()
        await collector.initialize()

        sample = await collector.sample()

        if collector._has_battery:
            assert sample is not None
            assert isinstance(sample, BatterySample)
            assert 0 <= sample.percent <= 100
        else:
            assert sample is None


class TestTemperatureCollector:
    """Tests for TemperatureCollector."""

    @pytest.mark.asyncio
    async def test_initialize(self):
        collector = TemperatureCollector()
        await collector.initialize()

        assert collector._temp_info is not None
        assert isinstance(collector._temp_info, TemperatureInfo)

    @pytest.mark.asyncio
    async def test_sample(self):
        collector = TemperatureCollector()
        await collector.initialize()

        sample = await collector.sample()

        assert isinstance(sample, TemperatureSample)
        assert sample.timestamp > 0
        assert isinstance(sample.all_sensors, dict)


class TestHardwareCollector:
    """Tests for unified HardwareCollector."""

    @pytest.mark.asyncio
    async def test_initialize(self):
        collector = HardwareCollector()
        await collector.initialize()

        # All sub-collectors should be initialized
        assert collector._cpu._cpu_info is not None
        assert collector._memory._memory_info is not None

    @pytest.mark.asyncio
    async def test_collect_snapshot(self):
        collector = HardwareCollector()
        await collector.initialize()

        snapshot = await collector._collect_snapshot()

        assert isinstance(snapshot, HardwareSnapshot)
        assert snapshot.timestamp > 0
        assert snapshot.cpu is not None
        assert isinstance(snapshot.gpus, list)
        assert snapshot.memory is not None
        assert snapshot.disk is not None
        assert snapshot.temperature is not None

    @pytest.mark.asyncio
    async def test_start_stop_polling(self):
        collector = HardwareCollector()
        await collector.initialize()

        assert not collector.is_running()

        await collector.start_polling()
        assert collector.is_running()

        # Wait a bit for at least one collection
        import asyncio
        await asyncio.sleep(0.1)

        await collector.stop_polling()
        assert not collector.is_running()

    @pytest.mark.asyncio
    async def test_callbacks(self):
        collector = HardwareCollector()
        await collector.initialize()

        received = []

        def callback(snapshot):
            received.append(snapshot)

        collector.register_callback(callback)

        await collector.start_polling()
        import asyncio
        await asyncio.sleep(0.1)
        await collector.stop_polling()

        collector.unregister_callback(callback)
        await asyncio.sleep(0.1)

        # Should have received at least one snapshot
        assert len(received) > 0

    @pytest.mark.asyncio
    async def test_get_recent(self):
        collector = HardwareCollector()
        await collector.initialize()

        # Collect a few snapshots
        for _ in range(3):
            await collector._collect_snapshot()
            import asyncio
            await asyncio.sleep(0.01)

        recent = await collector.get_recent(2)
        assert len(recent) == 2

    @pytest.mark.asyncio
    async def test_benchmark_context(self):
        collector = HardwareCollector()
        await collector.initialize()

        collector.set_benchmark_context(
            run_id=123,
            phase="running",
            tokens=100,
            tps=50.0
        )

        snapshot = await collector._collect_snapshot()

        assert snapshot.benchmark_run_id == 123
        assert snapshot.benchmark_phase == "running"
        assert snapshot.tokens_generated == 100
        assert snapshot.current_tps == 50.0

    @pytest.mark.asyncio
    async def test_static_info(self):
        collector = HardwareCollector()
        await collector.initialize()

        info = collector.get_static_info()

        assert "cpu" in info
        assert "gpus" in info
        assert "memory" in info
        assert "disks" in info
        assert "battery" in info
        assert "temperature_sensors" in info


class TestRingBuffer:
    """Tests for RingBuffer."""

    @pytest.mark.asyncio
    async def test_append_and_get(self):
        buffer = RingBuffer(max_size=5)

        for i in range(3):
            await buffer.append(f"item-{i}")

        recent = await buffer.get_recent(2)
        assert len(recent) == 2
        assert recent == ["item-1", "item-2"]

    @pytest.mark.asyncio
    async def test_overflow(self):
        buffer = RingBuffer(max_size=3)

        for i in range(5):
            await buffer.append(f"item-{i}")

        all_items = await buffer.get_all()
        assert len(all_items) == 3
        assert all_items == ["item-2", "item-3", "item-4"]

    @pytest.mark.asyncio
    async def test_clear(self):
        buffer = RingBuffer(max_size=5)

        await buffer.append("item-1")
        await buffer.clear()

        recent = await buffer.get_recent(10)
        assert len(recent) == 0


# Integration tests with mocked psutil
class TestHardwareWithMocks:
    """Tests with mocked psutil for consistent results."""

    @pytest.mark.asyncio
    async def test_cpu_collector_mocked(self):
        with patch('psutil.cpu_percent') as mock_cpu_percent, \
             patch('psutil.cpu_count') as mock_cpu_count, \
             patch('psutil.cpu_freq') as mock_cpu_freq, \
             patch('psutil.getloadavg') as mock_getloadavg:

            mock_cpu_percent.side_effect = [25.5, 30.2]
            mock_cpu_count.side_effect = [8, 4]  # logical, physical
            mock_cpu_freq.return_value = MagicMock(current=2500, min=800, max=4000)
            mock_getloadavg.return_value = (1.5, 1.2, 1.0)

            collector = CPUCollector()
            await collector.initialize()

            assert collector._cpu_info.logical_cores == 8
            assert collector._cpu_info.physical_cores == 4

            sample = await collector.sample()
            assert sample.total_percent == 30.2  # Second call

    @pytest.mark.asyncio
    async def test_memory_collector_mocked(self):
        with patch('psutil.virtual_memory') as mock_vmem, \
             patch('psutil.swap_memory') as mock_swap, \
             patch('psutil.Process') as mock_process:

            mock_vmem.return_value = MagicMock(
                total=16*1024**3, used=8*1024**3, available=8*1024**3,
                percent=50, free=4*1024**3, cached=2*1024**3, buffers=1*1024**3
            )
            mock_swap.return_value = MagicMock(
                total=4*1024**3, used=1*1024**3, free=3*1024**3, percent=25
            )
            mock_proc = MagicMock()
            mock_proc.memory_info.return_value = MagicMock(rss=500*1024**2, vms=1000*1024**2)
            mock_proc.memory_percent.return_value = 3.1
            mock_process.return_value = mock_proc

            collector = MemoryCollector()
            await collector.initialize()

            assert collector._memory_info.ram_total_mb == 16384

            sample = await collector.sample()
            assert sample.ram_percent == 50
            assert sample.process_rss_mb == 500