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
        self.page = page
        self.route = route
        self.title = title
        self.icon = icon
        self._mounted = False

        super().__init__(**kwargs)

        # Page configuration
        self.expand = True
        self.padding = ft.padding.all(24)
        self.content = self.build()

    @abstractmethod
    def build(self) -> ft.Control:
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
        """Show a snackbar message."""
        colors = {
            "info": ft.Colors.BLUE,
            "success": ft.Colors.GREEN,
            "warning": ft.Colors.AMBER,
            "error": ft.Colors.RED,
        }

        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=colors.get(severity, colors["info"]),
            duration=3000,
        )
        self.page.snack_bar.open = True
        self.page.update()

    def show_dialog(self, dialog: ft.AlertDialog):
        """Show a dialog."""
        self.page.open(dialog)

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