"""Navigation widgets for BenchLM - rail, drawer, tabs, breadcrumb."""

import flet as ft
from dataclasses import dataclass
from typing import Optional, Callable, Any
from enum import Enum

from benchlm.ui.theme import get_theme


class NavigationItem:
    """Navigation item definition."""

    def __init__(
        self,
        key: str,
        label: str,
        icon: str,
        selected_icon: str | None = None,
        badge: str | None = None,
        tooltip: str | None = None,
        enabled: bool = True,
        children: list["NavigationItem"] | None = None,
    ):
        self.key = key
        self.label = label
        self.icon = icon
        self.selected_icon = selected_icon or icon
        self.badge = badge
        self.tooltip = tooltip or label
        self.enabled = enabled
        self.children = children or []


class NavigationRail(ft.NavigationRail):
    """Custom navigation rail with theming."""

    def __init__(
        self,
        items: list[NavigationItem],
        selected_key: str = "",
        on_change: Optional[Callable[[str], None]] = None,
        extended: bool = False,
        min_width: int = 72,
        max_width: int = 280,
        **kwargs
    ):
        self.items = items
        self._selected_key = selected_key
        self.on_change = on_change
        self._theme = get_theme()

        # Build destinations
        destinations = []
        for item in items:
            if not item.enabled:
                continue
            destinations.append(
                ft.NavigationRailDestination(
                    icon=ft.Icon(item.icon, size=24),
                    selected_icon=ft.Icon(item.selected_icon, size=24),
                    label=item.label if extended else None,
                    tooltip=item.tooltip,
                )
            )

        super().__init__(
            destinations=destinations,
            selected_index=self._get_selected_index(),
            on_change=self._on_change,
            extended=extended,
            min_width=min_width,
            max_width=max_width,
            bgcolor=ft.Colors.TRANSPARENT,
            indicator_color=self._theme.colors.primary_container,
            label_type=ft.NavigationRailLabelType.ALL if extended else ft.NavigationRailLabelType.NONE,
            **kwargs
        )

    def _get_selected_index(self) -> int:
        """Get index of selected item."""
        enabled_items = [i for i in self.items if i.enabled]
        for idx, item in enumerate(enabled_items):
            if item.key == self._selected_key:
                return idx
        return 0

    def _on_change(self, e: ft.ControlEvent):
        """Handle selection change."""
        enabled_items = [i for i in self.items if i.enabled]
        if 0 <= e.control.selected_index < len(enabled_items):
            selected_item = enabled_items[e.control.selected_index]
            self._selected_key = selected_item.key
            if self.on_change:
                self.on_change(selected_item.key)

    @property
    def selected_key(self) -> str:
        return self._selected_key

    @selected_key.setter
    def selected_key(self, key: str):
        self._selected_key = key
        self.selected_index = self._get_selected_index()
        self.update()

    def set_badge(self, key: str, badge: str | None):
        """Set badge for item."""
        # NavigationRail doesn't support badges directly
        # Would need custom implementation
        pass


class NavigationDrawer(ft.NavigationDrawer):
    """Custom navigation drawer with theming."""

    def __init__(
        self,
        items: list[NavigationItem],
        selected_key: str = "",
        on_change: Optional[Callable[[str], None]] = None,
        header: ft.Control | None = None,
        footer: ft.Control | None = None,
        **kwargs
    ):
        self.items = items
        self._selected_key = selected_key
        self.on_change = on_change
        self._theme = get_theme()

        # Build controls
        controls = []

        if header:
            controls.append(header)
            controls.append(ft.Divider(height=1))

        # Build item tiles
        self._item_tiles = {}
        for item in items:
            if not item.enabled:
                continue
            tile = self._create_tile(item)
            self._item_tiles[item.key] = tile
            controls.append(tile)

        if footer:
            controls.append(ft.Divider(height=1))
            controls.append(footer)

        super().__init__(
            controls=controls,
            selected_index=self._get_selected_index(),
            on_change=self._on_change,
            bgcolor=self._theme.colors.surface,
            indicator_color=self._theme.colors.primary_container,
            **kwargs
        )

    def _create_tile(self, item: NavigationItem) -> ft.NavigationDrawerDestination:
        """Create navigation drawer destination."""
        is_selected = item.key == self._selected_key

        return ft.NavigationDrawerDestination(
            icon=ft.Icon(item.icon, color=self._theme.colors.on_surface_variant),
            selected_icon=ft.Icon(item.selected_icon, color=self._theme.colors.primary),
            label=item.label,
            tooltip=item.tooltip,
        )

    def _get_selected_index(self) -> int:
        """Get index of selected item."""
        enabled_items = [i for i in self.items if i.enabled]
        for idx, item in enumerate(enabled_items):
            if item.key == self._selected_key:
                return idx
        return 0

    def _on_change(self, e: ft.ControlEvent):
        """Handle selection change."""
        enabled_items = [i for i in self.items if i.enabled]
        if 0 <= e.control.selected_index < len(enabled_items):
            selected_item = enabled_items[e.control.selected_index]
            self._selected_key = selected_item.key

            # Update tile selection states
            for key, tile in self._item_tiles.items():
                tile.selected = (key == selected_item.key)

            if self.on_change:
                self.on_change(selected_item.key)

            self.update()

    @property
    def selected_key(self) -> str:
        return self._selected_key

    @selected_key.setter
    def selected_key(self, key: str):
        self._selected_key = key
        self.selected_index = self._get_selected_index()

        # Update tiles
        for k, tile in self._item_tiles.items():
            tile.selected = (k == key)

        self.update()


