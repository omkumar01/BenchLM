"""Chart widgets for BenchLM - Plotly integration with lazy loading."""

import flet as ft
import plotly.graph_objects as go
import plotly.io as pio
from typing import Optional, Callable, Any
from dataclasses import dataclass, field

from benchlm.ui.theme import get_theme


# Configure Plotly for offline use
pio.renderers.default = "svg"


@dataclass
class ChartConfig:
    """Configuration for chart appearance."""

    title: str = ""
    xaxis_title: str = ""
    yaxis_title: str = ""
    height: int = 400
    width: Optional[int] = None
    margin: dict = field(default_factory=lambda: {"l": 60, "r": 40, "t": 60, "b": 60})
    show_legend: bool = True
    legend_position: str = "top"  # top, bottom, left, right
    template: str = "plotly_dark"
    hover_mode: str = "x unified"
    responsive: bool = True
    animate: bool = True
    animation_duration: int = 300


class PlotlyChart(ft.Container):
    """Plotly chart rendered as Flet Image or WebView."""

    def __init__(
        self,
        figure: go.Figure | None = None,
        config: ChartConfig | None = None,
        on_click: Optional[Callable] = None,
        on_hover: Optional[Callable] = None,
        **kwargs
    ):
        self.figure = figure
        self.config = config or ChartConfig()
        self._on_click = on_click
        self._on_hover = on_hover
        self._theme = get_theme()
        self._image_control: Optional[ft.Image] = None
        self._webview_control: Optional[ft.WebView] = None
        self._use_webview = False  # Set to True for interactive charts

        super().__init__(**kwargs)
        self._build()

    def _build(self):
        """Build chart container."""
        if self._use_webview:
            self._build_webview()
        else:
            self._build_static_image()

    def _build_static_image(self):
        """Build static SVG/PNG image."""
        c = self._theme.colors

        if self.figure is None:
            # Placeholder
            self.content = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.INSERT_CHART_OUTLINED, size=64, color=c.on_surface_disabled),
                        ft.Container(height=16),
                        ft.Text(
                            "No data to display",
                            size=16,
                            color=c.on_surface_variant,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                height=self.config.height,
                expand=True,
            )
            return

        # Apply theme to figure
        self._apply_theme()

        # Generate SVG
        try:
            svg_bytes = self.figure.to_image(format="svg", width=self.config.width, height=self.config.height)
            svg_base64 = svg_bytes.decode("utf-8")
        except Exception:
            # Fallback to placeholder
            self.content = ft.Container(
                content=ft.Text("Failed to render chart", color=c.danger),
                alignment=ft.alignment.center,
                height=self.config.height,
            )
            return

        # Create image control
        self._image_control = ft.Image(
            src_base64=svg_base64,
            fit=ft.ImageFit.CONTAIN,
            width=self.config.width,
            height=self.config.height,
            expand=True,
        )

        self.content = ft.Container(
            content=self._image_control,
            expand=True,
        )

    def _build_webview(self):
        """Build interactive WebView chart."""
        if self.figure is None:
            html = self._get_empty_html()
        else:
            self._apply_theme()
            html = self.figure.to_html(
                include_plotlyjs="cdn",
                config={"displayModeBar": True, "responsive": True},
            )

        self._webview_control = ft.WebView(
            html=html,
            expand=True,
            on_page_started=lambda _: None,
            on_page_ended=lambda _: None,
            on_web_resource_error=lambda e: print(f"Chart error: {e}"),
        )

        self.content = ft.Container(
            content=self._webview_control,
            expand=True,
            height=self.config.height,
        )

    def _apply_theme(self):
        """Apply BenchLM theme to Plotly figure."""
        if self.figure is None:
            return

        c = self._theme.colors
        chart_colors = self._theme.chart_colors()

        # Update layout with theme colors
        self.figure.update_layout(
            template=self.config.template,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                family="Inter, system-ui, sans-serif",
                size=12,
                color=c.on_surface,
            ),
            title=dict(
                text=self.config.title,
                font=dict(size=16, color=c.on_surface, family="Inter"),
                x=0.5,
                xanchor="center",
            ),
            xaxis=dict(
                title=self.config.xaxis_title,
                title_font=dict(size=13, color=c.on_surface_variant),
                tickfont=dict(size=11, color=c.on_surface_disabled),
                gridcolor=c.outline_variant,
                zerolinecolor=c.outline,
                linecolor=c.outline,
            ),
            yaxis=dict(
                title=self.config.yaxis_title,
                title_font=dict(size=13, color=c.on_surface_variant),
                tickfont=dict(size=11, color=c.on_surface_disabled),
                gridcolor=c.outline_variant,
                zerolinecolor=c.outline,
                linecolor=c.outline,
            ),
            legend=dict(
                orientation="h" if self.config.legend_position in ["top", "bottom"] else "v",
                yanchor="bottom" if self.config.legend_position == "top" else "top",
                y=1.02 if self.config.legend_position == "top" else -0.15,
                xanchor="center",
                x=0.5,
                font=dict(size=11, color=c.on_surface),
                bgcolor="rgba(0,0,0,0)",
                bordercolor=c.outline,
                borderwidth=0,
            ),
            margin=self.config.margin,
            hovermode=self.config.hover_mode,
            hoverlabel=dict(
                bgcolor=c.surface,
                bordercolor=c.outline,
                font=dict(color=c.on_surface, size=12),
            ),
            colorway=chart_colors,
        )

        if self.config.animate:
            self.figure.update_layout(
                transition=dict(duration=self.config.animation_duration, easing="cubic-in-out"),
            )

    def _get_empty_html(self) -> str:
        """Get empty chart HTML."""
        c = self._theme.colors
        return f"""
        <html>
        <head>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{ margin: 0; background: transparent; font-family: Inter, system-ui; }}
                #chart {{ width: 100%; height: 100%; }}
            </style>
        </head>
        <body>
            <div id="chart"></div>
            <script>
                Plotly.newPlot('chart', [], {{
                    title: {{ text: 'No data', font: {{ color: '{c.on_surface_variant}' }} }},
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: {{ color: '{c.on_surface}' }},
                    xaxis: {{ gridcolor: '{c.outline_variant}', zerolinecolor: '{c.outline}' }},
                    yaxis: {{ gridcolor: '{c.outline_variant}', zerolinecolor: '{c.outline}' }},
                }}, {{ displayModeBar: false, responsive: true }});
            </script>
        </body>
        </html>
        """

    def set_figure(self, figure: go.Figure):
        """Update chart with new figure."""
        self.figure = figure
        self._build()
        self.update()

    def update_data(self, data: list[dict]):
        """Update chart data (for traces)."""
        if self.figure is None:
            return

        # Update traces with new data
        for i, trace_data in enumerate(data):
            if i < len(self.figure.data):
                trace = self.figure.data[i]
                if "x" in trace_data:
                    trace.x = trace_data["x"]
                if "y" in trace_data:
                    trace.y = trace_data["y"]
                if "text" in trace_data:
                    trace.text = trace_data["text"]

        self._build()
        self.update()

    def set_config(self, config: ChartConfig):
        """Update chart configuration."""
        self.config = config
        self._build()
        self.update()


