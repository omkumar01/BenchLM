"""Latency charts for BenchLM."""

import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Any, Optional
import numpy as np


class LatencyCharts:
    """Chart generators for latency metrics."""

    @staticmethod
    def ttft_timeline(
        timestamps: List[float],
        ttft_values: List[float],
        title: str = "TTFT Over Time",
        height: int = 400,
    ) -> go.Figure:
        """TTFT line chart over time."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=ttft_values,
            mode='lines+markers',
            name='TTFT',
            line=dict(color='#6366F1', width=2),
            marker=dict(size=4),
            fill='tozeroy',
            fillcolor='rgba(99, 102, 241, 0.1)',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Request",
            yaxis_title="TTFT (ms)",
            height=height,
            hovermode='x unified',
        )
        return fig

    @staticmethod
    def latency_percentiles(
        percentiles: Dict[str, float],
        title: str = "Latency Percentiles",
        height: int = 400,
    ) -> go.Figure:
        """Bar chart of latency percentiles."""
        labels = list(percentiles.keys())
        values = list(percentiles.values())

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=labels,
            y=values,
            marker_color=['#6366F1', '#A855F7', '#06B6D4', '#F59E0B', '#EF4444', '#DC2626'],
            text=[f"{v:.1f}ms" for v in values],
            textposition='outside',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Percentile",
            yaxis_title="Latency (ms)",
            height=height,
            showlegend=False,
        )
        return fig

    @staticmethod
    def latency_histogram(
        latencies: List[float],
        bins: int = 50,
        title: str = "Latency Distribution",
        height: int = 400,
    ) -> go.Figure:
        """Histogram of latency values."""
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=latencies,
            nbinsx=bins,
            marker_color='#6366F1',
            opacity=0.7,
            name='Frequency',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Latency (ms)",
            yaxis_title="Count",
            height=height,
            bargap=0.1,
        )
        return fig

    @staticmethod
    def latency_cdf(
        latencies: List[float],
        title: str = "Latency CDF",
        height: int = 400,
    ) -> go.Figure:
        """Cumulative distribution function of latency."""
        sorted_latencies = sorted(latencies)
        y = np.arange(1, len(sorted_latencies) + 1) / len(sorted_latencies)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=sorted_latencies,
            y=y,
            mode='lines',
            name='CDF',
            line=dict(color='#6366F1', width=2),
            fill='tozeroy',
            fillcolor='rgba(99, 102, 241, 0.1)',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Latency (ms)",
            yaxis_title="Cumulative Probability",
            yaxis=dict(range=[0, 1.05]),
            height=height,
        )
        return fig

    @staticmethod
    def ttft_vs_tpot_scatter(
        ttft: List[float],
        tpot: List[float],
        title: str = "TTFT vs TPOT",
        height: int = 400,
    ) -> go.Figure:
        """Scatter plot of TTFT vs TPOT."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ttft,
            y=tpot,
            mode='markers',
            marker=dict(
                size=8,
                color='#6366F1',
                opacity=0.6,
                line=dict(width=0),
            ),
            name='Requests',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="TTFT (ms)",
            yaxis_title="TPOT (ms)",
            height=height,
        )
        return fig

    @staticmethod
    def latency_by_context(
        context_lengths: List[int],
        ttft_means: List[float],
        ttft_p99: List[float],
        title: str = "Latency vs Context Length",
        height: int = 400,
    ) -> go.Figure:
        """Latency vs context length."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=context_lengths,
            y=ttft_means,
            mode='lines+markers',
            name='Mean TTFT',
            line=dict(color='#6366F1', width=2),
        ))
        fig.add_trace(go.Scatter(
            x=context_lengths,
            y=ttft_p99,
            mode='lines+markers',
            name='P99 TTFT',
            line=dict(color='#EF4444', width=2, dash='dash'),
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Context Length (tokens)",
            yaxis_title="Latency (ms)",
            xaxis_type="log",
            height=height,
        )
        return fig

    @staticmethod
    def inter_token_latency(
        token_positions: List[int],
        latencies: List[float],
        title: str = "Inter-token Latency",
        height: int = 400,
    ) -> go.Figure:
        """Inter-token latency over generation."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=token_positions,
            y=latencies,
            mode='lines',
            name='Inter-token Latency',
            line=dict(color='#F59E0B', width=2),
            fill='tozeroy',
            fillcolor='rgba(245, 158, 11, 0.1)',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Token Position",
            yaxis_title="Latency (ms)",
            height=height,
        )
        return fig

    @staticmethod
    def prefill_decode_split(
        prefill_times: List[float],
        decode_times: List[float],
        title: str = "Prefill vs Decode Time",
        height: int = 400,
    ) -> go.Figure:
        """Stacked bar chart of prefill vs decode times."""
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Prefill',
            x=list(range(len(prefill_times))),
            y=prefill_times,
            marker_color='#6366F1',
        ))
        fig.add_trace(go.Bar(
            name='Decode',
            x=list(range(len(decode_times))),
            y=decode_times,
            marker_color='#A855F7',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Request",
            yaxis_title="Time (ms)",
            barmode='stack',
            height=height,
        )
        return fig