"""Memory charts for BenchLM."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any
import numpy as np


class MemoryCharts:
    """Chart generators for memory metrics."""

    @staticmethod
    def memory_timeline(
        timestamps: List[float],
        ram_used: List[float],
        vram_used: List[float],
        ram_total: float,
        vram_total: float,
        title: str = "Memory Usage Timeline",
        height: int = 400,
    ) -> go.Figure:
        """RAM and VRAM usage over time."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=ram_used,
            mode='lines',
            name='RAM Used (GB)',
            line=dict(color='#F59E0B', width=2),
            fill='tozeroy',
            fillcolor='rgba(245, 158, 11, 0.1)',
        ))
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=vram_used,
            mode='lines',
            name='VRAM Used (GB)',
            line=dict(color='#EF4444', width=2),
            fill='tozeroy',
            fillcolor='rgba(239, 68, 68, 0.1)',
        ))
        # Add total lines
        fig.add_hline(y=ram_total, line_dash="dash", line_color="#F59E0B", 
                     annotation_text=f"RAM Total: {ram_total:.1f}GB")
        fig.add_hline(y=vram_total, line_dash="dash", line_color="#EF4444",
                     annotation_text=f"VRAM Total: {vram_total:.1f}GB")
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Memory (GB)",
            height=height,
        )
        return fig

    @staticmethod
    def kv_cache_growth(
        timestamps: List[float],
        kv_cache_sizes: List[float],
        title: str = "KV Cache Growth",
        height: int = 400,
    ) -> go.Figure:
        """KV cache growth over time."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=kv_cache_sizes,
            mode='lines',
            name='KV Cache (MB)',
            line=dict(color='#A855F7', width=2),
            fill='tozeroy',
            fillcolor='rgba(168, 85, 247, 0.1)',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="KV Cache Size (MB)",
            height=height,
        )
        return fig

    @staticmethod
    def memory_breakdown_stacked(
        timestamps: List[float],
        components: Dict[str, List[float]],
        title: str = "Memory Breakdown",
        height: int = 400,
    ) -> go.Figure:
        """Stacked area chart of memory components."""
        fig = go.Figure()

        colors = ['#6366F1', '#A855F7', '#06B6D4', '#22C55E', '#F59E0B', '#EF4444']
        for i, (name, values) in enumerate(components.items()):
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=values,
                mode='lines',
                name=name,
                line=dict(color=colors[i % len(colors)], width=1),
                stackgroup='one',
                fillcolor=colors[i % len(colors)] + '40',
            ))

        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Memory (GB)",
            height=height,
        )
        return fig

    @staticmethod
    def memory_peak_usage(
        models: List[str],
        peak_vram: List[float],
        avg_vram: List[float],
        peak_ram: List[float],
        avg_ram: List[float],
        title: str = "Peak vs Average Memory Usage",
        height: int = 400,
    ) -> go.Figure:
        """Grouped bar chart of peak vs average memory."""
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Peak VRAM',
            x=models,
            y=peak_vram,
            marker_color='#EF4444',
        ))
        fig.add_trace(go.Bar(
            name='Avg VRAM',
            x=models,
            y=avg_vram,
            marker_color='#EF4444',
            opacity=0.5,
        ))
        fig.add_trace(go.Bar(
            name='Peak RAM',
            x=models,
            y=peak_ram,
            marker_color='#F59E0B',
        ))
        fig.add_trace(go.Bar(
            name='Avg RAM',
            x=models,
            y=avg_ram,
            marker_color='#F59E0B',
            opacity=0.5,
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Model",
            yaxis_title="Memory (GB)",
            barmode='group',
            height=height,
        )
        return fig

    @staticmethod
    def memory_efficiency(
        models: List[str],
        vram_efficiency: List[float],
        ram_efficiency: List[float],
        title: str = "Memory Efficiency (Avg/Peak)",
        height: int = 400,
    ) -> go.Figure:
        """Memory efficiency (average/peak ratio)."""
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='VRAM Efficiency',
            x=models,
            y=vram_efficiency,
            marker_color='#EF4444',
            text=[f"{v:.1%}" for v in vram_efficiency],
            textposition='outside',
        ))
        fig.add_trace(go.Bar(
            name='RAM Efficiency',
            x=models,
            y=ram_efficiency,
            marker_color='#F59E0B',
            text=[f"{v:.1%}" for v in ram_efficiency],
            textposition='outside',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Model",
            yaxis_title="Efficiency Ratio",
            yaxis=dict(range=[0, 1.1]),
            barmode='group',
            height=height,
        )
        return fig

    @staticmethod
    def context_vs_memory(
        context_lengths: List[int],
        vram_usage: List[float],
        ram_usage: List[float],
        title: str = "Context Length vs Memory",
        height: int = 400,
    ) -> go.Figure:
        """Memory usage vs context length."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=context_lengths,
            y=vram_usage,
            mode='lines+markers',
            name='VRAM',
            line=dict(color='#EF4444', width=2),
        ))
        fig.add_trace(go.Scatter(
            x=context_lengths,
            y=ram_usage,
            mode='lines+markers',
            name='RAM',
            line=dict(color='#F59E0B', width=2),
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Context Length",
            xaxis_type="log",
            yaxis_title="Memory (GB)",
            height=height,
        )
        return fig