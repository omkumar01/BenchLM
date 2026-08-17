"""Table widgets for BenchLM - virtualized, sortable, and data tables."""

import flet as ft
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from enum import Enum

from benchlm.ui.theme import get_theme


class SortDirection(Enum):
    """Sort direction."""

    NONE = "none"
    ASC = "asc"
    DESC = "desc"


@dataclass
class ColumnConfig:
    """Configuration for a table column."""

    key: str
    label: str
    width: Optional[int] = None
    min_width: int = 80
    max_width: int = 500
    sortable: bool = True
    resizable: bool = True
    align: ft.CrossAxisAlignment = ft.CrossAxisAlignment.START
    format_fn: Optional[Callable[[Any], str]] = None
    tooltip: Optional[str] = None
    visible: bool = True
    pinned: bool = False  # Pin to left/right


@dataclass
class TableConfig:
    """Configuration for table behavior."""

    columns: list[ColumnConfig] = field(default_factory=list)
    row_height: int = 44
    header_height: int = 48
    show_header: bool = True
    show_borders: bool = True
    striped: bool = True
    hoverable: bool = True
    selectable: bool = False
    multi_select: bool = False
    virtualized: bool = True
    virtualization_threshold: int = 1000
    page_size: int = 50
    sort_column: Optional[str] = None
    sort_direction: SortDirection = SortDirection.NONE
    on_row_click: Optional[Callable[[dict], None]] = None
    on_selection_change: Optional[Callable[[list[dict]], None]] = None
    on_sort: Optional[Callable[[str, SortDirection], None]] = None


