"""Theme system for BenchLM - Material 3 dark mode with glassmorphism."""

import flet as ft
from dataclasses import dataclass, field
from typing import Optional

from benchlm.config import get_config, UIConfig


# Color palette - Material 3 inspired
class Colors:
    """Color constants for BenchLM theme."""

    # Dark mode (default)
    DARK = {
        # Background
        "background": "#09090B",       # zinc-950
        "surface": "#18181B",          # zinc-900
        "surface_variant": "#27272A",  # zinc-800
        "surface_container": "#3F3F46", # zinc-700
        "surface_container_high": "#52525B", # zinc-600
        # Primary
        "primary": "#6366F1",          # indigo-500
        "primary_container": "#4F46E5", # indigo-600
        "on_primary": "#FFFFFF",
        "on_primary_container": "#FFFFFF",
        # Secondary
        "secondary": "#A855F7",        # purple-500
        "secondary_container": "#9333EA", # purple-600
        "on_secondary": "#FFFFFF",
        # Tertiary
        "tertiary": "#06B6D4",         # cyan-500
        "tertiary_container": "#0891B2", # cyan-600
        "on_tertiary": "#FFFFFF",
        # Status
        "success": "#22C55E",          # green-500
        "success_container": "#16A34A", # green-600
        "warning": "#F59E0B",          # amber-500
        "warning_container": "#D97706", # amber-600
        "danger": "#EF4444",           # red-500
        "danger_container": "#DC2626", # red-600
        # Text
        "on_background": "#FAFAFA",    # zinc-50
        "on_surface": "#F4F4F5",       # zinc-100
        "on_surface_variant": "#D4D4D8", # zinc-300
        "on_surface_disabled": "#71717A", # zinc-500
        # Outline
        "outline": "#3F3F46",          # zinc-700
        "outline_variant": "#27272A",  # zinc-800
        # Glassmorphism
        "glass_bg": "rgba(24, 24, 27, 0.8)",      # surface with alpha
        "glass_border": "rgba(63, 63, 70, 0.5)",  # outline with alpha
        "glass_highlight": "rgba(255, 255, 255, 0.05)",
        # Shadow
        "shadow": "rgba(0, 0, 0, 0.4)",
        "shadow_strong": "rgba(0, 0, 0, 0.6)",
    }

    # Light mode
    LIGHT = {
        # Background
        "background": "#FAFAFA",       # zinc-50
        "surface": "#FFFFFF",          # white
        "surface_variant": "#F4F4F5",  # zinc-100
        "surface_container": "#E4E4E7", # zinc-200
        "surface_container_high": "#D4D4D8", # zinc-300
        # Primary
        "primary": "#4F46E5",          # indigo-600
        "primary_container": "#E0E7FF", # indigo-100
        "on_primary": "#FFFFFF",
        "on_primary_container": "#312E81", # indigo-900
        # Secondary
        "secondary": "#9333EA",        # purple-600
        "secondary_container": "#F3E8FF", # purple-100
        "on_secondary": "#FFFFFF",
        # Tertiary
        "tertiary": "#0891B2",         # cyan-600
        "tertiary_container": "#CFFAFE", # cyan-100
        "on_tertiary": "#FFFFFF",
        # Status
        "success": "#16A34A",          # green-600
        "success_container": "#DCFCE7", # green-100
        "warning": "#D97706",          # amber-600
        "warning_container": "#FEF3C7", # amber-100
        "danger": "#DC2626",           # red-600
        "danger_container": "#FEE2E2", # red-100
        # Text
        "on_background": "#18181B",    # zinc-900
        "on_surface": "#09090B",       # zinc-950
        "on_surface_variant": "#52525B", # zinc-600
        "on_surface_disabled": "#A1A1AA", # zinc-400
        # Outline
        "outline": "#D4D4D8",          # zinc-300
        "outline_variant": "#E4E4E7",  # zinc-200
        # Glassmorphism
        "glass_bg": "rgba(255, 255, 255, 0.8)",
        "glass_border": "rgba(212, 212, 216, 0.5)",
        "glass_highlight": "rgba(0, 0, 0, 0.03)",
        # Shadow
        "shadow": "rgba(0, 0, 0, 0.1)",
        "shadow_strong": "rgba(0, 0, 0, 0.15)",
    }


