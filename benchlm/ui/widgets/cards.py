"""Card widgets for BenchLM - metric cards, stat cards, glass cards, chart cards."""

import flet as ft
from dataclasses import dataclass
from typing import Optional, Callable, Any
from enum import Enum

from benchlm.ui.theme import get_theme


class CardVariant(Enum):
    """Card visual variants."""

    GLASS = "glass"
    ELEVATED = "elevated"
    OUTLINED = "outlined"
    FILLED = "filled"


@dataclass
class CardConfig:
    """Configuration for card appearance."""

    variant: CardVariant = CardVariant.GLASS
    padding: int = 16
    border_radius: int = 16
    elevation: int = 0
    on_click: Optional[Callable] = None
    hover_elevation: int = 4


class BaseCard(ft.Container):
    """Base card with theming support."""

    def __init__(self, config: CardConfig | None = None, **kwargs):
        self.config = config or CardConfig()
        self._theme = get_theme()
        super().__init__(**kwargs)
        self._apply_style()

    def _apply_style(self):
        """Apply card styling based on variant."""
        c = self._theme.colors
        cfg = self.config

        if cfg.variant == CardVariant.GLASS:
            self.bgcolor = c.glass_bg
            self.border = ft.border.all(1, c.glass_border)
            self.shadow = ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=c.shadow,
                offset=ft.Offset(0, 4),
            )
        elif cfg.variant == CardVariant.ELEVATED:
            self.bgcolor = c.surface
            self.border = ft.border.all(1, c.outline)
            self.shadow = ft.BoxShadow(
                spread_radius=0,
                blur_radius=15,
                color=c.shadow_strong,
                offset=ft.Offset(0, 4),
            )
        elif cfg.variant == CardVariant.OUTLINED:
            self.bgcolor = c.surface
            self.border = ft.border.all(1, c.outline)
            self.shadow = None
        elif cfg.variant == CardVariant.FILLED:
            self.bgcolor = c.surface_container
            self.border = None
            self.shadow = None

        self.border_radius = cfg.border_radius
        self.padding = cfg.padding

        if cfg.on_click:
            self.on_click = cfg.on_click
            self.ink = True
            self.animate = ft.Animation(200, ft.AnimationCurve.EASE_OUT)


