"""Base page class for BenchLM pages."""

import flet as ft
from typing import Optional, Any
from abc import ABC, abstractmethod


class BasePage(ft.Container, ABC):
    """Base class for all BenchLM pages."""

    def __init__(
        self,
        page: ft.Page,
        route: str = "",
        title: str = "",
        icon: str = "",
        **kwargs
    ):
        self.app_page = page
        self.route = route
        self.title = title
        self.icon = icon
        self._mounted = False

        super().__init__(**kwargs)

        # Page configuration
        self.expand = True
        self.padding = ft.Padding.all(0) # Padding is handled by app layout now

        # NOTE: no animated entry state - controls first painted at opacity 0
        # then patched to 1.0 with animate_opacity never animate up in the
        # Flet client, leaving pages invisible. Pages render statically.
        self.opacity = 1

        # _build may return the content control OR assign self.content itself
        built = self._build()
        if built is not None:
            self.content = built

    @abstractmethod
    def _build(self) -> ft.Control:
        """Build the page content. Must be implemented by subclasses."""
        pass

    async def on_mount(self):
        """Called when page is mounted/navigated to."""
        self._mounted = True
        await self._on_mount()

    async def on_unmount(self):
        """Called when page is unmounted/navigated away."""
        self._mounted = False
        await self._on_unmount()

    async def _on_mount(self):
        """Override in subclass for mount logic."""
        pass

    async def _on_unmount(self):
        """Override in subclass for unmount logic."""
        pass

    def show_snackbar(self, message: str, severity: str = "info"):
        """Show a modern snackbar message."""
        theme = self.get_theme()
        c = theme.colors
        
        colors = {
            "info": c.tertiary,
            "success": c.success,
            "warning": c.warning,
            "error": c.danger,
        }
        
        icons = {
            "info": ft.Icons.INFO_OUTLINED,
            "success": ft.Icons.CHECK_CIRCLE_OUTLINED,
            "warning": ft.Icons.WARNING_AMBER_OUTLINED,
            "error": ft.Icons.ERROR_OUTLINE,
        }

        self.page.show_dialog(
            ft.SnackBar(
                content=ft.Row(
                    controls=[
                        ft.Icon(icons.get(severity, icons["info"]), color=ft.Colors.WHITE),
                        ft.Text(message, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500),
                    ]
                ),
                bgcolor=colors.get(severity, colors["info"]),
                duration=3000,
                behavior=ft.SnackBarBehavior.FLOATING,
                margin=ft.Margin.all(24),
                shape=ft.RoundedRectangleBorder(radius=12),
            )
        )

    def show_dialog(self, dialog: ft.AlertDialog):
        """Show a dialog."""
        self.page.show_dialog(dialog)

    def navigate(self, route: str):
        """Navigate to a route."""
        self.page.go(route)

    def get_theme(self):
        """Get the current theme."""
        from benchlm.ui.theme import get_theme
        return get_theme()

    def get_config(self):
        """Get the current config."""
        from benchlm.config import get_config
        return get_config()