class LazyPlotlyChart(PlotlyChart):
    """Plotly chart with lazy loading - only renders when visible."""

    def __init__(
        self,
        figure_factory: Callable[[], go.Figure],
        config: ChartConfig | None = None,
        placeholder: ft.Control | None = None,
        **kwargs
    ):
        self.figure_factory = figure_factory
        self._placeholder = placeholder or ft.Container(
            content=ft.ProgressRing(width=32, height=32, stroke_width=3),
            alignment=ft.alignment.center,
        )
        self._loaded = False
        self._loading = False

        super().__init__(figure=None, config=config, **kwargs)
        self.content = self._placeholder

    def load(self):
        """Load chart data."""
        if self._loaded or self._loading:
            return

        self._loading = True
        self.content = ft.Container(
            content=ft.ProgressRing(width=32, height=32, stroke_width=3),
            alignment=ft.alignment.center,
            height=self.config.height,
        )
        self.update()

        try:
            figure = self.figure_factory()
            self.figure = figure
            self._loaded = True
            self._build()
        except Exception as e:
            self.content = ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.ERROR, size=48, color=self._theme.colors.danger),
                        ft.Text(f"Failed to load: {e}", color=self._theme.colors.danger),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                alignment=ft.alignment.center,
                height=self.config.height,
            )
        finally:
            self._loading = False
            self.update()

    def unload(self):
        """Unload chart to free memory."""
        self._loaded = False
        self.figure = None
        self.content = self._placeholder
        self.update()