class MetricCard(BaseCard):
    """Metric display card with icon, value, label, and trend."""

    def __init__(
        self,
        value: str | float = "0",
        label: str = "",
        icon: Optional[str] = None,
        icon_color: Optional[str] = None,
        trend: Optional[float] = None,  # Percentage change
        trend_label: str = "",
        unit: str = "",
        status: str = "normal",  # normal, success, warning, danger
        config: CardConfig | None = None,
        **kwargs
    ):
        self._value = str(value)
        self._label = label
        self._icon = icon
        self._icon_color = icon_color
        self._trend = trend
        self._trend_label = trend_label
        self._unit = unit
        self._status = status

        super().__init__(config, **kwargs)
        self._build()

    def _build(self):
        """Build metric card UI."""
        c = self._theme.colors
        cfg = self.config

        # Status color
        status_colors = {
            "normal": c.on_surface_variant,
            "success": c.success,
            "warning": c.warning,
            "danger": c.danger,
            "info": c.tertiary,
        }
        status_color = status_colors.get(self._status, c.on_surface_variant)

        # Icon
        icon_control = ft.Container()
        if self._icon:
            icon_control = ft.Icon(
                name=self._icon,
                size=24,
                color=self._icon_color or status_color,
            )

        # Value with unit
        value_text = ft.Text(
            self._value,
            size=28,
            weight=ft.FontWeight.BOLD,
            color=c.on_surface,
        )

        if self._unit:
            value_text = ft.Row(
                controls=[
                    value_text,
                    ft.Text(
                        self._unit,
                        size=16,
                        weight=ft.FontWeight.NORMAL,
                        color=c.on_surface_variant,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=4,
                vertical_alignment=ft.CrossAxisAlignment.BASELINE,
            )

        # Trend indicator
        trend_control = ft.Container()
        if self._trend is not None:
            trend_color = c.success if self._trend >= 0 else c.danger
            trend_icon = ft.Icons.TRENDING_UP if self._trend >= 0 else ft.Icons.TRENDING_DOWN
            trend_control = ft.Row(
                controls=[
                    ft.Icon(trend_icon, size=14, color=trend_color),
                    ft.Text(
                        f"{abs(self._trend):.1f}%",
                        size=12,
                        weight=ft.FontWeight.MEDIUM,
                        color=trend_color,
                    ),
                    ft.Text(
                        self._trend_label,
                        size=12,
                        color=c.on_surface_disabled,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=2,
            )

        # Label
        label_text = ft.Text(
            self._label,
            size=13,
            weight=ft.FontWeight.MEDIUM,
            color=c.on_surface_variant,
            text_align=ft.TextAlign.CENTER,
        )

        # Layout
        self.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[ft.Container(expand=True), icon_control],
                    alignment=ft.MainAxisAlignment.END,
                ),
                ft.Container(height=8),
                ft.Container(
                    content=value_text,
                    alignment=ft.alignment.center,
                ),
                ft.Container(height=4),
                trend_control,
                ft.Container(height=4),
                label_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            tight=True,
        )

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, val: str | float):
        self._value = str(val)
        if isinstance(self.content, ft.Column):
            # Find value text (it's in a container at index 2)
            value_container = self.content.controls[2]
            if isinstance(value_container, ft.Container) and isinstance(value_container.content, ft.Text):
                value_container.content.value = self._value
            elif isinstance(value_container, ft.Container) and isinstance(value_container.content, ft.Row):
                value_container.content.controls[0].value = self._value
        self.update()

    @property
    def trend(self) -> float | None:
        return self._trend

    @trend.setter
    def trend(self, val: float | None):
        self._trend = val
        # Would need to rebuild trend control
        self._build()
        self.update()


class StatCard(BaseCard):
    """Statistics card showing multiple metrics in a grid."""

    def __init__(
        self,
        title: str = "",
        stats: dict[str, Any] | None = None,
        layout: str = "grid",  # grid, row, column
        config: CardConfig | None = None,
        **kwargs
    ):
        self._title = title
        self._stats = stats or {}
        self._layout = layout
        super().__init__(config, **kwargs)
        self._build()

    def _build(self):
        """Build stat card UI."""
        c = self._theme.colors

        controls = []

        # Title
        if self._title:
            controls.append(
                ft.Text(
                    self._title,
                    size=16,
                    weight=ft.FontWeight.SEMIBOLD,
                    color=c.on_surface,
                )
            )
            controls.append(ft.Divider(height=1, color=c.outline_variant))
            controls.append(ft.Container(height=8))

        # Stats layout
        if self._layout == "grid":
            stat_controls = []
            for key, value in self._stats.items():
                stat_controls.append(self._create_stat_item(key, value))

            # Create rows of 2-3 items
            items_per_row = 3
            for i in range(0, len(stat_controls), items_per_row):
                row = ft.Row(
                    controls=stat_controls[i:i + items_per_row],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    expand=True,
                )
                controls.append(row)

        elif self._layout == "row":
            stat_controls = [self._create_stat_item(k, v) for k, v in self._stats.items()]
            controls.append(
                ft.Row(
                    controls=stat_controls,
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    expand=True,
                )
            )

        else:  # column
            for key, value in self._stats.items():
                controls.append(self._create_stat_item(key, value))

        self.content = ft.Column(
            controls=controls,
            spacing=8,
            tight=True,
        )

    def _create_stat_item(self, key: str, value: Any) -> ft.Container:
        """Create a single stat item."""
        c = self._theme.colors

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        str(value),
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=c.on_surface,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        key.replace("_", " ").title(),
                        size=11,
                        color=c.on_surface_disabled,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
                tight=True,
            ),
            expand=True,
            padding=ft.padding.symmetric(vertical=8),
        )

    def update_stats(self, stats: dict[str, Any]):
        """Update statistics."""
        self._stats = stats
        self._build()
        self.update()


class GlassCard(BaseCard):
    """Glassmorphism card with customizable content."""

    def __init__(
        self,
        content: ft.Control | None = None,
        header: ft.Control | None = None,
        footer: ft.Control | None = None,
        config: CardConfig | None = None,
        **kwargs
    ):
        self._header = header
        self._footer = footer
        self._main_content = content
        super().__init__(config or CardConfig(variant=CardVariant.GLASS), **kwargs)
        self._build()

    def _build(self):
        """Build glass card."""
        controls = []

        if self._header:
            controls.append(self._header)
            controls.append(ft.Divider(height=1, color=self._theme.colors.glass_border))

        if self._main_content:
            controls.append(self._main_content)

        if self._footer:
            controls.append(ft.Divider(height=1, color=self._theme.colors.glass_border))
            controls.append(self._footer)

        self.content = ft.Column(
            controls=controls,
            spacing=0,
            tight=True,
        )


