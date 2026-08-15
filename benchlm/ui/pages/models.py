"""Models page - Model management and provider integration."""

import flet as ft
from typing import Optional, List
from dataclasses import dataclass

from benchlm.ui.pages.base import BasePage
from benchlm.ui.widgets import (
    GlassCard,
    MetricCard,
    VirtualizedTable,
    ColumnConfig,
    TableConfig,
    SegmentedButton,
    SelectField,
    FormField,
    FormFieldConfig,
    StatusIndicator,
    StatusConfig,
    Badge,
)
from benchlm.ui.theme import get_theme
from benchlm.config import get_config
from benchlm.database.models import ProviderType


@dataclass
class ModelInfo:
    """Model information for display."""
    name: str
    provider: ProviderType
    quantization: str
    context_window: int
    parameters: str
    size_gb: float
    precision: str
    status: str = "available"  # available, loading, error


class ModelsPage(BasePage):
    """Models page with provider tabs and model management."""

    def __init__(self, page: ft.Page, **kwargs):
        self._theme = get_theme()
        self._config = get_config()
        self._selected_provider = ProviderType.OLLAMA
        self._models: List[ModelInfo] = []
        self._selected_models: set = set()
        super().__init__(page, route="/models", title="Models", icon=ft.Icons.MODEL_TRAINING, **kwargs)

    def _build(self):
        """Build models page UI."""
        c = self._theme.colors

        # Header
        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Models", size=self._theme.typography.headline_medium, weight=ft.FontWeight.BOLD, color=c.on_background),
                        ft.Text("Manage and select models for benchmarking", size=self._theme.typography.body_medium, color=c.on_surface_variant),
                    ],
                    spacing=4,
                ),
                ft.Container(expand=True),
                ft.Row(
                    controls=[
                        ft.FilledButton(
                            content=ft.Text("Refresh"),
                            icon=ft.Icons.REFRESH,
                            on_click=self._refresh_models,
                        ),
                        ft.Container(width=12),
                        ft.FilledButton(
                            content=ft.Text("Add Model"),
                            icon=ft.Icons.ADD,
                            on_click=self._add_model,
                            style=self._theme.button_primary_style(),
                        ),
                    ],
                    spacing=8,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Provider Tabs
        self._provider_tabs = SegmentedButton(
            options=[
                (ProviderType.OLLAMA.value, "Ollama", ft.Icons.CLOUD),
                (ProviderType.LLAMA_CPP.value, "llama.cpp", ft.Icons.CODE),
                (ProviderType.LMSTUDIO.value, "LM Studio", ft.Icons.DEVELOPER_BOARD),
                (ProviderType.VLLM.value, "vLLM", ft.Icons.SPEED),
                (ProviderType.OPENAI_COMPATIBLE.value, "OpenAI Compat.", ft.Icons.API),
            ],
            selected_key=self._selected_provider.value,
            on_change=self._on_provider_change,
        )

        # Model Table
        self._model_table = self._build_model_table()

        # Selection Toolbar (shown when models selected)
        self._selection_toolbar = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text("0 selected", size=14, weight=ft.FontWeight.W_500, color=c.on_surface),
                    ft.Container(expand=True),
                    ft.FilledButton(
                        content=ft.Text("Benchmark Selected"),
                        icon=ft.Icons.PLAY_ARROW,
                        on_click=self._benchmark_selected,
                        disabled=True,
                    ),
                    ft.Container(width=8),
                    ft.OutlinedButton(
                        content=ft.Text("Compare"),
                        icon=ft.Icons.COMPARE_ARROWS,
                        on_click=self._compare_selected,
                        disabled=True,
                    ),
                    ft.Container(width=8),
                    ft.TextButton(
                        content=ft.Text("Clear Selection"),
                        on_click=self._clear_selection,
                    ),
                ],
                alignment=ft.MainAxisAlignment.END,
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            bgcolor=c.primary_container,
            border_radius=ft.border_radius.only(top_left=12, top_right=12),
            visible=False,
        )

        # Main Content
        content = ft.Column(
            controls=[
                header,
                ft.Container(height=24),
                self._provider_tabs,
                ft.Container(height=16),
                GlassCard(
                    content=ft.Column(
                        controls=[
                            self._model_table,
                            self._selection_toolbar,
                        ],
                        spacing=0,
                    ),
                ),
            ],
            spacing=0,
            expand=True,
        )

        self.content = content

    def _build_model_table(self) -> VirtualizedTable:
        """Build the models table."""
        c = self._theme.colors

        columns = [
            ColumnConfig(key="select", label="", width=50, sortable=False, format_fn=lambda _: ""),
            ColumnConfig(key="name", label="Model Name", min_width=200, sortable=True),
            ColumnConfig(key="provider", label="Provider", width=120, sortable=True),
            ColumnConfig(key="quantization", label="Quantization", width=120, sortable=True),
            ColumnConfig(key="context", label="Context", width=100, sortable=True, format_fn=lambda v: f"{v//1024}K" if v >= 1024 else str(v)),
            ColumnConfig(key="parameters", label="Parameters", width=120, sortable=True),
            ColumnConfig(key="size", label="Size", width=100, sortable=True, format_fn=lambda v: f"{v:.1f} GB"),
            ColumnConfig(key="precision", label="Precision", width=100, sortable=True),
            ColumnConfig(key="status", label="Status", width=100, sortable=True),
            ColumnConfig(key="actions", label="", width=100, sortable=False),
        ]

        config = TableConfig(
            columns=columns,
            row_height=52,
            selectable=True,
            multi_select=True,
            on_selection_change=self._on_selection_change,
            virtualized=True,
        )

        return VirtualizedTable(config=config, data=self._get_model_data())

    def _get_model_data(self) -> List[dict]:
        """Get model data for table."""
        # TODO: Load from database/provider
        # Mock data for now
        return [
            {
                "name": "qwen3:8b",
                "provider": "Ollama",
                "quantization": "Q4_K_M",
                "context": 32768,
                "parameters": "8B",
                "size": 4.7,
                "precision": "INT4",
                "status": "available",
                "actions": "•••",
            },
            {
                "name": "gemma3:9b",
                "provider": "Ollama",
                "quantization": "Q4_K_M",
                "context": 8192,
                "parameters": "9B",
                "size": 5.2,
                "precision": "INT4",
                "status": "available",
                "actions": "•••",
            },
            {
                "name": "llama3.1:8b",
                "provider": "Ollama",
                "quantization": "Q4_K_M",
                "context": 131072,
                "parameters": "8B",
                "size": 4.9,
                "precision": "INT4",
                "status": "available",
                "actions": "•••",
            },
            {
                "name": "phi3:mini",
                "provider": "Ollama",
                "quantization": "Q4_K_M",
                "context": 4096,
                "parameters": "3.8B",
                "size": 2.3,
                "precision": "INT4",
                "status": "available",
                "actions": "•••",
            },
        ]

    def _on_provider_change(self, provider_key: str):
        """Handle provider tab change."""
        self._selected_provider = ProviderType(provider_key)
        self._refresh_models()

    def _on_selection_change(self, selected_data: List[dict]):
        """Handle model selection change."""
        self._selected_models = {m["name"] for m in selected_data}
        count = len(self._selected_models)

        self._selection_toolbar.visible = count > 0
        self._selection_toolbar.content.controls[0].value = f"{count} selected"
        self._selection_toolbar.content.controls[2].disabled = count == 0  # Benchmark
        self._selection_toolbar.content.controls[4].disabled = count < 2  # Compare
        self._selection_toolbar.update()

    def _refresh_models(self):
        """Refresh model list from provider."""
        self.show_snackbar(f"Refreshing {self._selected_provider.value} models...", "info")
        # TODO: Implement actual provider model fetching
        self._model_table.data = self._get_model_data()
        self._model_table.refresh()

    def _add_model(self):
        """Show add model dialog."""
        # TODO: Implement add model dialog
        self.show_snackbar("Add model dialog coming soon", "info")

    def _benchmark_selected(self):
        """Navigate to benchmark with selected models."""
        if self._selected_models:
            self.navigate(f"/benchmark?models={','.join(self._selected_models)}")

    def _compare_selected(self):
        """Navigate to comparison with selected models."""
        if len(self._selected_models) >= 2:
            self.navigate(f"/comparison?models={','.join(self._selected_models)}")

    def _clear_selection(self):
        """Clear model selection."""
        self._model_table.clear_selection()
        self._selected_models.clear()
        self._selection_toolbar.visible = False
        self._selection_toolbar.update()