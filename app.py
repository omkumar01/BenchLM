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
        self.page.title = "BenchLM - Premium Benchmarking Suite"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.window.min_width = 1100
        self.page.window.min_height = 800
        self.page.window.width = 1440
        self.page.window.height = 960
        self.page.padding = 0
        self.page.spacing = 0

        # Route handling
        self.page.on_route_change = self._on_route_change
        self.page.on_view_pop = self._on_view_pop

    def _build_ui(self):
        """Build the main application UI."""
        c = self._theme.colors

        # Navigation Rail (Desktop) - Enhanced with Premium Look
        self._navigation_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=80,
            min_extended_width=280,
            bgcolor=c.surface, # Used deep surface color
            indicator_color=c.primary_container,
            indicator_shape=ft.RoundedRectangleBorder(radius=12),
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.DASHBOARD_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.DASHBOARD, size=24, color=c.primary),
                    label="Dashboard",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.MODEL_TRAINING_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.MODEL_TRAINING, size=24, color=c.primary),
                    label="Models",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.SPEED_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.SPEED, size=24, color=c.primary),
                    label="Benchmark",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.MONITOR_HEART_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.MONITOR_HEART, size=24, color=c.primary),
                    label="Live Monitor",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.ANALYTICS_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.ANALYTICS, size=24, color=c.primary),
                    label="Results",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.COMPARE_ARROWS_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.COMPARE_ARROWS, size=24, color=c.primary),
                    label="Comparison",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.HISTORY_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.HISTORY, size=24, color=c.primary),
                    label="History",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.LEADERBOARD_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.LEADERBOARD, size=24, color=c.primary),
                    label="Leaderboard",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.DATASET_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.DATASET, size=24, color=c.primary),
                    label="Datasets",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.DESCRIPTION, size=24, color=c.primary),
                    label="Reports",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.SETTINGS_OUTLINED, size=24),
                    selected_icon=ft.Icon(ft.Icons.SETTINGS, size=24, color=c.primary),
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
                            ft.Text("Premium Benchmarking", size=13, color=c.on_surface_variant),
                        ],
                    ),
                    padding=24,
                ),
                ft.Divider(height=1, color=c.outline_variant),
                # Drawer destinations map to rail
                *[ft.NavigationDrawerDestination(
                    icon=ft.Icon(dest.icon.icon, color=c.on_surface_variant),
                    selected_icon=ft.Icon(dest.selected_icon.icon, color=c.primary),
                    label=dest.label,
                ) for dest in self._navigation_rail.destinations],
            ],
            on_change=self._on_drawer_change,
        )

        # Page Content Area (With Glassmorphism container support)
        self._page_content = ft.Container(
            content=ft.Text("Loading...", color=c.on_surface_variant),
            expand=True,
            bgcolor=c.background,
            padding=ft.Padding.all(32), # Added more padding
        )

        # Top App Bar for desktop
        desktop_header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.SPEED, size=28, color=c.primary),
                            ft.Text("BenchLM", size=20, weight=ft.FontWeight.BOLD, color=c.on_surface),
                        ]
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(icon=ft.Icons.BRIGHTNESS_6, on_click=self._toggle_theme, icon_color=c.on_surface_variant),
                    ft.IconButton(icon=ft.Icons.FULLSCREEN, on_click=self._toggle_fullscreen, icon_color=c.on_surface_variant),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.Padding.symmetric(horizontal=24, vertical=16),
            bgcolor=c.glass_bg,
            border=ft.Border.only(bottom=ft.BorderSide(1, c.glass_border)),
            blur=ft.Blur(10, 10, ft.BlurTileMode.CLAMP),
        )

        # Responsive Layout
        self._main_layout = ft.Column(
            controls=[
                desktop_header,
                ft.Row(
                    controls=[
                        # Navigation Rail (shown on desktop)
                        ft.Container(
                            content=self._navigation_rail,
                            visible=self._is_desktop_layout(),
                            width=80,
                            bgcolor=c.surface,
                            shadow=ft.BoxShadow(spread_radius=0, blur_radius=16, color=c.shadow, offset=ft.Offset(4, 0))
                        ),
                        # Page content
                        ft.Container(
                            content=self._page_content,
                            expand=True,
                        ),
                    ],
                    expand=True,
                    spacing=0,
                )
            ],
            expand=True,
            spacing=0,
        )

        # App Bar (Mobile)
        self._app_bar = ft.AppBar(
            leading=ft.IconButton(
                icon=ft.Icons.MENU,
                on_click=self._open_drawer,
            ),
            title=ft.Text("BenchLM", weight=ft.FontWeight.BOLD),
            bgcolor=c.surface,
            actions=[
                ft.IconButton(icon=ft.Icons.BRIGHTNESS_6, on_click=self._toggle_theme),
                ft.IconButton(icon=ft.Icons.FULLSCREEN, on_click=self._toggle_fullscreen),
            ],
            visible=not self._is_desktop_layout(),
        )

        # Main page structure
        self.page.appbar = self._app_bar
        self.page.drawer = self._navigation_drawer
        self.page.add(self._main_layout)

        # Resize handler
        self.page.on_resize = self._on_page_resize

        # Initial navigation - honor the route the client connected with
        asyncio.get_event_loop().create_task(
            self._handle_route((self.page.route or "/dashboard").split("?")[0])
        )

    def _is_desktop_layout(self) -> bool:
        """Width is None until the client reports window metrics."""
        return (self.page.width or 0) >= 900

    def _on_page_resize(self, e):
        """Handle window resize for responsive layout."""
        is_desktop = self._is_desktop_layout()
        
        # Update rail visibility
        rail_container = self._main_layout.controls[1].controls[0]
        if rail_container.visible != is_desktop:
            rail_container.visible = is_desktop
            
        # Update mobile appbar visibility
        if self._app_bar.visible == is_desktop:
            self._app_bar.visible = not is_desktop
            
        self.page.update()

    async def _handle_route(self, route: str):
        """Show the page for a route (server-side; no client round-trip)."""
        if "?" in route:
            base_route, params = route.split("?", 1)
        else:
            base_route, params = route, ""

        # Get or create page
        page_control, created = await self._get_page(base_route, params)

        if page_control:
            # Update navigation selection
            self._update_navigation_selection(base_route)

            # Swap the page into the content area
            await self._transition_page(page_control)

            # Mount only after attachment so pages can safely call update()
            if created:
                await page_control.on_mount()

            self._current_page = base_route

    async def _on_route_change(self, e: ft.RouteChangeEvent):
        """Handle route changes from the client (URL navigation)."""
        route = e.route
        if isinstance(route, dict):
            route = route.get("route", "/dashboard")
        await self._handle_route(route or "/dashboard")

    def _on_view_pop(self, e: ft.ViewPopEvent):
        """Handle view pop (back navigation)."""
        asyncio.get_event_loop().create_task(self._handle_route("/dashboard"))

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
            asyncio.get_event_loop().create_task(self._handle_route(routes[e.control.selected_index]))

    async def _open_drawer(self, _):
        """Open the mobile navigation drawer."""
        await self.page.show_drawer()

    async def _on_drawer_change(self, e: ft.ControlEvent):
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
            await self._handle_route(routes[e.control.selected_index])
            await self.page.close_drawer()

    async def _get_page(self, route: str, params: str) -> tuple[Optional[ft.Control], bool]:
        """Get or create page for route. Returns (control, newly_created)."""
        if route in self._pages:
            return self._pages[route], False

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
            self._pages[route] = page_instance
            return page_instance, True

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
        try:
            self._navigation_rail.update()
        except RuntimeError:
            pass
            
        try:
            self._navigation_drawer.update()
        except RuntimeError:
            pass

    async def _transition_page(self, new_page: ft.Control):
        """Swap the visible page; the entry animation lives on BasePage.

        The old wrapper-Stack fade choreography confused the Flet client's
        animation state (pages stayed invisible after navigation), so the
        swap is now a single content change - BasePage.on_mount animates
        opacity 0 -> 1 with its own animate_opacity.
        """
        self._page_content.content = new_page
        self._page_content.update()

    def _toggle_theme(self, _):
        """Toggle dark/light theme."""
        self._theme.toggle_dark_mode()
        apply_theme_to_page(self.page, self._theme)

        # We need to manually update some parts that depend on theme colors
        self.page.controls.clear()
        self._build_ui()

        if self._current_page in self._pages:
            # Re-mount current page to apply new theme colors
            page_instance = self._pages[self._current_page]
            self._page_content.content = page_instance

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


async def app_main(page: ft.Page):
    """Main entry point for Flet app."""
    app = BenchLMApplication(page)

    # Flet keeps the session alive while the client is connected;
    # main() must return after initialization so the initial page
    # patch is flushed to the client.
    async def _cleanup(_=None):
        await app.cleanup()

    page.on_disconnect = _cleanup

    try:
        await app.initialize()
    except Exception:
        await app.cleanup()
        raise


def main():
    """CLI entry point."""
    ft.app(target=app_main, assets_dir="assets", view=ft.AppView.FLET_APP)


if __name__ == "__main__":
    main()