@dataclass
class ThemeColors:
    """Theme color palette."""

    # Background
    background: str = Colors.DARK["background"]
    surface: str = Colors.DARK["surface"]
    surface_variant: str = Colors.DARK["surface_variant"]
    surface_container: str = Colors.DARK["surface_container"]
    surface_container_high: str = Colors.DARK["surface_container_high"]

    # Primary
    primary: str = Colors.DARK["primary"]
    primary_container: str = Colors.DARK["primary_container"]
    on_primary: str = Colors.DARK["on_primary"]
    on_primary_container: str = Colors.DARK["on_primary_container"]

    # Secondary
    secondary: str = Colors.DARK["secondary"]
    secondary_container: str = Colors.DARK["secondary_container"]
    on_secondary: str = Colors.DARK["on_secondary"]

    # Tertiary
    tertiary: str = Colors.DARK["tertiary"]
    tertiary_container: str = Colors.DARK["tertiary_container"]
    on_tertiary: str = Colors.DARK["on_tertiary"]

    # Status
    success: str = Colors.DARK["success"]
    success_container: str = Colors.DARK["success_container"]
    warning: str = Colors.DARK["warning"]
    warning_container: str = Colors.DARK["warning_container"]
    danger: str = Colors.DARK["danger"]
    danger_container: str = Colors.DARK["danger_container"]

    # Text
    on_background: str = Colors.DARK["on_background"]
    on_surface: str = Colors.DARK["on_surface"]
    on_surface_variant: str = Colors.DARK["on_surface_variant"]
    on_surface_disabled: str = Colors.DARK["on_surface_disabled"]

    # Outline
    outline: str = Colors.DARK["outline"]
    outline_variant: str = Colors.DARK["outline_variant"]

    # Glassmorphism
    glass_bg: str = Colors.DARK["glass_bg"]
    glass_border: str = Colors.DARK["glass_border"]
    glass_highlight: str = Colors.DARK["glass_highlight"]

    # Shadow
    shadow: str = Colors.DARK["shadow"]
    shadow_strong: str = Colors.DARK["shadow_strong"]

    @classmethod
    def dark(cls) -> "ThemeColors":
        return cls(**Colors.DARK)

    @classmethod
    def light(cls) -> "ThemeColors":
        return cls(**Colors.LIGHT)

    @classmethod
    def from_accent(cls, accent: str, dark: bool = True) -> "ThemeColors":
        """Create theme with custom accent color."""
        base = cls.dark() if dark else cls.light()
        # Generate accent variants
        base.primary = accent
        # Simple variant generation (darken/lighten)
        base.primary_container = _adjust_color(accent, -20) if dark else _adjust_color(accent, 20)
        return base


def _adjust_color(hex_color: str, amount: int) -> str:
    """Adjust color brightness."""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    r = max(0, min(255, r + amount))
    g = max(0, min(255, g + amount))
    b = max(0, min(255, b + amount))

    return f"#{r:02x}{g:02x}{b:02x}"


@dataclass
class ThemeSpacing:
    """Spacing scale."""

    xs: int = 4
    sm: int = 8
    md: int = 16
    lg: int = 24
    xl: int = 32
    xxl: int = 48

    # Component specific
    card_padding: int = 16
    card_gap: int = 16
    page_padding: int = 24
    sidebar_width: int = 280


@dataclass
class ThemeBorderRadius:
    """Border radius scale."""

    none: int = 0
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 24
    full: int = 9999

    card: int = 16
    button: int = 12
    input: int = 10
    dialog: int = 20