class ChartContainer(ft.Container):
    """Container for chart with toolbar and controls."""

    def __init__(
        self,
        chart: PlotlyChart | LazyPlotlyChart,
        title: str = "",
        actions: list[ft.Control] | None = None,
        show_toolbar: bool = True,
        **kwargs
    ):
        self.chart = chart
        self.title = title
        self.actions = actions or []
        self.show_toolbar = show_toolbar
        self._theme = get_theme()

        super().__init__(**kwargs)
        self._build()

    def _build(self):
        """Build chart container with toolbar."""
        c = self._theme.colors

        controls = []

        # Toolbar
        if self.show_toolbar:
            toolbar = ft.Row(
                controls=[
                    ft.Text(
                        self.title,
                        size=16,
                        weight=ft.FontWeight.SEMIBOLD,
                        color=c.on_surface,
                        expand=True,
                    ),
                    *self.actions,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
            controls.append(toolbar)
            controls.append(ft.Divider(height=1, color=c.outline_variant))

        # Chart
        controls.append(self.chart)

        self.content = ft.Column(
            controls=controls,
            spacing=12,
            expand=True,
        )


class MultiChart(ft.Container):
    """Multiple charts in a grid layout."""

    def __init__(
        self,
        charts: list[PlotlyChart | ChartContainer],
        columns: int = 2,
        gap: int = 16,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.charts = charts
        self.columns = columns
        self.gap = gap
        self._build()

    def _build(self):
        """Build grid of charts."""
        rows = []
        for i in range(0, len(self.charts), self.columns):
            row_charts = self.charts[i:i + self.columns]
            row = ft.Row(
                controls=[
                    ft.Container(content=chart, expand=True) for chart in row_charts
                ],
                spacing=self.gap,
                wrap=True,
            )
            rows.append(row)

        self.content = ft.Column(
            controls=rows,
            spacing=self.gap,
            expand=True,
        )


def create_line_chart(
    x_data: list,
    y_data: list,
    name: str = "",
    color: str | None = None,
    mode: str = "lines+markers",
    **kwargs
) -> go.Scatter:
    """Create a line chart trace."""
    return go.Scatter(
        x=x_data,
        y=y_data,
        mode=mode,
        name=name,
        line=dict(color=color, width=2) if color else dict(width=2),
        marker=dict(size=4) if "markers" in mode else None,
        **kwargs
    )


def create_bar_chart(
    x_data: list,
    y_data: list,
    name: str = "",
    color: str | None = None,
    orientation: str = "v",
    **kwargs
) -> go.Bar:
    """Create a bar chart trace."""
    return go.Bar(
        x=x_data if orientation == "v" else y_data,
        y=y_data if orientation == "v" else x_data,
        name=name,
        orientation=orientation,
        marker=dict(color=color) if color else None,
        **kwargs
    )


def create_scatter_chart(
    x_data: list,
    y_data: list,
    name: str = "",
    color: str | None = None,
    size: list | None = None,
    **kwargs
) -> go.Scatter:
    """Create a scatter chart trace."""
    return go.Scatter(
        x=x_data,
        y=y_data,
        mode="markers",
        name=name,
        marker=dict(
            color=color,
            size=size or 8,
            opacity=0.7,
            line=dict(width=0),
        ),
        **kwargs
    )


def create_heatmap(
    z_data: list[list],
    x_labels: list | None = None,
    y_labels: list | None = None,
    colorscale: str = "Viridis",
    **kwargs
) -> go.Heatmap:
    """Create a heatmap trace."""
    return go.Heatmap(
        z=z_data,
        x=x_labels,
        y=y_labels,
        colorscale=colorscale,
        showscale=True,
        **kwargs
    )


def create_box_plot(
    y_data: list,
    x_data: list | None = None,
    name: str = "",
    color: str | None = None,
    **kwargs
) -> go.Box:
    """Create a box plot trace."""
    return go.Box(
        y=y_data,
        x=x_data,
        name=name,
        marker=dict(color=color) if color else None,
        boxpoints="outliers",
        **kwargs
    )


def create_violin_plot(
    y_data: list,
    x_data: list | None = None,
    name: str = "",
    color: str | None = None,
    **kwargs
) -> go.Violin:
    """Create a violin plot trace."""
    return go.Violin(
        y=y_data,
        x=x_data,
        name=name,
        marker=dict(color=color) if color else None,
        box=dict(visible=True),
        meanline=dict(visible=True),
        **kwargs
    )


def create_histogram(
    data: list,
    name: str = "",
    color: str | None = None,
    nbins: int = 30,
    **kwargs
) -> go.Histogram:
    """Create a histogram trace."""
    return go.Histogram(
        x=data,
        name=name,
        marker=dict(color=color) if color else None,
        nbinsx=nbins,
        opacity=0.7,
        **kwargs
    )


def create_candlestick(
    open_data: list,
    high_data: list,
    low_data: list,
    close_data: list,
    x_data: list | None = None,
    name: str = "",
    **kwargs
) -> go.Candlestick:
    """Create a candlestick chart trace."""
    return go.Candlestick(
        x=x_data,
        open=open_data,
        high=high_data,
        low=low_data,
        close=close_data,
        name=name,
        **kwargs
    )