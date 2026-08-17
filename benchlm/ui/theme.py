"""Theme system for BenchLM - Premium Material 3 dark mode with glassmorphism."""

import flet as ft
from dataclasses import dataclass, field
from typing import Optional

from benchlm.config import get_config, UIConfig


# Color palette - Premium vibrant design
class Colors:
    """Color constants for BenchLM premium theme."""

    # Dark mode (default) - Deep violet/indigo base with vibrant accents
    DARK = {
        # Background
        "background": "#05050A",       # Very dark, almost black blue
        "surface": "#0C0C16",          # Deep violet-blue surface
        "surface_variant": "#151525",  # Slightly lighter surface
        "surface_container": "#1E1E32", # Elevated container
        "surface_container_high": "#282842", # High elevation
        # Primary
        "primary": "#818CF8",          # Vibrant Indigo
        "primary_container": "#4F46E5", # Deep Indigo
        "on_primary": "#FFFFFF",
        "on_primary_container": "#FFFFFF",
        # Secondary
        "secondary": "#C084FC",        # Vibrant Purple
        "secondary_container": "#9333EA", # Deep Purple
        "on_secondary": "#FFFFFF",
        # Tertiary
        "tertiary": "#2DD4BF",         # Vibrant Teal/Cyan
        "tertiary_container": "#0F766E", # Deep Teal
        "on_tertiary": "#FFFFFF",
        # Status
        "success": "#4ADE80",          # Neon Green
        "success_container": "#16A34A",
        "warning": "#FBBF24",          # Neon Amber
        "warning_container": "#D97706",
        "danger": "#F87171",           # Soft Neon Red
        "danger_container": "#DC2626",
        # Text
        "on_background": "#F8FAFC",    # slate-50
        "on_surface": "#F1F5F9",       # slate-100
        "on_surface_variant": "#CBD5E1", # slate-300
        "on_surface_disabled": "#64748B", # slate-500
        # Outline
        "outline": "#334155",          # slate-700
        "outline_variant": "#1E293B",  # slate-800
        # Glassmorphism (hex with alpha - the Flet client cannot parse CSS rgba())
        "glass_bg": "#A60C0C16",           # surface with 65% alpha
        "glass_border": "#26818CF8",       # primary tinted outline, 15% alpha
        "glass_highlight": "#14FFFFFF",    # white highlight, 8% alpha
        # Shadow
        "shadow": "#80000000",             # black, 50% alpha
        "shadow_strong": "#B3000000",      # black, 70% alpha
    }

    # Light mode - Clean, crisp white with vibrant accents
    LIGHT = {
        # Background
        "background": "#F8FAFC",       # slate-50
        "surface": "#FFFFFF",          # white
        "surface_variant": "#F1F5F9",  # slate-100
        "surface_container": "#E2E8F0", # slate-200
        "surface_container_high": "#CBD5E1", # slate-300
        # Primary
        "primary": "#4F46E5",          # Indigo 600
        "primary_container": "#E0E7FF", # Indigo 100
        "on_primary": "#FFFFFF",
        "on_primary_container": "#312E81",
        # Secondary
        "secondary": "#9333EA",        # Purple 600
        "secondary_container": "#F3E8FF",
        "on_secondary": "#FFFFFF",
        # Tertiary
        "tertiary": "#0D9488",         # Teal 600
        "tertiary_container": "#CCFBF1",
        "on_tertiary": "#FFFFFF",
        # Status
        "success": "#16A34A",
        "success_container": "#DCFCE7",
        "warning": "#D97706",
        "warning_container": "#FEF3C7",
        "danger": "#DC2626",
        "danger_container": "#FEE2E2",
        # Text
        "on_background": "#0F172A",    # slate-900
        "on_surface": "#1E293B",       # slate-800
        "on_surface_variant": "#475569", # slate-600
        "on_surface_disabled": "#94A3B8", # slate-400
        # Outline
        "outline": "#CBD5E1",          # slate-300
        "outline_variant": "#E2E8F0",  # slate-200
        # Glassmorphism (hex with alpha)
        "glass_bg": "#BFFFFFFF",
        "glass_border": "#264F46E5",
        "glass_highlight": "#80FFFFFF",
        # Shadow
        "shadow": "#14000000",
        "shadow_strong": "#1F000000",
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
        base.primary = accent
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
    xs: int = 6
    sm: int = 10
    md: int = 20
    lg: int = 32
    xl: int = 48
    xxl: int = 64

    # Component specific
    card_padding: int = 24
    card_gap: int = 24
    page_padding: int = 32
    sidebar_width: int = 280


@dataclass
class ThemeBorderRadius:
    """Border radius scale."""
    none: int = 0
    xs: int = 6
    sm: int = 12
    md: int = 16
    lg: int = 24
    xl: int = 32
    full: int = 9999

    card: int = 24
    button: int = 14
    input: int = 12
    dialog: int = 28


@dataclass
class ThemeTypography:
    """Typography scale."""
    # System default fonts (register real font files via page.fonts to customize)
    font_family: str = "Outfit"
    font_family_mono: str = "JetBrains Mono"

    display_large: int = 64
    display_medium: int = 52
    display_small: int = 44
    headline_large: int = 36
    headline_medium: int = 32
    headline_small: int = 28
    title_large: int = 24
    title_medium: int = 18
    title_small: int = 16
    label_large: int = 15
    label_medium: int = 13
    label_small: int = 12
    body_large: int = 18
    body_medium: int = 15
    body_small: int = 13

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
    xs: str = "0 2px 4px rgba(0,0,0,0.1)"
    sm: str = "0 4px 8px rgba(0,0,0,0.15), 0 2px 4px rgba(0,0,0,0.1)"
    md: str = "0 8px 16px rgba(0,0,0,0.2), 0 4px 8px rgba(0,0,0,0.1)"
    lg: str = "0 16px 24px rgba(0,0,0,0.25), 0 8px 12px rgba(0,0,0,0.15)"
    xl: str = "0 24px 32px rgba(0,0,0,0.3), 0 12px 16px rgba(0,0,0,0.2)"
    xxl: str = "0 32px 64px rgba(0,0,0,0.4)"

    # Glassmorphism shadows
    glass: str = "0 16px 40px rgba(0,0,0,0.4)"
    glass_strong: str = "0 24px 64px rgba(0,0,0,0.6)"


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

        accent_color = getattr(self.config, "accent_color", None)
        if accent_color:
            self._colors = ThemeColors.from_accent(accent_color, dark=True)

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
        accent_color = getattr(self.config, "accent_color", None)
        if accent_color:
            self._colors = ThemeColors.from_accent(accent_color, dark=self._dark_mode)

    def set_accent_color(self, color: str) -> None:
        """Set custom accent color."""
        if hasattr(self.config, "accent_color"):
            self.config.accent_color = color
        self._colors = ThemeColors.from_accent(color, dark=self._dark_mode)

    def get_flet_theme(self) -> ft.Theme:
        """Generate Flet theme object."""
        c = self.colors
        t = self.typography

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
            surface=c.surface,
            on_surface=c.on_surface,
            surface_container_highest=c.surface_variant,
            on_surface_variant=c.on_surface_variant,
            outline=c.outline,
            outline_variant=c.outline_variant,
            shadow=c.shadow,
            inverse_surface=c.on_background,
            on_inverse_surface=c.background,
            inverse_primary=c.primary_container,
        )

        # NOTE: text_theme omitted - see comment at the Theme construction below.

        # NOTE: text_theme is intentionally omitted. The Flet 0.86.5 desktop
        # client stops rendering (blank gray window) when a Theme carries both
        # color_scheme and a populated text_theme. Text styles are applied
        # per-control instead; see ThemeTypography for the scale.
        return ft.Theme(
            color_scheme=color_scheme,
            use_material3=True,
            page_transitions=ft.PageTransitionsTheme(
                windows=ft.PageTransitionTheme.FADE_UPWARDS,
                macos=ft.PageTransitionTheme.FADE_UPWARDS,
                linux=ft.PageTransitionTheme.FADE_UPWARDS,
                android=ft.PageTransitionTheme.FADE_UPWARDS,
                ios=ft.PageTransitionTheme.CUPERTINO,
            ),
        )

    def card_style(self) -> dict:
        """Get standard card style with modern aesthetics."""
        c = self.colors
        return {
            "bgcolor": c.surface,
            "border": ft.Border.all(1, c.outline_variant),
            "border_radius": self.border_radius.card,
            "padding": self.spacing.card_padding,
            "shadow": ft.BoxShadow(
                spread_radius=0,
                blur_radius=16,
                color=c.shadow,
                offset=ft.Offset(0, 8),
            ),
            "animate": ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        }

    def glass_card_style(self) -> dict:
        """Get premium glassmorphism card style."""
        c = self.colors
        return {
            "bgcolor": c.glass_bg,
            "border": ft.Border.all(1, c.glass_border),
            "border_radius": self.border_radius.card,
            "padding": self.spacing.card_padding,
            "shadow": ft.BoxShadow(
                spread_radius=0,
                blur_radius=40,
                color=c.shadow,
                offset=ft.Offset(0, 16),
            ),
            "animate": ft.Animation(300, ft.AnimationCurve.EASE_OUT_CUBIC),
            "blur": ft.Blur(10, 10, ft.BlurTileMode.CLAMP),
        }

    def elevated_card_style(self) -> dict:
        """Get elevated card style with strong presence."""
        c = self.colors
        return {
            "bgcolor": c.surface_container,
            "border": ft.Border.all(1, c.outline),
            "border_radius": self.border_radius.card,
            "padding": self.spacing.card_padding,
            "shadow": ft.BoxShadow(
                spread_radius=0,
                blur_radius=24,
                color=c.shadow_strong,
                offset=ft.Offset(0, 12),
            ),
            "animate": ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        }

    def button_primary_style(self) -> ft.ButtonStyle:
        c = self.colors
        return ft.ButtonStyle(
            color=c.on_primary,
            bgcolor=c.primary,
            shape=ft.RoundedRectangleBorder(radius=self.border_radius.button),
            padding=ft.Padding.symmetric(horizontal=32, vertical=16),
            elevation=4,
            overlay_color=c.primary_container,
            animation_duration=200,
        )

    def button_secondary_style(self) -> ft.ButtonStyle:
        c = self.colors
        return ft.ButtonStyle(
            color=c.on_surface,
            bgcolor=c.surface_variant,
            shape=ft.RoundedRectangleBorder(radius=self.border_radius.button),
            padding=ft.Padding.symmetric(horizontal=32, vertical=16),
            elevation=0,
            overlay_color=c.surface_container_high,
            animation_duration=200,
        )

    def button_outline_style(self) -> ft.ButtonStyle:
        c = self.colors
        return ft.ButtonStyle(
            color=c.on_surface,
            bgcolor=ft.Colors.TRANSPARENT,
            shape=ft.RoundedRectangleBorder(radius=self.border_radius.button),
            padding=ft.Padding.symmetric(horizontal=32, vertical=16),
            side=ft.BorderSide(1, c.outline),
            animation_duration=200,
        )

    def input_style(self) -> dict:
        c = self.colors
        return {
            "bgcolor": c.surface_variant,
            "border_radius": self.border_radius.input,
            "border_color": c.outline,
            "focused_border_color": c.primary,
            "color": c.on_surface,
            "cursor_color": c.primary,
            "selection_color": c.primary_container,
            "content_padding": ft.Padding.all(16),
        }

    def divider_style(self) -> dict:
        c = self.colors
        return {
            "color": c.outline_variant,
            "thickness": 1,
            "height": 1,
        }

    def gauge_colors(self) -> dict:
        c = self.colors
        return {
            "low": c.success,
            "medium": c.warning,
            "high": c.danger,
            "track": c.surface_container_high,
            "text": c.on_surface,
        }

    def chart_colors(self) -> list[str]:
        return [
            self.colors.primary,
            self.colors.secondary,
            self.colors.tertiary,
            self.colors.success,
            self.colors.warning,
            self.colors.danger,
            "#F97316",  # Vibrant Orange
            "#EC4899",  # Neon Pink
            "#84CC16",  # Electric Lime
            "#06B6D4",  # Cyan
        ]

    def status_color(self, status: str) -> str:
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


_theme: BenchLMTheme | None = None

def get_theme(config: UIConfig | None = None) -> BenchLMTheme:
    global _theme
    if _theme is None:
        _theme = BenchLMTheme(config)
    return _theme

def set_theme(theme: BenchLMTheme) -> None:
    global _theme
    _theme = theme

def apply_theme_to_page(page: ft.Page, theme: BenchLMTheme | None = None) -> None:
    theme = theme or get_theme()

    page.theme = theme.get_flet_theme()
    page.dark_theme = theme.get_flet_theme()
    page.theme_mode = ft.ThemeMode.DARK if theme.dark_mode else ft.ThemeMode.LIGHT
    page.bgcolor = theme.colors.background
    page.padding = theme.spacing.page_padding
    page.update()