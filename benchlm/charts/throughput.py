"""Throughput charts for BenchLM."""

import plotly.graph_objects as go
from typing import List, Dict, Any
import numpy as np


class ThroughputCharts:
    """Chart generators for throughput metrics."""

    @staticmethod
    def tps_timeline(
        timestamps: List[float],
        tps_values: List[float],
        title: str = "Tokens/Second Over Time",
        height: int = 400,
    ) -> go.Figure:
        """TPS line chart over time."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=tps_values,
            mode='lines',
            name='TPS',
            line=dict(color='#22C55E', width=2),
            fill='tozeroy',
            fillcolor='rgba(34, 197, 94, 0.1)',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Tokens/Second",
            height=height,
            hovermode='x unified',
        )
        return fig

    @staticmethod
    def throughput_comparison(
        models: List[str],
        output_tps: List[float],
        input_tps: List[float],
        total_tps: List[float],
        title: str = "Throughput Comparison",
        height: int = 400,
    ) -> go.Figure:
        """Grouped bar chart comparing throughput across models."""
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Output TPS',
            x=models,
            y=output_tps,
            marker_color='#22C55E',
            text=[f"{v:.1f}" for v in output_tps],
            textposition='outside',
        ))
        fig.add_trace(go.Bar(
            name='Input TPS',
            x=models,
            y=input_tps,
            marker_color='#06B6D4',
            text=[f"{v:.1f}" for v in input_tps],
            textposition='outside',
        ))
        fig.add_trace(go.Bar(
            name='Total TPS',
            x=models,
            y=total_tps,
            marker_color='#6366F1',
            text=[f"{v:.1f}" for v in total_tps],
            textposition='outside',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Model",
            yaxis_title="TPS",
            barmode='group',
            height=height,
        )
        return fig

    @staticmethod
    def batch_throughput(
        batch_sizes: List[int],
        throughputs: List[float],
        title: str = "Batch Size vs Throughput",
        height: int = 400,
    ) -> go.Figure:
        """Throughput vs batch size."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=batch_sizes,
            y=throughputs,
            mode='lines+markers',
            name='Throughput',
            line=dict(color='#22C55E', width=3),
            marker=dict(size=10),
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Batch Size",
            yaxis_title="Throughput (TPS)",
            height=height,
        )
        return fig

    @staticmethod
    def concurrent_throughput(
        concurrent_users: List[int],
        throughputs: List[float],
        latencies: List[float],
        title: str = "Concurrency vs Throughput/Latency",
        height: int = 400,
    ) -> go.Figure:
        """Dual-axis chart for concurrency scaling."""
        from plotly.subplots import make_subplots

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=concurrent_users,
                y=throughputs,
                mode='lines+markers',
                name='Throughput (TPS)',
                line=dict(color='#22C55E', width=3),
                marker=dict(size=10),
            ),
            secondary_y=False,
        )

        fig.add_trace(
            go.Scatter(
                x=concurrent_users,
                y=latencies,
                mode='lines+markers',
                name='Latency (ms)',
                line=dict(color='#EF4444', width=3, dash='dash'),
                marker=dict(size=10, symbol='diamond'),
            ),
            secondary_y=True,
        )

        fig.update_xaxes(title_text="Concurrent Users")
        fig.update_yaxes(title_text="Throughput (TPS)", secondary_y=False)
        fig.update_yaxes(title_text="Latency (ms)", secondary_y=True)

        fig.update_layout(title=title, height=height)
        return fig

    @staticmethod
    def throughput_efficiency(
        batch_sizes: List[int],
        efficiency: List[float],
        title: str = "Batch Efficiency",
        height: int = 400,
    ) -> go.Figure:
        """Batch efficiency (TPS per request in batch)."""
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=[str(b) for b in batch_sizes],
            y=efficiency,
            marker_color='#06B6D4',
            text=[f"{v:.1%}" for v in efficiency],
            textposition='outside',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Batch Size",
            yaxis_title="Efficiency",
            yaxis=dict(range=[0, 1.1]),
            height=height,
        )
        return fig

    @staticmethod
    def rps_qpm(
        timestamps: List[float],
        rps: List[float],
        qpm: List[float],
        title: str = "Requests/Second and Queries/Minute",
        height: int = 400,
    ) -> go.Figure:
        """RPS and QPM over time."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=rps,
            mode='lines',
            name='RPS',
            line=dict(color='#6366F1', width=2),
        ))
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=qpm,
            mode='lines',
            name='QPM',
            line=dict(color='#A855F7', width=2, dash='dash'),
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Rate",
            height=height,
        )
        return fig