"""Dialog widgets for BenchLM - confirm, alert, input, settings, progress dialogs."""

import flet as ft
from typing import Optional, Callable, Any, List
from dataclasses import dataclass

from benchlm.ui.theme import get_theme


class ConfirmDialog(ft.AlertDialog):
    """Confirmation dialog."""

    def __init__(
        self,
        title: str = "Confirm",
        message: str = "Are you sure?",
        confirm_text: str = "Confirm",
        cancel_text: str = "Cancel",
        confirm_color: str | None = None,
        on_confirm: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        **kwargs
    ):
        self._on_confirm = on_confirm
        self._on_cancel = on_cancel
        self._theme = get_theme()

        c = self._theme.colors
        confirm_color = confirm_color or c.primary

        super().__init__(
            title=ft.Text(title, size=18, weight=ft.FontWeight.SEMIBOLD),
            content=ft.Text(message, size=14),
            actions=[
                ft.TextButton(
                    text=cancel_text,
                    on_click=self._handle_cancel,
                ),
                ft.FilledButton(
                    text=confirm_text,
                    style=ft.ButtonStyle(bgcolor=confirm_color),
                    on_click=self._handle_confirm,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            **kwargs
        )

    def _handle_confirm(self, _):
        if self._on_confirm:
            self._on_confirm()
        self.open = False
        self.page.update()

    def _handle_cancel(self, _):
        if self._on_cancel:
            self._on_cancel()
        self.open = False
        self.page.update()


class AlertDialog(ft.AlertDialog):
    """Alert dialog with customizable severity."""

    class Severity:
        INFO = "info"
        SUCCESS = "success"
        WARNING = "warning"
        ERROR = "error"

    def __init__(
        self,
        title: str = "Alert",
        message: str = "",
        severity: str = Severity.INFO,
        action_text: str = "OK",
        on_action: Optional[Callable] = None,
        **kwargs
    ):
        self._on_action = on_action
        self._theme = get_theme()

        c = self._theme.colors

        # Severity colors
        severity_config = {
            self.Severity.INFO: {"icon": ft.Icons.INFO_OUTLINE, "color": c.tertiary, "bg": c.tertiary + "20"},
            self.Severity.SUCCESS: {"icon": ft.Icons.CHECK_CIRCLE_OUTLINE, "color": c.success, "bg": c.success + "20"},
            self.Severity.WARNING: {"icon": ft.Icons.WARNING_AMBER_OUTLINE, "color": c.warning, "bg": c.warning + "20"},
            self.Severity.ERROR: {"icon": ft.Icons.ERROR_OUTLINE, "color": c.danger, "bg": c.danger + "20"},
        }

        config = severity_config.get(severity, severity_config[self.Severity.INFO])

        super().__init__(
            title=ft.Row(
                controls=[
                    ft.Icon(config["icon"], size=24, color=config["color"]),
                    ft.Container(width=12),
                    ft.Text(title, size=18, weight=ft.FontWeight.SEMIBOLD, expand=True),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            content=ft.Container(
                content=ft.Text(message, size=14),
                bgcolor=config["bg"],
                border_radius=8,
                padding=12,
            ),
            actions=[
                ft.FilledButton(
                    text=action_text,
                    on_click=self._handle_action,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            **kwargs
        )

    def _handle_action(self, _):
        if self._on_action:
            self._on_action()
        self.open = False
        self.page.update()


class InputDialog(ft.AlertDialog):
    """Input dialog for text/numeric input."""

    def __init__(
        self,
        title: str = "Input",
        message: str = "",
        field_label: str = "Value",
        field_hint: str = "",
        initial_value: str = "",
        field_type: str = "text",  # text, number, password
        validator: Optional[Callable[[str], str | None]] = None,
        confirm_text: str = "OK",
        cancel_text: str = "Cancel",
        on_confirm: Optional[Callable[[str], None]] = None,
        on_cancel: Optional[Callable] = None,
        **kwargs
    ):
        self._validator = validator
        self._on_confirm = on_confirm
        self._on_cancel = on_cancel
        self._theme = get_theme()

        c = self._theme.colors

        # Create field
        self._field = ft.TextField(
            value=initial_value,
            label=field_label,
            hint_text=field_hint,
            password=field_type == "password",
            keyboard_type=ft.KeyboardType.NUMBER if field_type == "number" else ft.KeyboardType.TEXT,
            text_size=14,
            border_color=c.outline,
            focused_border_color=c.primary,
            focused_bgcolor=c.surface,
            bgcolor=c.surface_variant,
            color=c.on_surface,
            border_radius=8,
            filled=True,
            dense=True,
            autofocus=True,
            on_submit=self._handle_submit,
        )

        super().__init__(
            title=ft.Text(title, size=18, weight=ft.FontWeight.SEMIBOLD),
            content=ft.Column(
                controls=[
                    ft.Text(message, size=14) if message else ft.Container(),
                    ft.Container(height=16) if message else ft.Container(),
                    self._field,
                ],
                spacing=0,
                tight=True,
            ),
            actions=[
                ft.TextButton(
                    text=cancel_text,
                    on_click=self._handle_cancel,
                ),
                ft.FilledButton(
                    text=confirm_text,
                    on_click=self._handle_confirm,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            **kwargs
        )

    def _handle_confirm(self, _):
        value = self._field.value or ""
        if self._validator:
            error = self._validator(value)
            if error:
                self._field.error_text = error
                self._field.update()
                return

        if self._on_confirm:
            self._on_confirm(value)
        self.open = False
        self.page.update()

    def _handle_cancel(self, _):
        if self._on_cancel:
            self._on_cancel()
        self.open = False
        self.page.update()

    def _handle_submit(self, _):
        self._handle_confirm(None)


class SettingsDialog(ft.AlertDialog):
    """Settings dialog with tabs."""

    def __init__(
        self,
        title: str = "Settings",
        tabs: List[ft.Tab] | None = None,
        on_save: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        **kwargs
    ):
        self._on_save = on_save
        self._on_cancel = on_cancel
        self._theme = get_theme()

        c = self._theme.colors

        tabs_control = ft.Tabs(
            tabs=tabs or [],
            selected_index=0,
            divider_color=c.outline_variant,
            indicator_color=c.primary,
            label_color=c.on_surface,
            unselected_label_color=c.on_surface_disabled,
            expand=True,
        )

        super().__init__(
            title=ft.Text(title, size=18, weight=ft.FontWeight.SEMIBOLD),
            content=ft.Container(
                content=tabs_control,
                width=600,
                height=500,
            ),
            actions=[
                ft.TextButton(
                    text="Cancel",
                    on_click=self._handle_cancel,
                ),
                ft.FilledButton(
                    text="Save",
                    on_click=self._handle_save,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            **kwargs
        )

    def _handle_save(self, _):
        if self._on_save:
            self._on_save()
        self.open = False
        self.page.update()

    def _handle_cancel(self, _):
        if self._on_cancel:
            self._on_cancel()
        self.open = False
        self.page.update()


class ProgressDialog(ft.AlertDialog):
    """Progress dialog with indeterminate or determinate progress."""

    def __init__(
        self,
        title: str = "Processing",
        message: str = "Please wait...",
        show_progress: bool = True,
        determinate: bool = False,
        max_value: float = 100,
        on_cancel: Optional[Callable] = None,
        cancellable: bool = True,
        **kwargs
    ):
        self._on_cancel = on_cancel
        self._determinate = determinate
        self._max_value = max_value
        self._theme = get_theme()

        c = self._theme.colors

        progress_control = ft.ProgressRing(
            width=32,
            height=32,
            stroke_width=3,
            color=c.primary,
        ) if not determinate else ft.ProgressBar(
            value=0,
            width=300,
            height=6,
            color=c.primary,
            bgcolor=c.surface_variant,
            border_radius=3,
        )

        self._progress_control = progress_control
        self._message_text = ft.Text(message, size=14, color=c.on_surface_variant)
        self._value_text = ft.Text("0%", size=13, color=c.on_surface_disabled) if determinate else ft.Container()

        cancel_btn = ft.TextButton(
            text="Cancel",
            on_click=self._handle_cancel,
            visible=cancellable,
        )

        super().__init__(
            title=ft.Text(title, size=18, weight=ft.FontWeight.SEMIBOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[progress_control],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                        ft.Container(height=16),
                        self._message_text,
                        ft.Container(height=8),
                        self._value_text,
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                    tight=True,
                ),
                width=300,
                padding=24,
            ),
            actions=[cancel_btn] if cancellable else [],
            actions_alignment=ft.MainAxisAlignment.CENTER,
            modal=True,
            **kwargs
        )

    def set_progress(self, value: float, message: str | None = None):
        """Set progress value (0-1 for indeterminate, 0-max for determinate)."""
        if self._determinate:
            normalized = value / self._max_value
            self._progress_control.value = normalized
            self._value_text.value = f"{value:.0f} / {self._max_value:.0f}"
        else:
            self._progress_control.value = value if value > 0 else None

        if message:
            self._message_text.value = message

        self._progress_control.update()
        self._message_text.update()
        if hasattr(self._value_text, 'update'):
            self._value_text.update()

    def set_message(self, message: str):
        """Update message."""
        self._message_text.value = message
        self._message_text.update()

    def complete(self, message: str = "Complete"):
        """Mark as complete."""
        self.set_progress(1.0 if self._determinate else 1, message)
        # Auto-close after delay
        import asyncio
        asyncio.create_task(self._auto_close())

    async def _auto_close(self):
        await asyncio.sleep(1.5)
        self.open = False
        if self.page:
            self.page.update()

    def _handle_cancel(self, _):
        if self._on_cancel:
            self._on_cancel()
        self.open = False
        self.page.update()


class MultiStepDialog(ft.AlertDialog):
    """Multi-step dialog/wizard."""

    def __init__(
        self,
        title: str = "Wizard",
        steps: List[ft.Control] | None = None,
        step_labels: List[str] | None = None,
        on_next: Optional[Callable[[int], bool]] = None,  # Return False to prevent advance
        on_back: Optional[Callable[[int], None]] = None,
        on_finish: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
        **kwargs
    ):
        self._steps = steps or []
        self._step_labels = step_labels or [f"Step {i+1}" for i in range(len(steps))]
        self._current_step = 0
        self._on_next = on_next
        self._on_back = on_back
        self._on_finish = on_finish
        self._on_cancel = on_cancel
        self._theme = get_theme()

        c = self._theme.colors

        # Stepper
        self._stepper_controls = []
        for i, label in enumerate(self._step_labels):
            is_active = i == self._current_step
            is_completed = i < self._current_step

            circle = ft.Container(
                content=ft.Text(
                    str(i + 1),
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=c.on_primary if (is_active or is_completed) else c.on_surface_disabled,
                ) if not is_completed else ft.Icon(ft.Icons.CHECK, size=14, color=c.on_primary),
                width=28,
                height=28,
                bgcolor=c.primary if (is_active or is_completed) else c.surface_container_high,
                border_radius=14,
                alignment=ft.alignment.center,
                border=ft.border.all(2, c.primary) if is_active else None,
            )

            label_text = ft.Text(
                label,
                size=11,
                weight=ft.FontWeight.MEDIUM if is_active else ft.FontWeight.NORMAL,
                color=c.on_surface if (is_active or is_completed) else c.on_surface_disabled,
                text_align=ft.TextAlign.CENTER,
            )

            self._stepper_controls.append(
                ft.Column(
                    controls=[circle, ft.Container(height=4), label_text],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        self._stepper = ft.Row(
            controls=self._stepper_controls,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Step content
        self._step_content = ft.Container(
            content=self._steps[0] if self._steps else ft.Container(),
            expand=True,
            padding=ft.padding.only(top=24),
        )

        super().__init__(
            title=ft.Text(title, size=18, weight=ft.FontWeight.SEMIBOLD),
            content=ft.Column(
                controls=[
                    self._stepper,
                    ft.Divider(height=1, color=c.outline_variant),
                    self._step_content,
                ],
                spacing=0,
                tight=True,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=self._handle_cancel),
                ft.TextButton("Back", on_click=self._handle_back, visible=False, disabled=True),
                ft.FilledButton("Next", on_click=self._handle_next),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            **kwargs
        )

        self._back_btn = self.actions[1]
        self._next_btn = self.actions[2]

    def _update_stepper(self):
        """Update stepper visual state."""
        c = self._theme.colors

        for i, control in enumerate(self._stepper_controls):
            is_active = i == self._current_step
            is_completed = i < self._current_step

            circle = control.controls[0]
            label = control.controls[2]

            if is_completed:
                circle.content = ft.Icon(ft.Icons.CHECK, size=14, color=c.on_primary)
                circle.bgcolor = c.primary
            elif is_active:
                circle.content = ft.Text(str(i + 1), size=12, weight=ft.FontWeight.BOLD, color=c.on_primary)
                circle.bgcolor = c.primary
                circle.border = ft.border.all(2, c.primary)
            else:
                circle.content = ft.Text(str(i + 1), size=12, weight=ft.FontWeight.BOLD, color=c.on_surface_disabled)
                circle.bgcolor = c.surface_container_high
                circle.border = None

            label.weight = ft.FontWeight.MEDIUM if is_active else ft.FontWeight.NORMAL
            label.color = c.on_surface if (is_active or is_completed) else c.on_surface_disabled

        self._stepper.update()

    def _handle_next(self, _):
        # Validate current step
        if self._on_next:
            can_proceed = self._on_next(self._current_step)
            if not can_proceed:
                return

        if self._current_step < len(self._steps) - 1:
            self._current_step += 1
            self._step_content.content = self._steps[self._current_step]
            self._update_stepper()

            # Update buttons
            self._back_btn.visible = True
            self._back_btn.disabled = False
            if self._current_step == len(self._steps) - 1:
                self._next_btn.text = "Finish"
            self._next_btn.update()
            self._back_btn.update()
            self._step_content.update()
        else:
            self._handle_finish()

    def _handle_back(self, _):
        if self._current_step > 0:
            self._current_step -= 1
            self._step_content.content = self._steps[self._current_step]
            self._update_stepper()

            self._next_btn.text = "Next"
            if self._current_step == 0:
                self._back_btn.visible = False
                self._back_btn.disabled = True

            self._next_btn.update()
            self._back_btn.update()
            self._step_content.update()

            if self._on_back:
                self._on_back(self._current_step)

    def _handle_finish(self):
        if self._on_finish:
            self._on_finish()
        self.open = False
        self.page.update()

    def _handle_cancel(self, _):
        if self._on_cancel:
            self._on_cancel()
        self.open = False
        self.page.update()