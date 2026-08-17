"""Models page - Model management and provider integration."""

import asyncio
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
    AlertDialog,
    InputDialog,
)
from benchlm.ui.theme import get_theme
from benchlm.config import get_config
from benchlm.providers.base import ProviderType, ModelInfo as ProviderModelInfo
from benchlm.providers.registry import PROVIDER_CLASSES, DEFAULT_BASE_URLS


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
        self._provider_instance = None
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
                            on_click=self._on_refresh_clicked,
                        ),
                        ft.Container(width=12),
                        ft.FilledButton(
                            content=ft.Text("Add Model"),
                            icon=ft.Icons.ADD,
                            on_click=self._on_add_model_clicked,
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
            border_radius=ft.BorderRadius.only(top_left=12, top_right=12),
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
            ColumnConfig(key="name", label="Model Name", min_width=200, sortable=True),
            ColumnConfig(key="provider", label="Provider", width=120, sortable=True),
            ColumnConfig(key="quantization", label="Quantization", width=120, sortable=True),
            ColumnConfig(key="context", label="Context", width=100, sortable=True, format_fn=lambda v: f"{v//1024}K" if v >= 1024 else str(v)),
            ColumnConfig(key="parameters", label="Parameters", width=120, sortable=True),
            ColumnConfig(key="size", label="Size", width=100, sortable=True, format_fn=lambda v: f"{v:.1f} GB"),
            ColumnConfig(key="precision", label="Precision", width=100, sortable=True),
            ColumnConfig(key="status", label="Status", width=100, sortable=True),
            ColumnConfig(key="actions", label="", width=80, sortable=False),
        ]

        config = TableConfig(
            columns=columns,
            row_height=52,
            selectable=True,
            multi_select=True,
            on_selection_change=self._on_selection_change,
            on_row_action=self._on_row_action,
            virtualized=False,
        )

        return VirtualizedTable(config=config, data=self._get_model_data())

    def _get_model_data(self) -> List[dict]:
        """Get model data for table."""
        return [
            {
                "name": m.name,
                "provider": m.provider.value,
                "quantization": m.quantization,
                "context": m.context_window,
                "parameters": m.parameters,
                "size": m.size_gb,
                "precision": m.precision,
                "status": m.status,
                "actions": "•••",
            }
            for m in self._models
        ]

    def _get_base_url_for_provider(self, provider_type: ProviderType) -> str:
        """Get base URL for a provider type from config."""
        cfg = self._config.benchmark
        mapping = {
            ProviderType.OLLAMA: cfg.ollama_host,
            ProviderType.LLAMA_CPP: cfg.llama_cpp_host,
            ProviderType.LMSTUDIO: cfg.lmstudio_host,
            ProviderType.VLLM: cfg.vllm_host,
            ProviderType.OPENAI_COMPATIBLE: cfg.openai_compatible_host,
        }
        return mapping.get(provider_type, DEFAULT_BASE_URLS.get(provider_type, "http://localhost:8000/v1"))

    async def _fetch_models(self, force_refresh: bool = False) -> List[dict]:
        """Fetch models from the currently selected provider."""
        provider_type = self._selected_provider
        base_url = self._get_base_url_for_provider(provider_type)
        provider_class = PROVIDER_CLASSES.get(provider_type)

        if not provider_class:
            self.show_snackbar(f"Unknown provider type: {provider_type.value}", "error")
            return []

        provider = None
        try:
            provider = provider_class(base_url=base_url)
            await provider.initialize()
            models: List[ProviderModelInfo] = await provider.list_models(force_refresh=force_refresh)

            self._models = [
                ModelInfo(
                    name=m.name,
                    provider=ProviderType(m.provider.value),
                    quantization=m.quantization or "--",
                    context_window=m.context_window,
                    parameters=m.parameter_count or "--",
                    size_gb=round(m.size_bytes / (1024 ** 3), 1) if m.size_bytes else 0.0,
                    precision=m.quantization.split("_")[0] if m.quantization else "--",
                    status="available",
                )
                for m in models
            ]
            return self._get_model_data()
        except Exception as e:
            self.show_snackbar(f"Failed to fetch models from {provider_type.value}: {e}", "error")
            self._models = []
            return []
        finally:
            if provider:
                try:
                    await provider.close()
                except Exception:
                    pass

    def _on_provider_change(self, provider_key: str):
        """Handle provider tab change."""
        self._selected_provider = ProviderType(provider_key)
        asyncio.get_event_loop().create_task(self._refresh_models())

    def _on_selection_change(self, selected_data: List[dict]):
        """Handle model selection change."""
        self._selected_models = {m["name"] for m in selected_data}
        count = len(self._selected_models)

        self._selection_toolbar.visible = count > 0
        self._selection_toolbar.content.controls[0].value = f"{count} selected"
        self._selection_toolbar.content.controls[2].disabled = count == 0  # Benchmark
        self._selection_toolbar.content.controls[4].disabled = count < 2  # Compare
        self._selection_toolbar.update()

    async def _refresh_models(self):
        """Refresh model list from provider."""
        self.show_snackbar(f"Refreshing {self._selected_provider.value} models...", "info")
        models_data = await self._fetch_models(force_refresh=True)

        if not models_data:
            models_data = [
                {
                    "name": "No models found",
                    "provider": self._selected_provider.value,
                    "quantization": "--",
                    "context": 0,
                    "parameters": "--",
                    "size": 0.0,
                    "precision": "--",
                    "status": "error",
                    "actions": "",
                }
            ]

        self._model_table.data = models_data
        self._model_table.refresh()

    def _on_refresh_clicked(self, _):
        """Handle refresh button click."""
        asyncio.get_event_loop().create_task(self._refresh_models())

    def _on_row_action(self, row_data: dict, action: str):
        """Handle action button clicks from table rows."""
        if action == "benchmark":
            self._benchmark_model(row_data)
        elif action == "compare":
            self._compare_model(row_data)
        elif action == "details":
            self._show_model_details(row_data)

    def _benchmark_model(self, row_data: dict):
        """Navigate to benchmark with a single model."""
        self.navigate(f"/benchmark?models={row_data['name']}")

    def _compare_model(self, row_data: dict):
        """Navigate to comparison with a single model."""
        if len(self._selected_models) >= 2:
            self.navigate(f"/comparison?models={','.join(self._selected_models)}")
        else:
            self.show_snackbar("Select at least 2 models to compare", "warning")

    def _show_model_details(self, row_data: dict):
        """Show model details dialog."""
        c = self._theme.colors
        details = (
            f"Name: {row_data['name']}\n"
            f"Provider: {row_data['provider']}\n"
            f"Quantization: {row_data.get('quantization', '--')}\n"
            f"Context Window: {row_data.get('context', 0):,}\n"
            f"Parameters: {row_data.get('parameters', '--')}\n"
            f"Size: {row_data.get('size', 0.0):.1f} GB\n"
            f"Precision: {row_data.get('precision', '--')}\n"
            f"Status: {row_data.get('status', 'unknown')}"
        )
        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Model Details", size=18, weight=ft.FontWeight.W_600),
                content=ft.Container(
                    content=ft.Text(details, size=14, font_family="JetBrains Mono, monospace"),
                    padding=16,
                ),
                actions=[
                    ft.TextButton(content="Close", on_click=lambda _: self._close_dialog()),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def _close_dialog(self):
        """Close the current dialog."""
        self.page.pop_dialog()

    def _on_add_model_clicked(self, _):
        """Show add model dialog."""
        provider_type = self._selected_provider

        if provider_type == ProviderType.OLLAMA:
            self._show_pull_model_dialog()
        else:
            self._show_add_model_dialog()

    def _show_pull_model_dialog(self):
        """Show dialog to pull an Ollama model."""
        c = self._theme.colors

        name_field = ft.TextField(
            label="Model Name",
            hint_text="e.g. llama3.1:8b, qwen2.5:14b",
            border_color=c.outline,
            focused_border_color=c.primary,
            bgcolor=c.surface_variant,
            color=c.on_surface,
            border_radius=8,
            filled=True,
            dense=True,
            autofocus=True,
            on_submit=lambda _: asyncio.get_event_loop().create_task(self._pull_model(name_field.value)),
        )

        dlg = ft.AlertDialog(
            title=ft.Text("Pull Ollama Model", size=18, weight=ft.FontWeight.W_600),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Enter the model name to pull from Ollama registry.", size=14, color=c.on_surface_variant),
                        ft.Container(height=16),
                        name_field,
                    ],
                    spacing=0,
                    tight=True,
                ),
                padding=ft.Padding.all(16),
            ),
            actions=[
                ft.TextButton(content="Cancel", on_click=lambda _: self._close_dialog()),
                ft.FilledButton(
                    content="Pull",
                    style=ft.ButtonStyle(bgcolor=c.primary),
                    on_click=lambda _: asyncio.get_event_loop().create_task(self._pull_model(name_field.value)),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dlg)

    async def _pull_model(self, model_name: str):
        """Pull a model from Ollama."""
        if not model_name or not model_name.strip():
            self.show_snackbar("Please enter a model name", "warning")
            return

        self._close_dialog()
        self.show_snackbar(f"Pulling {model_name}...", "info")

        base_url = self._get_base_url_for_provider(ProviderType.OLLAMA)
        provider = PROVIDER_CLASSES[ProviderType.OLLAMA](base_url=base_url)

        try:
            await provider.initialize()
            async for _ in provider.pull_model(model_name.strip()):
                pass
            self.show_snackbar(f"Successfully pulled {model_name}", "success")
            await self._refresh_models()
        except Exception as e:
            self.show_snackbar(f"Failed to pull model: {e}", "error")
        finally:
            try:
                await provider.close()
            except Exception:
                pass

    def _show_add_model_dialog(self):
        """Show dialog to add a model reference manually."""
        c = self._theme.colors

        name_field = ft.TextField(
            label="Model Name / ID",
            hint_text="e.g. my-custom-model",
            border_color=c.outline,
            focused_border_color=c.primary,
            bgcolor=c.surface_variant,
            color=c.on_surface,
            border_radius=8,
            filled=True,
            dense=True,
            autofocus=True,
            on_submit=lambda _: asyncio.get_event_loop().create_task(self._add_model(name_field.value)),
        )

        dlg = ft.AlertDialog(
            title=ft.Text("Add Model", size=18, weight=ft.FontWeight.W_600),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Add a model reference to the current provider.", size=14, color=c.on_surface_variant),
                        ft.Container(height=16),
                        name_field,
                    ],
                    spacing=0,
                    tight=True,
                ),
                padding=ft.Padding.all(16),
            ),
            actions=[
                ft.TextButton(content="Cancel", on_click=lambda _: self._close_dialog()),
                ft.FilledButton(
                    content="Add",
                    style=ft.ButtonStyle(bgcolor=c.primary),
                    on_click=lambda _: asyncio.get_event_loop().create_task(self._add_model(name_field.value)),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.show_dialog(dlg)

    async def _add_model(self, model_name: str):
        """Add a model reference manually."""
        if not model_name or not model_name.strip():
            self.show_snackbar("Please enter a model name", "warning")
            return

        self._close_dialog()
        self.show_snackbar(f"Added {model_name.strip()} to list", "success")

        self._models.append(
            ModelInfo(
                name=model_name.strip(),
                provider=self._selected_provider,
                quantization="--",
                context_window=4096,
                parameters="--",
                size_gb=0.0,
                precision="--",
                status="available",
            )
        )
        self._model_table.data = self._get_model_data()
        self._model_table.refresh()

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

    async def _on_mount(self):
        """Fetch models when page mounts."""
        asyncio.get_event_loop().create_task(self._refresh_models())