class ElevatedCard(BaseCard):
    """Elevated material card."""

    def __init__(
        self,
        content: ft.Control | None = None,
        header: ft.Control | None = None,
        footer: ft.Control | None = None,
        config: CardConfig | None = None,
        **kwargs
    ):
        self._header = header
        self._footer = footer
        self._main_content = content
        super().__init__(config or CardConfig(variant=CardVariant.ELEVATED), **kwargs)
        self._build()

    def _build(self):
        controls = []

        if self._header:
            controls.append(self._header)
            controls.append(ft.Divider(height=1, color=self._theme.colors.outline_variant))

        if self._main_content:
            controls.append(self._main_content)

        if self._footer:
            controls.append(ft.Divider(height=1, color=self._theme.colors.outline_variant))
            controls.append(self._footer)

        self.content = ft.Column(
            controls=controls,
            spacing=0,
            tight=True,
        )


class ChartCard(GlassCard):
    """Card specifically for chart containers with lazy loading."""

    def __init__(
        self,
        title: str = "",
        chart: ft.Control | None = None,
        loading: bool = False,
        error: str | None = None,
        actions: list[ft.Control] | None = None,
        config: CardConfig | None = None,
        **kwargs
    ):
        self._title = title
        self._chart = chart
        self._loading = loading
        self._error = error
        self._actions = actions or []

        # Build header with title and actions
        header = self._build_header()
        # Build footer
        footer = None

        super().__init__(
            content=None,  # Built in _build
            header=header,
            footer=footer,
            config=config or CardConfig(variant=CardVariant.GLASS),
            **kwargs
        )
        self._build()

    def _build_header(self) -> ft.Control:
        """Build card header."""
        c = self._theme.colors

        title_text = ft.Text(
            self._title,
            size=16,
            weight=ft.FontWeight.SEMIBOLD,
            color=c.on_surface,
            expand=True,
        )

        action_controls = []
        for action in self._actions:
            action_controls.append(action)

        return ft.Container(
            content=ft.Row(
                controls=[
                    title_text,
                    *action_controls,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.only(bottom=12),
        )

    def _build(self):
        """Build chart card with loading/error states."""
        c = self._theme.colors

        # Chart content area
        if self._loading:
            chart_content = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.ProgressRing(
                            width=32,
                            height=32,
                            stroke_width=3,
                            color=c.primary,
                        ),
                        ft.Container(height=12),
                        ft.Text(
                            "Loading chart...",
                            size=14,
                            color=c.on_surface_variant,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                height=300,
            )
        elif self._error:
            chart_content = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.ERROR_OUTLINE, size=48, color=c.danger),
                        ft.Container(height=12),
                        ft.Text(
                            "Failed to load chart",
                            size=16,
                            weight=ft.FontWeight.MEDIUM,
                            color=c.on_surface,
                        ),
                        ft.Container(height=4),
                        ft.Text(
                            self._error,
                            size=13,
                            color=c.on_surface_variant,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=16),
                        ft.FilledButton(
                            text="Retry",
                            icon=ft.Icons.REFRESH,
                            on_click=lambda _: self._on_retry(),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                height=300,
            )
        else:
            chart_content = ft.Container(
                content=self._chart,
                height=300,
                clip_behavior=ft.ClipBehavior.NONE,
            )

        # Use parent's build but with our content
        controls = []

        if self._header:
            controls.append(self._header)

        controls.append(chart_content)

        self.content = ft.Column(
            controls=controls,
            spacing=0,
            tight=True,
        )

    def set_chart(self, chart: ft.Control):
        """Set chart content."""
        self._chart = chart
        self._loading = False
        self._error = None
        self._build()
        self.update()

    def set_loading(self, loading: bool):
        """Set loading state."""
        self._loading = loading
        self._build()
        self.update()

    def set_error(self, error: str):
        """Set error state."""
        self._error = error
        self._loading = False
        self._build()
        self.update()

    def _on_retry(self):
        """Handle retry click."""
        self.set_loading(True)
        # Parent should handle actual reload