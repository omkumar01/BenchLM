"""History page - Historical benchmark runs with trends and regression detection."""

import flet as ft
from typing import Optional
from datetime import datetime

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
    SegmentedButton,
    SelectField,
    FormField,
    FormFieldConfig,
    FormFieldType,
)
from benchlm.ui.theme import get_theme
from benchlm.config import get_config

import plotly.graph_objects as go


class HistoryPage(BasePage):
    """History page with benchmark run history and trends."""

    def __init__(self, page: ft.Page, **kwargs):
        super().__init__(page, route="/history", title="History", icon=ft.Icons.HISTORY, **kwargs)
        self._theme = get_theme()
        self._config = get_config()
        self._view_mode = "list"  # list, trends, regressions
        self._filter_model = ""
        self._filter_date = ""
        self._build()

    def _build(self):
        """Build history page UI."""
        c = self._theme.colors

        # Header
        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Benchmark History", size=self._theme.typography.headline_medium, weight=ft.FontWeight.BOLD, color=c.on_background),
                        ft.Text("View and analyze past benchmark runs", size=self._theme.typography.body_medium, color=c.on_surface_variant),
                    ],
                    spacing=4,
                ),
                ft.Container(expand=True),
                ft.Row(
                    controls=[
                        SegmentedButton(
                            options=[
                                ("list", "Runs", ft.Icons.LIST),
                                ("trends", "Trends", ft.Icons.TRENDING_UP),
                                ("regressions", "Regressions", ft.Icons.WARNING),
                            ],
                            selected_key=self._view_mode,
                            on_change=self._on_view_change,
                        ),
                    ],
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Filters
        filters = ft.Row(
            controls=[
                SelectField(
                    options=[("", "All Models"), ("qwen3-8b", "Qwen3-8B"), ("gemma3-9b", "Gemma3-9B"), ("llama3.1-8b", "Llama3.1-8B")],
                    value=self._filter_model,
                    label="Model",
                    on_change=lambda v: setattr(self, '_filter_model', v) or self._refresh(),
                ),
                ft.Container(width=16),
                FormField(
                    config=FormFieldConfig(label="Date Range", hint="YYYY-MM-DD to YYYY-MM-DD"),
                    value=self._filter_date,
                    on_change=lambda v: setattr(self, '_filter_date', v) or self._refresh(),
                ),
                ft.Container(width=16),
                ft.FilledButton(text="Export History", icon=ft.Icons.DOWNLOAD, on_click=self._export_history),
            ],
            spacing=0,
            wrap=True,
        )

        # Content based on view mode
        self._content_area = ft.Column(
            controls=[self._build_list_view()],
            expand=True,
        )

        # Main content
        self.content = ft.Column(
            controls=[
                header,
                ft.Container(height=16),
                filters,
                ft.Container(height=24),
                self._content_area,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _on_view_change(self, mode: str):
        """Handle view mode change."""
        self._view_mode = mode
        views = {
            "list": self._build_list_view,
            "trends": self._build_trends_view,
            "regressions": self._build_regressions_view,
        }
        self._content_area.controls = [views[mode]()]
        self._content_area.update()

    def _build_list_view(self) -> ft.Control:
        """Build benchmark runs list view."""
        c = self._theme.colors

        columns = [
            ColumnConfig(key="date", label="Date", width=180),
            ColumnConfig(key="model", label="Model", min_width=150),
            ColumnConfig(key="provider", label="Provider", width=120),
            ColumnConfig(key="score", label="Score", width=100, format_fn=lambda v: f"{v}/1000"),
            ColumnConfig(key="grade", label="Grade", width=80),
            ColumnConfig(key="ttft", label="TTFT", width=100, format_fn=lambda v: f"{v}ms"),
            ColumnConfig(key="tps", label="TPS", width=100),
            ColumnConfig(key="vram", label="VRAM", width=100, format_fn=lambda v: f"{v} GB"),
            ColumnConfig(key="status", label="Status", width=100),
            ColumnConfig(key="actions", label="", width=100, sortable=False),
        ]

        config = TableConfig(
            columns=columns,
            row_height=52,
            virtualized=True,
            on_row_click=self._on_run_click,
        )

        # Mock data
        data = [
            {
                "date": "2026-08-14 14:32",
                "model": "Qwen3-8B",
                "provider": "Ollama",
                "score": 847,
                "grade": "A",
                "ttft": 120,
                "tps": 87,
                "vram": 6.2,
                "status": "completed",
                "actions": "view",
            },
            {
                "date": "2026-08-13 10:15",
                "model": "Gemma3-9B",
                "provider": "Ollama",
                "score": 823,
                "grade": "A",
                "ttft": 95,
                "tps": 92,
                "vram": 7.1,
                "status": "completed",
                "actions": "view",
            },
            {
                "date": "2026-08-12 16:42",
                "model": "Llama3.1-8B",
                "provider": "llama.cpp",
                "score": 791,
                "grade": "B",
                "ttft": 150,
                "tps": 70,
                "vram": 8.4,
                "status": "completed",
                "actions": "view",
            },
            {
                "date": "2026-08-11 09:20",
                "model": "Qwen3-8B",
                "provider": "Ollama",
                "score": 834,
                "grade": "A",
                "ttft": 128,
                "tps": 85,
                "vram": 6.2,
                "status": "completed",
                "actions": "view",
            },
            {
                "date": "2026-08-10 13:55",
                "model": "Phi3-mini",
                "provider": "LM Studio",
                "score": 712,
                "grade": "B",
                "ttft": 89,
                "tps": 112,
                "vram": 3.8,
                "status": "completed",
                "actions": "view",
            },
        ] * 20  # Simulate more data

        return GlassCard(
            header=ft.Row([
                ft.Text("Benchmark Runs", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                ft.Container(expand=True),
                ft.Text(f"{len(data)} runs total", size=13, color=c.on_surface_variant),
            ]),
            content=VirtualizedTable(config=config, data=data),
        )

    def _build_trends_view(self) -> ft.Control:
        """Build trends visualization view."""
        c = self._theme.colors

        def create_trend_chart():
            fig = go.Figure()

            # Simulate daily average scores over time
            dates = [(datetime(2026, 8, 1) + ft.datetime.timedelta(days=i)).strftime("%m/%d") for i in range(14)]
            qwen_scores = [820 + 10 * (i % 5) + random_noise() * 5 for i in range(14)]
            gemma_scores = [810 + 8 * (i % 4) + random_noise() * 4 for i in range(14)]
            llama_scores = [780 + 12 * (i % 6) + random_noise() * 6 for i in range(14)]

            fig.add_trace(go.Scatter(x=dates, y=qwen_scores, mode='lines+markers', name='Qwen3-8B', line=dict(color=c.primary)))
            fig.add_trace(go.Scatter(x=dates, y=gemma_scores, mode='lines+markers', name='Gemma3-9B', line=dict(color=c.secondary)))
            fig.add_trace(go.Scatter(x=dates, y=llama_scores, mode='lines+markers', name='Llama3.1-8B', line=dict(color=c.tertiary)))

            fig.update_layout(title="Daily Average Score Trend", xaxis_title="Date", yaxis_title="Score", height=400)
            return fig

        def create_metric_trend_chart(metric: str, color: str):
            fig = go.Figure()
            dates = [(datetime(2026, 8, 1) + ft.datetime.timedelta(days=i)).strftime("%m/%d") for i in range(14)]

            if metric == "TTFT":
                qwen = [125 - 2 * (i % 5) + random_noise() * 3 for i in range(14)]
                gemma = [98 - 1 * (i % 4) + random_noise() * 2 for i in range(14)]
                llama = [155 - 3 * (i % 6) + random_noise() * 4 for i in range(14)]
            else:  # TPS
                qwen = [85 + 2 * (i % 5) + random_noise() * 2 for i in range(14)]
                gemma = [90 + 1 * (i % 4) + random_noise() * 2 for i in range(14)]
                llama = [68 + 1 * (i % 6) + random_noise() * 3 for i in range(14)]

            fig.add_trace(go.Scatter(x=dates, y=qwen, mode='lines+markers', name='Qwen3-8B', line=dict(color=c.primary)))
            fig.add_trace(go.Scatter(x=dates, y=gemma, mode='lines+markers', name='Gemma3-9B', line=dict(color=c.secondary)))
            fig.add_trace(go.Scatter(x=dates, y=llama, mode='lines+markers', name='Llama3.1-8B', line=dict(color=c.tertiary)))

            fig.update_layout(title=f"{metric} Trend", xaxis_title="Date", yaxis_title=metric, height=350)
            return fig

        return ft.Column(
            controls=[
                ChartContainer(
                    chart=LazyPlotlyChart(create_trend_chart, ChartConfig(height=400)),
                    title="Overall Score Trend (14 days)",
                ),
                ft.Container(height=16),
                ft.Row(
                    controls=[
                        ft.Container(content=ChartContainer(
                            chart=LazyPlotlyChart(lambda: create_metric_trend_chart("TTFT", c.warning), ChartConfig(height=350)),
                            title="TTFT Trend",
                        ), expand=True),
                        ft.Container(width=16),
                        ft.Container(content=ChartContainer(
                            chart=LazyPlotlyChart(lambda: create_metric_trend_chart("TPS", c.success), ChartConfig(height=350)),
                            title="TPS Trend",
                        ), expand=True),
                    ],
                    spacing=0,
                ),
                ft.Container(height=16),
                GlassCard(
                    header=ft.Text("Moving Averages", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Text("7-day and 30-day moving averages coming soon", size=14, color=c.on_surface_variant, text_align=ft.TextAlign.CENTER),
                ),
            ],
            spacing=0,
        )

    def _build_regressions_view(self) -> ft.Control:
        """Build regression detection view."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Row([
                        ft.Text("Performance Regressions", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                        ft.Container(expand=True),
                        ft.Text("No regressions detected", size=13, color=c.success),
                    ]),
                    content=ft.Column(
                        controls=[
                            ft.Text("All models performing within expected ranges.", size=14, color=c.on_surface_variant, text_align=ft.TextAlign.CENTER),
                            ft.Container(height=16),
                            ft.Text("Regression detection analyzes:", size=13, weight=ft.FontWeight.MEDIUM, color=c.on_surface),
                            ft.Container(height=8),
                            ft.Column(
                                controls=[
                                    self._build_regression_item("Score", "±5%", "Statistical threshold"),
                                    self._build_regression_item("TTFT", "±10%", "Percentile-based"),
                                    self._build_regression_item("TPS", "±8%", "Moving average"),
                                    self._build_regression_item("VRAM", "±5%", "Absolute threshold"),
                                ],
                                spacing=8,
                            ),
                        ],
                    ),
                ),
            ],
            spacing=0,
        )

    def _build_regression_item(self, metric: str, threshold: str, method: str) -> ft.Control:
        """Build regression config item."""
        c = self._theme.colors

        return ft.Row(
            controls=[
                ft.Text(metric, size=13, weight=ft.FontWeight.MEDIUM, color=c.on_surface, width=100),
                ft.Text(threshold, size=13, color=c.primary, width=80),
                ft.Text(method, size=13, color=c.on_surface_variant, expand=True),
                ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=c.success),
            ],
        )

    def _on_run_click(self, run_data: dict):
        """Handle run click - navigate to results."""
        self.page.go(f"/results?run_id={run_data.get('date', '').replace(' ', '_')}")

    def _refresh(self):
        """Refresh data."""
        self._on_view_change(self._view_mode)

    def _export_history(self, _):
        """Export history data."""
        self.show_snackbar("Exporting history...", "info")


import random
def random_noise() -> float:
    return random.uniform(-1, 1)