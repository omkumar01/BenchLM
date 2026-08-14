"""Quality charts for BenchLM."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any
import numpy as np


class QualityCharts:
    """Chart generators for quality metrics."""

    @staticmethod
    def quality_radar(
        categories: List[str],
        model_scores: Dict[str, List[float]],
        title: str = "Quality Radar Comparison",
        height: int = 500,
    ) -> go.Figure:
        """Radar chart for multi-model quality comparison."""
        fig = go.Figure()

        colors = ['#6366F1', '#A855F7', '#06B6D4', '#22C55E', '#F59E0B', '#EF4444']
        for i, (model, scores) in enumerate(model_scores.items()):
            fig.add_trace(go.Scatterpolar(
                r=scores + [scores[0]],
                theta=categories + [categories[0]],
                fill='toself',
                name=model,
                line=dict(color=colors[i % len(colors)], width=2),
                fillcolor=colors[i % len(colors)] + '30',
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100]),
            ),
            title=title,
            height=height,
        )
        return fig

    @staticmethod
    def pass_at_k(
        models: List[str],
        pass_at_1: List[float],
        pass_at_5: List[float],
        pass_at_10: List[float],
        title: str = "Pass@k Comparison",
        height: int = 400,
    ) -> go.Figure:
        """Grouped bar chart for Pass@k metrics."""
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Pass@1',
            x=models,
            y=pass_at_1,
            marker_color='#EF4444',
            text=[f"{v:.1%}" for v in pass_at_1],
            textposition='outside',
        ))
        fig.add_trace(go.Bar(
            name='Pass@5',
            x=models,
            y=pass_at_5,
            marker_color='#F59E0B',
            text=[f"{v:.1%}" for v in pass_at_5],
            textposition='outside',
        ))
        fig.add_trace(go.Bar(
            name='Pass@10',
            x=models,
            y=pass_at_10,
            marker_color='#22C55E',
            text=[f"{v:.1%}" for v in pass_at_10],
            textposition='outside',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Model",
            yaxis_title="Pass Rate",
            yaxis=dict(range=[0, 1.1]),
            barmode='group',
            height=height,
        )
        return fig

    @staticmethod
    def accuracy_comparison(
        models: List[str],
        benchmarks: Dict[str, List[float]],
        title: str = "Accuracy by Benchmark",
        height: int = 400,
    ) -> go.Figure:
        """Grouped bar chart for accuracy across benchmarks."""
        fig = go.Figure()

        colors = ['#6366F1', '#A855F7', '#06B6D4', '#22C55E', '#F59E0B', '#EF4444']
        for i, (benchmark, scores) in enumerate(benchmarks.items()):
            fig.add_trace(go.Bar(
                name=benchmark,
                x=models,
                y=scores,
                marker_color=colors[i % len(colors)],
                text=[f"{v:.1%}" for v in scores],
                textposition='outside',
            ))

        fig.update_layout(
            title=title,
            xaxis_title="Model",
            yaxis_title="Accuracy",
            yaxis=dict(range=[0, 1.1]),
            barmode='group',
            height=height,
        )
        return fig

    @staticmethod
    def win_rate_matrix(
        models: List[str],
        win_rates: List[List[float]],
        title: str = "Win Rate Matrix",
        height: int = 500,
    ) -> go.Figure:
        """Heatmap of pairwise win rates."""
        fig = go.Figure()
        fig.add_trace(go.Heatmap(
            z=win_rates,
            x=models,
            y=models,
            colorscale='RdYlGn',
            zmin=0,
            zmax=1,
            text=[[f"{v:.1%}" for v in row] for row in win_rates],
            texttemplate="%{text}",
            textfont={"size": 12},
        ))
        fig.update_layout(
            title=title,
            height=height,
        )
        return fig

    @staticmethod
    def elo_trend(
        timestamps: List[float],
        elo_ratings: Dict[str, List[float]],
        title: str = "Elo Rating Trend",
        height: int = 400,
    ) -> go.Figure:
        """Elo rating trends over time."""
        fig = go.Figure()

        colors = ['#6366F1', '#A855F7', '#06B6D4', '#22C55E', '#F59E0B', '#EF4444']
        for i, (model, ratings) in enumerate(elo_ratings.items()):
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=ratings,
                mode='lines+markers',
                name=model,
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=8),
            ))

        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Elo Rating",
            height=height,
        )
        return fig

    @staticmethod
    def benchmark_scores_detail(
        model: str,
        categories: List[str],
        scores: List[float],
        title: str = None,
        height: int = 400,
    ) -> go.Figure:
        """Horizontal bar chart for detailed benchmark scores."""
        if title is None:
            title = f"Quality Scores: {model}"

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=scores,
            y=categories,
            orientation='h',
            marker_color=['#6366F1', '#A855F7', '#06B6D4', '#22C55E', '#F59E0B', '#EF4444'][:len(categories)],
            text=[f"{s:.1%}" for s in scores],
            textposition='outside',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Score",
            xaxis=dict(range=[0, 1.1]),
            height=height,
            yaxis=dict(autorange="reversed"),
        )
        return fig