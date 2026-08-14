"""Main application entry point and shell for BenchLM."""

import flet as ft
import asyncio
from typing import Optional, Dict, Callable

from benchlm.config import get_config, Config
from benchlm.logging_config import setup_logging
from benchlm.di import configure_container, get_container, DIContainer
from benchlm.ui.theme import BenchLMTheme, get_theme, apply_theme_to_page
from benchlm.ui.pages import (
    DashboardPage,
    ModelsPage,
    BenchmarkPage,
    LiveMonitorPage,
    ResultsPage,
    ComparisonPage,
    HistoryPage,
    LeaderboardPage,
    DatasetsPage,
    ReportsPage,
    SettingsPage,
)
from benchlm.database import init_database, close_database


class BenchLMApplication:
    """Main BenchLM application class."""

    def __init__(self, page: ft.Page):
        self.page = page
        self._config: Optional[Config] = None
        self._theme: Optional[BenchLMTheme] = None
        self._container: Optional[DIContainer] = None
        self._pages: Dict[str, ft.Control] = {}
        self._current_page: Optional[str] = None
        self._navigation_rail: Optional[ft.NavigationRail] = None
        self._navigation_drawer: Optional[ft.NavigationDrawer] = None
        self._initialized = False

    async def initialize(self):
        """Initialize the application."""
        if self._initialized:
            return

        # Load configuration
        self._config = get_config()

        # Setup logging
        setup_logging(self._config.logging)

        # Setup theme
        self._theme = get_theme(self._config.ui)
        apply_theme_to_page(self.page, self._theme)

        # Configure DI container
        self._container = configure_container()

        # Initialize database
        await init_database()

        # Configure page
        self._configure_page()

        # Build UI
        self._build_ui()

        self._initialized = True

    def _configure_page(self):
        """Configure Flet page settings."""
        self.page.title = "BenchLM - LLM Benchmarking Suite"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.window.min_width = 1000
        self.page.window.min_height = 700
        self.page.window.width = 1400
        self.page.window.height = 900
        self.page.padding = 0
        self.page.spacing = 0

        # Fonts
        self.page.fonts = {
            "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@100;300;400;500;600;700;800&display=swap",
            "JetBrains Mono": "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap",
        }

        # Route handling
        self.page.on_route_change = self._on_route_change
        self.page.on_view_pop = self._on_view_pop

    def _build_ui(self):
        """Build the main application UI."""
        c = self._theme.colors

        # Navigation Rail (Desktop)
        self._navigation_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=72,
            max_width=280,
            bgcolor=ft.Colors.TRANSPARENT,
            indicator_color=c.primary_container,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.DASHBOARD_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.DASHBOARD, size=24),
                    label="Dashboard",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.MODEL_TRAINING_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.MODEL_TRAINING, size=24),
                    label="Models",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.SPEED_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.SPEED, size=24),
                    label="Benchmark",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.MONITOR_HEART_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.MONITOR_HEART, size=24),
                    label="Live Monitor",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.ANALYTICS_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.ANALYTICS, size=24),
                    label="Results",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.COMPARE_ARROWS_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.COMPARE_ARROWS, size=24),
                    label="Comparison",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.HISTORY_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.HISTORY, size=24),
                    label="History",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.LEADERBOARD_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.LEADERBOARD, size=24),
                    label="Leaderboard",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.DATASET_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.DATASET, size=24),
                    label="Datasets",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.DESCRIPTION, size=24),
                    label="Reports",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.SETTINGS_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.SETTINGS, size=24),
                    label="Settings",
                ),
            ],
            on_change=self._on_navigation_change,
        )

        # Navigation Drawer (Mobile)
        self._navigation_drawer = ft.NavigationDrawer(
            selected_index=0,
            bgcolor=c.surface,
            indicator_color=c.primary_container,
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.SPEED, size=32, color=c.primary),
                                    ft.Container(width=12),
                                    ft.Text("BenchLM", size=24, weight=ft.FontWeight.BOLD, color=c.on_surface),
                                ],
                            ),
                            ft.Text("LLM Benchmarking Suite", size=13, color=c.on_surface_variant),
                        ],
                    ),
                    padding=24,
                ),
                ft.Divider(height=1, color=c.outline_variant),
                ft.NavigationDrawerDestination(
                    icon=ft.Icon(ft.Icons.DASHBOARD_OUTLINED, color=c.on_surface_variant),
                    selected_icon=ft.Icon(ft.Icons.DASHBOARD, color=c.primary),
                    label="Dashboard",
                ),
                ft.NavigationDrawerDestination(
                    icon=ft.Icon(ft.Icons.MODEL_TRAINING_OUTLINED, color=c.on_surface_variant),
                    selected_icon=ft.Icon(ft.Icons.MODEL_TRAINING, color=c.primary),
                    label="Models",
                ),
                ft.NavigationDrawerDestination(
                    icon=ft.Icon(ft.Icons.SPEED_OUTLINED, color=c.on_surface_variant),
                    selected_icon=ft.Icon(ft.Icons.SPEED, color=c.primary),
                    label="Benchmark",
                ),
                ft.NavigationDrawerDestination(
                    icon=ft.Icon(ft.Icons.MONITOR_HEART_OUTLINED, color=c.on_surface_variant),
                    selected_icon=ft.Icon(ft.Icons.MONITOR_HEART, color=c.primary),
                    label="Live Monitor",
                ),
                ft.NavigationDrawerDestination(
                    icon=ft.Icon(ft.Icons.ANALYTICS_OUTLINED, color=c.on_surface_variant),
                    selected_icon=ft.Icon(ft.Icons.ANALYTICS, color=c.primary),
                    label="Results",
                ),
                ft.NavigationDrawerDestination(
                    icon=ft.Icon(ft.Icons.COMPARE_ARROWS_OUTLINED, color=c.on_surface_variant),
                    selected_icon=ft.Icon(ft.Icons.COMPARE_ARROWS, color=c.primary),
                    label="Comparison",
                ),
                ft.NavigationDrawerDestination(
                    icon=ft.Icon(ft.Icons.HISTORY_OUTLINED, color=c.on_surface_variant),
                    selected_icon=ft.Icon(ft.Icons.HISTORY, color=c.primary),
                    label="History",
                ),
                ft.NavigationDrawerDestination(
                    icon=ft.Icon(ft.Icons.LEADERBOARD_OUTLINED, color=c.on_surface_variant),
                    selected_icon=ft.Icon(ft.Icons.LEADERBOARD, color=c.primary),
                    label="Leaderboard",
                ),
                ft.NavigationDrawerDestination(
                    icon=ft.Icon(ft.Icons.DATASET_OUTLINED, color=c.on_surface_variant),
                    selected_icon=ft.Icon(ft.Icons.DATASET, color=c.primary),
                    label="Datasets",
                ),
                ft.NavigationDrawerDestination(
                    icon=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, color=c.on_surface_variant),
                    selected_icon=ft.Icon(ft.Icons.DESCRIPTION, color=c.primary),
                    label="Reports",
                ),
                ft.Divider(height=1, color=c.outline_variant),
                ft.NavigationDrawerDestination(
                    icon=ft.Icon(ft.Icons.SETTINGS_OUTLINED, color=c.on_surface_variant),
                    selected_icon=ft.Icon(ft.Icons.SETTINGS, color=c.primary),
                    label="Settings",
                ),
            ],
            on_change=self._on_drawer_change,
        )

        # Page Content Area
        self._page_content = ft.Container(
            content=ft.Text("Loading...", color=c.on_surface_variant),
            expand=True,
            bgcolor=c.background,
        )

        # Responsive Layout
        self._main_layout = ft.Row(
            controls=[
                # Navigation Rail (shown on desktop)
                ft.Container(
                    content=self._navigation_rail,
                    visible=self.page.width >= 900,
                    width=72,
                ),
                # Vertical divider
                ft.VerticalDivider(width=1, thickness=1, color=c.outline_variant, visible=self.page.width >= 900),
                # Page content
                ft.Container(
                    content=self._page_content,
                    expand=True,
                    padding=ft.padding.all(24),
                ),
            ],
            expand=True,
            spacing=0,
        )

        # App Bar (Mobile)
        self._app_bar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.Icons.MENU,
                on_click=lambda _: self.page.open(self._navigation_drawer),
            ),
            title=ft.Text("BenchLM", weight=ft.FontWeight.BOLD),
            bgcolor=c.surface,
            actions=[
                ft.IconButton(icon=ft.Icons.BRIGHTNESS_6, on_click=self._toggle_theme),
                ft.IconButton(icon=ft.Icons.FULLSCREEN, on_click=self._toggle_fullscreen),
            ],
            visible=self.page.width < 900,
        )

        # Main page structure
        self.page.appbar = self._app_bar
        self.page.add(self._main_layout)

        # Initial navigation
        self.page.go("/dashboard")

    async def _on_route_change(self, e: ft.RouteChangeEvent):
        """Handle route changes."""
        route = e.route

        # Parse route and parameters
        if "?" in route:
            base_route, params = route.split("?", 1)
        else:
            base_route, params = route, ""

        # Get or create page
        page_control = await self._get_page(base_route, params)

        if page_control:
            # Update navigation selection
            self._update_navigation_selection(base_route)

            # Animate page transition
            await self._transition_page(page_control)

            self._current_page = base_route

    def _on_view_pop(self, e: ft.ViewPopEvent):
        """Handle view pop (back navigation)."""
        self.page.go("/dashboard")

    def _on_navigation_change(self, e: ft.ControlEvent):
        """Handle navigation rail selection."""
        routes = [
            "/dashboard",
            "/models",
            "/benchmark",
            "/live-monitor",
            "/results",
            "/comparison",
            "/history",
            "/leaderboard",
            "/datasets",
            "/reports",
            "/settings",
        ]
        if 0 <= e.control.selected_index < len(routes):
            self.page.go(routes[e.control.selected_index])

    def _on_drawer_change(self, e: ft.ControlEvent):
        """Handle navigation drawer selection."""
        routes = [
            "/dashboard",
            "/models",
            "/benchmark",
            "/live-monitor",
            "/results",
            "/comparison",
            "/history",
            "/leaderboard",
            "/datasets",
            "/reports",
            "/settings",
        ]
        if 0 <= e.control.selected_index < len(routes):
            self.page.go(routes[e.control.selected_index])
            self.page.close(self._navigation_drawer)

    async def _get_page(self, route: str, params: str) -> Optional[ft.Control]:
        """Get or create page for route."""
        if route in self._pages:
            return self._pages[route]

        # Create page based on route
        page_map = {
            "/dashboard": lambda: DashboardPage(self.page),
            "/models": lambda: ModelsPage(self.page),
            "/benchmark": lambda: BenchmarkPage(self.page),
            "/live-monitor": lambda: LiveMonitorPage(self.page),
            "/results": lambda: ResultsPage(self.page, run_id=params),
            "/comparison": lambda: ComparisonPage(self.page, models=params),
            "/history": lambda: HistoryPage(self.page),
            "/leaderboard": lambda: LeaderboardPage(self.page),
            "/datasets": lambda: DatasetsPage(self.page),
            "/reports": lambda: ReportsPage(self.page),
            "/settings": lambda: SettingsPage(self.page),
        }

        if route in page_map:
            page_instance = page_map[route]()
            await page_instance.on_mount()
            self._pages[route] = page_instance
            return page_instance

        return None

    def _update_navigation_selection(self, route: str):
        """Update navigation selection based on route."""
        route_index = {
            "/dashboard": 0,
            "/models": 1,
            "/benchmark": 2,
            "/live-monitor": 3,
            "/results": 4,
            "/comparison": 5,
            "/history": 6,
            "/leaderboard": 7,
            "/datasets": 8,
            "/reports": 9,
            "/settings": 10,
        }

        index = route_index.get(route, 0)
        self._navigation_rail.selected_index = index
        self._navigation_drawer.selected_index = index
        self._navigation_rail.update()
        self._navigation_drawer.update()

    async def _transition_page(self, new_page: ft.Control):
        """Animate page transition."""
        old_content = self._page_content.content

        # Fade out
        if old_content:
            self._page_content.content = ft.Stack(
                controls=[
                    ft.Container(content=old_content, opacity=1, animate_opacity=200),
                    ft.Container(content=new_page, opacity=0, animate_opacity=200),
                ]
            )
            self._page_content.update()

            await asyncio.sleep(0.1)

            self._page_content.content.controls[0].opacity = 0
            self._page_content.content.controls[1].opacity = 1
            self._page_content.update()

            await asyncio.sleep(0.2)

        self._page_content.content = new_page
        self._page_content.update()

    def _toggle_theme(self, _):
        """Toggle dark/light theme."""
        self._theme.toggle_dark_mode()
        apply_theme_to_page(self.page, self._theme)
        self._config.ui.theme = "dark" if self._theme.dark_mode else "light"
        self._config.to_yaml("config.yaml")
        self.page.update()

    def _toggle_fullscreen(self, _):
        """Toggle fullscreen mode."""
        self.page.window.full_screen = not self.page.window.full_screen
        self.page.update()

    async def cleanup(self):
        """Cleanup on app close."""
        # Unmount current page
        if self._current_page and self._current_page in self._pages:
            await self._pages[self._current_page].on_unmount()

        # Close database
        await close_database()


async def main(page: ft.Page):
    """Main entry point for Flet app."""
    app = BenchLMApplication(page)

    try:
        await app.initialize()
        # Keep app running
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await app.cleanup()


def main_sync(page: ft.Page):
    """Synchronous wrapper for Flet."""
    asyncio.run(main(page))


if __name__ == "__main__":
    ft.app(target=main_sync, assets_dir="assets", view=ft.AppView.FLET_APP)