class TabBar(ft.Tabs):
    """Custom tab bar with theming."""

    def __init__(
        self,
        tabs: list[ft.Tab],
        selected_index: int = 0,
        on_change: Optional[Callable[[int], None]] = None,
        scrollable: bool = True,
        divider_color: str | None = None,
        indicator_color: str | None = None,
        label_color: str | None = None,
        unselected_label_color: str | None = None,
        **kwargs
    ):
        self._theme = get_theme()
        c = self._theme.colors

        super().__init__(
            tabs=tabs,
            selected_index=selected_index,
            on_change=lambda e: on_change(e.control.selected_index) if on_change else None,
            scrollable=scrollable,
            divider_color=divider_color or c.outline_variant,
            indicator_color=indicator_color or c.primary,
            label_color=label_color or c.on_surface,
            unselected_label_color=unselected_label_color or c.on_surface_disabled,
            overlay_color=ft.Colors.TRANSPARENT,
            **kwargs
        )


class Breadcrumb(ft.Container):
    """Breadcrumb navigation component."""

    def __init__(
        self,
        items: list[tuple[str, Optional[Callable]]],  # (label, on_click)
        separator: str = "/",
        **kwargs
    ):
        self.items = items
        self.separator = separator
        self._theme = get_theme()

        super().__init__(**kwargs)
        self._build()

    def _build(self):
        """Build breadcrumb."""
        c = self._theme.colors

        controls = []
        for i, (label, on_click) in enumerate(self.items):
            if i > 0:
                controls.append(
                    ft.Text(
                        self.separator,
                        size=13,
                        color=c.on_surface_disabled,
                    )
                )

            is_last = i == len(self.items) - 1

            if on_click and not is_last:
                controls.append(
                    ft.TextButton(
                        text=label,
                        style=ft.ButtonStyle(
                            color=c.on_surface_variant,
                            overlay_color=c.primary_container,
                        ),
                        on_click=on_click,
                    )
                )
            else:
                controls.append(
                    ft.Text(
                        label,
                        size=13,
                        weight=ft.FontWeight.W_500 if is_last else ft.FontWeight.NORMAL,
                        color=c.on_surface if is_last else c.on_surface_variant,
                    )
                )

        self.content = ft.Row(
            controls=controls,
            spacing=4,
            tight=True,
        )
        self.padding = ft.Padding.symmetric(vertical=8, horizontal=12)


