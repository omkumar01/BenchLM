"""Indicator widgets for BenchLM - status, loading, progress, pulse."""

import flet as ft
import asyncio
from typing import Optional
from dataclasses import dataclass

from benchlm.ui.theme import get_theme


@dataclass
class StatusConfig:
    """Status indicator configuration."""

    status: str = "idle"  # idle, running, success, warning, error, paused
    label: str = ""
    show_dot: bool = True
    show_label: bool = True
    animated: bool = True
    size: str = "medium"  # small, medium, large


class StatusIndicator(ft.Container):
    """Status indicator with dot and label."""

    def __init__(
        self,
        config: StatusConfig | None = None,
        **kwargs
    ):
        self.config = config or StatusConfig()
        self._theme = get_theme()
        self._dot: ft.Container | None = None
        self._label: ft.Text | None = None

        super().__init__(**kwargs)
        self._build()

    def _build(self):
        """Build status indicator."""
        c = self._theme.colors
        cfg = self.config

        # Status colors
        status_colors = {
            "idle": c.on_surface_disabled,
            "running": c.primary,
            "success": c.success,
            "warning": c.warning,
            "error": c.danger,
            "paused": c.warning,
        }

        dot_color = status_colors.get(cfg.status, c.on_surface_disabled)

        # Dot sizes
        dot_sizes = {"small": 8, "medium": 10, "large": 14}
        dot_size = dot_sizes.get(cfg.size, 10)

        self._dot = ft.Container(
            width=dot_size,
            height=dot_size,
            bgcolor=dot_color,
            border_radius=dot_size // 2,
            visible=cfg.show_dot,
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT) if cfg.animated else None,
        )

        # Add pulse animation for running status
        if cfg.status == "running" and cfg.animated:
            self._dot.animate = ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT)
            self._start_pulse()

        self._label = ft.Text(
            cfg.label or cfg.status.title(),
            size={"small": 11, "medium": 13, "large": 15}.get(cfg.size, 13),
            weight=ft.FontWeight.MEDIUM,
            color=c.on_surface,
            visible=cfg.show_label,
        )

        controls = []
        if cfg.show_dot:
            controls.append(self._dot)
            if cfg.show_label:
                controls.append(ft.Container(width=8))

        if cfg.show_label:
            controls.append(self._label)

        self.content = ft.Row(
            controls=controls,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        )

    def _start_pulse(self):
        """Start pulse animation for running status."""
        async def pulse():
            while self.config.status == "running" and self._dot:
                self._dot.width = 14
                self._dot.height = 14
                self._dot.update()
                await asyncio.sleep(500)
                self._dot.width = 10
                self._dot.height = 10
                self._dot.update()
                await asyncio.sleep(500)

        asyncio.create_task(pulse())

    def set_status(self, status: str, label: str | None = None):
        """Update status."""
        c = self._theme.colors
        cfg = self.config

        cfg.status = status
        if label:
            cfg.label = label

        status_colors = {
            "idle": c.on_surface_disabled,
            "running": c.primary,
            "success": c.success,
            "warning": c.warning,
            "error": c.danger,
            "paused": c.warning,
        }

        dot_color = status_colors.get(status, c.on_surface_disabled)

        if self._dot:
            self._dot.bgcolor = dot_color
            self._dot.update()

        if self._label:
            self._label.value = cfg.label or status.title()
            self._label.update()

        # Handle pulse animation
        if status == "running" and cfg.animated:
            self._start_pulse()


