"""Benchmark page - Configure and run benchmarks."""

import flet as ft
from typing import Optional, List
from dataclasses import dataclass

from benchlm.ui.pages.base import BasePage
from benchlm.ui.widgets import (
    GlassCard,
    FormField,
    FormFieldConfig,
    NumberField,
    SliderField,
    SelectField,
    ToggleField,
    SegmentedButton,
    FormFieldType,
)
from benchlm.ui.theme import get_theme
from benchlm.config import get_config
from benchlm.database.models import BenchmarkStatus


class BenchmarkPage(BasePage):
    """Benchmark configuration and execution page."""

    def __init__(self, page: ft.Page, **kwargs):
        self._theme = get_theme()
        self._config = get_config()
        self._selected_models: List[str] = []
        self._benchmark_running = False
        super().__init__(page, route="/benchmark", title="Benchmark", icon=ft.Icons.SPEED, **kwargs)

    def _build(self):
        """Build benchmark page UI."""
        c = self._theme.colors

        # Header
        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Benchmark", size=self._theme.typography.headline_medium, weight=ft.FontWeight.BOLD, color=c.on_background),
                        ft.Text("Configure and run performance benchmarks", size=self._theme.typography.body_medium, color=c.on_surface_variant),
                    ],
                    spacing=4,
                ),
                ft.Container(expand=True),
                self._build_run_button(),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Model Selection Section
        model_section = GlassCard(
            header=ft.Text("Model Selection", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
            content=ft.Column(
                controls=[
                    ft.Text(
                        "No models selected. Go to Models page to select models for benchmarking.",
                        size=14,
                        color=c.on_surface_variant,
                        text_align=ft.TextAlign.CENTER,
                    ) if not self._selected_models else self._build_selected_models_chips(),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

        # Configuration Tabs
        self._config_tabs = ft.Tabs(
            tabs=[
                ft.Tab(text="Generation", icon=ft.Icons.SETTINGS),
                ft.Tab(text="Execution", icon=ft.Icons.PLAY_CIRCLE),
                ft.Tab(text="Prompts", icon=ft.Icons.ARTICLE),
                ft.Tab(text="Advanced", icon=ft.Icons.TUNE),
            ],
            selected_index=0,
            on_change=self._on_tab_change,
        )

        # Tab Content
        self._tab_content = ft.Column(
            controls=[
                self._build_generation_tab(),
            ],
            expand=True,
        )

        # Presets
        presets_section = GlassCard(
            header=ft.Row(
                controls=[
                    ft.Text("Presets", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                    ft.Container(expand=True),
                    ft.TextButton("Save Current as Preset", on_click=self._save_preset),
                ],
            ),
            content=self._build_presets(),
        )

        # Main layout
        self.content = ft.Column(
            controls=[
                header,
                ft.Container(height=24),
                model_section,
                ft.Container(height=24),
                self._config_tabs,
                ft.Container(height=16),
                self._tab_content,
                ft.Container(height=24),
                presets_section,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _build_run_button(self) -> ft.Control:
        """Build the run benchmark button."""
        c = self._theme.colors

        self._run_button = ft.FilledButton(
            content=ft.Text("Start Benchmark") if not self._benchmark_running else "Running...",
            icon=ft.Icons.PLAY_ARROW if not self._benchmark_running else ft.Icons.HOURGLASS_TOP,
            on_click=self._run_benchmark,
            disabled=not self._selected_models or self._benchmark_running,
            style=self._theme.button_primary_style(),
        )

        self._pause_button = ft.OutlinedButton(
            content=ft.Text("Pause"),
            icon=ft.Icons.PAUSE,
            on_click=self._pause_benchmark,
            visible=False,
            disabled=True,
        )

        self._stop_button = ft.OutlinedButton(
            content=ft.Text("Stop"),
            icon=ft.Icons.STOP,
            on_click=self._stop_benchmark,
            visible=False,
            disabled=True,
            style=ft.ButtonStyle(color=c.danger),
        )

        return ft.Row(
            controls=[
                self._run_button,
                ft.Container(width=8),
                self._pause_button,
                ft.Container(width=8),
                self._stop_button,
            ],
            spacing=8,
        )

    def _build_selected_models_chips(self) -> ft.Control:
        """Build chips for selected models."""
        c = self._theme.colors

        chips = []
        for model in self._selected_models:
            chips.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.MODEL_TRAINING, size=16, color=c.primary),
                            ft.Text(model, size=13, color=c.on_surface),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=16,
                                on_click=lambda _, m=model: self._remove_model(m),
                            ),
                        ],
                        spacing=8,
                    ),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                    bgcolor=c.primary_container,
                    border_radius=20,
                )
            )

        return ft.Row(
            controls=chips,
            spacing=8,
            wrap=True,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def _remove_model(self, model: str):
        """Remove model from selection."""
        self._selected_models.remove(model)
        self._update_run_button()
        self._rebuild_model_section()

    def _update_run_button(self):
        """Update run button state."""
        self._run_button.disabled = not self._selected_models or self._benchmark_running
        self._run_button.update()

    def _rebuild_model_section(self):
        """Rebuild model selection section."""
        # This would require rebuilding the card content
        pass

    def _build_generation_tab(self) -> ft.Column:
        """Build generation parameters tab."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                ft.Text("Generation Parameters", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                ft.Container(height=16),
                ft.ResponsiveRow(
                    controls=[
                        SliderField(
                            min_value=0.0,
                            max_value=2.0,
                            value=self._config.benchmark.temperature,
                            step=0.1,
                            label="Temperature",
                            unit="",
                            col={"xs": 12, "sm": 6, "md": 4},
                        ),
                        SliderField(
                            min_value=0.0,
                            max_value=1.0,
                            value=self._config.benchmark.top_p,
                            step=0.05,
                            label="Top-P",
                            unit="",
                            col={"xs": 12, "sm": 6, "md": 4},
                        ),
                        NumberField(
                            config=FormFieldConfig(label="Top-K", hint="0 = disabled"),
                            value=self._config.benchmark.top_k,
                            col={"xs": 12, "sm": 6, "md": 4},
                        ),
                        NumberField(
                            config=FormFieldConfig(label="Seed", hint="-1 = random"),
                            value=self._config.benchmark.seed,
                            col={"xs": 12, "sm": 6, "md": 4},
                        ),
                        NumberField(
                            config=FormFieldConfig(label="Max Tokens"),
                            value=self._config.benchmark.max_tokens,
                            col={"xs": 12, "sm": 6, "md": 4},
                        ),
                        NumberField(
                            config=FormFieldConfig(label="Context Length"),
                            value=self._config.benchmark.context_length,
                            col={"xs": 12, "sm": 6, "md": 4},
                        ),
                    ],
                    spacing=16,
                    run_spacing=16,
                ),
                ft.Container(height=16),
                ft.Divider(height=1, color=c.outline_variant),
                ft.Container(height=16),
                ft.Text("Sampling Options", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                ft.Container(height=16),
                ft.Row(
                    controls=[
                        ToggleField(
                            label="Streaming",
                            value=self._config.benchmark.streaming,
                        ),
                        ToggleField(
                            label="Use Cache",
                            value=True,
                        ),
                    ],
                    spacing=24,
                ),
            ],
            spacing=0,
        )

    def _build_execution_tab(self) -> ft.Column:
        """Build execution parameters tab."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                ft.Text("Execution Parameters", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                ft.Container(height=16),
                ft.ResponsiveRow(
                    controls=[
                        NumberField(
                            config=FormFieldConfig(label="Iterations"),
                            value=self._config.benchmark.iterations,
                            col={"xs": 12, "sm": 6, "md": 3},
                        ),
                        NumberField(
                            config=FormFieldConfig(label="Warmup Runs"),
                            value=self._config.benchmark.warmup_runs,
                            col={"xs": 12, "sm": 6, "md": 3},
                        ),
                        NumberField(
                            config=FormFieldConfig(label="Cooldown (s)"),
                            value=self._config.benchmark.cooldown_seconds,
                            col={"xs": 12, "sm": 6, "md": 3},
                        ),
                        NumberField(
                            config=FormFieldConfig(label="Concurrent Users"),
                            value=self._config.benchmark.concurrent_users,
                            col={"xs": 12, "sm": 6, "md": 3},
                        ),
                        NumberField(
                            config=FormFieldConfig(label="Batch Size"),
                            value=self._config.benchmark.batch_size,
                            col={"xs": 12, "sm": 6, "md": 3},
                        ),
                    ],
                    spacing=16,
                    run_spacing=16,
                ),
                ft.Container(height=16),
                ft.Divider(height=1, color=c.outline_variant),
                ft.Container(height=16),
                ft.Text("Load Test Configuration", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                ft.Container(height=16),
                ft.Text("Configure concurrent user simulation and load patterns", size=14, color=c.on_surface_variant),
            ],
            spacing=0,
        )

    def _build_prompts_tab(self) -> ft.Column:
        """Build prompts configuration tab."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                ft.Text("Prompt Configuration", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                ft.Container(height=16),
                FormField(
                    config=FormFieldConfig(
                        label="System Prompt",
                        hint="Optional system prompt for all requests",
                        keyboard_type=FormFieldType.MULTILINE,
                    ),
                    value=self._config.benchmark.system_prompt,
                ),
                ft.Container(height=16),
                SelectField(
                    options=[
                        ("builtin:general", "General Chat"),
                        ("builtin:coding", "Coding Tasks"),
                        ("builtin:reasoning", "Reasoning"),
                        ("builtin:creative", "Creative Writing"),
                        ("builtin:analysis", "Analysis & Summary"),
                        ("custom", "Custom Prompts"),
                    ],
                    value=self._config.benchmark.prompt_dataset,
                    label="Prompt Dataset",
                    hint="Select a built-in dataset or use custom prompts",
                ),
                ft.Container(height=16),
                ft.Text("Custom Prompts (one per line)", size=14, weight=ft.FontWeight.W_500, color=c.on_surface),
                ft.Container(height=8),
                FormField(
                    config=FormFieldConfig(
                        label="Custom Prompts",
                        hint="Enter custom prompts, one per line",
                        keyboard_type=FormFieldType.MULTILINE,
                    ),
                    value="",
                ),
            ],
            spacing=0,
        )

    def _build_advanced_tab(self) -> ft.Column:
        """Build advanced options tab."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                ft.Text("Advanced Options", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                ft.Container(height=16),
                ft.Text("Hardware Monitoring", size=14, weight=ft.FontWeight.W_500, color=c.on_surface),
                ft.Container(height=8),
                ft.Row(
                    controls=[
                        ToggleField(label="CPU Monitoring", value=True),
                        ToggleField(label="GPU Monitoring", value=True),
                        ToggleField(label="Memory Tracking", value=True),
                        ToggleField(label="Power Tracking", value=True),
                    ],
                    spacing=16,
                    wrap=True,
                ),
                ft.Container(height=16),
                ft.Text("Quality Benchmarks", size=14, weight=ft.FontWeight.W_500, color=c.on_surface),
                ft.Container(height=8),
                ft.Row(
                    controls=[
                        ToggleField(label="MMLU", value=True),
                        ToggleField(label="HumanEval", value=True),
                        ToggleField(label="GSM8K", value=True),
                        ToggleField(label="Needle in Haystack", value=True),
                    ],
                    spacing=16,
                    wrap=True,
                ),
                ft.Container(height=16),
                ft.Text("Export Options", size=14, weight=ft.FontWeight.W_500, color=c.on_surface),
                ft.Container(height=8),
                ft.Row(
                    controls=[
                        ToggleField(label="Auto-export CSV", value=True),
                        ToggleField(label="Auto-export JSON", value=False),
                        ToggleField(label="Auto-export HTML", value=False),
                        ToggleField(label="Auto-export PDF", value=False),
                    ],
                    spacing=16,
                    wrap=True,
                ),
            ],
            spacing=0,
        )

    def _build_presets(self) -> ft.Control:
        """Build presets selector."""
        c = self._theme.colors

        presets = [
            ("Quick Test", "Fast benchmark with minimal iterations", ft.Icons.SPEED),
            ("Standard", "Balanced benchmark for general comparison", ft.Icons.BALANCE),
            ("Comprehensive", "Full benchmark suite with quality tests", ft.Icons.ANALYTICS),
            ("Load Test", "High concurrency stress test", ft.Icons.TRENDING_UP),
            ("Quality Focus", "Extended quality benchmarks", ft.Icons.VERIFIED),
        ]

        cards = []
        for name, desc, icon in presets:
            cards.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(icon, size=24, color=c.primary),
                            ft.Container(width=16),
                            ft.Column(
                                controls=[
                                    ft.Text(name, size=14, weight=ft.FontWeight.W_600, color=c.on_surface),
                                    ft.Text(desc, size=12, color=c.on_surface_variant),
                                ],
                                spacing=2,
                            ),
                            ft.Container(expand=True),
                            ft.TextButton("Load", on_click=lambda _, n=name: self._load_preset(n)),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=16,
                    border=ft.Border.all(1, c.outline_variant),
                    border_radius=12,
                    ink=True,
                    on_click=lambda _, n=name: self._load_preset(n),
                )
            )

        return ft.Column(
            controls=cards,
            spacing=12,
        )

    def _on_tab_change(self, e: ft.ControlEvent):
        """Handle tab change."""
        tab_index = e.control.selected_index
        tabs_content = [
            self._build_generation_tab(),
            self._build_execution_tab(),
            self._build_prompts_tab(),
            self._build_advanced_tab(),
        ]
        self._tab_content.controls = [tabs_content[tab_index]]
        self._tab_content.update()

    def _load_preset(self, name: str):
        """Load a benchmark preset."""
        presets = {
            "Quick Test": {"iterations": 3, "warmup_runs": 1, "concurrent_users": 1},
            "Standard": {"iterations": 10, "warmup_runs": 2, "concurrent_users": 1},
            "Comprehensive": {"iterations": 20, "warmup_runs": 3, "concurrent_users": 1},
            "Load Test": {"iterations": 10, "warmup_runs": 2, "concurrent_users": 10},
            "Quality Focus": {"iterations": 5, "warmup_runs": 2, "concurrent_users": 1},
        }

        if name in presets:
            preset = presets[name]
            # Update config
            self._config.benchmark.iterations = preset["iterations"]
            self._config.benchmark.warmup_runs = preset["warmup_runs"]
            self._config.benchmark.concurrent_users = preset["concurrent_users"]
            self.show_snackbar(f"Loaded {name} preset", "success")
            # Refresh current tab
            self._on_tab_change(ft.ControlEvent(self._config_tabs, "", self._config_tabs.selected_index, None))

    def _save_preset(self):
        """Save current configuration as preset."""
        # TODO: Implement preset saving
        self.show_snackbar("Preset saving coming soon", "info")

    async def _run_benchmark(self, _):
        """Start benchmark execution."""
        if not self._selected_models:
            self.show_snackbar("Please select at least one model", "warning")
            return

        self._benchmark_running = True
        self._run_button.visible = False
        self._pause_button.visible = True
        self._stop_button.visible = True
        self._run_button.update()
        self._pause_button.update()
        self._stop_button.update()

        self.show_snackbar("Benchmark started...", "info")
        self.navigate("/live-monitor")

    async def _pause_benchmark(self, _):
        """Pause benchmark."""
        self.show_snackbar("Benchmark paused", "warning")

    async def _stop_benchmark(self, _):
        """Stop benchmark."""
        self._benchmark_running = False
        self._run_button.visible = True
        self._pause_button.visible = False
        self._stop_button.visible = False
        self._run_button.text = "Start Benchmark"
        self._run_button.icon = ft.Icons.PLAY_ARROW
        self._run_button.update()
        self._pause_button.update()
        self._stop_button.update()
        self.show_snackbar("Benchmark stopped", "info")