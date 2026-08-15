"""Leaderboard page - Global model rankings with Elo ratings."""

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
    SegmentedButton,
)
from benchlm.ui.theme import get_theme
from benchlm.config import get_config

import plotly.graph_objects as go


class LeaderboardPage(BasePage):
    """Leaderboard page with global model rankings."""

    def __init__(self, page: ft.Page, **kwargs):
        self._theme = get_theme()
        self._config = get_config()
        self._leaderboard_mode = "global"  # global, by_category, by_hardware
        super().__init__(page, route="/leaderboard", title="Leaderboard", icon=ft.Icons.LEADERBOARD, **kwargs)

    def _build(self):
        """Build leaderboard page UI."""
        c = self._theme.colors

        # Header
        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Leaderboard", size=self._theme.typography.headline_medium, weight=ft.FontWeight.BOLD, color=c.on_background),
                        ft.Text("Global model rankings and Elo ratings", size=self._theme.typography.body_medium, color=c.on_surface_variant),
                    ],
                    spacing=4,
                ),
                ft.Container(expand=True),
                ft.Row(
                    controls=[
                        SegmentedButton(
                            options=[
                                ("global", "Global", ft.Icons.PUBLIC),
                                ("by_category", "By Category", ft.Icons.CATEGORY),
                                ("by_hardware", "By Hardware", ft.Icons.MEMORY),
                            ],
                            selected_key=self._leaderboard_mode,
                            on_change=self._on_mode_change,
                        ),
                    ],
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Top 3 Podium
        self._build_podium()

        # Leaderboard Table
        self._leaderboard_content = ft.Column(
            controls=[self._build_global_leaderboard()],
            expand=True,
        )

        # Charts Section
        self._charts_section = ft.Column(
            controls=[self._build_elo_chart()],
        )

        # Main content
        self.content = ft.Column(
            controls=[
                header,
                ft.Container(height=24),
                self._podium_row,
                ft.Container(height=24),
                self._leaderboard_content,
                ft.Container(height=24),
                self._charts_section,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _build_podium(self):
        """Build top 3 podium."""
        c = self._theme.colors

        podium_data = [
            (1, "Qwen3-8B", "Ollama", 1542, 847, "A", c.warning),  # Gold
            (2, "Gemma3-9B", "Ollama", 1518, 823, "A", c.outline),   # Silver
            (3, "Llama3.1-8B", "llama.cpp", 1487, 791, "B", c.tertiary),  # Bronze
        ]

        podium_cards = []
        for rank, model, provider, elo, score, grade, color in podium_data:
            height = 280 if rank == 1 else (220 if rank == 2 else 180)
            podium_cards.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Container(
                                content=ft.Text(f"#{rank}", size=48 if rank == 1 else (36 if rank == 2 else 28), weight=ft.FontWeight.BOLD, color=color),
                                alignment=ft.Alignment.CENTER,
                                padding=ft.Padding.only(top=24),
                            ),
                            ft.Container(height=16),
                            ft.Text(model, size=24 if rank == 1 else (20 if rank == 2 else 18), weight=ft.FontWeight.BOLD, color=c.on_surface, text_align=ft.TextAlign.CENTER),
                            ft.Text(provider, size=14, color=c.on_surface_variant, text_align=ft.TextAlign.CENTER),
                            ft.Container(height=16),
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("Elo Rating", size=12, color=c.on_surface_variant),
                                    ft.Text(str(elo), size=28, weight=ft.FontWeight.BOLD, color=color),
                                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                                padding=ft.Padding.symmetric(vertical=16),
                                bgcolor=color + "20",
                                border_radius=12,
                                margin=ft.Margin.symmetric(horizontal=24),
                            ),
                            ft.Container(height=16),
                            ft.Row(
                                controls=[
                                    ft.Column([
                                        ft.Text("Score", size=11, color=c.on_surface_variant),
                                        ft.Text(f"{score}/1000", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                                    ft.Column([
                                        ft.Text("Grade", size=11, color=c.on_surface_variant),
                                        ft.Text(grade, size=16, weight=ft.FontWeight.BOLD, color=color),
                                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
                                ],
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    width=220,
                    height=height,
                    bgcolor=c.surface,
                    border=ft.Border.all(2, color) if rank == 1 else ft.Border.all(1, c.outline_variant),
                    border_radius=16,
                    alignment=ft.Alignment.CENTER,
                )
            )

        # Order: 2nd, 1st, 3rd for visual podium effect
        self._podium_row = ft.Row(
            controls=[
                ft.Container(content=podium_cards[1], alignment=ft.Alignment.BOTTOM_CENTER, expand=True),
                ft.Container(content=podium_cards[0], alignment=ft.Alignment.BOTTOM_CENTER, expand=True),
                ft.Container(content=podium_cards[2], alignment=ft.Alignment.BOTTOM_CENTER, expand=True),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=24,
        )

    def _on_mode_change(self, mode: str):
        """Handle leaderboard mode change."""
        self._leaderboard_mode = mode
        modes = {
            "global": self._build_global_leaderboard,
            "by_category": self._build_category_leaderboard,
            "by_hardware": self._build_hardware_leaderboard,
        }
        self._leaderboard_content.controls = [modes[mode]()]
        self._leaderboard_content.update()

    def _build_global_leaderboard(self) -> ft.Control:
        """Build global leaderboard table."""
        c = self._theme.colors

        columns = [
            ColumnConfig(key="rank", label="#", width=50, sortable=False),
            ColumnConfig(key="model", label="Model", min_width=180),
            ColumnConfig(key="provider", label="Provider", width=130),
            ColumnConfig(key="elo", label="Elo", width=80, format_fn=lambda v: str(v)),
            ColumnConfig(key="score", label="Score", width=100, format_fn=lambda v: f"{v}/1000"),
            ColumnConfig(key="grade", label="Grade", width=80),
            ColumnConfig(key="ttft", label="TTFT", width=100, format_fn=lambda v: f"{v}ms"),
            ColumnConfig(key="tps", label="TPS", width=100),
            ColumnConfig(key="vram", label="VRAM", width=100, format_fn=lambda v: f"{v} GB"),
            ColumnConfig(key="quality", label="Quality", width=100, format_fn=lambda v: f"{v}%"),
            ColumnConfig(key="runs", label="Runs", width=80),
        ]

        config = TableConfig(
            columns=columns,
            row_height=52,
            virtualized=True,
            on_row_click=self._on_model_click,
        )

        # Extended mock data
        models = [
            ("Qwen3-8B", "Ollama", 1542, 847, "A", 120, 87, 6.2, 81, 12),
            ("Gemma3-9B", "Ollama", 1518, 823, "A", 95, 92, 7.1, 79, 8),
            ("Llama3.1-8B", "llama.cpp", 1487, 791, "B", 150, 70, 8.4, 83, 15),
            ("Phi3-mini", "LM Studio", 1423, 712, "B", 89, 112, 3.8, 74, 5),
            ("Mistral-7B", "vLLM", 1398, 689, "B", 110, 95, 5.2, 76, 7),
            ("Yi-34B", "Ollama", 1356, 645, "C", 210, 45, 19.8, 85, 4),
            ("CodeLlama-13B", "llama.cpp", 1312, 598, "C", 180, 58, 12.1, 78, 3),
            ("Zephyr-7B", "Ollama", 1289, 572, "C", 135, 82, 6.5, 72, 6),
        ]

        data = [
            {
                "rank": i + 1,
                "model": m[0],
                "provider": m[1],
                "elo": m[2],
                "score": m[3],
                "grade": m[4],
                "ttft": m[5],
                "tps": m[6],
                "vram": m[7],
                "quality": m[8],
                "runs": m[9],
            }
            for i, m in enumerate(models)
        ]

        return GlassCard(
            header=ft.Row([
                ft.Text("Global Rankings", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                ft.Container(expand=True),
                ft.Text(f"{len(data)} models ranked", size=13, color=c.on_surface_variant),
            ]),
            content=VirtualizedTable(config=config, data=data),
        )

    def _build_category_leaderboard(self) -> ft.Control:
        """Build category-specific leaderboards."""
        c = self._theme.colors

        categories = {
            "Speed": [
                ("Phi3-mini", "LM Studio", 89, 112),
                ("Gemma3-9B", "Ollama", 95, 92),
                ("Zephyr-7B", "Ollama", 135, 82),
            ],
            "Quality": [
                ("Yi-34B", "Ollama", 85),
                ("Llama3.1-8B", "llama.cpp", 83),
                ("Qwen3-8B", "Ollama", 81),
            ],
            "Efficiency": [
                ("Phi3-mini", "LM Studio", 3.8),
                ("Gemma3-9B", "Ollama", 7.1),
                ("Mistral-7B", "vLLM", 5.2),
            ],
            "Reliability": [
                ("Llama3.1-8B", "llama.cpp", 99.9),
                ("Qwen3-8B", "Ollama", 99.8),
                ("Mistral-7B", "vLLM", 99.7),
            ],
        }

        cards = []
        for cat, entries in categories.items():
            rows = []
            for i, entry in enumerate(entries):
                rows.append(
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Text(f"#{i+1}", size=13, weight=ft.FontWeight.BOLD, color=c.primary, width=30),
                                ft.Text(entry[0], size=13, weight=ft.FontWeight.W_500, color=c.on_surface, expand=True),
                                ft.Text(entry[1], size=12, color=c.on_surface_variant, width=100),
                                ft.Text(str(entry[2]) + (entry[3] if len(entry) > 3 else ""), size=13, weight=ft.FontWeight.W_600, color=c.on_surface, width=80),
                            ],
                        ),
                        padding=ft.Padding.symmetric(vertical=8, horizontal=12),
                        border=ft.Border.only(bottom=ft.BorderSide(1, c.outline_variant)) if i < len(entries) - 1 else None,
                    )
                )

            cards.append(
                GlassCard(
                    header=ft.Text(cat, size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                    content=ft.Column(controls=rows, spacing=0),
                )
            )

        return ft.Column(
            controls=cards,
            spacing=16,
        )

    def _build_hardware_leaderboard(self) -> ft.Control:
        """Build hardware-specific leaderboards."""
        c = self._theme.colors

        return GlassCard(
            header=ft.Text("By Hardware", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
            content=ft.Text("Hardware-specific rankings coming soon (RTX 4090, A100, M3 Max, etc.)", size=14, color=c.on_surface_variant, text_align=ft.TextAlign.CENTER),
        )

    def _build_elo_chart(self) -> ft.Control:
        """Build Elo rating chart."""
        c = self._theme.colors

        def create_elo_chart():
            fig = go.Figure()

            models = ["Qwen3-8B", "Gemma3-9B", "Llama3.1-8B", "Phi3-mini", "Mistral-7B", "Yi-34B", "CodeLlama-13B", "Zephyr-7B"]
            elo_ratings = [1542, 1518, 1487, 1423, 1398, 1356, 1312, 1289]
            colors = [c.warning, c.outline, c.tertiary, c.primary, c.secondary, c.success, c.danger, c.tertiary]

            fig.add_trace(go.Bar(
                x=models,
                y=elo_ratings,
                marker=dict(color=colors),
                text=[str(e) for e in elo_ratings],
                textposition='outside',
            ))

            fig.update_layout(
                title="Elo Ratings Distribution",
                xaxis_title="Model",
                yaxis_title="Elo Rating",
                height=400,
                showlegend=False,
            )
            return fig

        def create_scatter_chart():
            fig = go.Figure()

            # Speed vs Quality scatter
            models = ["Qwen3-8B", "Gemma3-9B", "Llama3.1-8B", "Phi3-mini", "Mistral-7B", "Yi-34B"]
            ttft = [120, 95, 150, 89, 110, 210]
            quality = [81, 79, 83, 74, 76, 85]
            tps = [87, 92, 70, 112, 95, 45]
            colors = [c.primary, c.secondary, c.tertiary, c.primary, c.secondary, c.success]

            for i, model in enumerate(models):
                fig.add_trace(go.Scatter(
                    x=[ttft[i]],
                    y=[quality[i]],
                    mode='markers+text',
                    name=model,
                    text=[model],
                    textposition='top center',
                    marker=dict(size=tps[i]/2 + 10, color=colors[i], opacity=0.8),
                    showlegend=False,
                ))

            fig.update_layout(
                title="Speed vs Quality (bubble size = TPS)",
                xaxis_title="TTFT (ms, lower is better)",
                yaxis_title="Quality Score (%)",
                height=400,
            )
            return fig

        return ft.Row(
            controls=[
                ft.Container(content=ChartContainer(
                    chart=LazyPlotlyChart(create_elo_chart, ChartConfig(height=400)),
                    title="Elo Ratings",
                ), expand=True),
                ft.Container(width=16),
                ft.Container(content=ChartContainer(
                    chart=LazyPlotlyChart(create_scatter_chart, ChartConfig(height=400)),
                    title="Speed vs Quality",
                ), expand=True),
            ],
            spacing=0,
        )

    def _on_model_click(self, model_data: dict):
        """Handle model click in leaderboard."""
        self.show_snackbar(f"Viewing details for {model_data.get('model', 'Unknown')}", "info")


import random
def random_noise() -> float:
    return random.uniform(-1, 1)