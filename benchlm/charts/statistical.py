"""Statistical charts for BenchLM."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any
import numpy as np


class StatisticalCharts:
    """Chart generators for statistical analysis."""

    @staticmethod
    def box_plot(
        data: Dict[str, List[float]],
        title: str = "Box Plot Comparison",
        height: int = 400,
    ) -> go.Figure:
        """Box plot for multiple groups."""
        fig = go.Figure()
        for name, values in data.items():
            fig.add_trace(go.Box(
                y=values,
                name=name,
                boxpoints='outliers',
                marker_color='#6366F1',
            ))
        fig.update_layout(
            title=title,
            yaxis_title="Value",
            height=height,
        )
        return fig

    @staticmethod
    def violin_plot(
        data: Dict[str, List[float]],
        title: str = "Violin Plot Comparison",
        height: int = 400,
    ) -> go.Figure:
        """Violin plot for multiple groups."""
        fig = go.Figure()
        colors = ['#6366F1', '#A855F7', '#06B6D4', '#22C55E', '#F59E0B', '#EF4444']
        for i, (name, values) in enumerate(data.items()):
            fig.add_trace(go.Violin(
                y=values,
                name=name,
                box_visible=True,
                meanline_visible=True,
                fillcolor=colors[i % len(colors)],
                opacity=0.6,
            ))
        fig.update_layout(
            title=title,
            yaxis_title="Value",
            height=height,
        )
        return fig

    @staticmethod
    def histogram_comparison(
        data: Dict[str, List[float]],
        bins: int = 30,
        title: str = "Histogram Comparison",
        height: int = 400,
    ) -> go.Figure:
        """Overlay histograms for multiple groups."""
        fig = go.Figure()
        colors = ['#6366F1', '#A855F7', '#06B6D4', '#22C55E', '#F59E0B', '#EF4444']
        for i, (name, values) in enumerate(data.items()):
            fig.add_trace(go.Histogram(
                x=values,
                name=name,
                nbinsx=bins,
                opacity=0.6,
                marker_color=colors[i % len(colors)],
            ))
        fig.update_layout(
            title=title,
            xaxis_title="Value",
            yaxis_title="Count",
            barmode='overlay',
            height=height,
        )
        return fig

    @staticmethod
    def density_plot(
        data: Dict[str, List[float]],
        title: str = "Density Plot",
        height: int = 400,
    ) -> go.Figure:
        """Kernel density estimation plot."""
        from scipy.stats import gaussian_kde

        fig = go.Figure()
        colors = ['#6366F1', '#A855F7', '#06B6D4', '#22C55E', '#F59E0B', '#EF4444']

        for i, (name, values) in enumerate(data.items()):
            if len(values) < 2:
                continue
            kde = gaussian_kde(values)
            x_range = np.linspace(min(values), max(values), 200)
            y = kde(x_range)
            fig.add_trace(go.Scatter(
                x=x_range,
                y=y,
                mode='lines',
                name=name,
                line=dict(color=colors[i % len(colors)], width=2),
                fill='tozeroy',
                fillcolor=colors[i % len(colors)] + '20',
            ))

        fig.update_layout(
            title=title,
            xaxis_title="Value",
            yaxis_title="Density",
            height=height,
        )
        return fig

    @staticmethod
    def heatmap(
        matrix: List[List[float]],
        x_labels: List[str],
        y_labels: List[str],
        title: str = "Heatmap",
        colorscale: str = "RdYlGn",
        height: int = 500,
    ) -> go.Figure:
        """Heatmap visualization."""
        fig = go.Figure()
        fig.add_trace(go.Heatmap(
            z=matrix,
            x=x_labels,
            y=y_labels,
            colorscale=colorscale,
            text=[[f"{v:.3f}" for v in row] for row in matrix],
            texttemplate="%{text}",
            textfont={"size": 10},
            colorbar=dict(title="Value"),
        ))
        fig.update_layout(
            title=title,
            height=height,
        )
        return fig

    @staticmethod
    def correlation_matrix(
        corr_matrix: List[List[float]],
        labels: List[str],
        title: str = "Correlation Matrix",
        height: int = 500,
    ) -> go.Figure:
        """Correlation matrix heatmap."""
        fig = go.Figure()
        fig.add_trace(go.Heatmap(
            z=corr_matrix,
            x=labels,
            y=labels,
            colorscale='RdBu',
            zmid=0,
            zmin=-1,
            zmax=1,
            text=[[f"{v:.2f}" for v in row] for row in corr_matrix],
            texttemplate="%{text}",
            colorbar=dict(title="Correlation"),
        ))
        fig.update_layout(
            title=title,
            height=height,
        )
        return fig

    @staticmethod
    def scatter_matrix(
        data: Dict[str, List[float]],
        title: str = "Scatter Matrix",
        height: int = 800,
    ) -> go.Figure:
        """Scatter plot matrix (pair plot)."""
        keys = list(data.keys())
        n = len(keys)

        fig = make_subplots(
            rows=n, cols=n,
            subplot_titles=[f"{keys[j]} vs {keys[i]}" for i in range(n) for j in range(n)],
            shared_xaxes=False, shared_yaxes=False,
        )

        for i, key_i in enumerate(keys):
            for j, key_j in enumerate(keys):
                row = i + 1
                col = j + 1

                if i == j:
                    # Diagonal: histogram
                    fig.add_trace(go.Histogram(
                        x=data[key_i],
                        name=key_i,
                        marker_color='#6366F1',
                        showlegend=False,
                    ), row=row, col=col)
                else:
                    # Off-diagonal: scatter
                    fig.add_trace(go.Scatter(
                        x=data[key_j],
                        y=data[key_i],
                        mode='markers',
                        marker=dict(color='#6366F1', size=4, opacity=0.5),
                        showlegend=False,
                    ), row=row, col=col)

        fig.update_layout(
            title=title,
            height=height,
            showlegend=False,
        )
        return fig

    @staticmethod
    def error_bars(
        categories: List[str],
        means: List[float],
        std_devs: List[float],
        title: str = "Means with Error Bars",
        height: int = 400,
    ) -> go.Figure:
        """Bar chart with error bars."""
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=categories,
            y=means,
            error_y=dict(
                type='data',
                array=std_devs,
                visible=True,
                color='black',
                thickness=1.5,
                width=5,
            ),
            marker_color='#6366F1',
            name='Mean ± Std Dev',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Category",
            yaxis_title="Value",
            height=height,
        )
        return fig

    @staticmethod
    def confidence_intervals(
        categories: List[str],
        means: List[float],
        ci_lower: List[float],
        ci_upper: List[float],
        title: str = "Confidence Intervals",
        height: int = 400,
    ) -> go.Figure:
        """Plot means with confidence intervals."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=categories,
            y=means,
            mode='markers',
            marker=dict(size=12, color='#6366F1'),
            name='Mean',
        ))
        fig.add_trace(go.Scatter(
            x=categories + categories[::-1],
            y=ci_upper + ci_lower[::-1],
            fill='toself',
            fillcolor='rgba(99, 102, 241, 0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            name='95% CI',
            showlegend=True,
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Category",
            yaxis_title="Value",
            height=height,
        )
        return fig