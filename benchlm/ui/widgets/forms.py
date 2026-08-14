"""Form widgets for BenchLM - form fields, sliders, selects, toggles, pickers."""

import flet as ft
from dataclasses import dataclass
from typing import Optional, Callable, Any, List
from enum import Enum

from benchlm.ui.theme import get_theme


class FormFieldType(Enum):
    """Form field types."""

    TEXT = "text"
    NUMBER = "number"
    PASSWORD = "password"
    EMAIL = "email"
    URL = "url"
    MULTILINE = "multiline"


@dataclass
class FormFieldConfig:
    """Configuration for form field."""

    label: str = ""
    hint: str = ""
    helper_text: str = ""
    prefix: str = ""
    suffix: str = ""
    required: bool = False
    disabled: bool = False
    read_only: bool = False
    error_text: str = ""
    min_length: int = 0
    max_length: int | None = None
    min_value: float | None = None
    max_value: float | None = None
    step: float = 1
    keyboard_type: ft.KeyboardType = ft.KeyboardType.TEXT
    autocorrect: bool = False
    autocapitalization: ft.TextCapitalization = ft.TextCapitalization.NONE
    on_change: Optional[Callable[[str], None]] = None
    on_submit: Optional[Callable[[str], None]] = None
    on_focus: Optional[Callable] = None
    on_blur: Optional[Callable] = None
    validator: Optional[Callable[[str], str | None]] = None  # Returns error message or None


class FormField(ft.Container):
    """Base form field with label, hint, error, and validation."""

    def __init__(
        self,
        config: FormFieldConfig | None = None,
        value: str = "",
        **kwargs
    ):
        self.config = config or FormFieldConfig()
        self._value = value
        self._theme = get_theme()
        self._error_shown = False

        super().__init__(**kwargs)
        self._build()

    def _build(self):
        """Build form field."""
        raise NotImplementedError

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, val: str):
        self._value = val
        self._update_control_value()
        self.validate()

    def _update_control_value(self):
        """Update the underlying control value."""
        pass

    def validate(self) -> bool:
        """Validate field value."""
        if self.config.validator:
            error = self.config.validator(self._value)
            self.set_error(error)
            return error is None

        if self.config.required and not self._value:
            self.set_error("This field is required")
            return False

        if self.config.min_length and len(self._value) < self.config.min_length:
            self.set_error(f"Minimum length is {self.config.min_length}")
            return False

        if self.config.max_length and len(self._value) > self.config.max_length:
            self.set_error(f"Maximum length is {self.config.max_length}")
            return False

        self.set_error(None)
        return True

    def set_error(self, error: str | None):
        """Set error state."""
        self.config.error_text = error or ""
        self._error_shown = bool(error)
        self._update_error_display()

    def _update_error_display(self):
        """Update error display."""
        pass

    def clear_error(self):
        """Clear error."""
        self.set_error(None)