@dataclass
class ThemeTypography:
    """Typography scale."""

    # Font families
    font_family: str = "Inter, system-ui, -apple-system, sans-serif"
    font_family_mono: str = "JetBrains Mono, Fira Code, Consolas, monospace"

    # Font sizes
    display_large: int = 57
    display_medium: int = 45
    display_small: int = 36
    headline_large: int = 32
    headline_medium: int = 28
    headline_small: int = 24
    title_large: int = 22
    title_medium: int = 16
    title_small: int = 14
    label_large: int = 14
    label_medium: int = 12
    label_small: int = 11
    body_large: int = 16
    body_medium: int = 14
    body_small: int = 12

    # Font weights
    weight_thin: int = 100
    weight_light: int = 300
    weight_regular: int = 400
    weight_medium: int = 500
    weight_semibold: int = 600
    weight_bold: int = 700
    weight_extrabold: int = 800


@dataclass
class ThemeShadows:
    """Shadow elevations."""

    none: str = "none"
    xs: str = "0 1px 2px rgba(0,0,0,0.05)"
    sm: str = "0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)"
    md: str = "0 4px 6px rgba(0,0,0,0.1), 0 2px 4px rgba(0,0,0,0.06)"
    lg: str = "0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05)"
    xl: str = "0 20px 25px rgba(0,0,0,0.15), 0 10px 10px rgba(0,0,0,0.04)"
    xxl: str = "0 25px 50px rgba(0,0,0,0.25)"

    # Glassmorphism shadows
    glass: str = "0 8px 32px rgba(0,0,0,0.3)"
    glass_strong: str = "0 16px 48px rgba(0,0,0,0.4)"


