"""UI widgets package for BenchLM."""

from benchlm.ui.widgets.gauges import (
    CircularGauge,
    LinearGauge,
    MultiGauge,
    GaugeSize,
)
from benchlm.ui.widgets.cards import (
    MetricCard,
    StatCard,
    GlassCard,
    ElevatedCard,
    ChartCard,
)
from benchlm.ui.widgets.tables import (
    VirtualizedTable,
    DataTable,
    SortableColumn,
)
from benchlm.ui.widgets.charts import (
    PlotlyChart,
    LazyPlotlyChart,
    ChartContainer,
)
from benchlm.ui.widgets.navigation import (
    NavigationRail,
    NavigationDrawer,
    TabBar,
    Breadcrumb,
)
from benchlm.ui.widgets.forms import (
    FormField,
    SliderField,
    SelectField,
    ToggleField,
    ColorPickerField,
    FilePickerField,
)
from benchlm.ui.widgets.dialogs import (
    ConfirmDialog,
    AlertDialog,
    InputDialog,
    SettingsDialog,
    ProgressDialog,
)
from benchlm.ui.widgets.indicators import (
    StatusIndicator,
    LoadingSpinner,
    ProgressRing,
    PulseIndicator,
)
from benchlm.ui.widgets.layout import (
    ResponsiveRow,
    ResponsiveColumn,
    GridLayout,
    FlexLayout,
    ScrollableContainer,
)

__all__ = [
    # Gauges
    "CircularGauge",
    "LinearGauge",
    "MultiGauge",
    "GaugeSize",
    # Cards
    "MetricCard",
    "StatCard",
    "GlassCard",
    "ElevatedCard",
    "ChartCard",
    # Tables
    "VirtualizedTable",
    "DataTable",
    "SortableColumn",
    # Charts
    "PlotlyChart",
    "LazyPlotlyChart",
    "ChartContainer",
    # Navigation
    "NavigationRail",
    "NavigationDrawer",
    "TabBar",
    "Breadcrumb",
    # Forms
    "FormField",
    "SliderField",
    "SelectField",
    "ToggleField",
    "ColorPickerField",
    "FilePickerField",
    # Dialogs
    "ConfirmDialog",
    "AlertDialog",
    "InputDialog",
    "SettingsDialog",
    "ProgressDialog",
    # Indicators
    "StatusIndicator",
    "LoadingSpinner",
    "ProgressRing",
    "PulseIndicator",
    # Layout
    "ResponsiveRow",
    "ResponsiveColumn",
    "GridLayout",
    "FlexLayout",
    "ScrollableContainer",
]