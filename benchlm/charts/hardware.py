"""Hardware utilization charts for BenchLM."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any
import numpy as np


class HardwareCharts:
    """Chart generators for hardware utilization metrics."""

    @staticmethod
    def cpu_gpu_timeline(
        timestamps: List[float],
        cpu_util: List[float],
        gpu_util: List[float],
        title: str = "CPU/GPU Utilization",
        height: int = 400,
    ) -> go.Figure:
        """CPU and GPU utilization over time."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=cpu_util,
            mode='lines',
            name='CPU %',
            line=dict(color='#6366F1', width=2),
            fill='tozeroy',
            fillcolor='rgba(99, 102, 241, 0.1)',
        ))
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=gpu_util,
            mode='lines',
            name='GPU %',
            line=dict(color='#06B6D4', width=2),
            fill='tozeroy',
            fillcolor='rgba(6, 182, 212, 0.1)',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Utilization (%)",
            yaxis=dict(range=[0, 100]),
            height=height,
        )
        return fig

    @staticmethod
    def per_core_heatmap(
        core_data: List[List[float]],  # [time][core]
        title: str = "Per-Core CPU Utilization",
        height: int = 500,
    ) -> go.Figure:
        """Heatmap of per-core CPU utilization over time."""
        # Transpose for heatmap: cores on y-axis, time on x-axis
        n_cores = len(core_data[0]) if core_data else 0
        z = np.array(core_data).T.tolist()

        fig = go.Figure()
        fig.add_trace(go.Heatmap(
            z=z,
            x=list(range(len(core_data))),
            y=[f"Core {i}" for i in range(n_cores)],
            colorscale='Viridis',
            colorbar=dict(title="Util %"),
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Time Sample",
            yaxis_title="CPU Core",
            height=height,
        )
        return fig

    @staticmethod
    def gpu_occupancy(
        timestamps: List[float],
        compute_util: List[float],
        memory_util: List[float],
        encoder_util: List[float] = None,
        decoder_util: List[float] = None,
        title: str = "GPU Occupancy",
        height: int = 400,
    ) -> go.Figure:
        """GPU compute, memory, encoder, decoder utilization."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=compute_util,
            mode='lines',
            name='Compute',
            line=dict(color='#6366F1', width=2),
        ))
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=memory_util,
            mode='lines',
            name='Memory',
            line=dict(color='#06B6D4', width=2),
        ))
        if encoder_util:
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=encoder_util,
                mode='lines',
                name='Encoder',
                line=dict(color='#F59E0B', width=2, dash='dash'),
            ))
        if decoder_util:
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=decoder_util,
                mode='lines',
                name='Decoder',
                line=dict(color='#EF4444', width=2, dash='dash'),
            ))
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Utilization (%)",
            yaxis=dict(range=[0, 100]),
            height=height,
        )
        return fig

    @staticmethod
    def memory_bandwidth(
        timestamps: List[float],
        bandwidth_gb_s: List[float],
        title: str = "Memory Bandwidth",
        height: int = 400,
    ) -> go.Figure:
        """GPU memory bandwidth over time."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=bandwidth_gb_s,
            mode='lines',
            name='Bandwidth (GB/s)',
            line=dict(color='#A855F7', width=2),
            fill='tozeroy',
            fillcolor='rgba(168, 85, 247, 0.1)',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Bandwidth (GB/s)",
            height=height,
        )
        return fig

    @staticmethod
    def pcie_utilization(
        timestamps: List[float],
        pcie_throughput: List[float],
        title: str = "PCIe Throughput",
        height: int = 400,
    ) -> go.Figure:
        """PCIe throughput over time."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=pcie_throughput,
            mode='lines',
            name='PCIe Throughput (GB/s)',
            line=dict(color='#22C55E', width=2),
            fill='tozeroy',
            fillcolor='rgba(34, 197, 94, 0.1)',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Throughput (GB/s)",
            height=height,
        )
        return fig

    @staticmethod
    def clock_frequencies(
        timestamps: List[float],
        core_clocks: List[float],
        memory_clocks: List[float],
        title: str = "GPU Clock Frequencies",
        height: int = 400,
    ) -> go.Figure:
        """GPU core and memory clock frequencies."""
        from plotly.subplots import make_subplots

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=core_clocks,
                mode='lines',
                name='Core Clock (MHz)',
                line=dict(color='#6366F1', width=2),
            ),
            secondary_y=False,
        )

        fig.add_trace(
            go.Scatter(
                x=timestamps,
                y=memory_clocks,
                mode='lines',
                name='Memory Clock (MHz)',
                line=dict(color='#06B6D4', width=2, dash='dash'),
            ),
            secondary_y=True,
        )

        fig.update_xaxes(title_text="Time")
        fig.update_yaxes(title_text="Core Clock (MHz)", secondary_y=False)
        fig.update_yaxes(title_text="Memory Clock (MHz)", secondary_y=True)
        fig.update_layout(title=title, height=height)
        return fig

    @staticmethod
    def utilization_distribution(
        cpu_samples: List[float],
        gpu_samples: List[float],
        title: str = "Utilization Distribution",
        height: int = 400,
    ) -> go.Figure:
        """Histogram of CPU/GPU utilization."""
        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=cpu_samples,
            name='CPU',
            nbinsx=30,
            opacity=0.7,
            marker_color='#6366F1',
        ))
        fig.add_trace(go.Histogram(
            x=gpu_samples,
            name='GPU',
            nbinsx=30,
            opacity=0.7,
            marker_color='#06B6D4',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Utilization (%)",
            yaxis_title="Frequency",
            barmode='overlay',
            height=height,
        )
        return fig