class BenchLMTheme:
    """Main theme class for BenchLM."""

    def __init__(self, config: UIConfig | None = None):
        self.config = config or get_config().ui
        self._colors = ThemeColors.dark()
        self._spacing = ThemeSpacing()
        self._border_radius = ThemeBorderRadius()
        self._typography = ThemeTypography()
        self._shadows = ThemeShadows()
        self._dark_mode = True

        # Apply accent color from config
        if self.config.accent_color:
            self._colors = ThemeColors.from_accent(self.config.accent_color, dark=True)

    @property
    def colors(self) -> ThemeColors:
        return self._colors

    @property
    def spacing(self) -> ThemeSpacing:
        return self._spacing

    @property
    def border_radius(self) -> ThemeBorderRadius:
        return self._border_radius

    @property
    def typography(self) -> ThemeTypography:
        return self._typography

    @property
    def shadows(self) -> ThemeShadows:
        return self._shadows

    @property
    def dark_mode(self) -> bool:
        return self._dark_mode

    def toggle_dark_mode(self) -> None:
        """Toggle between dark and light mode."""
        self._dark_mode = not self._dark_mode
        self._colors = ThemeColors.dark() if self._dark_mode else ThemeColors.light()

        # Reapply accent
        if self.config.accent_color:
            self._colors = ThemeColors.from_accent(self.config.accent_color, dark=self._dark_mode)

    def set_accent_color(self, color: str) -> None:
        """Set custom accent color."""
        self.config.accent_color = color
        self._colors = ThemeColors.from_accent(color, dark=self._dark_mode)

    def get_flet_theme(self) -> ft.Theme:
        """Generate Flet theme object."""
        c = self.colors
        t = self.typography

        # Color scheme
        color_scheme = ft.ColorScheme(
            primary=c.primary,
            on_primary=c.on_primary,
            primary_container=c.primary_container,
            on_primary_container=c.on_primary_container,
            secondary=c.secondary,
            on_secondary=c.on_secondary,
            secondary_container=c.secondary_container,
            tertiary=c.tertiary,
            on_tertiary=c.on_tertiary,
            tertiary_container=c.tertiary_container,
            error=c.danger,
            on_error=c.on_primary,
            error_container=c.danger_container,
            background=c.background,
            on_background=c.on_background,
            surface=c.surface,
            on_surface=c.on_surface,
            surface_variant=c.surface_variant,
            on_surface_variant=c.on_surface_variant,
            outline=c.outline,
            outline_variant=c.outline_variant,
            shadow=c.shadow,
            inverse_surface=c.on_background,
            on_inverse_surface=c.background,
            inverse_primary=c.primary_container,
        )

        # Text theme
        text_theme = ft.TextTheme(
            display_large=ft.TextStyle(
                size=t.display_large, weight=t.weight_thin, font_family=t.font_family, color=c.on_background
            ),
            display_medium=ft.TextStyle(
                size=t.display_medium, weight=t.weight_thin, font_family=t.font_family, color=c.on_background
            ),
            display_small=ft.TextStyle(
                size=t.display_small, weight=t.weight_regular, font_family=t.font_family, color=c.on_background
            ),
            headline_large=ft.TextStyle(
                size=t.headline_large, weight=t.weight_regular, font_family=t.font_family, color=c.on_background
            ),
            headline_medium=ft.TextStyle(
                size=t.headline_medium, weight=t.weight_regular, font_family=t.font_family, color=c.on_background
            ),
            headline_small=ft.TextStyle(
                size=t.headline_small, weight=t.weight_regular, font_family=t.font_family, color=c.on_background
            ),
            title_large=ft.TextStyle(
                size=t.title_large, weight=t.weight_medium, font_family=t.font_family, color=c.on_background
            ),
            title_medium=ft.TextStyle(
                size=t.title_medium, weight=t.weight_medium, font_family=t.font_family, color=c.on_background
            ),
            title_small=ft.TextStyle(
                size=t.title_small, weight=t.weight_medium, font_family=t.font_family, color=c.on_background
            ),
            label_large=ft.TextStyle(
                size=t.label_large, weight=t.weight_medium, font_family=t.font_family, color=c.on_background
            ),
            label_medium=ft.TextStyle(
                size=t.label_medium, weight=t.weight_medium, font_family=t.font_family, color=c.on_background
            ),
            label_small=ft.TextStyle(
                size=t.label_small, weight=t.weight_regular, font_family=t.font_family, color=c.on_background
            ),
            body_large=ft.TextStyle(
                size=t.body_large, weight=t.weight_regular, font_family=t.font_family, color=c.on_background
            ),
            body_medium=ft.TextStyle(
                size=t.body_medium, weight=t.weight_regular, font_family=t.font_family, color=c.on_background
            ),
            body_small=ft.TextStyle(
                size=t.body_small, weight=t.weight_regular, font_family=t.font_family, color=c.on_background
            ),
        )

        return ft.Theme(
            color_scheme=color_scheme,
            text_theme=text_theme,
            font_family=t.font_family,
            use_material3=True,
            page_transitions=ft.PageTransitionsTheme(
                windows=ft.PageTransitionTheme.OPEN_UPWARDS,
                macos=ft.PageTransitionTheme.OPEN_UPWARDS,
                linux=ft.PageTransitionTheme.OPEN_UPWARDS,
                android=ft.PageTransitionTheme.OPEN_UPWARDS,
                ios=ft.PageTransitionTheme.CUPERTINO,
            ),
        )

    # Component style helpers
    def card_style(self) -> dict:
        """Get card container style."""
        c = self.colors
        return {
            "bgcolor": c.glass_bg,
            "border": ft.border.all(1, c.glass_border),
            "border_radius": self.border_radius.card,
            "padding": self.spacing.card_padding,
            "shadow": ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=c.shadow,
                offset=ft.Offset(0, 4),
            ),
        }

    def glass_card_style(self) -> dict:
        """Get glassmorphism card style."""
        c = self.colors
        return {
            "bgcolor": c.glass_bg,
            "border": ft.border.all(1, c.glass_border),
            "border_radius": self.border_radius.card,
            "padding": self.spacing.card_padding,
            "shadow": ft.BoxShadow(
                spread_radius=0,
                blur_radius=32,
                color=c.shadow,
                offset=ft.Offset(0, 8),
            ),
        }

    def elevated_card_style(self) -> dict:
        """Get elevated card style."""
        c = self.colors
        return {
            "bgcolor": c.surface,
            "border": ft.border.all(1, c.outline),
            "border_radius": self.border_radius.card,
            "padding": self.spacing.card_padding,
            "shadow": ft.BoxShadow(
                spread_radius=0,
                blur_radius=15,
                color=c.shadow_strong,
                offset=ft.Offset(0, 4),
            ),
        }

    def button_primary_style(self) -> ft.ButtonStyle:
        """Primary button style."""
        c = self.colors
        return ft.ButtonStyle(
            color=c.on_primary,
            bgcolor=c.primary,
            shape=ft.RoundedRectangleBorder(radius=self.border_radius.button),
            padding=ft.padding.symmetric(horizontal=24, vertical=12),
            elevation=2,
            overlay_color=c.primary_container,
        )

    def button_secondary_style(self) -> ft.ButtonStyle:
        """Secondary button style."""
        c = self.colors
        return ft.ButtonStyle(
            color=c.primary,
            bgcolor=c.primary_container,
            shape=ft.RoundedRectangleBorder(radius=self.border_radius.button),
            padding=ft.padding.symmetric(horizontal=24, vertical=12),
            side=ft.BorderSide(1, c.outline),
        )

    def button_outline_style(self) -> ft.ButtonStyle:
        """Outline button style."""
        c = self.colors
        return ft.ButtonStyle(
            color=c.on_surface,
            bgcolor=ft.Colors.TRANSPARENT,
            shape=ft.RoundedRectangleBorder(radius=self.border_radius.button),
            padding=ft.padding.symmetric(horizontal=24, vertical=12),
            side=ft.BorderSide(1, c.outline),
        )

    def input_style(self) -> dict:
        """Input field style."""
        c = self.colors
        return {
            "bgcolor": c.surface_variant,
            "border_radius": self.border_radius.input,
            "border_color": c.outline,
            "focused_border_color": c.primary,
            "focused_bgcolor": c.surface,
            "color": c.on_surface,
            "cursor_color": c.primary,
            "selection_color": c.primary_container,
        }

    def divider_style(self) -> dict:
        """Divider style."""
        c = self.colors
        return {
            "color": c.outline_variant,
            "thickness": 1,
            "height": 1,
        }

    def gauge_colors(self) -> dict:
        """Colors for gauge charts."""
        c = self.colors
        return {
            "low": c.success,
            "medium": c.warning,
            "high": c.danger,
            "track": c.surface_container_high,
            "text": c.on_surface,
        }

    def chart_colors(self) -> list[str]:
        """Color palette for charts."""
        return [
            self.colors.primary,
            self.colors.secondary,
            self.colors.tertiary,
            self.colors.success,
            self.colors.warning,
            self.colors.danger,
            "#F97316",  # orange
            "#EC4899",  # pink
            "#84CC16",  # lime
            "#14B8A6",  # teal
        ]

    def status_color(self, status: str) -> str:
        """Get color for status."""
        c = self.colors
        status_map = {
            "success": c.success,
            "warning": c.warning,
            "danger": c.danger,
            "info": c.tertiary,
            "pending": c.on_surface_disabled,
            "running": c.primary,
            "completed": c.success,
            "failed": c.danger,
            "paused": c.warning,
            "cancelled": c.on_surface_disabled,
        }
        return status_map.get(status.lower(), c.on_surface_variant)


# Global theme instance
_theme: BenchLMTheme | None = None


def get_theme(config: UIConfig | None = None) -> BenchLMTheme:
    """Get the global theme instance."""
    global _theme
    if _theme is None:
        _theme = BenchLMTheme(config)
    return _theme


def set_theme(theme: BenchLMTheme) -> None:
    """Set the global theme instance."""
    global _theme
    _theme = theme


def apply_theme_to_page(page: ft.Page, theme: BenchLMTheme | None = None) -> None:
    """Apply theme to a Flet page."""
    theme = theme or get_theme()

    page.theme = theme.get_flet_theme()
    page.dark_theme = theme.get_flet_theme()
    page.theme_mode = ft.ThemeMode.DARK if theme.dark_mode else ft.ThemeMode.LIGHT
    page.bgcolor = theme.colors.background
    page.padding = theme.spacing.page_padding

    # Set default font
    page.fonts = {
        "Inter": "https://fonts.googleapis.com/css2?family=Inter:wght@100;300;400;500;600;700;800&display=swap",
        "JetBrains Mono": "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap",
    }

    page.update()