class LoadingSpinner(ft.Container):
    """Loading spinner with optional message."""

    def __init__(
        self,
        message: str = "",
        size: str = "medium",  # small, medium, large
        color: str | None = None,
        **kwargs
    ):
        self.message = message
        self.size = size
        self._color = color
        self._theme = get_theme()
        self._spinner: ft.ProgressRing | None = None

        super().__init__(**kwargs)
        self._build()

    def _build(self):
        """Build loading spinner."""
        c = self._theme.colors
        color = self._color or c.primary

        sizes = {"small": 24, "medium": 40, "large": 56}
        size = sizes.get(self.size, 40)
        stroke = {"small": 2, "medium": 3, "large": 4}[self.size]

        self._spinner = ft.ProgressRing(
            width=size,
            height=size,
            stroke_width=stroke,
            color=color,
        )

        message_text = ft.Text(
            self.message,
            size={"small": 12, "medium": 14, "large": 16}[self.size],
            color=c.on_surface_variant,
            text_align=ft.TextAlign.CENTER,
        ) if self.message else ft.Container()

        self.content = ft.Column(
            controls=[
                ft.Container(
                    content=self._spinner,
                    alignment=ft.alignment.center,
                ),
                ft.Container(height=12) if self.message else ft.Container(),
                message_text,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=0,
            tight=True,
        )

        self.alignment = ft.alignment.center


class ProgressRing(ft.Container):
    """Circular progress ring with value display."""

    def __init__(
        self,
        value: float = 0,
        max_value: float = 100,
        size: int = 80,
        stroke_width: int = 6,
        show_value: bool = True,
        show_label: bool = False,
        label: str = "",
        color: str | None = None,
        track_color: str | None = None,
        **kwargs
    ):
        self._value = value
        self.max_value = max_value
        self.size = size
        self.stroke_width = stroke_width
        self.show_value = show_value
        self.show_label = show_label
        self.label = label
        self._theme = get_theme()

        c = self._theme.colors
        self._color = color or c.primary
        self._track_color = track_color or c.surface_container_high

        super().__init__(**kwargs)
        self._build()

    def _build(self):
        """Build progress ring."""
        c = self._theme.colors

        # Background track
        self._track = ft.Container(
            width=self.size,
            height=self.size,
            border=ft.border.all(self.stroke_width, self._track_color),
            border_radius=self.size // 2,
        )

        # Progress arc (using Stack with rotation)
        # Flet doesn't have native arc, so we use a custom approach
        # For now, use ProgressRing with value
        self._progress = ft.ProgressRing(
            value=self._normalized_value,
            width=self.size,
            height=self.size,
            stroke_width=self.stroke_width,
            color=self._color,
            bgcolor=ft.Colors.TRANSPARENT,
        )

        # Center content
        center_content = ft.Column(
            controls=[
                ft.Text(
                    f"{self._percentage:.0f}%",
                    size=self.size // 5,
                    weight=ft.FontWeight.BOLD,
                    color=c.on_surface,
                ) if self.show_value else ft.Container(),
                ft.Text(
                    self.label,
                    size=self.size // 12,
                    color=c.on_surface_variant,
                ) if self.show_label and self.label else ft.Container(),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=2,
            tight=True,
        )

        self.content = ft.Stack(
            controls=[
                self._track,
                self._progress,
                ft.Container(
                    content=center_content,
                    width=self.size,
                    height=self.size,
                    alignment=ft.alignment.center,
                ),
            ],
            width=self.size,
            height=self.size,
        )

    @property
    def _normalized_value(self) -> float:
        if self.max_value == 0:
            return 0
        return max(0, min(1, self._value / self.max_value))

    @property
    def _percentage(self) -> float:
        return self._normalized_value * 100

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float):
        self._value = max(0, min(self.max_value, val))
        self._progress.value = self._normalized_value
        if self.show_value:
            # Update center text - find it in stack
            for control in self.content.controls:
                if isinstance(control, ft.Container) and isinstance(control.content, ft.Column):
                    for child in control.content.controls:
                        if isinstance(child, ft.Text) and "%" in child.value:
                            child.value = f"{self._percentage:.0f}%"
                            child.update()
        self.update()


class PulseIndicator(ft.Container):
    """Pulsing indicator for live/recording states."""

    def __init__(
        self,
        color: str | None = None,
        size: int = 12,
        speed: float = 1.0,  # pulses per second
        **kwargs
    ):
        self._color = color
        self.size = size
        self.speed = speed
        self._theme = get_theme()
        self._pulse_container: ft.Container | None = None
        self._running = False

        super().__init__(**kwargs)
        self._build()

    def _build(self):
        """Build pulse indicator."""
        c = self._theme.colors
        color = self._color or c.danger

        self._pulse_container = ft.Container(
            width=self.size,
            height=self.size,
            bgcolor=color,
            border_radius=self.size // 2,
        )

        self.content = self._pulse_container

    def start(self):
        """Start pulsing."""
        self._running = True
        asyncio.create_task(self._pulse_loop())

    def stop(self):
        """Stop pulsing."""
        self._running = False

    async def _pulse_loop(self):
        """Pulse animation loop."""
        import math

        while self._running and self._pulse_container:
            # Fade in/out using opacity
            for i in range(20):
                if not self._running:
                    break
                opacity = 0.3 + 0.7 * (1 + math.sin(i * math.pi / 10)) / 2
                self._pulse_container.opacity = opacity
                self._pulse_container.update()
                await asyncio.sleep(1 / (self.speed * 20))

            await asyncio.sleep(1 / self.speed)


class SkeletonLoader(ft.Container):
    """Skeleton loading placeholder for content."""

    def __init__(
        self,
        width: float | None = None,
        height: float = 20,
        border_radius: int = 4,
        **kwargs
    ):
        self._width = width
        self._height = height
        self._border_radius = border_radius
        self._theme = get_theme()

        super().__init__(**kwargs)
        self._build()

    def _build(self):
        """Build skeleton loader."""
        c = self._theme.colors

        self.content = ft.Container(
            width=self._width,
            height=self._height,
            bgcolor=c.surface_container_high,
            border_radius=self._border_radius,
            animate=ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT),
        )

        # Start shimmer animation
        self._start_shimmer()

    def _start_shimmer(self):
        """Start shimmer animation."""
        import asyncio

        async def shimmer():
            c = self._theme.colors
            while True:
                self.content.bgcolor = c.surface_container_high
                self.content.update()
                await asyncio.sleep(500)
                self.content.bgcolor = c.surface_container
                self.content.update()
                await asyncio.sleep(500)

        asyncio.create_task(shimmer())