class TextField(FormField):
    """Text input field."""

    def __init__(
        self,
        config: FormFieldConfig | None = None,
        value: str = "",
        **kwargs
    ):
        self._text_field: ft.TextField | None = None
        super().__init__(config, value, **kwargs)

    def _build(self):
        """Build text field."""
        c = self._theme.colors
        cfg = self.config

        self._text_field = ft.TextField(
            value=self._value,
            label=cfg.label or None,
            hint_text=cfg.hint or None,
            helper_text=cfg.helper_text or None,
            prefix_text=cfg.prefix or None,
            suffix_text=cfg.suffix or None,
            password=cfg.keyboard_type == ft.KeyboardType.VISIBLE_PASSWORD,
            read_only=cfg.read_only,
            disabled=cfg.disabled,
            max_length=cfg.max_length,
            min_length=cfg.min_length if cfg.min_length > 0 else None,
            keyboard_type=cfg.keyboard_type,
            autocorrect=cfg.autocorrect,
            capitalization=cfg.autocapitalization,
            text_size=14,
            label_style=ft.TextStyle(color=c.on_surface_variant, size=12),
            hint_style=ft.TextStyle(color=c.on_surface_disabled, size=12),
            border_color=c.outline,
            focused_border_color=c.primary,
            focused_bgcolor=c.surface,
            bgcolor=c.surface_variant,
            color=c.on_surface,
            cursor_color=c.primary,
            selection_color=c.primary_container,
            border_radius=8,
            filled=True,
            dense=True,
            on_change=self._on_change,
            on_submit=self._on_submit,
            on_focus=self._on_focus,
            on_blur=self._on_blur,
            error_text=cfg.error_text or None,
            counter_style=ft.TextStyle(color=c.on_surface_disabled, size=11),
        )

        self.content = ft.Column(
            controls=[self._text_field],
            spacing=0,
            tight=True,
        )

    def _update_control_value(self):
        if self._text_field:
            self._text_field.value = self._value
            self._text_field.update()

    def _update_error_display(self):
        if self._text_field:
            self._text_field.error_text = self.config.error_text or None
            self._text_field.update()

    def _on_change(self, e: ft.ControlEvent):
        self._value = e.control.value
        if self.config.on_change:
            self.config.on_change(self._value)
        # Clear error on change
        if self._error_shown:
            self.validate()

    def _on_submit(self, e: ft.ControlEvent):
        if self.config.on_submit:
            self.config.on_submit(self._value)

    def _on_focus(self, e: ft.ControlEvent):
        if self.config.on_focus:
            self.config.on_focus()

    def _on_blur(self, e: ft.ControlEvent):
        if self.config.on_blur:
            self.config.on_blur()
        # Validate on blur
        self.validate()


