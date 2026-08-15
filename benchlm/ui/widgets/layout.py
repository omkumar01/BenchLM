"""Layout widgets for BenchLM - responsive, grid, flex, scrollable containers."""

import flet as ft
from typing import Optional, List, Callable
from dataclasses import dataclass
from enum import Enum

from benchlm.ui.theme import get_theme


class Breakpoint(Enum):
    """Responsive breakpoints."""

    XS = 0      # < 600px
    SM = 600    # 600px - 900px
    MD = 900    # 900px - 1200px
    LG = 1200   # 1200px - 1800px
    XL = 1800   # > 1800px


@dataclass
class ResponsiveConfig:
    """Responsive configuration for layouts."""

    xs: int = 1
    sm: int = 2
    md: int = 3
    lg: int = 4
    xl: int = 4

    def get_columns(self, width: float) -> int:
        """Get column count for given width."""
        if width >= Breakpoint.XL.value:
            return self.xl
        elif width >= Breakpoint.LG.value:
            return self.lg
        elif width >= Breakpoint.MD.value:
            return self.md
        elif width >= Breakpoint.SM.value:
            return self.sm
        return self.xs


class ResponsiveRow(ft.Row):
    """Responsive row that adapts column count based on width."""

    def __init__(
        self,
        controls: List[ft.Control] = [],
        responsive: ResponsiveConfig | None = None,
        spacing: int = 16,
        run_spacing: int = 16,
        **kwargs
    ):
        self._responsive = responsive or ResponsiveConfig()
        self._original_controls = controls
        self._theme = get_theme()

        super().__init__(
            controls=controls,
            spacing=spacing,
            run_spacing=run_spacing,
            wrap=True,
            **kwargs
        )

        # Listen for resize
        self.on_resize = self._on_resize

    def _on_resize(self, e: ft.ControlEvent):
        """Handle container resize."""
        if hasattr(e.control, 'width') and e.control.width:
            self._update_layout(e.control.width)

    def _update_layout(self, width: float):
        """Update layout based on width."""
        # In Flet, we'd need to recalculate column spans
        # This is a simplified version
        pass

    def set_controls(self, controls: List[ft.Control]):
        """Update controls."""
        self._original_controls = controls
        self.controls = controls
        self.update()


class ResponsiveColumn(ft.Column):
    """Responsive column with adaptive spacing."""

    def __init__(
        self,
        controls: List[ft.Control] = [],
        spacing: dict = None,  # breakpoint -> spacing
        **kwargs
    ):
        self._responsive_spacing = spacing or {
            Breakpoint.XS: 8,
            Breakpoint.SM: 12,
            Breakpoint.MD: 16,
            Breakpoint.LG: 20,
            Breakpoint.XL: 24,
        }
        self._theme = get_theme()

        # Default spacing
        default_spacing = self._responsive_spacing.get(Breakpoint.MD, 16)

        super().__init__(
            controls=controls,
            spacing=default_spacing,
            **kwargs
        )

        self.on_resize = self._on_resize

    def _on_resize(self, e: ft.ControlEvent):
        """Handle resize to update spacing."""
        if hasattr(e.control, 'width') and e.control.width:
            width = e.control.width
            for bp in reversed(list(Breakpoint)):
                if width >= bp.value:
                    self.spacing = self._responsive_spacing.get(bp, 16)
                    break
            self.update()


