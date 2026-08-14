"""Pages package for BenchLM - 11 main application pages."""

from benchlm.ui.pages.dashboard import DashboardPage
from benchlm.ui.pages.models import ModelsPage
from benchlm.ui.pages.benchmark import BenchmarkPage
from benchlm.ui.pages.live_monitor import LiveMonitorPage
from benchlm.ui.pages.results import ResultsPage
from benchlm.ui.pages.comparison import ComparisonPage
from benchlm.ui.pages.history import HistoryPage
from benchlm.ui.pages.leaderboard import LeaderboardPage
from benchlm.ui.pages.datasets import DatasetsPage
from benchlm.ui.pages.reports import ReportsPage
from benchlm.ui.pages.settings import SettingsPage

__all__ = [
    "DashboardPage",
    "ModelsPage",
    "BenchmarkPage",
    "LiveMonitorPage",
    "ResultsPage",
    "ComparisonPage",
    "HistoryPage",
    "LeaderboardPage",
    "DatasetsPage",
    "ReportsPage",
    "SettingsPage",
]