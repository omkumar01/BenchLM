"""Dashboard page - Home dashboard with live hardware gauges."""

import flet as ft
from typing import Optional
import asyncio

from benchlm.ui.pages.base import BasePage
from benchlm.ui.widgets import (
    MetricCard,
    GlassCard,
    MultiGauge,
    GaugeConfig,
    GaugeSize,
    StatusIndicator,
    StatusConfig,
    Breadcrumb,
)
from benchlm.ui.theme import get_theme
from benchlm.config import get_config


class DashboardPage(BasePage):
    """Dashboard page with live hardware gauges and current model info."""

    def __init__(self, page: ft.Page, **kwargs):
        self._theme = get_theme()
        self._config = get_config()
        self._hardware_task: Optional[asyncio.Task] = None
        self._running = False

        # Hardware gauge widgets
        self._cpu_gauge: Optional[MultiGauge] = None
        self._gpu_gauge: Optional[MultiGauge] = None
        self._memory_gauges: dict = {}
        self._temp_gauges: dict = {}
        self._power_gauges: dict = {}

        # Model info
        self._current_model_card: Optional[MetricCard] = None
        self._benchmark_status: Optional[StatusIndicator] = None

        super().__init__(page, **kwargs)

    def _build(self):
        """Build dashboard UI."""
        c = self._theme.colors
        s = self._theme.spacing

        # Breadcrumb
        breadcrumb = Breadcrumb(
            items=[
                ("Dashboard", None),
            ]
        )

        # Header
        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(
                            "Dashboard",
                            size=self._theme.typography.headline_medium,
                            weight=ft.FontWeight.BOLD,
                            color=c.on_background,
                        ),
                        ft.Text(
                            "Live system monitoring and benchmark overview",
                            size=self._theme.typography.body_medium,
                            color=c.on_surface_variant,
                        ),
                    ],
                    spacing=4,
                ),
                ft.Container(expand=True),
                ft.FilledButton(
                    content=ft.Text("New Benchmark"),
                    icon=ft.Icons.PLAY_ARROW,
                    on_click=lambda _: self._navigate_to("benchmark"),
                    style=self._theme.button_primary_style(),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Current Model & Benchmark Status Row
        self._current_model_card = MetricCard(
            value="No model selected",
            label="Current Model",
            icon=ft.Icons.MODEL_TRAINING,
            unit="",
        )

        self._benchmark_status = StatusIndicator(
            config=StatusConfig(
                status="idle",
                label="No benchmark running",
                size="medium",
            )
        )

        model_status_row = ft.Row(
            controls=[
                ft.Container(content=self._current_model_card, expand=True),
                ft.Container(width=16),
                ft.Container(content=self._benchmark_status, width=250),
            ],
            spacing=0,
        )

        # Hardware Gauges Grid
        self._build_hardware_gauges()

        hardware_section = GlassCard(
            header=ft.Row(
                controls=[
                    ft.Text("Hardware Monitor", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                    ft.Container(expand=True),
                    StatusIndicator(
                        config=StatusConfig(status="running", label="Live", size="small"),
                    ),
                ],
            ),
            content=ft.Column(
                controls=[
                    self._cpu_gauges_row,
                    ft.Container(height=16),
                    self._gpu_gauges_row,
                    ft.Container(height=16),
                    self._memory_gauges_row,
                    ft.Container(height=16),
                    self._thermal_power_row,
                ],
                spacing=0,
            ),
        )

        # Quick Stats Row
        self._quick_stats = ft.Row(
            controls=[
                self._create_stat_card("TTFT", "-- ms", ft.Icons.SPEED, c.primary),
                self._create_stat_card("Tokens/sec", "--", ft.Icons.BOLT, c.success),
                self._create_stat_card("GPU Usage", "--%", ft.Icons.MEMORY, c.warning),
                self._create_stat_card("VRAM", "-- GB", ft.Icons.STORAGE, c.tertiary),
            ],
            spacing=s.card_gap,
            wrap=True,
        )

        # Recent Benchmarks
        recent_section = GlassCard(
            header=ft.Row(
                controls=[
                    ft.Text("Recent Benchmarks", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                    ft.Container(expand=True),
                    ft.TextButton("View All", on_click=lambda _: self._navigate_to("history")),
                ],
            ),
            content=ft.Container(
                content=ft.Text(
                    "No recent benchmarks. Run your first benchmark to see results here.",
                    size=14,
                    color=c.on_surface_variant,
                    text_align=ft.TextAlign.CENTER,
                ),
                padding=ft.Padding.symmetric(vertical=48),
                alignment=ft.Alignment.CENTER,
            ),
        )

        # Main content
        self.content = ft.Column(
            controls=[
                breadcrumb,
                ft.Container(height=16),
                header,
                ft.Container(height=24),
                model_status_row,
                ft.Container(height=24),
                self._quick_stats,
                ft.Container(height=24),
                hardware_section,
                ft.Container(height=24),
                recent_section,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _build_hardware_gauges(self):
        """Build hardware gauge widgets."""
        c = self._theme.colors

        # CPU Gauges
        cpu_config = GaugeConfig(
            size=GaugeSize.MEDIUM,
            min_value=0,
            max_value=100,
            label="CPU",
            unit="%",
            show_value=True,
            show_label=True,
            track_color=c.surface_container_high,
        )
        self._cpu_gauges = MultiGauge(
            gauges=[
                GaugeConfig(**{**cpu_config.__dict__, "label": f"Core {i}", "max_value": 100})
                for i in range(8)  # Default 8 cores
            ],
            columns=4,
            gap=12,
        )

        self._cpu_gauges_row = ft.Column(
            controls=[
                ft.Text("CPU Utilization", size=13, weight=ft.FontWeight.W_500, color=c.on_surface_variant),
                ft.Container(height=8),
                self._cpu_gauges,
            ],
            spacing=0,
        )

        # GPU Gauges
        gpu_config = GaugeConfig(
            size=GaugeSize.MEDIUM,
            min_value=0,
            max_value=100,
            label="GPU",
            unit="%",
            track_color=c.surface_container_high,
        )
        self._gpu_gauges = MultiGauge(
            gauges=[
                GaugeConfig(**{**gpu_config.__dict__, "label": "GPU Core", "max_value": 100}),
                GaugeConfig(**{**gpu_config.__dict__, "label": "GPU Memory", "max_value": 100}),
                GaugeConfig(**{**gpu_config.__dict__, "label": "Encoder", "max_value": 100}),
                GaugeConfig(**{**gpu_config.__dict__, "label": "Decoder", "max_value": 100}),
            ],
            columns=4,
            gap=12,
        )

        self._gpu_gauges_row = ft.Column(
            controls=[
                ft.Text("GPU Utilization", size=13, weight=ft.FontWeight.W_500, color=c.on_surface_variant),
                ft.Container(height=8),
                self._gpu_gauges,
            ],
            spacing=0,
        )

        # Memory Gauges
        self._memory_gauges = {
            "ram": MultiGauge(
                gauges=[
                    GaugeConfig(size=GaugeSize.MEDIUM, min_value=0, max_value=100, label="RAM Usage", unit="%", track_color=c.surface_container_high),
                    GaugeConfig(size=GaugeSize.MEDIUM, min_value=0, max_value=64, label="RAM Used", unit="GB", track_color=c.surface_container_high),
                ],
                columns=2,
                gap=12,
            ),
            "vram": MultiGauge(
                gauges=[
                    GaugeConfig(size=GaugeSize.MEDIUM, min_value=0, max_value=100, label="VRAM Usage", unit="%", track_color=c.surface_container_high),
                    GaugeConfig(size=GaugeSize.MEDIUM, min_value=0, max_value=24, label="VRAM Used", unit="GB", track_color=c.surface_container_high),
                ],
                columns=2,
                gap=12,
            ),
        }

        self._memory_gauges_row = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("System Memory", size=13, weight=ft.FontWeight.W_500, color=c.on_surface_variant),
                            ft.Container(height=8),
                            self._memory_gauges["ram"],
                        ],
                        spacing=0,
                    ),
                    expand=True,
                ),
                ft.Container(width=16),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("GPU Memory", size=13, weight=ft.FontWeight.W_500, color=c.on_surface_variant),
                            ft.Container(height=8),
                            self._memory_gauges["vram"],
                        ],
                        spacing=0,
                    ),
                    expand=True,
                ),
            ],
            spacing=0,
        )

        # Thermal & Power
        self._temp_gauges = MultiGauge(
            gauges=[
                GaugeConfig(size=GaugeSize.MEDIUM, min_value=0, max_value=100, label="CPU Temp", unit="°C", track_color=c.surface_container_high, progress_color=c.warning),
                GaugeConfig(size=GaugeSize.MEDIUM, min_value=0, max_value=100, label="GPU Temp", unit="°C", track_color=c.surface_container_high, progress_color=c.danger),
                GaugeConfig(size=GaugeSize.MEDIUM, min_value=0, max_value=100, label="VRAM Temp", unit="°C", track_color=c.surface_container_high, progress_color=c.warning),
                GaugeConfig(size=GaugeSize.MEDIUM, min_value=0, max_value=100, label="Hotspot", unit="°C", track_color=c.surface_container_high, progress_color=c.danger),
            ],
            columns=4,
            gap=12,
        )

        self._power_gauges = MultiGauge(
            gauges=[
                GaugeConfig(size=GaugeSize.MEDIUM, min_value=0, max_value=300, label="CPU Power", unit="W", track_color=c.surface_container_high, progress_color=c.tertiary),
                GaugeConfig(size=GaugeSize.MEDIUM, min_value=0, max_value=500, label="GPU Power", unit="W", track_color=c.surface_container_high, progress_color=c.tertiary),
                GaugeConfig(size=GaugeSize.MEDIUM, min_value=0, max_value=100, label="Total Power", unit="W", track_color=c.surface_container_high, progress_color=c.tertiary),
                GaugeConfig(size=GaugeSize.MEDIUM, min_value=0, max_value=100, label="Perf/W", unit="tok/J", track_color=c.surface_container_high, progress_color=c.success),
            ],
            columns=4,
            gap=12,
        )

        self._thermal_power_row = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Thermal", size=13, weight=ft.FontWeight.W_500, color=c.on_surface_variant),
                            ft.Container(height=8),
                            self._temp_gauges,
                        ],
                        spacing=0,
                    ),
                    expand=True,
                ),
                ft.Container(width=16),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text("Power", size=13, weight=ft.FontWeight.W_500, color=c.on_surface_variant),
                            ft.Container(height=8),
                            self._power_gauges,
                        ],
                        spacing=0,
                    ),
                    expand=True,
                ),
            ],
            spacing=0,
        )

    def _create_stat_card(self, label: str, value: str, icon: str, color: str) -> ft.Container:
        """Create a quick stat card."""
        c = self._theme.colors

        return ft.Container(
            content=MetricCard(
                value=value,
                label=label,
                icon=icon,
                icon_color=color,
                config=None,  # Will use default card config
            ),
            expand=True,
            width=200,
        )

    def _navigate_to(self, page: str):
        """Navigate to another page."""
        self.page.go(f"/{page}")

    async def on_mount(self):
        """Called when page is mounted."""
        self._running = True
        self._hardware_task = asyncio.create_task(self._update_hardware_loop())

    async def on_unmount(self):
        """Called when page is unmounted."""
        self._running = False
        if self._hardware_task:
            self._hardware_task.cancel()
            try:
                await self._hardware_task
            except asyncio.CancelledError:
                pass

    async def _update_hardware_loop(self):
        """Background task to update hardware gauges."""
        interval = self._config.ui.hardware_poll_interval / 1000  # Convert to seconds

        while self._running:
            try:
                await self._update_hardware_data()
            except Exception as e:
                print(f"Hardware update error: {e}")

            await asyncio.sleep(interval)

    async def _update_hardware_data(self):
        """Update hardware gauge values with real data."""
        # TODO: Connect to actual hardware collector
        # For now, simulate data
        import random

        # Update CPU cores
        if self._cpu_gauges:
            for i, gauge in enumerate(self._cpu_gauges._gauge_widgets):
                gauge.value = random.uniform(10, 90)

        # Update GPU
        if self._gpu_gauges:
            self._gpu_gauges._gauge_widgets[0].value = random.uniform(20, 95)  # Core
            self._gpu_gauges._gauge_widgets[1].value = random.uniform(30, 85)  # Memory
            self._gpu_gauges._gauge_widgets[2].value = random.uniform(0, 50)   # Encoder
            self._gpu_gauges._gauge_widgets[3].value = random.uniform(0, 30)   # Decoder

        # Update Memory
        if self._memory_gauges:
            self._memory_gauges["ram"]._gauge_widgets[0].value = random.uniform(30, 80)  # RAM %
            self._memory_gauges["ram"]._gauge_widgets[1].value = random.uniform(8, 32)   # RAM GB
            self._memory_gauges["vram"]._gauge_widgets[0].value = random.uniform(20, 90) # VRAM %
            self._memory_gauges["vram"]._gauge_widgets[1].value = random.uniform(2, 20)  # VRAM GB

        # Update Thermal
        if self._temp_gauges:
            self._temp_gauges._gauge_widgets[0].value = random.uniform(35, 85)  # CPU
            self._temp_gauges._gauge_widgets[1].value = random.uniform(40, 88)  # GPU
            self._temp_gauges._gauge_widgets[2].value = random.uniform(38, 82)  # VRAM
            self._temp_gauges._gauge_widgets[3].value = random.uniform(45, 95)  # Hotspot

        # Update Power
        if self._power_gauges:
            self._power_gauges._gauge_widgets[0].value = random.uniform(30, 150)   # CPU
            self._power_gauges._gauge_widgets[1].value = random.uniform(100, 400)  # GPU
            self._power_gauges._gauge_widgets[2].value = random.uniform(150, 500)  # Total
            self._power_gauges._gauge_widgets[3].value = random.uniform(0.5, 3.0)  # Perf/W

        # Update quick stats
        # TODO: Update stat cards

        try:
            self.update()
        except RuntimeError:
            pass

    def update_model_info(self, model_name: str, provider: str, params: dict):
        """Update current model display."""
        if self._current_model_card:
            self._current_model_card.value = model_name
            self._current_model_card.label = f"{provider} • {params.get('quantization', 'Unknown')}"
            self._current_model_card.update()

    def update_benchmark_status(self, status: str, label: str = ""):
        """Update benchmark status indicator."""
        if self._benchmark_status:
            self._benchmark_status.set_status(status, label or status.title())