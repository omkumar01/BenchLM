"""Settings page - Application settings and preferences."""

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
    SliderField,
    ColorPickerField,
    FilePickerField,
    SegmentedButton,
)
from benchlm.ui.theme import get_theme
from benchlm.config import get_config


class SettingsPage(BasePage):
    """Settings page with all application preferences."""

    def __init__(self, page: ft.Page, **kwargs):
        super().__init__(page, route="/settings", title="Settings", icon=ft.Icons.SETTINGS, **kwargs)
        self._theme = get_theme()
        self._config = get_config()
        self._settings_tab = "general"  # general, appearance, benchmark, hardware, exports, advanced
        self._build()

    def _build(self):
        """Build settings page UI."""
        c = self._theme.colors

        # Header
        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Settings", size=self._theme.typography.headline_medium, weight=ft.FontWeight.BOLD, color=c.on_background),
                        ft.Text("Configure application preferences", size=self._theme.typography.body_medium, color=c.on_surface_variant),
                    ],
                    spacing=4,
                ),
                ft.Container(expand=True),
                ft.FilledButton(
                    text="Reset to Defaults",
                    icon=ft.Icons.RESTORE,
                    on_click=self._reset_defaults,
                    style=ft.ButtonStyle(color=c.danger),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Settings Tabs
        self._tabs = ft.Tabs(
            tabs=[
                ft.Tab(text="General", icon=ft.Icons.SETTINGS),
                ft.Tab(text="Appearance", icon=ft.Icons.PALETTE),
                ft.Tab(text="Benchmark", icon=ft.Icons.SPEED),
                ft.Tab(text="Hardware", icon=ft.Icons.MEMORY),
                ft.Tab(text="Exports", icon=ft.Icons.DOWNLOAD),
                ft.Tab(text="Advanced", icon=ft.Icons.TUNE),
            ],
            selected_index=0,
            on_change=self._on_tab_change,
            scrollable=True,
        )

        # Tab Content
        self._tab_content = ft.Column(
            controls=[self._build_general_tab()],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )

        # Main content
        self.content = ft.Column(
            controls=[
                header,
                ft.Container(height=24),
                self._tabs,
                ft.Container(height=16),
                self._tab_content,
            ],
            spacing=0,
            expand=True,
        )

    def _on_tab_change(self, e: ft.ControlEvent):
        """Handle tab change."""
        tabs = [
            self._build_general_tab,
            self._build_appearance_tab,
            self._build_benchmark_tab,
            self._build_hardware_tab,
            self._build_exports_tab,
            self._build_advanced_tab,
        ]
        self._tab_content.controls = [tabs[e.control.selected_index]()]
        self._tab_content.update()

    def _build_general_tab(self) -> ft.Control:
        """Build general settings tab."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Text("Application", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            SelectField(
                                options=[
                                    ("dark", "Dark"),
                                    ("light", "Light"),
                                    ("system", "System"),
                                ],
                                value=self._config.app.theme,
                                label="Theme",
                                on_change=lambda v: self._update_config("app.theme", v),
                            ),
                            ft.Container(height=16),
                            ColorPickerField(
                                value=self._config.app.accent_color,
                                label="Accent Color",
                                on_change=lambda v: self._update_config("app.accent_color", v),
                            ),
                            ft.Container(height=16),
                            SelectField(
                                options=[
                                    ("en", "English"),
                                    ("zh", "Chinese"),
                                    ("es", "Spanish"),
                                    ("fr", "French"),
                                    ("de", "German"),
                                    ("ja", "Japanese"),
                                ],
                                value=self._config.app.language,
                                label="Language",
                                on_change=lambda v: self._update_config("app.language", v),
                            ),
                        ],
                    ),
                ),
                ft.Container(height=16),
                GlassCard(
                    header=ft.Text("Data & Storage", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            FormField(
                                config=FormFieldConfig(label="Data Directory", hint=self._config.app.data_dir),
                                value=self._config.app.data_dir,
                            ),
                            ft.Container(height=16),
                            SelectField(
                                options=[
                                    ("DEBUG", "Debug"),
                                    ("INFO", "Info"),
                                    ("WARNING", "Warning"),
                                    ("ERROR", "Error"),
                                ],
                                value=self._config.app.log_level,
                                label="Log Level",
                                on_change=lambda v: self._update_config("app.log_level", v),
                            ),
                            ft.Container(height=16),
                            ToggleField(
                                label="Auto-save benchmark configurations",
                                value=True,
                                on_change=lambda v: self._update_config("benchmark.auto_save", v),
                            ),
                        ],
                    ),
                ),
                ft.Container(height=16),
                GlassCard(
                    header=ft.Text("Default Provider", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            SelectField(
                                options=[
                                    ("ollama", "Ollama"),
                                    ("llama_cpp", "llama.cpp"),
                                    ("lmstudio", "LM Studio"),
                                    ("vllm", "vLLM"),
                                    ("openai_compatible", "OpenAI Compatible"),
                                ],
                                value=self._config.benchmark.default_provider,
                                label="Default Provider",
                                on_change=lambda v: self._update_config("benchmark.default_provider", v),
                            ),
                            ft.Container(height=16),
                            FormField(
                                config=FormFieldConfig(label="Ollama Host", hint=self._config.benchmark.ollama_host),
                                value=self._config.benchmark.ollama_host,
                            ),
                            ft.Container(height=8),
                            FormField(
                                config=FormFieldConfig(label="llama.cpp Host", hint=self._config.benchmark.llama_cpp_host),
                                value=self._config.benchmark.llama_cpp_host,
                            ),
                            ft.Container(height=8),
                            FormField(
                                config=FormFieldConfig(label="LM Studio Host", hint=self._config.benchmark.lmstudio_host),
                                value=self._config.benchmark.lmstudio_host,
                            ),
                            ft.Container(height=8),
                            FormField(
                                config=FormFieldConfig(label="vLLM Host", hint=self._config.benchmark.vllm_host),
                                value=self._config.benchmark.vllm_host,
                            ),
                        ],
                    ),
                ),
            ],
            spacing=0,
        )

    def _build_appearance_tab(self) -> ft.Control:
        """Build appearance settings tab."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Text("UI Customization", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            ToggleField(
                                label="Glassmorphism Panels",
                                value=self._config.ui.glassmorphism_enabled,
                                on_change=lambda v: self._update_config("ui.glassmorphism_enabled", v),
                            ),
                            ft.Container(height=8),
                            ToggleField(
                                label="Smooth Animations",
                                value=self._config.ui.animations_enabled,
                                on_change=lambda v: self._update_config("ui.animations_enabled", v),
                            ),
                            ft.Container(height=8),
                            ToggleField(
                                label="Compact Mode",
                                value=self._config.ui.compact_mode,
                                on_change=lambda v: self._update_config("ui.compact_mode", v),
                            ),
                            ft.Container(height=16),
                            FormField(
                                config=FormFieldConfig(label="Card Border Radius", hint=str(self._config.ui.card_border_radius)),
                                value=str(self._config.ui.card_border_radius),
                                on_change=lambda v: self._update_config("ui.card_border_radius", int(v) if v.isdigit() else 16),
                            ),
                            ft.Container(height=16),
                            FormField(
                                config=FormFieldConfig(label="Sidebar Width", hint=str(self._config.ui.sidebar_width)),
                                value=str(self._config.ui.sidebar_width),
                                on_change=lambda v: self._update_config("ui.sidebar_width", int(v) if v.isdigit() else 280),
                            ),
                        ],
                    ),
                ),
                ft.Container(height=16),
                GlassCard(
                    header=ft.Text("Mobile Optimization", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            ToggleField(
                                label="Mobile Optimized Layout",
                                value=self._config.ui.mobile_optimization,
                                on_change=lambda v: self._update_config("ui.mobile_optimization", v),
                            ),
                            ft.Container(height=8),
                            ToggleField(
                                label="Touch Friendly Controls",
                                value=self._config.ui.touch_friendly,
                                on_change=lambda v: self._update_config("ui.touch_friendly", v),
                            ),
                            ft.Container(height=16),
                            FormField(
                                config=FormFieldConfig(label="Table Virtualization Threshold", hint=str(self._config.ui.table_virtualization_threshold)),
                                value=str(self._config.ui.table_virtualization_threshold),
                                on_change=lambda v: self._update_config("ui.table_virtualization_threshold", int(v) if v.isdigit() else 1000),
                            ),
                            ft.Container(height=8),
                            ToggleField(
                                label="Lazy Load Charts",
                                value=self._config.ui.chart_lazy_load,
                                on_change=lambda v: self._update_config("ui.chart_lazy_load", v),
                            ),
                        ],
                    ),
                ),
            ],
            spacing=0,
        )

    def _build_benchmark_tab(self) -> ft.Control:
        """Build benchmark settings tab."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Text("Default Generation Parameters", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            ft.ResponsiveRow(
                                controls=[
                                    SliderField(min_value=0.0, max_value=2.0, value=self._config.benchmark.temperature, step=0.1, label="Temperature", col={"xs": 12, "sm": 6, "md": 4}, on_change=lambda v: self._update_config("benchmark.temperature", v)),
                                    SliderField(min_value=0.0, max_value=1.0, value=self._config.benchmark.top_p, step=0.05, label="Top-P", col={"xs": 12, "sm": 6, "md": 4}, on_change=lambda v: self._update_config("benchmark.top_p", v)),
                                    FormField(config=FormFieldConfig(label="Top-K"), value=str(self._config.benchmark.top_k), col={"xs": 12, "sm": 6, "md": 4}, on_change=lambda v: self._update_config("benchmark.top_k", int(v) if v.isdigit() else 40)),
                                ],
                                spacing=16,
                            ),
                            ft.Container(height=16),
                            ft.ResponsiveRow(
                                controls=[
                                    FormField(config=FormFieldConfig(label="Seed (-1 = random)"), value=str(self._config.benchmark.seed), col={"xs": 12, "sm": 6, "md": 4}, on_change=lambda v: self._update_config("benchmark.seed", int(v) if v.lstrip('-').isdigit() else -1)),
                                    FormField(config=FormFieldConfig(label="Max Tokens"), value=str(self._config.benchmark.max_tokens), col={"xs": 12, "sm": 6, "md": 4}, on_change=lambda v: self._update_config("benchmark.max_tokens", int(v) if v.isdigit() else 2048)),
                                    FormField(config=FormFieldConfig(label="Context Length"), value=str(self._config.benchmark.context_length), col={"xs": 12, "sm": 6, "md": 4}, on_change=lambda v: self._update_config("benchmark.context_length", int(v) if v.isdigit() else 4096)),
                                ],
                                spacing=16,
                            ),
                            ft.Container(height=16),
                            ToggleField(
                                label="Enable Streaming",
                                value=self._config.benchmark.streaming,
                                on_change=lambda v: self._update_config("benchmark.streaming", v),
                            ),
                        ],
                    ),
                ),
                ft.Container(height=16),
                GlassCard(
                    header=ft.Text("Default Execution Parameters", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            ft.ResponsiveRow(
                                controls=[
                                    FormField(config=FormFieldConfig(label="Iterations"), value=str(self._config.benchmark.iterations), col={"xs": 12, "sm": 6, "md": 3}, on_change=lambda v: self._update_config("benchmark.iterations", int(v) if v.isdigit() else 10)),
                                    FormField(config=FormFieldConfig(label="Warmup Runs"), value=str(self._config.benchmark.warmup_runs), col={"xs": 12, "sm": 6, "md": 3}, on_change=lambda v: self._update_config("benchmark.warmup_runs", int(v) if v.isdigit() else 2)),
                                    FormField(config=FormFieldConfig(label="Cooldown (seconds)"), value=str(self._config.benchmark.cooldown_seconds), col={"xs": 12, "sm": 6, "md": 3}, on_change=lambda v: self._update_config("benchmark.cooldown_seconds", int(v) if v.isdigit() else 5)),
                                    FormField(config=FormFieldConfig(label="Concurrent Users"), value=str(self._config.benchmark.concurrent_users), col={"xs": 12, "sm": 6, "md": 3}, on_change=lambda v: self._update_config("benchmark.concurrent_users", int(v) if v.isdigit() else 1)),
                                ],
                                spacing=16,
                            ),
                            ft.Container(height=16),
                            FormField(config=FormFieldConfig(label="Batch Size"), value=str(self._config.benchmark.batch_size), on_change=lambda v: self._update_config("benchmark.batch_size", int(v) if v.isdigit() else 1)),
                            ft.Container(height=16),
                            FormField(config=FormFieldConfig(label="Default System Prompt", hint="Optional system prompt"), value=self._config.benchmark.system_prompt, on_change=lambda v: self._update_config("benchmark.system_prompt", v)),
                            ft.Container(height=16),
                            SelectField(
                                options=[
                                    ("builtin:general", "General Chat"),
                                    ("builtin:coding", "Coding Tasks"),
                                    ("builtin:reasoning", "Reasoning"),
                                    ("builtin:creative", "Creative Writing"),
                                ],
                                value=self._config.benchmark.prompt_dataset,
                                label="Default Prompt Dataset",
                                on_change=lambda v: self._update_config("benchmark.prompt_dataset", v),
                            ),
                        ],
                    ),
                ),
                ft.Container(height=16),
                GlassCard(
                    header=ft.Text("Default Quality Benchmarks", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            ft.Text("Enable/disable quality benchmarks by default", size=13, color=c.on_surface_variant),
                            ft.Container(height=16),
                            ft.Row(
                                controls=[
                                    ToggleField(label="MMLU", value=self._config.quality_benchmarks.mmlu, on_change=lambda v: self._update_config("quality_benchmarks.mmlu", v)),
                                    ToggleField(label="HumanEval", value=self._config.quality_benchmarks.humaneval, on_change=lambda v: self._update_config("quality_benchmarks.humaneval", v)),
                                    ToggleField(label="GSM8K", value=self._config.quality_benchmarks.gsm8k, on_change=lambda v: self._update_config("quality_benchmarks.gsm8k", v)),
                                    ToggleField(label="Needle in Haystack", value=self._config.quality_benchmarks.needle, on_change=lambda v: self._update_config("quality_benchmarks.needle", v)),
                                ],
                                spacing=16,
                                wrap=True,
                            ),
                            ft.Container(height=8),
                            ft.Row(
                                controls=[
                                    ToggleField(label="MMLU-Pro", value=self._config.quality_benchmarks.mmlu_pro, on_change=lambda v: self._update_config("quality_benchmarks.mmlu_pro", v)),
                                    ToggleField(label="GPQA", value=self._config.quality_benchmarks.gpqa, on_change=lambda v: self._update_config("quality_benchmarks.gpqa", v)),
                                    ToggleField(label="MBPP", value=self._config.quality_benchmarks.mbpp, on_change=lambda v: self._update_config("quality_benchmarks.mbpp", v)),
                                    ToggleField(label="Instruction Following", value=self._config.quality_benchmarks.instruction_following, on_change=lambda v: self._update_config("quality_benchmarks.instruction_following", v)),
                                ],
                                spacing=16,
                                wrap=True,
                            ),
                            ft.Container(height=8),
                            ft.Row(
                                controls=[
                                    ToggleField(label="Reliability", value=self._config.quality_benchmarks.reliability, on_change=lambda v: self._update_config("quality_benchmarks.reliability", v)),
                                    ToggleField(label="Safety", value=self._config.quality_benchmarks.safety, on_change=lambda v: self._update_config("quality_benchmarks.safety", v)),
                                    ToggleField(label="Agent Metrics", value=self._config.quality_benchmarks.agent, on_change=lambda v: self._update_config("quality_benchmarks.agent", v)),
                                ],
                                spacing=16,
                                wrap=True,
                            ),
                        ],
                    ),
                ),
            ],
            spacing=0,
        )

    def _build_hardware_tab(self) -> ft.Control:
        """Build hardware monitoring settings tab."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Text("Polling Intervals", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            ft.Text("Update intervals for hardware monitoring (milliseconds)", size=13, color=c.on_surface_variant),
                            ft.Container(height=16),
                            ft.ResponsiveRow(
                                controls=[
                                    FormField(config=FormFieldConfig(label="Hardware Polling (CPU/GPU/Memory)"), value=str(self._config.ui.hardware_poll_interval), col={"xs": 12, "sm": 6}, on_change=lambda v: self._update_config("ui.hardware_poll_interval", int(v) if v.isdigit() else 250)),
                                    FormField(config=FormFieldConfig(label="Temperature Polling"), value=str(self._config.ui.temperature_poll_interval), col={"xs": 12, "sm": 6}, on_change=lambda v: self._update_config("ui.temperature_poll_interval", int(v) if v.isdigit() else 500)),
                                ],
                                spacing=16,
                            ),
                            ft.Container(height=8),
                            FormField(config=FormFieldConfig(label="Power Polling"), value=str(self._config.ui.power_poll_interval), on_change=lambda v: self._update_config("ui.power_poll_interval", int(v) if v.isdigit() else 500)),
                            ft.Container(height=16),
                            ToggleField(
                                label="TPS Update Per Token",
                                value=self._config.ui.tps_update_per_token,
                                on_change=lambda v: self._update_config("ui.tps_update_per_token", v),
                            ),
                        ],
                    ),
                ),
                ft.Container(height=16),
                GlassCard(
                    header=ft.Text("Monitoring Backends", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            SelectField(
                                options=[
                                    ("auto", "Auto-detect"),
                                    ("psutil", "psutil (CPU)"),
                                ],
                                value=self._config.hardware.cpu_backend,
                                label="CPU Backend",
                                on_change=lambda v: self._update_config("hardware.cpu_backend", v),
                            ),
                            ft.Container(height=8),
                            SelectField(
                                options=[
                                    ("auto", "Auto-detect"),
                                    ("pynvml", "NVIDIA (pynvml)"),
                                    ("rocm-smi", "AMD (rocm-smi)"),
                                    ("intel-gpu-top", "Intel (intel-gpu-top)"),
                                ],
                                value=self._config.hardware.gpu_backend,
                                label="GPU Backend",
                                on_change=lambda v: self._update_config("hardware.gpu_backend", v),
                            ),
                            ft.Container(height=8),
                            SelectField(
                                options=[
                                    ("auto", "Auto-detect"),
                                    ("psutil", "psutil"),
                                ],
                                value=self._config.hardware.memory_backend,
                                label="Memory Backend",
                                on_change=lambda v: self._update_config("hardware.memory_backend", v),
                            ),
                            ft.Container(height=16),
                            FormField(config=FormFieldConfig(label="NVIDIA GPU Index"), value=str(self._config.hardware.nvidia_gpu_index), on_change=lambda v: self._update_config("hardware.nvidia_gpu_index", int(v) if v.isdigit() else 0)),
                            ft.Container(height=8),
                            FormField(config=FormFieldConfig(label="rocm-smi Path"), value=self._config.hardware.rocm_smi_path, on_change=lambda v: self._update_config("hardware.rocm_smi_path", v)),
                            ft.Container(height=8),
                            FormField(config=FormFieldConfig(label="intel-gpu-top Path"), value=self._config.hardware.intel_gpu_top_path, on_change=lambda v: self._update_config("hardware.intel_gpu_top_path", v)),
                            ft.Container(height=16),
                            FormField(config=FormFieldConfig(label="Sample History Size"), value=str(self._config.hardware.sample_history_size), on_change=lambda v: self._update_config("hardware.sample_history_size", int(v) if v.isdigit() else 100000)),
                        ],
                    ),
                ),
            ],
            spacing=0,
        )

    def _build_exports_tab(self) -> ft.Control:
        """Build exports settings tab."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Text("Export Configuration", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            FilePickerField(
                                label="Default Export Directory",
                                on_result=lambda files: self._update_config("exports.default_directory", files[0] if files else self._config.exports.default_directory),
                            ),
                            ft.Container(height=16),
                            ft.Text("Default Export Formats", size=13, weight=ft.FontWeight.MEDIUM, color=c.on_surface),
                            ft.Container(height=8),
                            ft.Row(
                                controls=[
                                    ToggleField(label="CSV", value="csv" in self._config.exports.formats, on_change=lambda v: self._toggle_format("csv", v)),
                                    ToggleField(label="JSON", value="json" in self._config.exports.formats, on_change=lambda v: self._toggle_format("json", v)),
                                    ToggleField(label="HTML", value="html" in self._config.exports.formats, on_change=lambda v: self._toggle_format("html", v)),
                                    ToggleField(label="PDF", value="pdf" in self._config.exports.formats, on_change=lambda v: self._toggle_format("pdf", v)),
                                    ToggleField(label="SQLite Backup", value="sqlite" in self._config.exports.formats, on_change=lambda v: self._toggle_format("sqlite", v)),
                                ],
                                spacing=16,
                                wrap=True,
                            ),
                            ft.Container(height=16),
                            SelectField(
                                options=[
                                    ("reportlab", "ReportLab (Pure Python)"),
                                    ("weasyprint", "WeasyPrint (HTML to PDF)"),
                                ],
                                value=self._config.exports.pdf_engine,
                                label="PDF Engine",
                                on_change=lambda v: self._update_config("exports.pdf_engine", v),
                            ),
                            ft.Container(height=16),
                            ToggleField(
                                label="Include Charts in PDF",
                                value=self._config.exports.include_charts_in_pdf,
                                on_change=lambda v: self._update_config("exports.include_charts_in_pdf", v),
                            ),
                            ft.Container(height=8),
                            ToggleField(
                                label="Include Raw Data in Exports",
                                value=self._config.exports.include_raw_data,
                                on_change=lambda v: self._update_config("exports.include_raw_data", v),
                            ),
                        ],
                    ),
                ),
                ft.Container(height=16),
                GlassCard(
                    header=ft.Text("Database Backup", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            ToggleField(
                                label="Enable Automatic Backups",
                                value=self._config.database.backup_enabled,
                                on_change=lambda v: self._update_config("database.backup_enabled", v),
                            ),
                            ft.Container(height=8),
                            FormField(config=FormFieldConfig(label="Backup Interval (hours)"), value=str(self._config.database.backup_interval_hours), on_change=lambda v: self._update_config("database.backup_interval_hours", int(v) if v.isdigit() else 24)),
                            ft.Container(height=8),
                            FormField(config=FormFieldConfig(label="Backup Retention (days)"), value=str(self._config.database.backup_retention_days), on_change=lambda v: self._update_config("database.backup_retention_days", int(v) if v.isdigit() else 30)),
                        ],
                    ),
                ),
            ],
            spacing=0,
        )

    def _build_advanced_tab(self) -> ft.Control:
        """Build advanced settings tab."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Text("Scoring Weights", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            ft.Text("Adjust category weights for overall score (must sum to 100)", size=13, color=c.on_surface_variant),
                            ft.Container(height=16),
                            ft.ResponsiveRow(
                                controls=[
                                    FormField(config=FormFieldConfig(label="Latency Weight"), value=str(self._config.scoring.weights.latency), col={"xs": 12, "sm": 6, "md": 4}, on_change=lambda v: self._update_config("scoring.weights.latency", int(v) if v.isdigit() else 20)),
                                    FormField(config=FormFieldConfig(label="Throughput Weight"), value=str(self._config.scoring.weights.throughput), col={"xs": 12, "sm": 6, "md": 4}, on_change=lambda v: self._update_config("scoring.weights.throughput", int(v) if v.isdigit() else 20)),
                                    FormField(config=FormFieldConfig(label="Quality Weight"), value=str(self._config.scoring.weights.quality), col={"xs": 12, "sm": 6, "md": 4}, on_change=lambda v: self._update_config("scoring.weights.quality", int(v) if v.isdigit() else 25)),
                                ],
                                spacing=16,
                            ),
                            ft.Container(height=8),
                            ft.ResponsiveRow(
                                controls=[
                                    FormField(config=FormFieldConfig(label="Reliability Weight"), value=str(self._config.scoring.weights.reliability), col={"xs": 12, "sm": 6, "md": 4}, on_change=lambda v: self._update_config("scoring.weights.reliability", int(v) if v.isdigit() else 15)),
                                    FormField(config=FormFieldConfig(label="Memory Weight"), value=str(self._config.scoring.weights.memory), col={"xs": 12, "sm": 6, "md": 4}, on_change=lambda v: self._update_config("scoring.weights.memory", int(v) if v.isdigit() else 10)),
                                    FormField(config=FormFieldConfig(label="Energy Weight"), value=str(self._config.scoring.weights.energy), col={"xs": 12, "sm": 6, "md": 4}, on_change=lambda v: self._update_config("scoring.weights.energy", int(v) if v.isdigit() else 5)),
                                ],
                                spacing=16,
                            ),
                            ft.Container(height=8),
                            FormField(config=FormFieldConfig(label="Context Weight"), value=str(self._config.scoring.weights.context), on_change=lambda v: self._update_config("scoring.weights.context", int(v) if v.isdigit() else 5)),
                            ft.Container(height=16),
                            ft.Text("Grade Thresholds", size=13, weight=ft.FontWeight.MEDIUM, color=c.on_surface),
                            ft.Container(height=8),
                            ft.ResponsiveRow(
                                controls=[
                                    FormField(config=FormFieldConfig(label="S+ Threshold"), value=str(self._config.scoring.grades.s_plus), col={"xs": 12, "sm": 6, "md": 4}, on_change=lambda v: self._update_config("scoring.grades.s_plus", int(v) if v.isdigit() else 950)),
                                    FormField(config=FormFieldConfig(label="S Threshold"), value=str(self._config.scoring.grades.s), col={"xs": 12, "sm": 6, "md": 4}, on_change=lambda v: self._update_config("scoring.grades.s", int(v) if v.isdigit() else 900)),
                                    FormField(config=FormFieldConfig(label="A Threshold"), value=str(self._config.scoring.grades.a), col={"xs": 12, "sm": 6, "md": 4}, on_change=lambda v: self._update_config("scoring.grades.a", int(v) if v.isdigit() else 800)),
                                ],
                                spacing=16,
                            ),
                            ft.Container(height=8),
                            ft.ResponsiveRow(
                                controls=[
                                    FormField(config=FormFieldConfig(label="B Threshold"), value=str(self._config.scoring.grades.b), col={"xs": 12, "sm": 6, "md": 4}, on_change=lambda v: self._update_config("scoring.grades.b", int(v) if v.isdigit() else 700)),
                                    FormField(config=FormFieldConfig(label="C Threshold"), value=str(self._config.scoring.grades.c), col={"xs": 12, "sm": 6, "md": 4}, on_change=lambda v: self._update_config("scoring.grades.c", int(v) if v.isdigit() else 600)),
                                ],
                                spacing=16,
                            ),
                        ],
                    ),
                ),
                ft.Container(height=16),
                GlassCard(
                    header=ft.Text("Units", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            SegmentedButton(
                                options=[
                                    ("metric", "Metric (W, J, °C)", ft.Icons.STRAIGHTEN),
                                    ("imperial", "Imperial (BTU, °F)", ft.Icons.STRAIGHTEN),
                                ],
                                selected_key="metric",
                                on_change=lambda v: self._update_config("ui.units", v),
                            ),
                        ],
                    ),
                ),
                ft.Container(height=16),
                GlassCard(
                    header=ft.Text("Danger Zone", size=16, weight=ft.FontWeight.SEMIBOLD, color=c.danger),
                    content=ft.Column(
                        controls=[
                            ft.Text("These actions cannot be undone", size=13, color=c.on_surface_variant),
                            ft.Container(height=16),
                            ft.FilledButton(
                                text="Clear All Benchmark Data",
                                icon=ft.Icons.DELETE_FOREVER,
                                on_click=self._clear_all_data,
                                style=ft.ButtonStyle(bgcolor=c.danger),
                            ),
                            ft.Container(height=8),
                            ft.FilledButton(
                                text="Reset All Settings",
                                icon=ft.Icons.FACTORY_RESET,
                                on_click=self._reset_defaults,
                                style=ft.ButtonStyle(bgcolor=c.warning),
                            ),
                        ],
                    ),
                ),
            ],
            spacing=0,
        )

    def _update_config(self, path: str, value):
        """Update configuration value."""
        # Navigate to nested config and update
        parts = path.split(".")
        obj = self._config
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)

        # Save to file
        self._config.to_yaml("config.yaml")
        self.show_snackbar(f"Updated {path}", "success")

    def _toggle_format(self, fmt: str, enabled: bool):
        """Toggle export format."""
        formats = list(self._config.exports.formats)
        if enabled and fmt not in formats:
            formats.append(fmt)
        elif not enabled and fmt in formats:
            formats.remove(fmt)
        self._config.exports.formats = formats
        self._config.to_yaml("config.yaml")

    def _reset_defaults(self, _):
        """Reset all settings to defaults."""
        # TODO: Implement reset
        self.show_snackbar("Settings reset to defaults", "info")

    def _clear_all_data(self, _):
        """Clear all benchmark data."""
        # TODO: Implement with confirmation dialog
        self.show_snackbar("Data clearing requires confirmation", "warning")