class VirtualizedTable(ft.Container):
    """High-performance virtualized table for large datasets."""

    def __init__(
        self,
        config: TableConfig | None = None,
        data: list[dict] | None = None,
        **kwargs
    ):
        self.config = config or TableConfig()
        self._data = data or []
        self._filtered_data = self._data.copy()
        self._selected_rows: set[int] = set()
        self._sort_column = self.config.sort_column
        self._sort_direction = self.config.sort_direction
        self._theme = get_theme()
        self._visible_range = (0, 0)

        super().__init__(**kwargs)
        self._build()

    def _build(self):
        """Build table UI."""
        if not self.config.virtualized or len(self._filtered_data) < self.config.virtualization_threshold:
            # Use regular DataTable for small datasets
            self.content = self._build_data_table()
        else:
            # Use virtualized ListView
            self.content = self._build_virtualized_table()

    def _build_data_table(self) -> ft.DataTable:
        """Build standard Flet DataTable."""
        c = self._theme.colors
        cfg = self.config

        # Columns
        columns = []
        for col_cfg in cfg.columns:
            if not col_cfg.visible:
                continue

            columns.append(
                ft.DataColumn(
                    label=ft.Text(
                        col_cfg.label,
                        size=13,
                        weight=ft.FontWeight.W_600,
                        color=c.on_surface_variant,
                    ),
                    numeric=col_cfg.align == ft.CrossAxisAlignment.END,
                    on_sort=lambda e, key=col_cfg.key: self._handle_sort(key) if col_cfg.sortable else None,
                )
            )

        # Rows
        rows = []
        for idx, row_data in enumerate(self._filtered_data):
            cells = []
            for col_cfg in cfg.columns:
                if not col_cfg.visible:
                    continue

                value = row_data.get(col_cfg.key, "")
                if col_cfg.format_fn:
                    value = col_cfg.format_fn(value)
                else:
                    value = str(value)

                cells.append(
                    ft.DataCell(
                        ft.Text(
                            value,
                            size=13,
                            color=c.on_surface,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        on_tap=lambda e, data=row_data: self._handle_row_click(data) if cfg.on_row_click else None,
                    )
                )

            rows.append(
                ft.DataRow(
                    cells=cells,
                    selected=idx in self._selected_rows,
                    on_select_changed=lambda e, idx=idx: self._handle_selection(idx, e.control.selected)
                    if cfg.selectable else None,
                    color={
                        ft.ControlState.HOVERED: c.surface_container_high if cfg.hoverable else None,
                        ft.ControlState.SELECTED: c.primary_container if cfg.selectable else None,
                    },
                )
            )

        return ft.DataTable(
            columns=columns,
            rows=rows,
            heading_row_height=cfg.header_height,
            data_row_min_height=cfg.row_height,
            data_row_max_height=cfg.row_height,
            show_checkbox_column=cfg.selectable,
            border=ft.Border.all(1, c.outline_variant) if cfg.show_borders else None,
            horizontal_margin=12,
            column_spacing=16,
            sort_column_index=self._get_sort_column_index() if cfg.sort_column else None,
            sort_ascending=self._sort_direction == SortDirection.ASC,
        )

    def _build_virtualized_table(self) -> ft.Column:
        """Build virtualized table using ListView."""
        c = self._theme.colors
        cfg = self.config

        # Header
        header_cells = []
        for col_cfg in cfg.columns:
            if not col_cfg.visible:
                continue

            width = col_cfg.width or 150
            header_cells.append(
                ft.Container(
                    content=ft.Text(
                        col_cfg.label,
                        size=13,
                        weight=ft.FontWeight.W_600,
                        color=c.on_surface_variant,
                    ),
                    width=width,
                    height=cfg.header_height,
                    alignment=ft.Alignment.CENTER_LEFT,
                    padding=ft.Padding.symmetric(horizontal=12),
                    border=ft.Border.only(bottom=ft.BorderSide(1, c.outline_variant)),
                )
            )

        header = ft.Container(
            content=ft.Row(
                controls=header_cells,
                spacing=0,
            ),
            bgcolor=c.surface_container,
            border_radius=ft.BorderRadius.only(top_left=8, top_right=8),
        )

        # Virtualized body using ListView
        self._list_view = ft.ListView(
            controls=[],
            spacing=0,
            padding=ft.Padding.only(bottom=8),
            expand=True,
            auto_scroll=False,
        )

        # Initial render
        self._render_visible_rows()

        # Scroll listener for virtualization
        self._list_view.on_scroll = self._on_scroll

        return ft.Column(
            controls=[
                header,
                ft.Container(
                    content=self._list_view,
                    expand=True,
                    border=ft.Border.all(1, c.outline_variant),
                    border_radius=ft.BorderRadius.only(bottom_left=8, bottom_right=8),
                ),
            ],
            spacing=0,
            expand=True,
        )

    def _render_visible_rows(self):
        """Render only visible rows for virtualization."""
        if not hasattr(self, "_list_view"):
            return

        cfg = self.config
        # Calculate visible range based on scroll position
        # For simplicity, render first page_size rows
        start = 0
        end = min(cfg.page_size, len(self._filtered_data))

        self._visible_range = (start, end)

        rows = []
        for idx in range(start, end):
            row_data = self._filtered_data[idx]
            rows.append(self._create_row(idx, row_data))

        self._list_view.controls = rows
        self._list_view.update()

    def _create_row(self, idx: int, row_data: dict) -> ft.Container:
        """Create a single row container."""
        c = self._theme.colors
        cfg = self.config

        cells = []
        for col_cfg in cfg.columns:
            if not col_cfg.visible:
                continue

            value = row_data.get(col_cfg.key, "")
            if col_cfg.format_fn:
                value = col_cfg.format_fn(value)
            else:
                value = str(value)

            width = col_cfg.width or 150
            cells.append(
                ft.Container(
                    content=ft.Text(
                        value,
                        size=13,
                        color=c.on_surface,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    width=width,
                    height=cfg.row_height,
                    alignment=ft.Alignment.CENTER_LEFT,
                    padding=ft.Padding.symmetric(horizontal=12),
                    border=ft.Border.only(right=ft.BorderSide(1, c.outline_variant)) if col_cfg != cfg.columns[-1] else None,
                )
            )

        row = ft.Container(
            content=ft.Row(controls=cells, spacing=0),
            height=cfg.row_height,
            bgcolor=c.primary_container if idx in self._selected_rows else (
                c.surface_container_high if idx % 2 == 1 and cfg.striped else c.surface
            ),
            on_click=lambda e, data=row_data: self._handle_row_click(data) if cfg.on_row_click else None,
            on_hover=lambda e: self._on_row_hover(e, idx) if cfg.hoverable else None,
            ink=True,
        )

        return row

    def _on_scroll(self, e: ft.OnScrollEvent):
        """Handle scroll for virtualization."""
        # In a real implementation, calculate visible range from scroll position
        # For now, just re-render (simplified)
        pass

    def _on_row_hover(self, e: ft.HoverEvent, idx: int):
        """Handle row hover."""
        # Visual feedback handled by container bgcolor
        pass

    def _handle_row_click(self, row_data: dict):
        """Handle row click."""
        if self.config.on_row_click:
            self.config.on_row_click(row_data)

    def _handle_selection(self, idx: int, selected: bool):
        """Handle row selection."""
        if selected:
            self._selected_rows.add(idx)
        else:
            self._selected_rows.discard(idx)

        if self.config.on_selection_change:
            selected_data = [self._filtered_data[i] for i in self._selected_rows]
            self.config.on_selection_change(selected_data)

    def _handle_sort(self, column_key: str):
        """Handle column sort."""
        if self._sort_column == column_key:
            # Toggle direction
            if self._sort_direction == SortDirection.ASC:
                self._sort_direction = SortDirection.DESC
            else:
                self._sort_direction = SortDirection.ASC
        else:
            self._sort_column = column_key
            self._sort_direction = SortDirection.ASC

        self._apply_sort()
        self.refresh()

        if self.config.on_sort:
            self.config.on_sort(column_key, self._sort_direction)

    def _apply_sort(self):
        """Apply sorting to filtered data."""
        if not self._sort_column:
            return

        # Find column config
        col_cfg = next((c for c in self.config.columns if c.key == self._sort_column), None)
        if not col_cfg:
            return

        reverse = self._sort_direction == SortDirection.DESC

        def sort_key(row):
            val = row.get(self._sort_column, "")
            if isinstance(val, str):
                return val.lower()
            return val

        self._filtered_data.sort(key=sort_key, reverse=reverse)

    def _get_sort_column_index(self) -> int:
        """Get sort column index for DataTable."""
        if not self._sort_column:
            return 0
        visible_cols = [c for c in self.config.columns if c.visible]
        for i, col in enumerate(visible_cols):
            if col.key == self._sort_column:
                return i
        return 0

    @property
    def data(self) -> list[dict]:
        return self._data

    @data.setter
    def data(self, value: list[dict] | None):
        # Flet's generated control __init__ assigns None for unset fields
        value = value or []
        self._data = value
        self._filtered_data = value.copy()
        self._apply_sort()
        self.refresh()

    def refresh(self):
        """Refresh table display."""
        if self.config.virtualized and len(self._filtered_data) >= self.config.virtualization_threshold:
            self._render_visible_rows()
        else:
            self.content = self._build_data_table()
            # update() only when attached to a page (safe during construction)
            try:
                self.update()
            except (RuntimeError, AttributeError):
                pass

    def filter(self, filter_fn: Callable[[dict], bool]):
        """Filter data."""
        self._filtered_data = [row for row in self._data if filter_fn(row)]
        self._apply_sort()
        self.refresh()

    def get_selected_data(self) -> list[dict]:
        """Get selected row data."""
        return [self._filtered_data[i] for i in self._selected_rows]

    def clear_selection(self):
        """Clear all selections."""
        self._selected_rows.clear()
        self.refresh()


class SortableColumn(ft.Container):
    """Sortable column header."""

    def __init__(
        self,
        label: str,
        key: str,
        on_sort: Callable[[str, SortDirection], None],
        current_sort: tuple[str, SortDirection] | None = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.label = label
        self.key = key
        self.on_sort = on_sort
        self.current_sort = current_sort
        self._theme = get_theme()
        self._build()

    def _build(self):
        """Build sortable column header."""
        c = self._theme.colors

        is_sorted = self.current_sort and self.current_sort[0] == self.key
        sort_dir = self.current_sort[1] if is_sorted else SortDirection.NONE

        icon = ft.Icon(
            ft.Icons.ARROW_UPWARD if sort_dir == SortDirection.ASC else ft.Icons.ARROW_DOWNWARD,
            size=16,
            color=c.primary if is_sorted else c.on_surface_disabled,
            visible=is_sorted,
        )

        self.content = ft.Row(
            controls=[
                ft.Text(
                    self.label,
                    size=13,
                    weight=ft.FontWeight.W_600,
                    color=c.on_surface,
                ),
                icon,
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        self.padding = ft.Padding.symmetric(horizontal=12, vertical=8)
        self.on_click = lambda _: self._handle_click()
        self.ink = True
        self.tooltip = "Click to sort"

    def _handle_click(self):
        """Handle click to sort."""
        if self.current_sort and self.current_sort[0] == self.key:
            new_dir = SortDirection.DESC if self.current_sort[1] == SortDirection.ASC else SortDirection.ASC
        else:
            new_dir = SortDirection.ASC

        self.on_sort(self.key, new_dir)


class DataTable(ft.Container):
    """Enhanced DataTable with additional features."""

    def __init__(
        self,
        columns: list[ColumnConfig],
        data: list[dict] = [],
        page_size: int = 50,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.columns = columns
        self.data = data
        self.page_size = page_size
        self.current_page = 0
        self._theme = get_theme()
        self._build()

    def _build(self):
        """Build paginated data table."""
        # Implementation similar to VirtualizedTable but with pagination
        pass


class PaginatedTable(VirtualizedTable):
    """Table with pagination controls."""

    def __init__(
        self,
        config: TableConfig | None = None,
        data: list[dict] | None = None,
        show_page_size_selector: bool = True,
        page_sizes: list[int] = [25, 50, 100, 200],
        **kwargs
    ):
        self.show_page_size_selector = show_page_size_selector
        self.page_sizes = page_sizes
        self._pagination_controls = None
        super().__init__(config, data, **kwargs)

    def _build(self):
        """Build table with pagination."""
        table_content = super()._build()

        # Pagination controls
        self._pagination_controls = self._build_pagination()

        self.content = ft.Column(
            controls=[
                ft.Container(content=table_content, expand=True),
                self._pagination_controls,
            ],
            spacing=16,
            expand=True,
        )

    def _build_pagination(self) -> ft.Row:
        """Build pagination controls."""
        c = self._theme.colors
        total_pages = max(1, (len(self._filtered_data) + self.config.page_size - 1) // self.config.page_size)

        # Page size selector
        page_size_control = ft.Container()
        if self.show_page_size_selector:
            page_size_control = ft.Dropdown(
                value=str(self.config.page_size),
                options=[ft.dropdown.Option(str(s)) for s in self.page_sizes],
                width=80,
                border_color=c.outline,
                focused_border_color=c.primary,
            )
            page_size_control.on_select = lambda e: self._change_page_size(int(e.control.value))

        # Page navigation
        self._prev_btn = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            disabled=self.current_page == 0,
            on_click=lambda _: self._prev_page(),
        )

        self._next_btn = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT,
            disabled=self.current_page >= total_pages - 1,
            on_click=lambda _: self._next_page(),
        )

        self._page_indicator = ft.Text(
            f"Page {self.current_page + 1} of {total_pages}",
            size=13,
            color=c.on_surface_variant,
        )

        self._total_indicator = ft.Text(
            f"Total: {len(self._filtered_data)} rows",
            size=13,
            color=c.on_surface_disabled,
        )

        return ft.Row(
            controls=[
                self._total_indicator,
                ft.Container(expand=True),
                page_size_control,
                ft.Container(width=16),
                self._prev_btn,
                self._page_indicator,
                self._next_btn,
            ],
            alignment=ft.MainAxisAlignment.END,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _change_page_size(self, size: int):
        """Change page size."""
        self.config.page_size = size
        self.current_page = 0
        self.refresh()
        self._update_pagination()

    def _prev_page(self):
        """Go to previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh()
            self._update_pagination()

    def _next_page(self):
        """Go to next page."""
        total_pages = max(1, (len(self._filtered_data) + self.config.page_size - 1) // self.config.page_size)
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.refresh()
            self._update_pagination()

    def _update_pagination(self):
        """Update pagination controls."""
        if not self._pagination_controls:
            return

        total_pages = max(1, (len(self._filtered_data) + self.config.page_size - 1) // self.config.page_size)

        self._prev_btn.disabled = self.current_page == 0
        self._next_btn.disabled = self.current_page >= total_pages - 1
        self._page_indicator.value = f"Page {self.current_page + 1} of {total_pages}"
        self._total_indicator.value = f"Total: {len(self._filtered_data)} rows"

        self._pagination_controls.update()