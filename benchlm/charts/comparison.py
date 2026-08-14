"""Comparison charts for BenchLM."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any
import numpy as np


class ComparisonCharts:
    """Chart generators for model comparison."""

    @staticmethod
    def leaderboard_table(
        models: List[str],
        scores: List[float],
        grades: List[str],
        metrics: Dict[str, List[float]],
        title: str = "Leaderboard",
        height: int = 500,
    ) -> go.Figure:
        """Leaderboard table with scores and metrics."""
        fig = go.Figure()
        fig.add_trace(go.Table(
            header=dict(
                values=['Rank', 'Model', 'Score', 'Grade'] + list(metrics.keys()),
                fill_color='#18181B',
                font=dict(color='#FAFAFA', size=12),
                align='center',
            ),
            cells=dict(
                values=[
                    list(range(1, len(models) + 1)),
                    models,
                    [f"{s:.0f}" for s in scores],
                    grades,
                ] + [metrics[k] for k in metrics.keys()],
                fill_color='#09090B',
                font=dict(color='#FAFAFA', size=11),
                align='center',
            ),
        ))
        fig.update_layout(title=title, height=height)
        return fig

    @staticmethod
    def speed_quality_scatter(
        models: List[str],
        ttft: List[float],
        quality: List[float],
        tps: List[float],
        sizes: List[float] = None,
        title: str = "Speed vs Quality",
        height: int = 500,
    ) -> go.Figure:
        """Bubble chart: TTFT vs Quality (bubble size = TPS)."""
        if sizes is None:
            sizes = tps

        fig = go.Figure()
        for i, model in enumerate(models):
            fig.add_trace(go.Scatter(
                x=[ttft[i]],
                y=[quality[i]],
                mode='markers+text',
                name=model,
                text=[model],
                textposition='top center',
                marker=dict(
                    size=max(10, sizes[i] / 2),
                    color='#6366F1',
                    opacity=0.8,
                    line=dict(width=2, color='white'),
                ),
            ))

        fig.update_layout(
            title=title,
            xaxis_title="TTFT (ms, lower is better)",
            xaxis=dict(autorange="reversed"),
            yaxis_title="Quality Score (%)",
            height=height,
            showlegend=False,
        )
        return fig

    @staticmethod
    def pareto_frontier(
        models: List[str],
        x_metric: List[float],  # Lower is better (e.g., latency)
        y_metric: List[float],  # Higher is better (e.g., quality)
        x_label: str = "Latency (ms)",
        y_label: str = "Quality (%)",
        title: str = "Pareto Frontier",
        height: int = 500,
    ) -> go.Figure:
        """Pareto frontier visualization."""
        # Find Pareto optimal points
        points = list(zip(models, x_metric, y_metric))
        points.sort(key=lambda p: p[1])  # Sort by x (ascending)

        pareto = []
        best_y = -1
        for model, x, y in points:
            if y > best_y:
                pareto.append((model, x, y))
                best_y = y

        fig = go.Figure()

        # All points
        fig.add_trace(go.Scatter(
            x=x_metric,
            y=y_metric,
            mode='markers+text',
            text=models,
            textposition='top center',
            marker=dict(size=12, color='#6366F1', opacity=0.6),
            name='All Models',
        ))

        # Pareto frontier
        if pareto:
            pareto_models, pareto_x, pareto_y = zip(*pareto)
            fig.add_trace(go.Scatter(
                x=pareto_x,
                y=pareto_y,
                mode='lines+markers',
                line=dict(color='#22C55E', width=3, dash='dash'),
                marker=dict(size=14, color='#22C55E', symbol='star'),
                name='Pareto Frontier',
            ))

        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            xaxis=dict(autorange="reversed"),
            yaxis_title=y_label,
            height=height,
        )
        return fig

    @staticmethod
    def model_size_performance(
        models: List[str],
        param_counts: List[float],  # In billions
        scores: List[float],
        title: str = "Model Size vs Performance",
        height: int = 500,
    ) -> go.Figure:
        """Model parameter count vs performance."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=param_counts,
            y=scores,
            mode='markers+text',
            text=models,
            textposition='top center',
            marker=dict(
                size=[max(10, p * 2) for p in param_counts],
                color='#A855F7',
                opacity=0.8,
            ),
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Parameters (B)",
            yaxis_title="Score",
            height=height,
            showlegend=False,
        )
        return fig

    @staticmethod
    def quantization_comparison(
        models: List[str],
        quantizations: List[str],
        scores: List[float],
        title: str = "Quantization Impact",
        height: int = 500,
    ) -> go.Figure:
        """Grouped bar chart for quantization comparison."""
        # Group by base model
        base_models = list(set('_'.join(m.split('_')[:-1]) for m in models))

        fig = go.Figure()
        colors = ['#6366F1', '#A855F7', '#06B6D4', '#22C55E', '#F59E0B', '#EF4444']

        for i, base in enumerate(base_models):
            # Filter models for this base
            indices = [j for j, m in enumerate(models) if m.startswith(base)]
            if not indices:
                continue

            model_names = [models[j].split('_')[-1] for j in indices]
            model_scores = [scores[j] for j in indices]

            fig.add_trace(go.Bar(
                name=base,
                x=model_names,
                y=model_scores,
                marker_color=colors[i % len(colors)],
            ))

        fig.update_layout(
            title=title,
            xaxis_title="Quantization",
            yaxis_title="Score",
            barmode='group',
            height=height,
        )
        return fig

    @staticmethod
    def radar_comparison(
        models: List[str],
        categories: List[str],
        scores: Dict[str, List[float]],
        title: str = "Multi-Model Radar",
        height: int = 500,
    ) -> go.Figure:
        """Radar chart for multi-model comparison."""
        fig = go.Figure()

        colors = ['#6366F1', '#A855F7', '#06B6D4', '#22C55E', '#F59E0B', '#EF4444']
        for i, model in enumerate(models):
            model_scores = scores.get(model, [0] * len(categories))
            fig.add_trace(go.Scatterpolar(
                r=model_scores + [model_scores[0]],
                theta=categories + [categories[0]],
                fill='toself',
                name=model,
                line=dict(color=colors[i % len(colors)], width=2),
                fillcolor=colors[i % len(colors)] + '30',
            ))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            title=title,
            height=height,
        )
        return fig

    @staticmethod
    def diff_view(
        base_model: str,
        compare_model: str,
        metrics: Dict[str, float],
        diffs: Dict[str, float],
        title: str = None,
        height: int = 400,
    ) -> go.Figure:
        """Difference view between two models."""
        if title is None:
            title = f"Diff: {compare_model} vs {base_model}"

        categories = list(metrics.keys())
        base_values = [metrics[k] for k in categories]
        compare_values = [metrics[k] + diffs.get(k, 0) for k in categories]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name=base_model,
            x=categories,
            y=base_values,
            marker_color='#6366F1',
        ))
        fig.add_trace(go.Bar(
            name=compare_model,
            x=categories,
            y=compare_values,
            marker_color='#A855F7',
        ))

        fig.update_layout(
            title=title,
            xaxis_title="Metric",
            yaxis_title="Value",
            barmode='group',
            height=height,
        )
        return fig