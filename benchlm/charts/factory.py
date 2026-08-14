"""Chart factory for BenchLM - creates and manages chart instances."""

from typing import Dict, List, Optional, Any, Type
from benchlm.charts.latency import LatencyCharts
from benchlm.charts.throughput import ThroughputCharts
from benchlm.charts.memory import MemoryCharts
from benchlm.charts.quality import QualityCharts
from benchlm.charts.statistical import StatisticalCharts
from benchlm.charts.comparison import ComparisonCharts
from benchlm.charts.hardware import HardwareCharts
from benchlm.charts.thermal import ThermalCharts


class ChartFactory:
    """Factory for creating and managing charts."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._chart_generators = {
            'latency': LatencyCharts(),
            'throughput': ThroughputCharts(),
            'memory': MemoryCharts(),
            'quality': QualityCharts(),
            'statistical': StatisticalCharts(),
            'comparison': ComparisonCharts(),
            'hardware': HardwareCharts(),
            'thermal': ThermalCharts(),
        }

        self._chart_cache: Dict[str, Any] = {}
        self._initialized = True

    def get_generator(self, category: str) -> Optional[Any]:
        """Get chart generator by category."""
        return self._chart_generators.get(category)

    def get_all_categories(self) -> List[str]:
        """Get all available chart categories."""
        return list(self._chart_generators.keys())

    def create_chart(
        self,
        category: str,
        chart_type: str,
        *args,
        **kwargs
    ) -> Any:
        """Create a chart using the specified generator."""
        generator = self.get_generator(category)
        if not generator:
            raise ValueError(f"Unknown chart category: {category}")

        method = getattr(generator, chart_type, None)
        if not method:
            raise ValueError(f"Chart type '{chart_type}' not found in category '{category}'")

        return method(*args, **kwargs)

    def create_all_for_category(
        self,
        category: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create all standard charts for a category."""
        generator = self.get_generator(category)
        if not generator:
            return {}

        charts = {}
        # Get all public methods (not starting with _)
        methods = [m for m in dir(generator) if not m.startswith('_') and callable(getattr(generator, m))]

        for method_name in methods:
            try:
                method = getattr(generator, method_name)
                # Try to call with data
                # This is a simplified approach - in practice you'd need specific data mapping
                pass
            except Exception:
                pass

        return charts

    def clear_cache(self):
        """Clear chart cache."""
        self._chart_cache.clear()


# Chart definitions for each results tab
CHART_DEFINITIONS = {
    "latency": [
        ("ttft_timeline", "TTFT Timeline"),
        ("latency_percentiles", "Latency Percentiles"),
        ("latency_histogram", "Latency Histogram"),
        ("latency_cdf", "Latency CDF"),
        ("ttft_vs_tpot_scatter", "TTFT vs TPOT"),
        ("latency_by_context", "Latency vs Context"),
        ("inter_token_latency", "Inter-token Latency"),
        ("prefill_decode_split", "Prefill vs Decode"),
    ],
    "throughput": [
        ("tps_timeline", "TPS Timeline"),
        ("throughput_comparison", "Model Comparison"),
        ("batch_throughput", "Batch Throughput"),
        ("concurrent_throughput", "Concurrency Scaling"),
        ("throughput_efficiency", "Batch Efficiency"),
        ("rps_qpm", "RPS/QPM"),
    ],
    "memory": [
        ("memory_timeline", "Memory Timeline"),
        ("kv_cache_growth", "KV Cache Growth"),
        ("memory_breakdown_stacked", "Memory Breakdown"),
        ("memory_peak_usage", "Peak vs Average"),
        ("memory_efficiency", "Memory Efficiency"),
        ("context_vs_memory", "Context vs Memory"),
    ],
    "quality": [
        ("quality_radar", "Quality Radar"),
        ("pass_at_k", "Pass@k"),
        ("accuracy_comparison", "Accuracy Comparison"),
        ("win_rate_matrix", "Win Rate Matrix"),
        ("elo_trend", "Elo Trend"),
        ("benchmark_scores_detail", "Detailed Scores"),
    ],
    "hardware": [
        ("cpu_gpu_timeline", "CPU/GPU Timeline"),
        ("per_core_heatmap", "Per-Core Heatmap"),
        ("gpu_occupancy", "GPU Occupancy"),
        ("memory_bandwidth", "Memory Bandwidth"),
        ("pcie_utilization", "PCIe Utilization"),
        ("clock_frequencies", "Clock Frequencies"),
        ("utilization_distribution", "Utilization Distribution"),
    ],
    "thermal": [
        ("temperature_timeline", "Temperature Timeline"),
        ("power_timeline", "Power Timeline"),
        ("energy_per_token", "Energy/Token"),
        ("perf_per_watt", "Perf/Watt"),
        ("thermal_throttling_timeline", "Throttling Timeline"),
        ("fan_speed_timeline", "Fan Speed"),
        ("thermal_power_combined", "Thermal & Power Combined"),
    ],
    "statistical": [
        ("box_plot", "Box Plot"),
        ("violin_plot", "Violin Plot"),
        ("histogram_comparison", "Histogram"),
        ("density_plot", "Density Plot"),
        ("heatmap", "Heatmap"),
        ("correlation_matrix", "Correlation Matrix"),
        ("scatter_matrix", "Scatter Matrix"),
        ("error_bars", "Error Bars"),
        ("confidence_intervals", "Confidence Intervals"),
    ],
    "comparison": [
        ("leaderboard_table", "Leaderboard"),
        ("speed_quality_scatter", "Speed vs Quality"),
        ("pareto_frontier", "Pareto Frontier"),
        ("model_size_performance", "Size vs Performance"),
        ("quantization_comparison", "Quantization"),
        ("radar_comparison", "Radar Comparison"),
        ("diff_view", "Diff View"),
    ],
}


def get_chart_factory() -> ChartFactory:
    """Get the global chart factory."""
    return ChartFactory()


def get_chart_definitions(category: str) -> List[tuple]:
    """Get chart definitions for a category."""
    return CHART_DEFINITIONS.get(category, [])