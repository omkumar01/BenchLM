"""Results page - Detailed benchmark results with 13 tabs."""

import flet as ft
from typing import Optional

from benchlm.ui.pages.base import BasePage
from benchlm.ui.widgets import (
    GlassCard,
    MetricCard,
    VirtualizedTable,
    ColumnConfig,
    TableConfig,
    ChartContainer,
    LazyPlotlyChart,
    ChartConfig,
    TabBar,
    Badge,
)
from benchlm.ui.theme import get_theme
from benchlm.config import get_config

import plotly.graph_objects as go


class ResultsPage(BasePage):
    """Results page with 13 tabs for detailed benchmark analysis."""

    def __init__(self, page: ft.Page, run_id: str = "", **kwargs):
        super().__init__(page, route="/results", title="Results", icon=ft.Icons.ANALYTICS, **kwargs)
        self._theme = get_theme()
        self._config = get_config()
        self._run_id = run_id
        self._current_tab = 0
        self._build()

    def _build(self):
        """Build results page UI."""
        c = self._theme.colors

        # Header
        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Benchmark Results", size=self._theme.typography.headline_medium, weight=ft.FontWeight.BOLD, color=c.on_background),
                        ft.Text(f"Run ID: {self._run_id or 'Latest'}", size=self._theme.typography.body_medium, color=c.on_surface_variant),
                    ],
                    spacing=4,
                ),
                ft.Container(expand=True),
                ft.Row(
                    controls=[
                        ft.OutlinedButton(text="Export", icon=ft.Icons.DOWNLOAD, on_click=self._export_results),
                        ft.Container(width=8),
                        ft.FilledButton(text="Compare", icon=ft.Icons.COMPARE_ARROWS, on_click=self._navigate_compare),
                    ],
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Summary Cards
        self._build_summary_cards()

        # Tabs
        self._tabs = TabBar(
            tabs=[
                ft.Tab(text="Summary", icon=ft.Icons.SUMMARIZE),
                ft.Tab(text="Latency", icon=ft.Icons.TIMER),
                ft.Tab(text="Throughput", icon=ft.Icons.SPEED),
                ft.Tab(text="Memory", icon=ft.Icons.MEMORY),
                ft.Tab(text="CPU/GPU", icon=ft.Icons.MONITOR_CHART),
                ft.Tab(text="Thermal", icon=ft.Icons.THERMOSTAT),
                ft.Tab(text="Context", icon=ft.Icons.ARROW_RANGE),
                ft.Tab(text="Concurrency", icon=ft.Icons.GROUPS),
                ft.Tab(text="Quality", icon=ft.Icons.VERIFIED),
                ft.Tab(text="Reliability", icon=ft.Icons.SHIELD),
                ft.Tab(text="Statistics", icon=ft.Icons.ANALYTICS),
                ft.Tab(text="Raw Samples", icon=ft.Icons.TABLE_VIEW),
                ft.Tab(text="Export", icon=ft.Icons.DOWNLOAD),
            ],
            selected_index=0,
            on_change=self._on_tab_change,
        )

        # Tab Content
        self._tab_content = ft.Column(
            controls=[self._build_summary_tab()],
            expand=True,
        )

        # Main content
        self.content = ft.Column(
            controls=[
                header,
                ft.Container(height=16),
                self._summary_row,
                ft.Container(height=24),
                self._tabs,
                ft.Container(height=16),
                self._tab_content,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _build_summary_cards(self):
        """Build summary metric cards."""
        c = self._theme.colors

        self._summary_cards = {
            "overall_score": MetricCard(value="847", label="Overall Score", icon=ft.Icons.STAR, icon_color=c.warning, unit="/1000"),
            "grade": MetricCard(value="A", label="Grade", icon=ft.Icons.GRADE, icon_color=c.success),
            "ttft": MetricCard(value="124ms", label="TTFT (P50)", icon=ft.Icons.TIMER, icon_color=c.primary),
            "tps": MetricCard(value="87.3", label="Output TPS", icon=ft.Icons.BOLT, icon_color=c.success, unit="tok/s"),
            "vram": MetricCard(value="6.2 GB", label="Peak VRAM", icon=ft.Icons.STORAGE, icon_color=c.warning),
            "accuracy": MetricCard(value="81%", label="Quality Score", icon=ft.Icons.TARGET, icon_color=c.tertiary),
        }

        self._summary_row = ft.Row(
            controls=[ft.Container(content=card, expand=True) for card in self._summary_cards.values()],
            spacing=16,
            wrap=True,
        )

    def _on_tab_change(self, e: ft.ControlEvent):
        """Handle tab change."""
        self._current_tab = e.control.selected_index
        tab_builders = [
            self._build_summary_tab,
            self._build_latency_tab,
            self._build_throughput_tab,
            self._build_memory_tab,
            self._build_cpu_gpu_tab,
            self._build_thermal_tab,
            self._build_context_tab,
            self._build_concurrency_tab,
            self._build_quality_tab,
            self._build_reliability_tab,
            self._build_statistics_tab,
            self._build_raw_samples_tab,
            self._build_export_tab,
        ]
        self._tab_content.controls = [tab_builders[self._current_tab]()]
        self._tab_content.update()

    def _build_summary_tab(self) -> ft.Control:
        """Build summary tab."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Text("Benchmark Overview", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Column([
                                        ft.Text("Model", size=12, color=c.on_surface_variant),
                                        ft.Text("Qwen3-8B (Q4_K_M)", size=14, weight=ft.FontWeight.MEDIUM, color=c.on_surface),
                                    ], expand=True),
                                    ft.Column([
                                        ft.Text("Provider", size=12, color=c.on_surface_variant),
                                        ft.Text("Ollama", size=14, weight=ft.FontWeight.MEDIUM, color=c.on_surface),
                                    ], expand=True),
                                    ft.Column([
                                        ft.Text("Date", size=12, color=c.on_surface_variant),
                                        ft.Text("2026-08-14 14:32", size=14, weight=ft.FontWeight.MEDIUM, color=c.on_surface),
                                    ], expand=True),
                                    ft.Column([
                                        ft.Text("Duration", size=12, color=c.on_surface_variant),
                                        ft.Text("45.2s", size=14, weight=ft.FontWeight.MEDIUM, color=c.on_surface),
                                    ], expand=True),
                                ],
                                spacing=16,
                            ),
                        ],
                    ),
                ),
                ft.Container(height=16),
                GlassCard(
                    header=ft.Text("Key Metrics", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            self._build_metric_row("Time to First Token", "124ms (P50)", "89ms (P90)", "2.1ms (P99)"),
                            self._build_metric_row("Tokens per Second", "87.3 (avg)", "92.1 (peak)", "78.4 (min)"),
                            self._build_metric_row("Peak VRAM Usage", "6.2 GB", "5.8 GB (avg)", "94% utilization"),
                            self._build_metric_row("CPU Utilization", "67% (avg)", "89% (peak)", "4 cores active"),
                            self._build_metric_row("Energy per Token", "0.42 J/tok", "0.38 J/tok (best)", "18.9 W total"),
                        ],
                    ),
                ),
            ],
            spacing=0,
        )

    def _build_metric_row(self, label: str, val1: str, val2: str, val3: str) -> ft.Control:
        """Build a metric row."""
        c = self._theme.colors

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(label, size=13, weight=ft.FontWeight.MEDIUM, color=c.on_surface, width=180),
                    ft.Text(val1, size=13, color=c.on_surface, expand=True),
                    ft.Text(val2, size=13, color=c.on_surface_variant, expand=True),
                    ft.Text(val3, size=13, color=c.on_surface_disabled, expand=True),
                ],
            ),
            padding=ft.padding.symmetric(vertical=8),
        )

    def _build_latency_tab(self) -> ft.Control:
        """Build latency analysis tab."""
        c = self._theme.colors

        # Latency chart
        def create_latency_chart():
            fig = go.Figure()
            # Simulated data
            x = list(range(100))
            ttft = [100 + 20 * (i % 10) + random_noise() for i in x]
            e2e = [500 + 100 * (i % 15) + random_noise() * 5 for i in x]

            fig.add_trace(go.Scatter(x=x, y=ttft, mode='lines', name='TTFT', line=dict(color=c.primary)))
            fig.add_trace(go.Scatter(x=x, y=e2e, mode='lines', name='E2E Latency', line=dict(color=c.tertiary)))
            fig.update_layout(title="Latency Over Time", xaxis_title="Request", yaxis_title="ms", height=400)
            return fig

        return ft.Column(
            controls=[
                ChartContainer(
                    chart=LazyPlotlyChart(create_latency_chart, ChartConfig(height=400)),
                    title="Latency Timeline",
                ),
                ft.Container(height=16),
                GlassCard(
                    header=ft.Text("Percentile Distribution", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=self._build_percentile_table("TTFT (ms)", [50, 90, 95, 99, 99.9], [124, 189, 234, 412, 567]),
                ),
            ],
            spacing=0,
        )

    def _build_throughput_tab(self) -> ft.Control:
        """Build throughput analysis tab."""
        c = self._theme.colors

        def create_tps_chart():
            fig = go.Figure()
            x = list(range(100))
            tps = [85 + 10 * (i % 7) + random_noise() * 3 for i in x]
            fig.add_trace(go.Scatter(x=x, y=tps, mode='lines', name='TPS', line=dict(color=c.success), fill='tozeroy'))
            fig.update_layout(title="Throughput Over Time", xaxis_title="Time", yaxis_title="TPS", height=400)
            return fig

        return ft.Column(
            controls=[
                ChartContainer(
                    chart=LazyPlotlyChart(create_tps_chart, ChartConfig(height=400)),
                    title="Throughput Timeline",
                ),
                ft.Container(height=16),
                ft.Row(
                    controls=[
                        GlassCard(
                            header=ft.Text("Throughput Metrics", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                            content=self._build_metric_grid({
                                "Output TPS": "87.3",
                                "Input TPS": "1,240",
                                "Total TPS": "1,327",
                                "Requests/sec": "12.4",
                            }),
                        ),
                        GlassCard(
                            header=ft.Text("Batch Efficiency", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                            content=self._build_metric_grid({
                                "Batch Size": "1",
                                "Efficiency": "94%",
                                "Max TPS": "112.4",
                                "Concurrent Users": "1",
                            }),
                        ),
                    ],
                    spacing=16,
                    wrap=True,
                ),
            ],
            spacing=0,
        )

    def _build_memory_tab(self) -> ft.Control:
        """Build memory analysis tab."""
        c = self._theme.colors

        def create_memory_chart():
            fig = go.Figure()
            x = list(range(100))
            vram = [5.2 + 0.5 * (i % 10) + random_noise() * 0.1 for i in x]
            ram = [12.4 + 2 * (i % 8) + random_noise() * 0.5 for i in x]

            fig.add_trace(go.Scatter(x=x, y=vram, mode='lines', name='VRAM (GB)', line=dict(color=c.danger), fill='tozeroy'))
            fig.add_trace(go.Scatter(x=x, y=ram, mode='lines', name='RAM (GB)', line=dict(color=c.warning), fill='tozeroy'))
            fig.update_layout(title="Memory Usage Timeline", xaxis_title="Time", yaxis_title="GB", height=400)
            return fig

        return ft.Column(
            controls=[
                ChartContainer(
                    chart=LazyPlotlyChart(create_memory_chart, ChartConfig(height=400)),
                    title="Memory Timeline",
                ),
                ft.Container(height=16),
                ft.Row(
                    controls=[
                        GlassCard(
                            header=ft.Text("VRAM Breakdown", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                            content=self._build_metric_grid({
                                "Model Weights": "4.2 GB",
                                "KV Cache": "1.8 GB",
                                "Activations": "0.2 GB",
                                "Free": "0.8 GB",
                            }),
                        ),
                        GlassCard(
                            header=ft.Text("RAM Breakdown", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                            content=self._build_metric_grid({
                                "Model (CPU)": "2.1 GB",
                                "KV Cache (CPU)": "4.5 GB",
                                "System": "3.2 GB",
                                "Free": "8.7 GB",
                            }),
                        ),
                    ],
                    spacing=16,
                    wrap=True,
                ),
            ],
            spacing=0,
        )

    def _build_cpu_gpu_tab(self) -> ft.Control:
        """Build CPU/GPU utilization tab."""
        c = self._theme.colors

        def create_util_chart():
            fig = go.Figure()
            x = list(range(100))
            cpu = [60 + 15 * (i % 12) + random_noise() * 3 for i in x]
            gpu = [75 + 10 * (i % 8) + random_noise() * 2 for i in x]

            fig.add_trace(go.Scatter(x=x, y=cpu, mode='lines', name='CPU %', line=dict(color=c.primary)))
            fig.add_trace(go.Scatter(x=x, y=gpu, mode='lines', name='GPU %', line=dict(color=c.tertiary)))
            fig.update_layout(title="Utilization Over Time", xaxis_title="Time", yaxis_title="%", yaxis=dict(range=[0, 100]), height=400)
            return fig

        return ft.Column(
            controls=[
                ChartContainer(
                    chart=LazyPlotlyChart(create_util_chart, ChartConfig(height=400)),
                    title="Utilization",
                ),
                ft.Container(height=16),
                GlassCard(
                    header=ft.Text("Per-Core CPU Utilization", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Text("Heatmap visualization coming soon", size=14, color=c.on_surface_variant, text_align=ft.TextAlign.CENTER),
                ),
            ],
            spacing=0,
        )

    def _build_thermal_tab(self) -> ft.Control:
        """Build thermal analysis tab."""
        c = self._theme.colors

        def create_thermal_chart():
            fig = go.Figure()
            x = list(range(100))
            cpu_temp = [55 + 10 * (i % 10) + random_noise() * 1 for i in x]
            gpu_temp = [62 + 8 * (i % 12) + random_noise() * 1 for i in x]

            fig.add_trace(go.Scatter(x=x, y=cpu_temp, mode='lines', name='CPU Temp', line=dict(color=c.warning)))
            fig.add_trace(go.Scatter(x=x, y=gpu_temp, mode='lines', name='GPU Temp', line=dict(color=c.danger)))
            fig.update_layout(title="Temperature Over Time", xaxis_title="Time", yaxis_title="°C", height=400)
            return fig

        return ft.Column(
            controls=[
                ChartContainer(
                    chart=LazyPlotlyChart(create_thermal_chart, ChartConfig(height=400)),
                    title="Thermal Timeline",
                ),
                ft.Container(height=16),
                GlassCard(
                    header=ft.Text("Power & Efficiency", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=self._build_metric_grid({
                        "Avg GPU Power": "287 W",
                        "Peak GPU Power": "342 W",
                        "Avg CPU Power": "98 W",
                        "Energy/Token": "0.42 J",
                        "Perf/Watt": "2.37 tok/J",
                        "Throttling Events": "0",
                    }),
                ),
            ],
            spacing=0,
        )

    def _build_context_tab(self) -> ft.Control:
        """Build context scaling tab."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Text("Context Length Scaling", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Text("Context vs TTFT/TPS/Memory charts coming soon", size=14, color=c.on_surface_variant, text_align=ft.TextAlign.CENTER),
                ),
            ],
            spacing=0,
        )

    def _build_concurrency_tab(self) -> ft.Control:
        """Build concurrency analysis tab."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Text("Concurrency Scaling", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Text("Users vs Latency/Throughput charts coming soon", size=14, color=c.on_surface_variant, text_align=ft.TextAlign.CENTER),
                ),
            ],
            spacing=0,
        )

    def _build_quality_tab(self) -> ft.Control:
        """Build quality benchmarks tab."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Text("Quality Benchmarks", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            self._build_quality_row("MMLU", "78.4%", "75.2%", "81.1%"),
                            self._build_quality_row("HumanEval Pass@1", "67.3%", "Pass@5: 78.1%", "Pass@10: 84.2%"),
                            self._build_quality_row("GSM8K", "82.1%", "EM: 79.3%", "F1: 85.7%"),
                            self._build_quality_row("Needle in Haystack", "94.2%", "Retrieval: 96.1%", "Retention: 92.8%"),
                        ],
                    ),
                ),
            ],
            spacing=0,
        )

    def _build_reliability_tab(self) -> ft.Control:
        """Build reliability tab."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Text("Reliability Metrics", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=self._build_metric_grid({
                        "Success Rate": "100%",
                        "Timeout Rate": "0%",
                        "OOM Rate": "0%",
                        "Error Rate": "0%",
                        "Determinism": "99.8%",
                        "Consistency": "98.5%",
                    }),
                ),
            ],
            spacing=0,
        )

    def _build_statistics_tab(self) -> ft.Control:
        """Build statistical analysis tab."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Text("Statistical Summary", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=self._build_percentile_table("TTFT (ms)", [50, 75, 90, 95, 99, 99.9], [124, 156, 189, 234, 412, 567]),
                ),
            ],
            spacing=0,
        )

    def _build_raw_samples_tab(self) -> ft.Control:
        """Build raw samples tab."""
        c = self._theme.colors

        columns = [
            ColumnConfig(key="timestamp", label="Timestamp", width=150),
            ColumnConfig(key="prompt_id", label="Prompt", width=100),
            ColumnConfig(key="ttft_ms", label="TTFT (ms)", width=100),
            ColumnConfig(key="tpot_ms", label="TPOT (ms)", width=100),
            ColumnConfig(key="tokens", label="Tokens", width=80),
            ColumnConfig(key="tps", label="TPS", width=100),
            ColumnConfig(key="vram_mb", label="VRAM (MB)", width=120),
            ColumnConfig(key="cpu_pct", label="CPU %", width=100),
        ]

        config = TableConfig(
            columns=columns,
            row_height=44,
            virtualized=True,
            virtualization_threshold=1000,
        )

        # Mock data
        data = [
            {"timestamp": "14:32:15.234", "prompt_id": 1, "ttft_ms": 118, "tpot_ms": 11.4, "tokens": 256, "tps": 87.7, "vram_mb": 6144, "cpu_pct": 65},
            {"timestamp": "14:32:18.567", "prompt_id": 2, "ttft_ms": 134, "tpot_ms": 12.1, "tokens": 512, "tps": 82.6, "vram_mb": 6210, "cpu_pct": 68},
        ] * 50

        return ft.Column(
            controls=[
                VirtualizedTable(config=config, data=data),
            ],
            spacing=0,
        )

    def _build_export_tab(self) -> ft.Control:
        """Build export tab."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Text("Export Results", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            ft.Text("Choose export format and options", size=14, color=c.on_surface_variant),
                            ft.Container(height=16),
                            ft.Row(
                                controls=[
                                    self._build_export_button("CSV", ft.Icons.TABLE_VIEW, "Export raw data and statistics"),
                                    ft.Container(width=16),
                                    self._build_export_button("JSON", ft.Icons.CODE, "Export complete results as JSON"),
                                    ft.Container(width=16),
                                    self._build_export_button("HTML", ft.Icons.WEB, "Interactive HTML report with charts"),
                                    ft.Container(width=16),
                                    self._build_export_button("PDF", ft.Icons.PICTURE_AS_PDF, "Professional PDF report"),
                                ],
                                wrap=True,
                            ),
                        ],
                    ),
                ),
            ],
            spacing=0,
        )

    def _build_export_button(self, label: str, icon: str, tooltip: str) -> ft.Control:
        """Build export format button."""
        c = self._theme.colors

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(icon, size=32, color=c.primary),
                    ft.Container(height=8),
                    ft.Text(label, size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    ft.Text(tooltip, size=12, color=c.on_surface_variant, text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=24,
            border=ft.border.all(1, c.outline_variant),
            border_radius=12,
            ink=True,
            on_click=lambda _: self._export_format(label.lower()),
            width=180,
        )

    def _build_metric_grid(self, metrics: dict) -> ft.Control:
        """Build a grid of metrics."""
        c = self._theme.colors

        rows = []
        items = list(metrics.items())
        for i in range(0, len(items), 2):
            row_items = items[i:i+2]
            controls = []
            for label, value in row_items:
                controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(label, size=12, color=c.on_surface_variant),
                            ft.Text(value, size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        expand=True,
                        padding=ft.padding.symmetric(vertical=8),
                    )
                )
            rows.append(ft.Row(controls=controls, spacing=16))

        return ft.Column(controls=rows, spacing=8)

    def _build_percentile_table(self, metric: str, percentiles: list, values: list) -> ft.Control:
        """Build percentile table."""
        c = self._theme.colors

        rows = []
        for p, v in zip(percentiles, values):
            rows.append(
                ft.Row(
                    controls=[
                        ft.Text(f"P{p}", size=13, weight=ft.FontWeight.MEDIUM, color=c.on_surface, width=80),
                        ft.Text(f"{v} ms", size=13, color=c.on_surface, expand=True),
                        ft.ProgressBar(value=v/600, color=c.primary, bgcolor=c.surface_variant, height=6, expand=True),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        return ft.Column(controls=rows, spacing=12)

    def _build_quality_row(self, name: str, val1: str, val2: str, val3: str) -> ft.Control:
        """Build quality metric row."""
        c = self._theme.colors

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(name, size=13, weight=ft.FontWeight.MEDIUM, color=c.on_surface, width=200),
                    ft.Text(val1, size=13, weight=ft.FontWeight.SEMIBOLD, color=c.primary, expand=True),
                    ft.Text(val2, size=13, color=c.on_surface_variant, expand=True),
                    ft.Text(val3, size=13, color=c.on_surface_disabled, expand=True),
                ],
            ),
            padding=ft.padding.symmetric(vertical=8),
            border=ft.border.only(bottom=ft.BorderSide(1, c.outline_variant)),
        )

    def _export_results(self, _):
        """Export all results."""
        self.show_snackbar("Export dialog coming soon", "info")

    def _navigate_compare(self, _):
        """Navigate to comparison."""
        self.page.go("/comparison")

    def _export_format(self, fmt: str):
        """Export in specific format."""
        self.show_snackbar(f"Exporting as {fmt.upper()}...", "info")


import random
def random_noise() -> float:
    return random.uniform(-1, 1)