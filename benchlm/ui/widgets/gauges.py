"""Gauge widgets for BenchLM - circular, linear, and multi-gauge displays."""

import flet as ft
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable
import math

from benchlm.ui.theme import get_theme


class GaugeSize(Enum):
    """Predefined gauge sizes."""

    SMALL = 80
    MEDIUM = 120
    LARGE = 180
    XLARGE = 240

    @property
    def diameter(self) -> int:
        return self.value

    @property
    def stroke_width(self) -> int:
        return max(4, self.value // 20)

    @property
    def font_size(self) -> int:
        return self.value // 6

    @property
    def label_font_size(self) -> int:
        return self.value // 12


@dataclass
class GaugeConfig:
    """Configuration for gauge appearance."""

    size: GaugeSize = GaugeSize.MEDIUM
    min_value: float = 0
    max_value: float = 100
    value: float = 0
    label: str = ""
    unit: str = ""
    show_value: bool = True
    show_label: bool = True
    show_min_max: bool = False
    start_angle: float = -90  # degrees
    sweep_angle: float = 360  # degrees
    track_color: Optional[str] = None
    progress_color: Optional[str] = None
    stroke_width: float = 8
    font_size: int = 16
    label_font_size: int = 12
    icon: Optional[str] = None
    gradient_colors: Optional[list[str]] = None
    animation_duration: int = 500
    easing: ft.AnimationCurve = ft.AnimationCurve.EASE_OUT
    on_click: Optional[Callable] = None


class CircularGauge(ft.Container):
    """Circular gauge widget with animated progress."""

    def __init__(self, config: GaugeConfig | None = None, **kwargs):
        self.config = config or GaugeConfig()
        super().__init__(**kwargs)

        self._value = self.config.value
        self._theme = get_theme()
        self._build()

    def _build(self):
        """Build the gauge UI."""
        c = self._theme.colors
        cfg = self.config

        # Colors
        track_color = cfg.track_color or c.surface_container_high
        progress_color = cfg.progress_color or c.primary

        # Stack with track and progress
        self._track_arc = ft.ProgressRing(
            value=1.0,
            width=cfg.size.diameter,
            height=cfg.size.diameter,
            stroke_width=cfg.stroke_width,
            color=track_color,
            bgcolor=ft.Colors.TRANSPARENT,
        )

        self._progress_arc = ft.ProgressRing(
            value=self._normalized_value,
            width=cfg.size.diameter,
            height=cfg.size.diameter,
            stroke_width=cfg.stroke_width,
            color=progress_color,
            bgcolor=ft.Colors.TRANSPARENT,
        )

        # Value text
        self._value_text = ft.Text(
            self._format_value(self._value),
            size=cfg.font_size,
            weight=ft.FontWeight.BOLD,
            color=c.on_surface,
            text_align=ft.TextAlign.CENTER,
        )

        # Label text
        self._label_text = ft.Text(
            cfg.label,
            size=cfg.label_font_size,
            weight=ft.FontWeight.NORMAL,
            color=c.on_surface_variant,
            text_align=ft.TextAlign.CENTER,
        ) if cfg.show_label else ft.Container()

        # Unit text
        self._unit_text = ft.Text(
            cfg.unit,
            size=cfg.label_font_size - 2,
            weight=ft.FontWeight.NORMAL,
            color=c.on_surface_disabled,
            text_align=ft.TextAlign.CENTER,
        ) if cfg.unit else ft.Container()

        # Min/Max
        self._min_max_text = ft.Text(
            f"{cfg.min_value:.0f} - {cfg.max_value:.0f}",
            size=cfg.label_font_size - 4,
            weight=ft.FontWeight.NORMAL,
            color=c.on_surface_disabled,
            text_align=ft.TextAlign.CENTER,
        ) if cfg.show_min_max else ft.Container()

        # Center content
        center_content = ft.Column(
            controls=[
                self._value_text if cfg.show_value else ft.Container(),
                self._unit_text,
                self._label_text,
                self._min_max_text,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=2,
            tight=True,
        )

        # Stack
        self.content = ft.Stack(
            controls=[
                self._track_arc,
                self._progress_arc,
                ft.Container(
                    content=center_content,
                    width=cfg.size.diameter,
                    height=cfg.size.diameter,
                    alignment=ft.Alignment.CENTER,
                ),
            ],
            width=cfg.size.diameter,
            height=cfg.size.diameter,
        )

        # Apply card styling
        self.width = cfg.size.diameter
        self.height = cfg.size.diameter
        self.border_radius = cfg.size.diameter // 2
        self.animate = ft.Animation(cfg.animation_duration, cfg.easing)

        if cfg.on_click:
            self.on_click = cfg.on_click

    @property
    def _normalized_value(self) -> float:
        """Get normalized value (0-1)."""
        cfg = self.config
        if cfg.max_value == cfg.min_value:
            return 0
        return max(0, min(1, (self._value - cfg.min_value) / (cfg.max_value - cfg.min_value)))

    def _format_value(self, value: float) -> str:
        """Format value for display."""
        if value >= 1000000:
            return f"{value / 1000000:.1f}M"
        elif value >= 1000:
            return f"{value / 1000:.1f}K"
        elif value == int(value):
            return f"{int(value)}"
        else:
            return f"{value:.1f}"

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float):
        self._value = max(self.config.min_value, min(self.config.max_value, val))
        self._progress_arc.value = self._normalized_value
        if self.config.show_value:
            self._value_text.value = self._format_value(self._value)
        try:
            self.update()
        except RuntimeError:
            pass

    def animate_to(self, value: float, duration: int | None = None):
        """Animate gauge to new value."""
        self.value = value

    def set_config(self, config: GaugeConfig):
        """Update gauge configuration."""
        self.config = config
        self._build()
        self.update()


class LinearGauge(ft.Container):
    """Linear (horizontal) gauge widget."""

    def __init__(self, config: GaugeConfig | None = None, **kwargs):
        self.config = config or GaugeConfig()
        super().__init__(**kwargs)

        self._value = self.config.value
        self._theme = get_theme()
        self._build()

    def _build(self):
        """Build the linear gauge UI."""
        c = self._theme.colors
        cfg = self.config

        track_color = cfg.track_color or c.surface_container_high
        progress_color = cfg.progress_color or c.primary

        # Track
        self._track = ft.Container(
            height=8,
            bgcolor=track_color,
            border_radius=4,
        )

        # Progress bar
        self._progress = ft.Container(
            height=8,
            bgcolor=progress_color,
            border_radius=4,
            width=0,  # Will be set by value
            animate=ft.Animation(cfg.animation_duration, cfg.easing),
        )

        # Labels
        self._label_text = ft.Text(
            cfg.label,
            size=12,
            weight=ft.FontWeight.W_500,
            color=c.on_surface,
        ) if cfg.show_label else ft.Container()

        self._value_text = ft.Text(
            self._format_value(self._value) + (f" {cfg.unit}" if cfg.unit else ""),
            size=12,
            weight=ft.FontWeight.BOLD,
            color=c.on_surface,
            text_align=ft.TextAlign.RIGHT,
        ) if cfg.show_value else ft.Container()

        # Min/Max
        self._min_text = ft.Text(
            f"{cfg.min_value:.0f}",
            size=10,
            color=c.on_surface_disabled,
        ) if cfg.show_min_max else ft.Container()

        self._max_text = ft.Text(
            f"{cfg.max_value:.0f}",
            size=10,
            color=c.on_surface_disabled,
        ) if cfg.show_min_max else ft.Container()

        # Layout
        top_row = ft.Row(
            controls=[
                self._label_text,
                ft.Container(expand=True),
                self._value_text,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ) if cfg.show_label or cfg.show_value else ft.Container()

        bottom_row = ft.Row(
            controls=[
                self._min_text,
                ft.Container(expand=True),
                self._max_text,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ) if cfg.show_min_max else ft.Container()

        self.content = ft.Column(
            controls=[
                top_row,
                ft.Container(height=4),
                ft.Stack(
                    controls=[self._track, self._progress],
                    height=8,
                ),
                ft.Container(height=4) if cfg.show_min_max else ft.Container(),
                bottom_row,
            ],
            spacing=0,
            tight=True,
        )

        self.width = cfg.size.diameter * 2 if cfg.size != GaugeSize.SMALL else 200
        self.padding = ft.Padding.symmetric(vertical=8)

    def _format_value(self, value: float) -> str:
        if value >= 1000000:
            return f"{value / 1000000:.1f}M"
        elif value >= 1000:
            return f"{value / 1000:.1f}K"
        elif value == int(value):
            return f"{int(value)}"
        else:
            return f"{value:.1f}"

    @property
    def _normalized_value(self) -> float:
        cfg = self.config
        if cfg.max_value == cfg.min_value:
            return 0
        return max(0, min(1, (self._value - cfg.min_value) / (cfg.max_value - cfg.min_value)))

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float):
        self._value = max(self.config.min_value, min(self.config.max_value, val))
        self._progress.width = self._normalized_value * (self.width or 200)
        if self.config.show_value:
            self._value_text.value = self._format_value(self._value) + (f" {self.config.unit}" if self.config.unit else "")
        self.update()


class MultiGauge(ft.Container):
    """Multi-gauge widget showing multiple circular gauges in a grid."""

    def __init__(
        self,
        gauges: list[GaugeConfig] | None = None,
        columns: int = 3,
        gap: int = 16,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.gauges_config = gauges or []
        self.columns = columns
        self.gap = gap
        self._gauge_widgets: list[CircularGauge] = []
        self._theme = get_theme()
        self._build()

    def _build(self):
        """Build the multi-gauge grid."""
        self._gauge_widgets = [
            CircularGauge(config=gauge_config)
            for gauge_config in self.gauges_config
        ]

        # Create grid
        rows = []
        for i in range(0, len(self._gauge_widgets), self.columns):
            row_gauges = self._gauge_widgets[i:i + self.columns]
            row = ft.Row(
                controls=row_gauges,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=self.gap,
                wrap=True,
            )
            rows.append(row)

        self.content = ft.Column(
            controls=rows,
            spacing=self.gap,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def add_gauge(self, config: GaugeConfig) -> CircularGauge:
        """Add a new gauge."""
        gauge = CircularGauge(config=config)
        self.gauges_config.append(config)
        self._gauge_widgets.append(gauge)
        self._rebuild_grid()
        return gauge

    def remove_gauge(self, index: int) -> bool:
        """Remove gauge at index."""
        if 0 <= index < len(self._gauge_widgets):
            self.gauges_config.pop(index)
            self._gauge_widgets.pop(index)
            self._rebuild_grid()
            return True
        return False

    def _rebuild_grid(self):
        """Rebuild the grid layout."""
        rows = []
        for i in range(0, len(self._gauge_widgets), self.columns):
            row_gauges = self._gauge_widgets[i:i + self.columns]
            row = ft.Row(
                controls=row_gauges,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=self.gap,
                wrap=True,
            )
            rows.append(row)

        self.content.controls = rows
        self.update()

    def get_gauge(self, index: int) -> CircularGauge | None:
        """Get gauge widget by index."""
        if 0 <= index < len(self._gauge_widgets):
            return self._gauge_widgets[index]
        return None

    def set_values(self, values: list[float]):
        """Set values for all gauges."""
        for i, value in enumerate(values):
            if i < len(self._gauge_widgets):
                self._gauge_widgets[i].value = value


class RadialGauge(ft.Container):
    """Radial gauge with gradient and threshold zones."""

    def __init__(
        self,
        value: float = 0,
        min_value: float = 0,
        max_value: float = 100,
        size: GaugeSize = GaugeSize.MEDIUM,
        label: str = "",
        unit: str = "",
        thresholds: list[tuple[float, str]] | None = None,  # (threshold, color)
        **kwargs
    ):
        super().__init__(**kwargs)
        self._value = value
        self.min_value = min_value
        self.max_value = max_value
        self.size = size
        self.label = label
        self.unit = unit
        self.thresholds = thresholds or [
            (0.5, "#22C55E"),    # green
            (0.75, "#F59E0B"),   # amber
            (1.0, "#EF4444"),    # red
        ]
        self._theme = get_theme()
        self._build()

    def _build(self):
        """Build radial gauge with custom painter."""
        # Using a custom paint approach with Stack
        c = self._theme.colors
        d = self.size.diameter
        stroke = self.size.stroke_width

        # Create gradient segments based on thresholds
        segments = []
        prev_threshold = 0.0
        for threshold, color in self.thresholds:
            sweep = (threshold - prev_threshold) * 360
            if sweep > 0:
                segments.append({
                    "sweep": sweep,
                    "color": color,
                    "start": prev_threshold * 360 - 90,
                })
            prev_threshold = threshold

        # Current value arc
        normalized = max(0, min(1, (self._value - self.min_value) / (self.max_value - self.min_value)))
        value_sweep = normalized * 360

        # Build visual representation using stacked containers
        self.content = ft.Stack(
            controls=[
                # Background track
                ft.Container(
                    width=d,
                    height=d,
                    border=ft.Border.all(stroke, c.surface_container_high),
                    border_radius=d // 2,
                ),
                # Threshold arcs (would need custom paint for true arcs)
                # For now, use a progress ring with gradient simulation
                ft.ProgressRing(
                    value=normalized,
                    width=d,
                    height=d,
                    stroke_width=stroke,
                    color=self.thresholds[-1][1],  # Use highest threshold color
                    bgcolor=ft.Colors.TRANSPARENT,
                ),
                # Center content
                ft.Container(
                    width=d,
                    height=d,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                f"{self._value:.1f}{self.unit}",
                                size=self.size.font_size,
                                weight=ft.FontWeight.BOLD,
                                color=c.on_surface,
                            ),
                            ft.Text(
                                self.label,
                                size=self.size.label_font_size,
                                color=c.on_surface_variant,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                    ),
                ),
            ],
            width=d,
            height=d,
        )

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float):
        self._value = max(self.min_value, min(self.max_value, val))
        # Update progress ring
        if isinstance(self.content, ft.Stack) and len(self.content.controls) > 1:
            progress_ring = self.content.controls[1]
            if isinstance(progress_ring, ft.ProgressRing):
                normalized = max(0, min(1, (self._value - self.min_value) / (self.max_value - self.min_value)))
                progress_ring.value = normalized
                # Update value text
                center = self.content.controls[2]
                if isinstance(center, ft.Container) and isinstance(center.content, ft.Column):
                    center.content.controls[0].value = f"{self._value:.1f}{self.unit}"
        self.update()