class NumberField(FormField):
    """Number input field with stepper."""

    def __init__(
        self,
        config: FormFieldConfig | None = None,
        value: float = 0,
        **kwargs
    ):
        self._value = float(value)
        self._text_field: ft.TextField | None = None
        super().__init__(config, str(value), **kwargs)

    def _build(self):
        """Build number field."""
        c = self._theme.colors
        cfg = self.config

        # Create buttons for increment/decrement
        def decrement(_):
            new_val = self._value - cfg.step
            if cfg.min_value is None or new_val >= cfg.min_value:
                self.value = str(new_val)

        def increment(_):
            new_val = self._value + cfg.step
            if cfg.max_value is None or new_val <= cfg.max_value:
                self.value = str(new_val)

        decrement_btn = ft.IconButton(
            icon=ft.Icons.REMOVE,
            icon_size=18,
            on_click=decrement,
            disabled=cfg.disabled or (cfg.min_value is not None and self._value <= cfg.min_value),
        )

        increment_btn = ft.IconButton(
            icon=ft.Icons.ADD,
            icon_size=18,
            on_click=increment,
            disabled=cfg.disabled or (cfg.max_value is not None and self._value >= cfg.max_value),
        )

        self._text_field = ft.TextField(
            value=str(self._value),
            label=cfg.label or None,
            hint_text=cfg.hint or None,
            read_only=cfg.read_only,
            disabled=cfg.disabled,
            keyboard_type=ft.KeyboardType.NUMBER,
            text_size=14,
            text_align=ft.TextAlign.CENTER,
            label_style=ft.TextStyle(color=c.on_surface_variant, size=12),
            border_color=c.outline,
            focused_border_color=c.primary,
            focused_bgcolor=c.surface,
            bgcolor=c.surface_variant,
            color=c.on_surface,
            cursor_color=c.primary,
            border_radius=8,
            filled=True,
            dense=True,
            on_change=self._on_change,
            on_submit=self._on_submit,
            on_blur=self._on_blur,
            error_text=cfg.error_text or None,
            expand=True,
        )

        self.content = ft.Row(
            controls=[
                decrement_btn,
                ft.Container(content=self._text_field, expand=True),
                increment_btn,
            ],
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _update_control_value(self):
        if self._text_field:
            self._text_field.value = str(self._value)
            self._text_field.update()

    def _update_error_display(self):
        if self._text_field:
            self._text_field.error_text = self.config.error_text or None
            self._text_field.update()

    def _on_change(self, e: ft.ControlEvent):
        try:
            self._value = float(e.control.value) if e.control.value else 0
        except ValueError:
            self._value = 0
        if self.config.on_change:
            self.config.on_change(str(self._value))
        if self._error_shown:
            self.validate()

    def _on_submit(self, e: ft.ControlEvent):
        self.validate()
        if self.config.on_submit:
            self.config.on_submit(str(self._value))

    def _on_blur(self, e: ft.ControlEvent):
        self.validate()
        if self.config.on_blur:
            self.config.on_blur()


class SliderField(ft.Container):
    """Slider field with value display."""

    def __init__(
        self,
        min_value: float = 0,
        max_value: float = 100,
        value: float = 0,
        step: float = 1,
        label: str = "",
        unit: str = "",
        show_value: bool = True,
        divisions: int | None = None,
        on_change: Optional[Callable[[float], None]] = None,
        on_change_end: Optional[Callable[[float], None]] = None,
        **kwargs
    ):
        self.min_value = min_value
        self.max_value = max_value
        self._value = value
        self.step = step
        self.label = label
        self.unit = unit
        self.show_value = show_value
        self.divisions = divisions or int((max_value - min_value) / step)
        self.on_change = on_change
        self.on_change_end = on_change_end
        self._theme = get_theme()

        super().__init__(**kwargs)
        self._build()

    def _build(self):
        """Build slider field."""
        c = self._theme.colors

        self._slider = ft.Slider(
            min=self.min_value,
            max=self.max_value,
            value=self._value,
            step=self.step,
            divisions=self.divisions,
            label="{value}" + (f" {self.unit}" if self.unit else ""),
            active_color=c.primary,
            inactive_color=c.outline_variant,
            thumb_color=c.primary,
            on_change=self._on_change,
            on_change_end=self._on_change_end,
            expand=True,
        )

        self._value_text = ft.Text(
            f"{self._value:.1f}{self.unit}",
            size=14,
            weight=ft.FontWeight.MEDIUM,
            color=c.on_surface,
            width=80,
            text_align=ft.TextAlign.RIGHT,
        ) if self.show_value else ft.Container()

        label_text = ft.Text(
            self.label,
            size=13,
            weight=ft.FontWeight.MEDIUM,
            color=c.on_surface,
            width=120,
        ) if self.label else ft.Container()

        self.content = ft.Row(
            controls=[
                label_text,
                ft.Container(content=self._slider, expand=True),
                self._value_text,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
        )

    def _on_change(self, e: ft.ControlEvent):
        self._value = e.control.value
        if self.show_value:
            self._value_text.value = f"{self._value:.1f}{self.unit}"
            self._value_text.update()
        if self.on_change:
            self.on_change(self._value)

    def _on_change_end(self, e: ft.ControlEvent):
        if self.on_change_end:
            self.on_change_end(self._value)

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, val: float):
        self._value = max(self.min_value, min(self.max_value, val))
        self._slider.value = self._value
        if self.show_value:
            self._value_text.value = f"{self._value:.1f}{self.unit}"
        self.update()


class SelectField(ft.Container):
    """Dropdown select field."""

    def __init__(
        self,
        options: list[tuple[str, str]],  # (value, label)
        value: str = "",
        label: str = "",
        hint: str = "",
        allow_clear: bool = False,
        on_change: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        self.options = options
        self._value = value
        self.label = label
        self.hint = hint
        self.allow_clear = allow_clear
        self.on_change = on_change
        self._theme = get_theme()
        self._dropdown: ft.Dropdown | None = None

        super().__init__(**kwargs)
        self._build()

    def _build(self):
        """Build select field."""
        c = self._theme.colors

        dropdown_options = []
        if self.allow_clear:
            dropdown_options.append(ft.dropdown.Option("", "Select..."))

        for val, lbl in self.options:
            dropdown_options.append(ft.dropdown.Option(val, lbl))

        self._dropdown = ft.Dropdown(
            value=self._value or None,
            options=dropdown_options,
            label=self.label or None,
            hint_text=self.hint or None,
            text_size=14,
            label_style=ft.TextStyle(color=c.on_surface_variant, size=12),
            hint_style=ft.TextStyle(color=c.on_surface_disabled, size=12),
            border_color=c.outline,
            focused_border_color=c.primary,
            focused_bgcolor=c.surface,
            bgcolor=c.surface_variant,
            color=c.on_surface,
            border_radius=8,
            filled=True,
            dense=True,
            on_change=self._on_change,
            expand=True,
        )

        self.content = self._dropdown

    def _on_change(self, e: ft.ControlEvent):
        self._value = e.control.value or ""
        if self.on_change:
            self.on_change(self._value)

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, val: str):
        self._value = val
        if self._dropdown:
            self._dropdown.value = val or None
            self._dropdown.update()


class ToggleField(ft.Container):
    """Toggle switch field."""

    def __init__(
        self,
        label: str = "",
        value: bool = False,
        on_change: Optional[Callable[[bool], None]] = None,
        **kwargs
    ):
        self.label = label
        self._value = value
        self.on_change = on_change
        self._theme = get_theme()
        self._switch: ft.Switch | None = None

        super().__init__(**kwargs)
        self._build()

    def _build(self):
        """Build toggle field."""
        c = self._theme.colors

        self._switch = ft.Switch(
            value=self._value,
            active_color=c.primary,
            active_track_color=c.primary_container,
            inactive_thumb_color=c.on_surface_disabled,
            inactive_track_color=c.outline_variant,
            on_change=self._on_change,
        )

        label_text = ft.Text(
            self.label,
            size=14,
            color=c.on_surface,
            expand=True,
        ) if self.label else ft.Container()

        self.content = ft.Row(
            controls=[
                label_text,
                self._switch,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _on_change(self, e: ft.ControlEvent):
        self._value = e.control.value
        if self.on_change:
            self.on_change(self._value)

    @property
    def value(self) -> bool:
        return self._value

    @value.setter
    def value(self, val: bool):
        self._value = val
        if self._switch:
            self._switch.value = val
            self._switch.update()


class ColorPickerField(ft.Container):
    """Color picker field."""

    def __init__(
        self,
        value: str = "#6366F1",
        label: str = "",
        on_change: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        self._value = value
        self.label = label
        self.on_change = on_change
        self._theme = get_theme()
        self._color_button: ft.Container | None = None
        self._dialog: ft.AlertDialog | None = None

        super().__init__(**kwargs)
        self._build()

    def _build(self):
        """Build color picker."""
        c = self._theme.colors

        self._color_button = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.COLOR_LENS, size=20, color=c.on_surface),
                    ft.Text(
                        self._value,
                        size=13,
                        color=c.on_surface,
                        expand=True,
                    ),
                ],
                spacing=8,
            ),
            padding=ft.padding.symmetric(horizontal=12, vertical=10),
            bgcolor=self._value,
            border_radius=8,
            border=ft.border.all(1, c.outline),
            on_click=self._open_picker,
            ink=True,
        )

        label_text = ft.Text(
            self.label,
            size=13,
            weight=ft.FontWeight.MEDIUM,
            color=c.on_surface,
        ) if self.label else ft.Container()

        self.content = ft.Column(
            controls=[
                label_text,
                ft.Container(height=8),
                self._color_button,
            ],
            spacing=0,
            tight=True,
        )

    def _open_picker(self, _):
        """Open color picker dialog."""
        c = self._theme.colors

        # Preset colors
        presets = [
            "#6366F1", "#A855F7", "#06B6D4", "#22C55E",
            "#F59E0B", "#EF4444", "#F97316", "#EC4899",
            "#84CC16", "#14B8A6", "#FFFFFF", "#000000",
        ]

        color_controls = []
        for color in presets:
            color_controls.append(
                ft.Container(
                    width=36,
                    height=36,
                    bgcolor=color,
                    border_radius=8,
                    border=ft.border.all(2, c.primary) if color == self._value else ft.border.all(1, c.outline),
                    on_click=lambda e, col=color: self._select_color(col),
                    ink=True,
                    tooltip=color,
                )
            )

        # Custom color input
        custom_input = TextField(
            config=FormFieldConfig(label="Custom Hex", hint="#RRGGBB"),
            value=self._value,
            on_submit=lambda v: self._select_color(v) if v.startswith("#") else None,
        )

        self._dialog = ft.AlertDialog(
            title=ft.Text("Pick a color", size=18, weight=ft.FontWeight.SEMIBOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("Presets", size=13, weight=ft.FontWeight.MEDIUM, color=c.on_surface_variant),
                        ft.Container(height=8),
                        ft.Row(
                            controls=color_controls,
                            spacing=8,
                            wrap=True,
                        ),
                        ft.Container(height=16),
                        ft.Divider(height=1, color=c.outline_variant),
                        ft.Container(height=16),
                        custom_input,
                    ],
                    spacing=0,
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=320,
                padding=16,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self._close_dialog()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.open(self._dialog)

    def _select_color(self, color: str):
        """Select color."""
        self._value = color
        self._color_button.bgcolor = color
        self._color_button.content.controls[1].value = color
        self._color_button.update()
        self._close_dialog()
        if self.on_change:
            self.on_change(color)

    def _close_dialog(self):
        """Close dialog."""
        if self._dialog:
            self._dialog.open = False
            self.page.update()

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, val: str):
        self._value = val
        if self._color_button:
            self._color_button.bgcolor = val
            self._color_button.content.controls[1].value = val
            self._color_button.update()