class GridLayout(ft.Container):
    """CSS Grid-like layout with responsive columns."""

    def __init__(
        self,
        controls: List[ft.Control] = [],
        columns: ResponsiveConfig | int = 4,
        gap: int = 16,
        auto_rows: bool = True,
        **kwargs
    ):
        if isinstance(columns, int):
            columns = ResponsiveConfig(xs=1, sm=2, md=columns, lg=columns, xl=columns)

        self._responsive_columns = columns
        self._gap = gap
        self._auto_rows = auto_rows
        self._theme = get_theme()

        super().__init__(**kwargs)
        self.content = ft.ResponsiveRow(
            controls=controls,
            spacing=gap,
            run_spacing=gap,
        )

        self.on_resize = self._on_resize

    def _on_resize(self, e: ft.ControlEvent):
        """Handle resize for responsive columns."""
        if hasattr(e.control, 'width') and e.control.width:
            cols = self._responsive_columns.get_columns(e.control.width)
            # Update column spans for all controls
            for control in self.content.controls:
                if hasattr(control, 'col'):
                    control.col = {"xs": 12, "sm": 6, "md": 12 // cols, "lg": 12 // cols, "xl": 12 // cols}
            self.content.update()


class FlexLayout(ft.Container):
    """Flexbox layout container."""

    def __init__(
        self,
        controls: List[ft.Control] = [],
        direction: str = "row",  # row, column, row-reverse, column-reverse
        wrap: bool = False,
        justify: str = "start",  # start, center, end, space-between, space-around, space-evenly
        align: str = "stretch",  # start, center, end, stretch, baseline
        gap: int = 0,
        **kwargs
    ):
        self._direction = direction
        self._wrap = wrap
        self._justify = justify
        self._align = align
        self._gap = gap
        self._theme = get_theme()

        super().__init__(**kwargs)

        # Convert to Flet Row/Column
        if direction in ["row", "row-reverse"]:
            self.content = ft.Row(
                controls=controls,
                wrap=wrap,
                alignment=self._get_main_axis_alignment(justify),
                vertical_alignment=self._get_cross_axis_alignment(align),
                spacing=gap,
            )
        else:
            self.content = ft.Column(
                controls=controls,
                wrap=wrap,
                alignment=self._get_main_axis_alignment(justify),
                horizontal_alignment=self._get_cross_axis_alignment(align),
                spacing=gap,
            )

    def _get_main_axis_alignment(self, justify: str) -> ft.MainAxisAlignment:
        mapping = {
            "start": ft.MainAxisAlignment.START,
            "center": ft.MainAxisAlignment.CENTER,
            "end": ft.MainAxisAlignment.END,
            "space-between": ft.MainAxisAlignment.SPACE_BETWEEN,
            "space-around": ft.MainAxisAlignment.SPACE_AROUND,
            "space-evenly": ft.MainAxisAlignment.SPACE_EVENLY,
        }
        return mapping.get(justify, ft.MainAxisAlignment.START)

    def _get_cross_axis_alignment(self, align: str) -> ft.CrossAxisAlignment:
        mapping = {
            "start": ft.CrossAxisAlignment.START,
            "center": ft.CrossAxisAlignment.CENTER,
            "end": ft.CrossAxisAlignment.END,
            "stretch": ft.CrossAxisAlignment.STRETCH,
            "baseline": ft.CrossAxisAlignment.BASELINE,
        }
        return mapping.get(align, ft.CrossAxisAlignment.STRETCH)


class ScrollableContainer(ft.Container):
    """Scrollable container with custom scrollbars."""

    def __init__(
        self,
        content: ft.Control | None = None,
        scroll: str = "auto",  # auto, always, hidden, adaptive
        direction: str = "vertical",  # vertical, horizontal, both
        expand: bool = True,
        show_scrollbar: bool = True,
        **kwargs
    ):
        self._scroll = scroll
        self._direction = direction
        self._show_scrollbar = show_scrollbar
        self._theme = get_theme()

        c = self._theme.colors

        # Create scrollable content
        if direction == "vertical":
            scrollable = ft.ListView(
                controls=[content] if content else [],
                spacing=0,
                padding=0,
                auto_scroll=False,
                expand=expand,
            )
        elif direction == "horizontal":
            scrollable = ft.ListView(
                controls=[content] if content else [],
                spacing=0,
                padding=0,
                auto_scroll=False,
                expand=expand,
            )
            # Flet doesn't have native horizontal ListView, use Row in Container
        else:
            # Both directions - use Column with horizontal scroll
            scrollable = ft.Column(
                controls=[content] if content else [],
                scroll=ft.ScrollMode.AUTO if scroll == "auto" else ft.ScrollMode.ALWAYS,
                expand=expand,
            )

        super().__init__(
            content=scrollable,
            expand=expand,
            **kwargs
        )

    def set_content(self, content: ft.Control):
        """Set container content."""
        if isinstance(self.content, ft.ListView):
            self.content.controls = [content]
        elif isinstance(self.content, ft.Column):
            self.content.controls = [content]
        self.update()


class SplitView(ft.Container):
    """Split view with resizable panes."""

    def __init__(
        self,
        primary: ft.Control,
        secondary: ft.Control,
        orientation: str = "horizontal",  # horizontal, vertical
        primary_fraction: float = 0.5,
        min_primary: int = 200,
        max_primary: int | None = None,
        **kwargs
    ):
        self._primary = primary
        self._secondary = secondary
        self._orientation = orientation
        self._primary_fraction = primary_fraction
        self._min_primary = min_primary
        self._max_primary = max_primary
        self._theme = get_theme()
        self._dragging = False

        super().__init__(**kwargs)
        self._build()

    def _build(self):
        """Build split view."""
        c = self._theme.colors

        # Create draggable divider
        self._divider = ft.Container(
            width=8 if self._orientation == "horizontal" else None,
            height=8 if self._orientation == "vertical" else None,
            bgcolor=c.outline_variant,
            border_radius=4,
            on_hover=self._on_divider_hover,
            on_pan_start=self._on_pan_start,
            on_pan_update=self._on_pan_update,
            on_pan_end=self._on_pan_end,
            cursor=ft.MouseCursor.RESIZE_COLUMN if self._orientation == "horizontal" else ft.MouseCursor.RESIZE_ROW,
        )

        if self._orientation == "horizontal":
            self.content = ft.Row(
                controls=[
                    ft.Container(content=self._primary, expand=True),
                    self._divider,
                    ft.Container(content=self._secondary, expand=True),
                ],
                spacing=0,
                expand=True,
            )
        else:
            self.content = ft.Column(
                controls=[
                    ft.Container(content=self._primary, expand=True),
                    self._divider,
                    ft.Container(content=self._secondary, expand=True),
                ],
                spacing=0,
                expand=True,
            )

    def _on_divider_hover(self, e: ft.HoverEvent):
        """Handle divider hover."""
        if e.data == "true":
            self._divider.bgcolor = self._theme.colors.primary
        else:
            self._divider.bgcolor = self._theme.colors.outline_variant
        self._divider.update()

    def _on_pan_start(self, e: ft.DragStartEvent):
        """Handle drag start."""
        self._dragging = True

    def _on_pan_update(self, e: ft.DragUpdateEvent):
        """Handle drag update."""
        if not self._dragging:
            return

        # In a real implementation, calculate new fractions based on drag delta
        # This would require access to parent container size
        pass

    def _on_pan_end(self, e: ft.DragEndEvent):
        """Handle drag end."""
        self._dragging = False


class MasonryLayout(ft.Container):
    """Masonry (Pinterest-style) layout for variable-height items."""

    def __init__(
        self,
        controls: List[ft.Control] = [],
        columns: ResponsiveConfig | int = 3,
        gap: int = 16,
        **kwargs
    ):
        if isinstance(columns, int):
            columns = ResponsiveConfig(xs=1, sm=2, md=columns, lg=columns, xl=columns)

        self._responsive_columns = columns
        self._gap = gap
        self._theme = get_theme()
        self._columns: List[ft.Column] = []

        super().__init__(**kwargs)
        self._rebuild(controls)

    def _rebuild(self, controls: List[ft.Control]):
        """Rebuild masonry layout."""
        # For simplicity, use ResponsiveRow with columns
        self.content = ft.ResponsiveRow(
            controls=controls,
            spacing=self._gap,
            run_spacing=self._gap,
        )

    def add_control(self, control: ft.Control):
        """Add control to masonry."""
        if isinstance(self.content, ft.ResponsiveRow):
            self.content.controls.append(control)
            self.content.update()


class StackLayout(ft.Stack):
    """Enhanced Stack layout with positioning helpers."""

    @staticmethod
    def positioned(
        control: ft.Control,
        left: float | None = None,
        top: float | None = None,
        right: float | None = None,
        bottom: float | None = None,
        width: float | None = None,
        height: float | None = None,
    ) -> ft.Container:
        """Create positioned container."""
        return ft.Container(
            content=control,
            left=left,
            top=top,
            right=right,
            bottom=bottom,
            width=width,
            height=height,
        )

    @staticmethod
    def centered(control: ft.Control) -> ft.Container:
        """Center control in stack."""
        return ft.Container(
            content=control,
            alignment=ft.Alignment.CENTER,
            expand=True,
        )

    @staticmethod
    def fullscreen(control: ft.Control) -> ft.Container:
        """Fullscreen overlay."""
        return ft.Container(
            content=control,
            expand=True,
            alignment=ft.Alignment.CENTER,
        )


class ConstrainedBox(ft.Container):
    """Container with min/max constraints."""

    def __init__(
        self,
        child: ft.Control,
        min_width: float = 0,
        max_width: float = float('inf'),
        min_height: float = 0,
        max_height: float = float('inf'),
        **kwargs
    ):
        super().__init__(
            content=child,
            width=None,
            height=None,
            min_width=min_width if min_width > 0 else None,
            max_width=max_width if max_width < float('inf') else None,
            min_height=min_height if min_height > 0 else None,
            max_height=max_height if max_height < float('inf') else None,
            **kwargs
        )


class AspectRatio(ft.Container):
    """Container that maintains aspect ratio."""

    def __init__(
        self,
        child: ft.Control,
        aspect_ratio: float = 16/9,
        **kwargs
    ):
        self._aspect_ratio = aspect_ratio
        self._child = child

        super().__init__(**kwargs)
        self.content = child
        self.on_resize = self._on_resize

    def _on_resize(self, e: ft.ControlEvent):
        """Maintain aspect ratio on resize."""
        if hasattr(e.control, 'width') and e.control.width:
            width = e.control.width
            self.height = width / self._aspect_ratio
            self.update()


class SafeArea(ft.Container):
    """Safe area container for mobile notches."""

    def __init__(
        self,
        child: ft.Control,
        top: bool = True,
        bottom: bool = True,
        left: bool = True,
        right: bool = True,
        **kwargs
    ):
        # Flet doesn't have native safe area, simulate with padding
        padding = ft.Padding.only(
            top=44 if top else 0,  # iOS status bar
            bottom=34 if bottom else 0,  # iOS home indicator
            left=0 if left else 0,
            right=0 if right else 0,
        )

        super().__init__(
            content=child,
            padding=padding,
            **kwargs
        )


class AnimatedSwitcher(ft.Container):
    """Animated container that switches between children."""

    def __init__(
        self,
        child: ft.Control | None = None,
        duration: int = 300,
        curve: ft.AnimationCurve = ft.AnimationCurve.EASE_IN_OUT,
        transition: str = "fade",  # fade, slide, scale
        **kwargs
    ):
        self._duration = duration
        self._curve = curve
        self._transition = transition
        self._current_child = child

        super().__init__(
            content=child,
            animate_opacity=duration if transition == "fade" else None,
            animate_scale=ft.Animation(duration, curve) if transition == "scale" else None,
            animate_offset=ft.Animation(duration, curve) if transition == "slide" else None,
            **kwargs
        )

    def set_child(self, child: ft.Control):
        """Switch to new child with animation."""
        if self._transition == "fade":
            self.opacity = 0
            self.update()
            self.content = child
            self.opacity = 1
        elif self._transition == "scale":
            self.scale = 0.8
            self.update()
            self.content = child
            self.scale = 1.0
        elif self._transition == "slide":
            self.offset = ft.Offset(0.1, 0)
            self.update()
            self.content = child
            self.offset = ft.Offset(0, 0)

        self._current_child = child
        self.update()