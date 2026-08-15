"""Datasets page - Built-in and custom benchmark datasets."""

import flet as ft
from typing import Optional, List

from benchlm.ui.pages.base import BasePage
from benchlm.ui.widgets import (
    GlassCard,
    VirtualizedTable,
    ColumnConfig,
    TableConfig,
    FormField,
    FormFieldConfig,
    FormFieldType,
    SelectField,
    SegmentedButton,
    Badge,
)
from benchlm.ui.theme import get_theme
from benchlm.config import get_config


class DatasetsPage(BasePage):
    """Datasets page for managing benchmark prompt datasets."""

    def __init__(self, page: ft.Page, **kwargs):
        self._theme = get_theme()
        self._config = get_config()
        self._dataset_tab = "builtin"  # builtin, custom, validation
        super().__init__(page, route="/datasets", title="Datasets", icon=ft.Icons.DATASET, **kwargs)

    def _build(self):
        """Build datasets page UI."""
        c = self._theme.colors

        # Header
        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Datasets", size=self._theme.typography.headline_medium, weight=ft.FontWeight.BOLD, color=c.on_background),
                        ft.Text("Manage benchmark prompt datasets", size=self._theme.typography.body_medium, color=c.on_surface_variant),
                    ],
                    spacing=4,
                ),
                ft.Container(expand=True),
                ft.FilledButton(
                    content=ft.Text("Create Dataset"),
                    icon=ft.Icons.ADD,
                    on_click=self._create_dataset,
                    style=self._theme.button_primary_style(),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Tab selector
        self._tab_selector = SegmentedButton(
            options=[
                ("builtin", "Built-in", ft.Icons.LIBRARY_BOOKS),
                ("custom", "Custom", ft.Icons.FOLDER),
                ("validation", "Validation", ft.Icons.VERIFIED),
            ],
            selected_key=self._dataset_tab,
            on_change=self._on_tab_change,
        )

        # Content
        self._content_area = ft.Column(
            controls=[self._build_builtin_tab()],
            expand=True,
        )

        # Main content
        self.content = ft.Column(
            controls=[
                header,
                ft.Container(height=24),
                self._tab_selector,
                ft.Container(height=16),
                self._content_area,
            ],
            spacing=0,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    def _on_tab_change(self, tab: str):
        """Handle tab change."""
        self._dataset_tab = tab
        tabs = {
            "builtin": self._build_builtin_tab,
            "custom": self._build_custom_tab,
            "validation": self._build_validation_tab,
        }
        self._content_area.controls = [tabs[tab]()]
        self._content_area.update()

    def _build_builtin_tab(self) -> ft.Control:
        """Build built-in datasets tab."""
        c = self._theme.colors

        builtin_datasets = [
            {
                "name": "General Chat",
                "id": "builtin:general",
                "description": "Diverse conversational prompts for general benchmarking",
                "categories": ["chat", "qa", "creative"],
                "size": 500,
                "languages": ["en"],
                "source": "BenchLM curated",
            },
            {
                "name": "Coding Tasks",
                "id": "builtin:coding",
                "description": "Programming challenges, debugging, code generation",
                "categories": ["coding", "algorithms", "debugging"],
                "size": 300,
                "languages": ["en", "python", "javascript", "rust", "go"],
                "source": "HumanEval + MBPP + custom",
            },
            {
                "name": "Reasoning",
                "id": "builtin:reasoning",
                "description": "Logical reasoning, math, multi-step problems",
                "categories": ["math", "logic", "reasoning"],
                "size": 250,
                "languages": ["en"],
                "source": "GSM8K + MATH + custom",
            },
            {
                "name": "Creative Writing",
                "id": "builtin:creative",
                "description": "Story generation, poetry, creative prompts",
                "categories": ["creative", "story", "poetry"],
                "size": 200,
                "languages": ["en"],
                "source": "BenchLM curated",
            },
            {
                "name": "Analysis & Summary",
                "id": "builtin:analysis",
                "description": "Document analysis, summarization, extraction",
                "categories": ["analysis", "summary", "extraction"],
                "size": 150,
                "languages": ["en"],
                "source": "BenchLM curated",
            },
            {
                "name": "MMLU Questions",
                "id": "builtin:mmlu",
                "description": "Massive Multitask Language Understanding benchmark",
                "categories": ["knowledge", "academic"],
                "size": 14000,
                "languages": ["en"],
                "source": "HuggingFace MMLU",
            },
            {
                "name": "HumanEval",
                "id": "builtin:humaneval",
                "description": "Code generation benchmark with unit tests",
                "categories": ["coding", "evaluation"],
                "size": 164,
                "languages": ["python"],
                "source": "OpenAI HumanEval",
            },
            {
                "name": "GSM8K",
                "id": "builtin:gsm8k",
                "description": "Grade school math word problems",
                "categories": ["math", "reasoning"],
                "size": 8500,
                "languages": ["en"],
                "source": "OpenAI GSM8K",
            },
        ]

        cards = []
        for ds in builtin_datasets:
            cats = " • ".join([f'<span class="badge">{c}</span>' for c in ds["categories"]])

            cards.append(
                GlassCard(
                    header=ft.Row(
                        controls=[
                            ft.Column([
                                ft.Text(ds["name"], size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                                ft.Text(ds["description"], size=13, color=c.on_surface_variant),
                            ], expand=True, spacing=4),
                            ft.Column([
                                Badge(text=f"{ds['size']} prompts", color=c.primary),
                                ft.Container(height=4),
                                Badge(text=ds["source"], color=c.tertiary),
                            ], horizontal_alignment=ft.CrossAxisAlignment.END),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    content=ft.Row(
                        controls=[
                            ft.Text("Categories:", size=12, color=c.on_surface_variant),
                            ft.Text(" • ".join(ds["categories"]), size=12, color=c.on_surface),
                            ft.Container(expand=True),
                            ft.Text(f"Languages: {', '.join(ds['languages'])}", size=12, color=c.on_surface_disabled),
                            ft.Container(width=16),
                            ft.FilledButton(
                                content=ft.Text("Use Dataset"),
                                on_click=lambda _, d=ds: self._select_dataset(d),
                            ),
                        ],
                        spacing=8,
                        wrap=True,
                    ),
                )
            )

        return ft.Column(
            controls=cards,
            spacing=16,
        )

    def _build_custom_tab(self) -> ft.Control:
        """Build custom datasets tab."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Text("Custom Datasets", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            ft.Text("Create and manage your own prompt datasets", size=14, color=c.on_surface_variant),
                            ft.Container(height=16),
                            ft.Row(
                                controls=[
                                    FormField(
                                        config=FormFieldConfig(label="Dataset Name", hint="My Custom Dataset"),
                                    ),
                                    ft.Container(width=16),
                                    FormField(
                                        config=FormFieldConfig(label="Description", hint="Dataset description"),
                                    ),
                                ],
                                wrap=True,
                            ),
                            ft.Container(height=16),
                            FormField(
                                config=FormFieldConfig(
                                    label="Prompts (one per line)",
                                    hint="Enter prompts...",
                                    keyboard_type=FormFieldType.MULTILINE,
                                ),
                                value="",
                            ),
                            ft.Container(height=16),
                            ft.Row(
                                controls=[
                                    ft.FilledButton(content=ft.Text("Save Dataset"), icon=ft.Icons.SAVE, on_click=self._save_custom_dataset),
                                    ft.Container(width=8),
                                    ft.OutlinedButton(content=ft.Text("Import from File"), icon=ft.Icons.UPLOAD_FILE, on_click=self._import_dataset),
                                ],
                            ),
                        ],
                    ),
                ),
                ft.Container(height=16),
                GlassCard(
                    header=ft.Text("Saved Custom Datasets", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                    content=ft.Text("No custom datasets saved yet. Create one above!", size=14, color=c.on_surface_variant, text_align=ft.TextAlign.CENTER),
                ),
            ],
            spacing=0,
        )

    def _build_validation_tab(self) -> ft.Control:
        """Build dataset validation tab."""
        c = self._theme.colors

        return ft.Column(
            controls=[
                GlassCard(
                    header=ft.Text("Dataset Validation", size=16, weight=ft.FontWeight.W_600, color=c.on_surface),
                    content=ft.Column(
                        controls=[
                            ft.Text("Validate dataset quality and compatibility", size=14, color=c.on_surface_variant),
                            ft.Container(height=16),
                            SelectField(
                                options=[
                                    ("builtin:general", "General Chat"),
                                    ("builtin:coding", "Coding Tasks"),
                                    ("builtin:reasoning", "Reasoning"),
                                    ("custom", "Custom Dataset"),
                                ],
                                label="Select Dataset to Validate",
                            ),
                            ft.Container(height=16),
                            ft.FilledButton(content=ft.Text("Run Validation"), icon=ft.Icons.CHECK_CIRCLE, on_click=self._validate_dataset),
                            ft.Container(height=16),
                            ft.Text("Validation checks:", size=13, weight=ft.FontWeight.W_500, color=c.on_surface),
                            ft.Container(height=8),
                            ft.Column(
                                controls=[
                                    self._build_check_item("Prompt length distribution", "Analyzes token count distribution"),
                                    self._build_check_item("Category balance", "Checks category distribution"),
                                    self._build_check_item("Duplicate detection", "Finds duplicate or near-duplicate prompts"),
                                    self._build_check_item("Tokenization compatibility", "Verifies tokenization across models"),
                                    self._build_check_item("Quality metrics", "Estimates difficulty and diversity"),
                                ],
                                spacing=8,
                            ),
                        ],
                    ),
                ),
            ],
            spacing=0,
        )

    def _build_check_item(self, name: str, desc: str) -> ft.Control:
        """Build validation check item."""
        c = self._theme.colors

        return ft.Row(
            controls=[
                ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, size=20, color=c.on_surface_variant),
                ft.Container(width=12),
                ft.Column([
                    ft.Text(name, size=13, weight=ft.FontWeight.W_500, color=c.on_surface),
                    ft.Text(desc, size=12, color=c.on_surface_variant),
                ], expand=True),
                ft.Icon(ft.Icons.INFO_OUTLINE, size=18, color=c.tertiary),
            ],
        )

    def _select_dataset(self, dataset: dict):
        """Select a dataset for benchmarking."""
        self._config.benchmark.prompt_dataset = dataset["id"]
        self.show_snackbar(f"Selected dataset: {dataset['name']}", "success")

    def _create_dataset(self):
        """Create new custom dataset."""
        self._dataset_tab = "custom"
        self._on_tab_change("custom")

    def _save_custom_dataset(self):
        """Save custom dataset."""
        self.show_snackbar("Custom dataset saved!", "success")

    def _import_dataset(self):
        """Import dataset from file."""
        self.show_snackbar("File import dialog coming soon", "info")

    def _validate_dataset(self):
        """Run dataset validation."""
        self.show_snackbar("Validation started...", "info")