class SegmentedButton(ft.Container):
    """Segmented button group for mutually exclusive options."""

    def __init__(
        self,
        options: list[tuple[str, str, Any]],  # (key, label, icon)
        selected_key: str = "",
        on_change: Optional[Callable[[str], None]] = None,
        allow_empty: bool = False,
        **kwargs
    ):
        self.options = options
        self._selected_key = selected_key
        self.on_change = on_change
        self.allow_empty = allow_empty
        self._theme = get_theme()
        self._buttons = {}

        super().__init__(**kwargs)
        self._build()

    def _build(self):
        """Build segmented button."""
        c = self._theme.colors

        buttons = []
        for key, label, icon in self.options:
            is_selected = key == self._selected_key

            btn = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(icon, size=18, color=c.primary if is_selected else c.on_surface_variant),
                        ft.Text(
                            label,
                            size=13,
                            weight=ft.FontWeight.W_500,
                            color=c.on_primary if is_selected else c.on_surface,
                        ),
                    ],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                bgcolor=c.primary if is_selected else c.surface_variant,
                border_radius=8,
                border=ft.Border.all(1, c.outline_variant) if not is_selected else None,
                on_click=lambda e, k=key: self._on_click(k),
                ink=True,
                animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            )

            self._buttons[key] = btn
            buttons.append(btn)

        self.content = ft.Row(
            controls=buttons,
            spacing=4,
            tight=True,
        )

    def _on_click(self, key: str):
        """Handle button click."""
        if key == self._selected_key and self.allow_empty:
            self._selected_key = ""
        else:
            self._selected_key = key

        # Update button states
        c = self._theme.colors
        for k, btn in self._buttons.items():
            is_selected = k == self._selected_key
            btn.bgcolor = c.primary if is_selected else c.surface_variant
            btn.border = None if is_selected else ft.Border.all(1, c.outline_variant)

            # Update content colors
            if isinstance(btn.content, ft.Row):
                for control in btn.content.controls:
                    if isinstance(control, ft.Icon):
                        control.color = c.on_primary if is_selected else c.on_surface_variant
                    elif isinstance(control, ft.Text):
                        control.color = c.on_primary if is_selected else c.on_surface

        if self.on_change:
            self.on_change(self._selected_key)

        self.update()

    @property
    def selected_key(self) -> str:
        return self._selected_key

    @selected_key.setter
    def selected_key(self, key: str):
        self._selected_key = key
        self._on_click(key)


class Stepper(ft.Container):
    """Stepper component for multi-step flows."""

    def __init__(
        self,
        steps: list[tuple[str, str]],  # (key, label)
        current_step: int = 0,
        on_step_change: Optional[Callable[[int], None]] = None,
        **kwargs
    ):
        self.steps = steps
        self._current_step = current_step
        self.on_step_change = on_step_change
        self._theme = get_theme()
        self._step_controls = []

        super().__init__(**kwargs)
        self._build()

    def _build(self):
        """Build stepper."""
        c = self._theme.colors

        controls = []
        for i, (key, label) in enumerate(self.steps):
            is_active = i == self._current_step
            is_completed = i < self._current_step

            # Step circle
            circle = ft.Container(
                content=ft.Text(
                    str(i + 1),
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=c.on_primary if (is_active or is_completed) else c.on_surface_disabled,
                ) if not is_completed else ft.Icon(
                    ft.Icons.CHECK,
                    size=16,
                    color=c.on_primary,
                ),
                width=32,
                height=32,
                bgcolor=c.primary if (is_active or is_completed) else c.surface_container_high,
                border_radius=16,
                alignment=ft.Alignment.CENTER,
                border=ft.Border.all(2, c.primary) if is_active else None,
            )

            # Step label
            label_text = ft.Text(
                label,
                size=12,
                weight=ft.FontWeight.W_500 if is_active else ft.FontWeight.NORMAL,
                color=c.on_surface if (is_active or is_completed) else c.on_surface_disabled,
                text_align=ft.TextAlign.CENTER,
                max_lines=2,
            )

            step_column = ft.Column(
                controls=[circle, ft.Container(height=4), label_text],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            )

            self._step_controls.append(step_column)
            controls.append(step_column)

            # Connector line (except last)
            if i < len(self.steps) - 1:
                controls.append(
                    ft.Container(
                        width=2,
                        height=24,
                        bgcolor=c.primary if is_completed else c.outline_variant,
                        margin=ft.Margin.only(top=4, bottom=4),
                        alignment=ft.Alignment.CENTER,
                    )
                )

        self.content = ft.Row(
            controls=controls,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    @property
    def current_step(self) -> int:
        return self._current_step

    @current_step.setter
    def current_step(self, step: int):
        self._current_step = max(0, min(step, len(self.steps) - 1))
        self._build()
        self.update()

    def next_step(self):
        """Go to next step."""
        if self._current_step < len(self.steps) - 1:
            self.current_step = self._current_step + 1
            if self.on_step_change:
                self.on_step_change(self._current_step)

    def prev_step(self):
        """Go to previous step."""
        if self._current_step > 0:
            self.current_step = self._current_step - 1
            if self.on_step_change:
                self.on_step_change(self._current_step)