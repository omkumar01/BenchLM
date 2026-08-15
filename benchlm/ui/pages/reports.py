"""Reports page - Generate and export benchmark reports."""

import flet as ft
from typing import Optional

from benchlm.ui.pages.base import BasePage
from benchlm.ui.widgets import (
    GlassCard,
    FormField,
    FormFieldConfig,
    FormFieldType,
    SelectField,
    ToggleField,
    SegmentedButton,
)
from benchlm.ui.theme import get_theme
from benchlm.config import get_config


class ReportsPage(BasePage):
    """Reports page for generating and exporting benchmark reports."""

    def __init__(self, page: ft.Page, **kwargs):
        self._theme = get_theme()
        self._config = get_config()
        self._report_type = "single"  # single, comparison, trend
        super().__init__(page, route="/reports", title="Reports", icon=ft.Icons.DESCRIPTION, **kwargs)

    def _build(self):
        """Build reports page UI."""
        c = self._theme.colors

        # Header
        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Reports", size=self._theme.typography.headline_medium, weight=ft.FontWeight.BOLD, color=c.on_background),
                        ft.Text("Generate professional benchmark reports", size=self._theme.typography.body_medium, color=c.on_surface_variant),
                    ],
                    spacing=4,
                ),
                ft.Container(expand=True),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Report Type Selector
        self._type_selector = SegmentedButton(
            options=[
                ("single", "Single Run", ft.Icons.ARTICLE),
                ("comparison", "Comparison", ft.Icons.COMPARE_ARROWS),
                ("trend", "Trend Report", ft.Icons.TRENDING_UP),
            ],
            selected_key=self._report_type,
            on_change=self._on_type_change,
        )

        # Content
        self._content_area = ft.Column(
            controls=[self._build_single_report()],
            expand=True,
        )

        # Main content
        self.content = ft.Column(
            controls=[
                header,
                ft.Container(height=24),
                self._type_selector,
                ft.Container(height=16),
                self._content_area,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _on_type_change(self, rtype: str):
        """Handle report type change."""
        self._report_type = rtype
        types = {
            "single": self._build_single_report,
            "comparison": self._build_comparison_report,
            "trend": self._build_trend_report,
        }
        self._content_area.controls = [types[rtype]()]
        self._content_area.update()

    def _build_single_report(self) -> ft.Control:
        """Build single run report builder."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Text("Report Configuration", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            # Run Selection
                            ft.Text("Select Benchmark Run", size=14, weight=ft.FontWeight.W_500, color=c.on_surface),
                            ft.Container(height=8),
                            SelectField(
                                options=[
                                    ("latest", "Latest Run (Qwen3-8B - 2026-08-14)"),
                                    ("run_001", "Gemma3-9B - 2026-08-13"),
                                    ("run_002", "Llama3.1-8B - 2026-08-12"),
                                    ("run_003", "Qwen3-8B - 2026-08-11"),
                                ],
                                label="Benchmark Run",
                            ),
                            ft.Container(height=24),

                            # Sections to Include
                            ft.Text("Sections to Include", size=14, weight=ft.FontWeight.W_500, color=c.on_surface),
                            ft.Container(height=8),
                            ft.Column(
                                controls=[
                                    ToggleField(label="Hardware Configuration", value=True),
                                    ToggleField(label="Model Information", value=True),
                                    ToggleField(label="Latency Analysis", value=True),
                                    ToggleField(label="Throughput Analysis", value=True),
                                    ToggleField(label="Memory Analysis", value=True),
                                    ToggleField(label="CPU/GPU Utilization", value=True),
                                    ToggleField(label="Thermal & Power", value=True),
                                    ToggleField(label="Context Scaling", value=False),
                                    ToggleField(label="Concurrency Analysis", value=False),
                                    ToggleField(label="Quality Benchmarks", value=True),
                                    ToggleField(label="Reliability Metrics", value=True),
                                    ToggleField(label="Statistical Summary", value=True),
                                    ToggleField(label="Leaderboard Comparison", value=True),
                                    ToggleField(label="Radar Chart", value=True),
                                    ToggleField(label="Recommendations", value=True),
                                ],
                                spacing=8,
                            ),
                            ft.Container(height=24),

                            # Export Format
                            ft.Text("Export Format", size=14, weight=ft.FontWeight.W_500, color=c.on_surface),
                            ft.Container(height=8),
                            ft.Row(
                                controls=[
                                    ToggleField(label="PDF", value=True),
                                    ToggleField(label="HTML", value=True),
                                    ToggleField(label="CSV", value=False),
                                    ToggleField(label="JSON", value=False),
                                ],
                                spacing=24,
                                wrap=True,
                            ),
                            ft.Container(height=24),

                            # PDF Options
                            ft.Text("PDF Options", size=14, weight=ft.FontWeight.W_500, color=c.on_surface),
                            ft.Container(height=8),
                            ft.Row(
                                controls=[
                                    ToggleField(label="Include Charts", value=self._config.exports.include_charts_in_pdf),
                                    ToggleField(label="Include Raw Data", value=self._config.exports.include_raw_data),
                                ],
                                spacing=24,
                            ),
                            ft.Container(height=24),

                            # Output Directory
                            FormField(
                                config=FormFieldConfig(label="Output Directory", hint=self._config.exports.default_directory),
                                value=self._config.exports.default_directory,
                            ),
                            ft.Container(height=24),

                            # Generate Button
                            ft.FilledButton(
                                content=ft.Text("Generate Report"),
                                icon=ft.Icons.DESCRIPTION,
                                on_click=self._generate_report,
                                style=self._theme.button_primary_style(),
                            ),
                        ],
                    ),
                ),
            ],
            spacing=0,
        )

    def _build_comparison_report(self) -> ft.Control:
        """Build comparison report builder."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Text("Comparison Report", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            ft.Text("Select models to compare", size=14, color=c.on_surface_variant),
                            ft.Container(height=16),
                            ft.Text("Model selection UI coming soon", size=14, color=c.on_surface_variant, text_align=ft.TextAlign.CENTER),
                            ft.Container(height=24),
                            ft.FilledButton(
                                content=ft.Text("Generate Comparison Report"),
                                icon=ft.Icons.COMPARE_ARROWS,
                                on_click=self._generate_comparison,
                                style=self._theme.button_primary_style(),
                            ),
                        ],
                    ),
                ),
            ],
            spacing=0,
        )

    def _build_trend_report(self) -> ft.Control:
        """Build trend report builder."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Text("Trend Report", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            ft.Text("Historical trend analysis report", size=14, color=c.on_surface_variant),
                            ft.Container(height=16),
                            FormField(
                                config=FormFieldConfig(label="Date Range", hint="Last 30 days"),
                            ),
                            ft.Container(height=16),
                            SelectField(
                                options=[
                                    ("all", "All Models"),
                                    ("qwen3-8b", "Qwen3-8B"),
                                    ("gemma3-9b", "Gemma3-9B"),
                                ],
                                label="Model Filter",
                            ),
                            ft.Container(height=24),
                            ft.FilledButton(
                                content=ft.Text("Generate Trend Report"),
                                icon=ft.Icons.TRENDING_UP,
                                on_click=self._generate_trend,
                                style=self._theme.button_primary_style(),
                            ),
                        ],
                    ),
                ),
            ],
            spacing=0,
        )

    def _generate_report(self, _):
        """Generate single run report."""
        self.show_snackbar("Generating report...", "info")
        # TODO: Implement actual report generation

    def _generate_comparison(self, _):
        """Generate comparison report."""
        self.show_snackbar("Generating comparison report...", "info")

    def _generate_trend(self, _):
        """Generate trend report."""
        self.show_snackbar("Generating trend report...", "info")