class Badge(ft.Container):
    """Badge component for counts and labels."""

    def __init__(
        self,
        text: str = "",
        color: str | None = None,
        size: str = "medium",  # small, medium, large
        dot: bool = False,
        **kwargs
    ):
        self.text = text
        self._color = color
        self.size = size
        self.dot = dot
        self._theme = get_theme()

        super().__init__(**kwargs)
        self._build()

    def _build(self):
        """Build badge."""
        c = self._theme.colors
        color = self._color or c.primary

        sizes = {
            "small": {"padding": 4, "font_size": 10, "height": 18},
            "medium": {"padding": 6, "font_size": 11, "height": 22},
            "large": {"padding": 8, "font_size": 12, "height": 26},
        }
        sz = sizes.get(self.size, sizes["medium"])

        if self.dot:
            content = ft.Row(
                controls=[
                    ft.Container(
                        width=6,
                        height=6,
                        bgcolor=color,
                        border_radius=3,
                    ),
                    ft.Container(width=4),
                    ft.Text(
                        self.text,
                        size=sz["font_size"],
                        weight=ft.FontWeight.BOLD,
                        color=c.on_primary,
                    ),
                ],
                spacing=0,
            )
        else:
            content = ft.Text(
                self.text,
                size=sz["font_size"],
                weight=ft.FontWeight.BOLD,
                color=c.on_primary,
            )

        self.content = content
        self.padding = ft.padding.symmetric(horizontal=sz["padding"], vertical=2)
        self.bgcolor = color
        self.border_radius = sz["height"] // 2
        self.height = sz["height"]
        self.alignment = ft.alignment.center