class FilePickerField(ft.Container):
    """File picker field."""

    def __init__(
        self,
        label: str = "",
        allowed_extensions: list[str] | None = None,
        allow_multiple: bool = False,
        on_result: Optional[Callable[[list[str]], None]] = None,
        **kwargs
    ):
        self.label = label
        self.allowed_extensions = allowed_extensions
        self.allow_multiple = allow_multiple
        self.on_result = on_result
        self._theme = get_theme()
        self._file_picker: ft.FilePicker | None = None
        self._selected_files: list[str] = []

        super().__init__(**kwargs)
        self._build()

    def _build(self):
        """Build file picker."""
        c = self._theme.colors

        self._file_picker = ft.FilePicker(on_result=self._on_result)
        if self.page:
            self.page.overlay.append(self._file_picker)

        self._file_text = ft.Text(
            "No file selected",
            size=13,
            color=c.on_surface_variant,
            expand=True,
        )

        pick_button = ft.FilledButton(
            text="Choose File" + ("s" if self.allow_multiple else ""),
            icon=ft.Icons.FOLDER_OPEN,
            on_click=self._pick_files,
        )

        clear_button = ft.TextButton(
            text="Clear",
            icon=ft.Icons.CLEAR,
            on_click=self._clear,
            visible=False,
        )
        self._clear_button = clear_button

        self.content = ft.Column(
            controls=[
                ft.Text(self.label, size=13, weight=ft.FontWeight.MEDIUM, color=c.on_surface) if self.label else ft.Container(),
                ft.Container(height=8) if self.label else ft.Container(),
                ft.Row(
                    controls=[
                        self._file_text,
                        pick_button,
                        clear_button,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=0,
            tight=True,
        )

    def _pick_files(self, _):
        """Open file picker."""
        if self.allow_multiple:
            self._file_picker.pick_files(
                allowed_extensions=self.allowed_extensions,
                allow_multiple=True,
            )
        else:
            self._file_picker.pick_files(
                allowed_extensions=self.allowed_extensions,
                allow_multiple=False,
            )

    def _on_result(self, e: ft.FilePickerResultEvent):
        """Handle file picker result."""
        if e.files:
            self._selected_files = [f.path for f in e.files]
            if self.allow_multiple:
                self._file_text.value = f"{len(self._selected_files)} files selected"
            else:
                self._file_text.value = e.files[0].name
            self._file_text.color = self._theme.colors.on_surface
            self._clear_button.visible = True
        else:
            self._selected_files = []
            self._file_text.value = "No file selected"
            self._file_text.color = self._theme.colors.on_surface_variant
            self._clear_button.visible = False

        self._file_text.update()
        self._clear_button.update()

        if self.on_result:
            self.on_result(self._selected_files)

    def _clear(self, _):
        """Clear selection."""
        self._selected_files = []
        self._file_text.value = "No file selected"
        self._file_text.color = self._theme.colors.on_surface_variant
        self._clear_button.visible = False
        self._file_text.update()
        self._clear_button.update()

        if self.on_result:
            self.on_result([])

    @property
    def files(self) -> list[str]:
        return self._selected_files