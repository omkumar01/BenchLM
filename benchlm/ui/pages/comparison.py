"""Comparison page - Multi-model comparison with charts and leaderboard."""

import flet as ft
from typing import Optional, List

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
    RadialGauge,
    GaugeSize,
)
from benchlm.ui.theme import get_theme
from benchlm.config import get_config

import plotly.graph_objects as go


class ComparisonPage(BasePage):
    """Comparison page for multi-model benchmark comparison."""

    def __init__(self, page: ft.Page, models: str = "", **kwargs):
        self._theme = get_theme()
        self._config = get_config()
        self._selected_models = models.split(",") if models else ["Qwen3-8B", "Gemma3-9B", "Llama3.1-8B"]
        self._comparison_mode = "overlay"  # overlay, side_by_side, radar, diff, ranking
        super().__init__(page, route="/comparison", title="Comparison", icon=ft.Icons.COMPARE_ARROWS, **kwargs)

    def _build(self):
        """Build comparison page UI."""
        c = self._theme.colors

        # Header
        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Model Comparison", size=self._theme.typography.headline_medium, weight=ft.FontWeight.BOLD, color=c.on_background),
                        ft.Text(f"Comparing {len(self._selected_models)} models", size=self._theme.typography.body_medium, color=c.on_surface_variant),
                    ],
                    spacing=4,
                ),
                ft.Container(expand=True),
                ft.Row(
                    controls=[
                        SegmentedButton(
                            options=[
                                ("overlay", "Overlay", ft.Icons.LAYERS),
                                ("side_by_side", "Side-by-Side", ft.Icons.VIEW_SIDE),
                                ("radar", "Radar", ft.Icons.RADAR),
                                ("diff", "Diff", ft.Icons.COMPARE),
                                ("ranking", "Ranking", ft.Icons.LEADERBOARD),
                            ],
                            selected_key=self._comparison_mode,
                            on_change=self._on_mode_change,
                        ),
                    ],
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Model Selector
        model_selector = self._build_model_selector()

        # Summary Cards
        self._build_summary_cards()

        # Comparison Content
        self._comparison_content = ft.Column(
            controls=[self._build_overlay_view()],
            expand=True,
        )

        # Main content
        self.content = ft.Column(
            controls=[
                header,
                ft.Container(height=16),
                model_selector,
                ft.Container(height=16),
                self._summary_row,
                ft.Container(height=24),
                self._comparison_content,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _build_model_selector(self) -> ft.Control:
        """Build model selector chips."""
        c = self._theme.colors

        chips = []
        for model in self._selected_models:
            chips.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.MODEL_TRAINING, size=16, color=c.primary),
                            ft.Text(model, size=13, color=c.on_surface),
                            ft.IconButton(icon=ft.Icons.CLOSE, icon_size=16, on_click=lambda _, m=model: self._remove_model(m)),
                        ],
                        spacing=8,
                    ),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                    bgcolor=c.primary_container,
                    border_radius=20,
                )
            )

        chips.append(
            ft.Container(
                content=ft.TextButton(
                    content=ft.Text("+ Add Model"),
                    icon=ft.Icons.ADD,
                    on_click=self._add_model,
                ),
                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            )
        )

        return ft.Row(controls=chips, spacing=8, wrap=True)

    def _build_summary_cards(self):
        """Build comparison summary cards."""
        c = self._theme.colors

        # Mock data for comparison
        models_data = [
            ("Qwen3-8B", "120ms", "87", "6.2 GB", "81%", "#6366F1"),
            ("Gemma3-9B", "95ms", "92", "7.1 GB", "79%", "#A855F7"),
            ("Llama3.1-8B", "150ms", "70", "8.4 GB", "83%", "#06B6D4"),
        ]

        cards = []
        for name, ttft, tps, vram, acc, color in models_data:
            cards.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Container(
                                content=ft.Text(name, size=14, weight=ft.FontWeight.BOLD, color=c.on_surface, text_align=ft.TextAlign.CENTER),
                                padding=ft.Padding.only(bottom=8),
                                border=ft.Border.only(bottom=ft.BorderSide(3, color)),
                            ),
                            ft.Container(height=8),
                            self._build_compact_metric("TTFT", ttft, ft.Icons.TIMER, c.primary),
                            ft.Container(height=4),
                            self._build_compact_metric("TPS", tps, ft.Icons.SPEED, c.success),
                            ft.Container(height=4),
                            self._build_compact_metric("VRAM", vram, ft.Icons.MEMORY, c.warning),
                            ft.Container(height=4),
                            self._build_compact_metric("Quality", acc, ft.Icons.TARGET, c.tertiary),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    expand=True,
                    padding=16,
                    bgcolor=c.surface,
                    border=ft.Border.all(1, c.outline_variant),
                    border_radius=12,
                )
            )

        self._summary_row = ft.Row(controls=cards, spacing=16, wrap=True)

    def _build_compact_metric(self, label: str, value: str, icon: str, color: str) -> ft.Control:
        """Build compact metric display."""
        c = self._theme.colors

        return ft.Row(
            controls=[
                ft.Icon(icon, size=16, color=color),
                ft.Text(label, size=11, color=c.on_surface_variant, width=50),
                ft.Text(value, size=13, weight=ft.FontWeight.W_600, color=c.on_surface, text_align=ft.TextAlign.RIGHT, expand=True),
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _on_mode_change(self, mode: str):
        """Handle comparison mode change."""
        self._comparison_mode = mode
        mode_builders = {
            "overlay": self._build_overlay_view,
            "side_by_side": self._build_side_by_side_view,
            "radar": self._build_radar_view,
            "diff": self._build_diff_view,
            "ranking": self._build_ranking_view,
        }
        self._comparison_content.controls = [mode_builders[mode]()]
        self._comparison_content.update()

    def _build_overlay_view(self) -> ft.Control:
        """Build overlay charts view."""
        c = self._theme.colors

        def create_overlay_chart():
            fig = go.Figure()
            models = ["Qwen3-8B", "Gemma3-9B", "Llama3.1-8B"]
            colors = [c.primary, c.secondary, c.tertiary]

            for i, (model, color) in enumerate(zip(models, colors)):
                x = list(range(100))
                y = [80 + 15 * (j % 7) + random_noise() * 3 for j in x]
                if i == 1:
                    y = [v + 5 for v in y]
                elif i == 2:
                    y = [v - 10 for v in y]

                fig.add_trace(go.Scatter(
                    x=x, y=y, mode='lines', name=model,
                    line=dict(color=color, width=2), opacity=0.8
                ))

            fig.update_layout(title="TPS Comparison Overlay", xaxis_title="Time", yaxis_title="TPS", height=400)
            return fig

        def create_latency_overlay():
            fig = go.Figure()
            models = ["Qwen3-8B", "Gemma3-9B", "Llama3.1-8B"]
            colors = [c.primary, c.secondary, c.tertiary]

            for i, (model, color) in enumerate(zip(models, colors)):
                x = list(range(100))
                y = [100 + 20 * (j % 10) + random_noise() * 5 for j in x]
                if i == 1:
                    y = [v - 15 for v in y]
                elif i == 2:
                    y = [v + 25 for v in y]

                fig.add_trace(go.Scatter(
                    x=x, y=y, mode='lines', name=model,
                    line=dict(color=color, width=2), opacity=0.8
                ))

            fig.update_layout(title="TTFT Comparison Overlay", xaxis_title="Request", yaxis_title="ms", height=400)
            return fig

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Container(content=ChartContainer(
                            chart=LazyPlotlyChart(create_overlay_chart, ChartConfig(height=400)),
                            title="Throughput Overlay",
                        ), expand=True),
                        ft.Container(width=16),
                        ft.Container(content=ChartContainer(
                            chart=LazyPlotlyChart(create_latency_overlay, ChartConfig(height=400)),
                            title="Latency Overlay",
                        ), expand=True),
                    ],
                    spacing=0,
                ),
            ],
            spacing=0,
        )

    def _build_side_by_side_view(self) -> ft.Control:
        """Build side-by-side charts view."""
        c = self._theme.colors

        def create_model_chart(model: str, color: str):
            fig = go.Figure()
            x = list(range(100))
            base_tps = 85 if model == "Qwen3-8B" else (92 if model == "Gemma3-9B" else 70)
            y = [base_tps + 10 * (j % 7) + random_noise() * 3 for j in x]
            fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name=model, line=dict(color=color, width=2), fill='tozeroy'))
            fig.update_layout(title=f"{model} TPS", xaxis_title="Time", yaxis_title="TPS", height=300, showlegend=False)
            return fig

        models = [
            ("Qwen3-8B", c.primary),
            ("Gemma3-9B", c.secondary),
            ("Llama3.1-8B", c.tertiary),
        ]

        charts = []
        for model, color in models:
            charts.append(
                ft.Container(
                    content=ChartContainer(
                        chart=LazyPlotlyChart(lambda m=model, col=color: create_model_chart(m, col), ChartConfig(height=300)),
                        title=model,
                    ),
                    expand=True,
                )
            )

        return ft.Row(
            controls=charts,
            spacing=16,
            wrap=True,
        )

    def _build_radar_view(self) -> ft.Control:
        """Build radar chart comparison."""
        c = self._theme.colors

        def create_radar_chart():
            fig = go.Figure()

            categories = ['Speed', 'Throughput', 'Quality', 'Efficiency', 'Reliability', 'Memory']
            models_data = {
                "Qwen3-8B": [85, 87, 81, 78, 92, 85],
                "Gemma3-9B": [92, 92, 79, 82, 88, 79],
                "Llama3.1-8B": [70, 70, 83, 75, 95, 70],
            }

            colors = [c.primary, c.secondary, c.tertiary]

            for i, (model, values) in enumerate(models_data.items()):
                fig.add_trace(go.Scatterpolar(
                    r=values + [values[0]],
                    theta=categories + [categories[0]],
                    fill='toself',
                    name=model,
                    line=dict(color=colors[i], width=2),
                    fillcolor=colors[i] + '30',
                ))

            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                title="Multi-Model Radar Comparison",
                height=500,
            )
            return fig

        return ft.Column(
            controls=[
                ChartContainer(
                    chart=LazyPlotlyChart(create_radar_chart, ChartConfig(height=500)),
                    title="Radar Comparison",
                ),
            ],
            spacing=0,
        )

    def _build_diff_view(self) -> ft.Control:
        """Build difference view."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Text("Difference Analysis (vs Qwen3-8B)", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            self._build_diff_row("Gemma3-9B", "TTFT", "-25ms", "better", c.success),
                            self._build_diff_row("Gemma3-9B", "TPS", "+5 tok/s", "better", c.success),
                            self._build_diff_row("Gemma3-9B", "VRAM", "+0.9 GB", "worse", c.warning),
                            self._build_diff_row("Gemma3-9B", "Quality", "-2%", "worse", c.warning),
                            ft.Divider(height=1, color=c.outline_variant),
                            self._build_diff_row("Llama3.1-8B", "TTFT", "+30ms", "worse", c.danger),
                            self._build_diff_row("Llama3.1-8B", "TPS", "-17 tok/s", "worse", c.danger),
                            self._build_diff_row("Llama3.1-8B", "VRAM", "+2.2 GB", "worse", c.danger),
                            self._build_diff_row("Llama3.1-8B", "Quality", "+2%", "better", c.success),
                        ],
                    ),
                ),
            ],
            spacing=0,
        )

    def _build_diff_row(self, model: str, metric: str, diff: str, direction: str, color: str) -> ft.Control:
        """Build a diff row."""
        c = self._theme.colors

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(model, size=13, weight=ft.FontWeight.W_500, color=c.on_surface, width=100),
                    ft.Text(metric, size=13, color=c.on_surface_variant, width=100),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.ARROW_UPWARD if direction == "better" else ft.Icons.ARROW_DOWNWARD, size=14, color=color),
                            ft.Text(diff, size=13, weight=ft.FontWeight.W_600, color=color),
                        ], spacing=4),
                        padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                        bgcolor=color + "20",
                        border_radius=6,
                    ),
                ],
            ),
            padding=ft.Padding.symmetric(vertical=8),
        )

    def _build_ranking_view(self) -> ft.Control:
        """Build ranking/leaderboard view."""
        c = self._theme.colors

        # Leaderboard table
        columns = [
            ColumnConfig(key="rank", label="#", width=50, sortable=False),
            ColumnConfig(key="model", label="Model", min_width=150),
            ColumnConfig(key="score", label="Score", width=100, format_fn=lambda v: f"{v}/1000"),
            ColumnConfig(key="grade", label="Grade", width=80),
            ColumnConfig(key="ttft", label="TTFT", width=100, format_fn=lambda v: f"{v}ms"),
            ColumnConfig(key="tps", label="TPS", width=100),
            ColumnConfig(key="vram", label="VRAM", width=100, format_fn=lambda v: f"{v} GB"),
            ColumnConfig(key="quality", label="Quality", width=100, format_fn=lambda v: f"{v}%"),
        ]

        config = TableConfig(
            columns=columns,
            row_height=52,
            virtualized=True,
        )

        data = [
            {"rank": 1, "model": "Qwen3-8B", "score": 847, "grade": "A", "ttft": 120, "tps": 87, "vram": 6.2, "quality": 81},
            {"rank": 2, "model": "Gemma3-9B", "score": 823, "grade": "A", "ttft": 95, "tps": 92, "vram": 7.1, "quality": 79},
            {"rank": 3, "model": "Llama3.1-8B", "score": 791, "grade": "B", "ttft": 150, "tps": 70, "vram": 8.4, "quality": 83},
        ]

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Text("Leaderboard", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                    content=VirtualizedTable(config=config, data=data),
                ),
            ],
            spacing=0,
        )

    def _remove_model(self, model: str):
        """Remove model from comparison."""
        self._selected_models.remove(model)
        self._rebuild()

    def _add_model(self, _):
        """Add model to comparison."""
        self.show_snackbar("Model selection dialog coming soon", "info")

    def _rebuild(self):
        """Rebuild page after model changes."""
        # Would need to rebuild the whole page
        pass


import random
def random_noise() -> float:
    return random.uniform(-1, 1)