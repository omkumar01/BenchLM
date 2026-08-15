"""Live Monitor page - Real-time charts during benchmark execution."""

import flet as ft
import asyncio
import random
from typing import Optional
from collections import deque

from benchlm.ui.pages.base import BasePage
from benchlm.ui.widgets import (
    GlassCard,
    MetricCard,
    CircularGauge,
    GaugeConfig,
    GaugeSize,
    StatusIndicator,
    StatusConfig,
    LazyPlotlyChart,
    ChartContainer,
    ChartConfig,
)
from benchlm.ui.theme import get_theme
from benchlm.config import get_config

import plotly.graph_objects as go


class LiveMonitorPage(BasePage):
    """Live monitor page with real-time charts during benchmark."""

    def __init__(self, page: ft.Page, **kwargs):
        self._theme = get_theme()
        self._config = get_config()
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None

        # Data buffers
        self._tps_history = deque(maxlen=100)
        self._latency_history = deque(maxlen=100)
        self._cpu_history = deque(maxlen=100)
        self._gpu_history = deque(maxlen=100)
        self._vram_history = deque(maxlen=100)
        self._ram_history = deque(maxlen=100)
        self._temp_history = deque(maxlen=100)
        self._power_history = deque(maxlen=100)

        # Chart widgets
        self._tps_chart: Optional[ChartContainer] = None
        self._latency_chart: Optional[ChartContainer] = None
        self._hardware_chart: Optional[ChartContainer] = None
        self._memory_chart: Optional[ChartContainer] = None

        # Gauges
        self._tps_gauge: Optional[CircularGauge] = None
        self._ttft_gauge: Optional[CircularGauge] = None
        self._cpu_gauge: Optional[CircularGauge] = None
        self._gpu_gauge: Optional[CircularGauge] = None

        super().__init__(page, route="/live-monitor", title="Live Monitor", icon=ft.Icons.MONITOR_HEART, **kwargs)

    def _build(self):
        """Build live monitor page UI."""
        c = self._theme.colors

        # Header with status
        self._status_indicator = StatusIndicator(
            config=StatusConfig(status="idle", label="Waiting for benchmark", size="large"),
        )

        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Live Monitor", size=self._theme.typography.headline_medium, weight=ft.FontWeight.BOLD, color=c.on_background),
                        ft.Text("Real-time benchmark metrics", size=self._theme.typography.body_medium, color=c.on_surface_variant),
                    ],
                    spacing=4,
                ),
                ft.Container(expand=True),
                self._status_indicator,
                ft.Container(width=24),
                ft.Row(
                    controls=[
                        ft.IconButton(icon=ft.Icons.PAUSE, on_click=self._pause, tooltip="Pause"),
                        ft.IconButton(icon=ft.Icons.STOP, on_click=self._stop, tooltip="Stop"),
                        ft.IconButton(icon=ft.Icons.FULLSCREEN, on_click=self._toggle_fullscreen, tooltip="Fullscreen"),
                    ],
                    spacing=4,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Key Metrics Row
        self._build_key_metrics()

        # Charts Grid
        self._build_charts()

        # Hardware Gauges
        self._build_hardware_gauges()

        # Token Stream
        self._build_token_stream()

        # Main content
        self.content = ft.Column(
            controls=[
                header,
                ft.Container(height=24),
                self._metrics_row,
                ft.Container(height=24),
                self._charts_row1,
                ft.Container(height=16),
                self._charts_row2,
                ft.Container(height=24),
                self._gauges_row,
                ft.Container(height=24),
                self._token_stream_card,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _build_key_metrics(self):
        """Build key metrics cards."""
        c = self._theme.colors

        self._metrics_cards = {
            "tokens_generated": MetricCard(value="0", label="Tokens Generated", icon=ft.Icons.TOKEN, icon_color=c.primary),
            "current_tps": MetricCard(value="0.0", label="Current TPS", icon=ft.Icons.SPEED, icon_color=c.success, unit="tok/s"),
            "avg_tps": MetricCard(value="0.0", label="Avg TPS", icon=ft.Icons.TRENDING_UP, icon_color=c.tertiary, unit="tok/s"),
            "ttft": MetricCard(value="--", label="TTFT", icon=ft.Icons.TIMER, icon_color=c.warning, unit="ms"),
            "tpot": MetricCard(value="--", label="TPOT", icon=ft.Icons.SPEED, icon_color=c.tertiary, unit="ms"),
            "elapsed": MetricCard(value="00:00", label="Elapsed", icon=ft.Icons.ACCESS_TIME, icon_color=c.on_surface_variant),
        }

        self._metrics_row = ft.Row(
            controls=[ft.Container(content=card, expand=True) for card in self._metrics_cards.values()],
            spacing=16,
            wrap=True,
        )

    def _build_charts(self):
        """Build real-time charts."""
        c = self._theme.colors

        # TPS Chart
        def create_tps_chart():
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(range(len(self._tps_history))),
                y=list(self._tps_history),
                mode='lines',
                name='TPS',
                line=dict(color=c.primary, width=2),
                fill='tozeroy',
                fillcolor=c.primary + '30',
            ))
            fig.update_layout(
                title="Tokens/Second Over Time",
                xaxis_title="Samples",
                yaxis_title="TPS",
                height=300,
                showlegend=False,
            )
            return fig

        self._tps_chart = ChartContainer(
            chart=LazyPlotlyChart(create_tps_chart, ChartConfig(height=300)),
            title="Throughput",
        )

        # Latency Chart
        def create_latency_chart():
            fig = go.Figure()
            if self._latency_history:
                fig.add_trace(go.Scatter(
                    x=list(range(len(self._latency_history))),
                    y=list(self._latency_history),
                    mode='lines',
                    name='TTFT',
                    line=dict(color=c.warning, width=2),
                ))
            fig.update_layout(
                title="Latency (TTFT)",
                xaxis_title="Request",
                yaxis_title="ms",
                height=300,
                showlegend=False,
            )
            return fig

        self._latency_chart = ChartContainer(
            chart=LazyPlotlyChart(create_latency_chart, ChartConfig(height=300)),
            title="Latency",
        )

        # Hardware Chart
        def create_hardware_chart():
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(range(len(self._cpu_history))),
                y=list(self._cpu_history),
                mode='lines',
                name='CPU %',
                line=dict(color=c.primary, width=2),
            ))
            fig.add_trace(go.Scatter(
                x=list(range(len(self._gpu_history))),
                y=list(self._gpu_history),
                mode='lines',
                name='GPU %',
                line=dict(color=c.tertiary, width=2),
            ))
            fig.update_layout(
                title="CPU/GPU Utilization",
                xaxis_title="Time",
                yaxis_title="%",
                height=300,
                yaxis=dict(range=[0, 100]),
            )
            return fig

        self._hardware_chart = ChartContainer(
            chart=LazyPlotlyChart(create_hardware_chart, ChartConfig(height=300)),
            title="Compute Utilization",
        )

        # Memory Chart
        def create_memory_chart():
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(range(len(self._vram_history))),
                y=list(self._vram_history),
                mode='lines',
                name='VRAM (GB)',
                line=dict(color=c.danger, width=2),
                fill='tozeroy',
                fillcolor=c.danger + '20',
            ))
            fig.add_trace(go.Scatter(
                x=list(range(len(self._ram_history))),
                y=list(self._ram_history),
                mode='lines',
                name='RAM (GB)',
                line=dict(color=c.warning, width=2),
                fill='tozeroy',
                fillcolor=c.warning + '20',
            ))
            fig.update_layout(
                title="Memory Usage",
                xaxis_title="Time",
                yaxis_title="GB",
                height=300,
            )
            return fig

        self._memory_chart = ChartContainer(
            chart=LazyPlotlyChart(create_memory_chart, ChartConfig(height=300)),
            title="Memory",
        )

        # Charts rows
        self._charts_row1 = ft.Row(
            controls=[
                ft.Container(content=self._tps_chart, expand=True),
                ft.Container(width=16),
                ft.Container(content=self._latency_chart, expand=True),
            ],
            spacing=0,
        )

        self._charts_row2 = ft.Row(
            controls=[
                ft.Container(content=self._hardware_chart, expand=True),
                ft.Container(width=16),
                ft.Container(content=self._memory_chart, expand=True),
            ],
            spacing=0,
        )

    def _build_hardware_gauges(self):
        """Build hardware gauges."""
        c = self._theme.colors

        gauge_config = GaugeConfig(
            size=GaugeSize.MEDIUM,
            min_value=0,
            max_value=100,
            unit="%",
            show_value=True,
            show_label=True,
            track_color=c.surface_container_high,
        )

        self._cpu_gauge = CircularGauge(
            config=GaugeConfig(**{**gauge_config.__dict__, "label": "CPU", "progress_color": c.primary}),
        )
        self._gpu_gauge = CircularGauge(
            config=GaugeConfig(**{**gauge_config.__dict__, "label": "GPU", "progress_color": c.tertiary}),
        )

        # Temperature gauges
        self._cpu_temp_gauge = CircularGauge(
            config=GaugeConfig(**{**gauge_config.__dict__, "label": "CPU Temp", "max_value": 100, "unit": "°C", "progress_color": c.warning}),
        )
        self._gpu_temp_gauge = CircularGauge(
            config=GaugeConfig(**{**gauge_config.__dict__, "label": "GPU Temp", "max_value": 100, "unit": "°C", "progress_color": c.danger}),
        )

        # Power gauges
        self._cpu_power_gauge = CircularGauge(
            config=GaugeConfig(**{**gauge_config.__dict__, "label": "CPU Power", "max_value": 200, "unit": "W", "progress_color": c.tertiary}),
        )
        self._gpu_power_gauge = CircularGauge(
            config=GaugeConfig(**{**gauge_config.__dict__, "label": "GPU Power", "max_value": 500, "unit": "W", "progress_color": c.tertiary}),
        )

        self._gauges_row = ft.Row(
            controls=[
                ft.Container(content=ft.Column([
                    ft.Text("Utilization", size=14, weight=ft.FontWeight.W_500, color=c.on_surface_variant),
                    ft.Container(height=8),
                    ft.Row([self._cpu_gauge, ft.Container(width=24), self._gpu_gauge], alignment=ft.MainAxisAlignment.CENTER),
                ]), expand=True),
                ft.Container(width=16),
                ft.Container(content=ft.Column([
                    ft.Text("Temperature", size=14, weight=ft.FontWeight.W_500, color=c.on_surface_variant),
                    ft.Container(height=8),
                    ft.Row([self._cpu_temp_gauge, ft.Container(width=24), self._gpu_temp_gauge], alignment=ft.MainAxisAlignment.CENTER),
                ]), expand=True),
                ft.Container(width=16),
                ft.Container(content=ft.Column([
                    ft.Text("Power", size=14, weight=ft.FontWeight.W_500, color=c.on_surface_variant),
                    ft.Container(height=8),
                    ft.Row([self._cpu_power_gauge, ft.Container(width=24), self._gpu_power_gauge], alignment=ft.MainAxisAlignment.CENTER),
                ]), expand=True),
            ],
            spacing=0,
        )

    def _build_token_stream(self):
        """Build token stream display."""
        c = self._theme.colors

        self._token_stream_text = ft.Text(
            "Waiting for benchmark to start...",
            size=13,
            font_family="JetBrains Mono, monospace",
            color=c.on_surface_variant,
            selectable=True,
        )

        self._token_stream_card = GlassCard(
            header=ft.Row(
                controls=[
                    ft.Text("Token Stream", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                    ft.Container(expand=True),
                    StatusIndicator(config=StatusConfig(status="idle", label="Idle", size="small")),
                ],
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Container(
                            content=self._token_stream_text,
                            padding=16,
                            bgcolor=c.surface,
                            border_radius=8,
                            height=200,
                        ),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                ),
            ),
        )

    async def on_mount(self):
        """Start monitoring when page loads."""
        self._running = True
        self._status_indicator.set_status("running", "Benchmark Running")
        self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def on_unmount(self):
        """Stop monitoring when page unloads."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

    async def _monitor_loop(self):
        """Background monitoring loop."""
        interval = self._config.ui.hardware_poll_interval / 1000

        while self._running:
            try:
                await self._update_metrics()
            except Exception as e:
                print(f"Monitor update error: {e}")

            await asyncio.sleep(interval)

    async def _update_metrics(self):
        """Update all metrics with simulated data."""
        c = self._theme.colors

        # Simulate data (replace with real hardware/benchmark data)
        import time

        # TPS
        tps = random.uniform(20, 120)
        self._tps_history.append(tps)
        self._metrics_cards["current_tps"].value = f"{tps:.1f}"
        avg_tps = sum(self._tps_history) / len(self._tps_history)
        self._metrics_cards["avg_tps"].value = f"{avg_tps:.1f}"

        # Tokens generated
        tokens = len(self._tps_history) * int(tps * 0.1)
        self._metrics_cards["tokens_generated"].value = f"{tokens:,}"

        # Latency
        ttft = random.uniform(50, 200)
        self._latency_history.append(ttft)
        self._metrics_cards["ttft"].value = f"{ttft:.0f}"

        tpot = random.uniform(5, 20)
        self._metrics_cards["tpot"].value = f"{tpot:.1f}"

        # Elapsed time
        elapsed = len(self._tps_history) * interval
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        self._metrics_cards["elapsed"].value = f"{mins:02d}:{secs:02d}"

        # Hardware
        cpu = random.uniform(20, 95)
        gpu = random.uniform(30, 98)
        vram = random.uniform(4, 20)
        ram = random.uniform(8, 32)
        cpu_temp = random.uniform(40, 85)
        gpu_temp = random.uniform(45, 88)
        cpu_power = random.uniform(50, 180)
        gpu_power = random.uniform(100, 400)

        self._cpu_history.append(cpu)
        self._gpu_history.append(gpu)
        self._vram_history.append(vram)
        self._ram_history.append(ram)
        self._temp_history.append((cpu_temp + gpu_temp) / 2)
        self._power_history.append(cpu_power + gpu_power)

        # Update gauges
        self._cpu_gauge.value = cpu
        self._gpu_gauge.value = gpu
        self._cpu_temp_gauge.value = cpu_temp
        self._gpu_temp_gauge.value = gpu_temp
        self._cpu_power_gauge.value = cpu_power
        self._gpu_power_gauge.value = gpu_power

        # Update token stream
        if random.random() < 0.3:
            tokens = ["the", "quick", "brown", "fox", "jumps", "over", "lazy", "dog", "."]
            self._token_stream_text.value += " " + random.choice(tokens)
            # Keep last 500 chars
            if len(self._token_stream_text.value) > 500:
                self._token_stream_text.value = "..." + self._token_stream_text.value[-500:]

        # Refresh charts (lazy charts will re-render on next load)
        self._tps_chart.chart.load()
        self._latency_chart.chart.load()
        self._hardware_chart.chart.load()
        self._memory_chart.chart.load()

        self.update()

    def _pause(self, _):
        """Pause monitoring."""
        self._running = not self._running
        if self._running:
            self._status_indicator.set_status("running", "Benchmark Running")
            self._monitor_task = asyncio.create_task(self._monitor_loop())
        else:
            self._status_indicator.set_status("paused", "Paused")

    def _stop(self, _):
        """Stop monitoring and navigate back."""
        self._running = False
        self._status_indicator.set_status("completed", "Completed")
        self.page.go("/results")

    def _toggle_fullscreen(self, _):
        """Toggle fullscreen mode."""
        self.page.window.full_screen = not self.page.window.full_screen
        self.page.update()