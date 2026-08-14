"""Thermal and power charts for BenchLM."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any
import numpy as np


class ThermalCharts:
    """Chart generators for thermal and power metrics."""

    @staticmethod
    def temperature_timeline(
        timestamps: List[float],
        gpu_temp: List[float],
        cpu_temp: List[float],
        gpu_hotspot: List[float] = None,
        vram_temp: List[float] = None,
        title: str = "Temperature Timeline",
        height: int = 400,
    ) -> go.Figure:
        """Temperature over time."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=gpu_temp,
            mode='lines',
            name='GPU Core',
            line=dict(color='#EF4444', width=2),
            fill='tozeroy',
            fillcolor='rgba(239, 68, 68, 0.1)',
        ))
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=cpu_temp,
            mode='lines',
            name='CPU Package',
            line=dict(color='#F59E0B', width=2),
            fill='tozeroy',
            fillcolor='rgba(245, 158, 11, 0.1)',
        ))
        if gpu_hotspot:
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=gpu_hotspot,
                mode='lines',
                name='GPU Hotspot',
                line=dict(color='#DC2626', width=2, dash='dash'),
            ))
        if vram_temp:
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=vram_temp,
                mode='lines',
                name='VRAM',
                line=dict(color='#F97316', width=2, dash='dash'),
            ))

        # Add thermal throttle line
        fig.add_hline(y=83, line_dash="dot", line_color="red",
                     annotation_text="Throttle Threshold (83°C)")

        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Temperature (°C)",
            height=height,
        )
        return fig

    @staticmethod
    def power_timeline(
        timestamps: List[float],
        gpu_power: List[float],
        cpu_power: List[float],
        total_power: List[float] = None,
        title: str = "Power Consumption",
        height: int = 400,
    ) -> go.Figure:
        """Power consumption over time."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=gpu_power,
            mode='lines',
            name='GPU Power (W)',
            line=dict(color='#EF4444', width=2),
            fill='tozeroy',
            fillcolor='rgba(239, 68, 68, 0.1)',
        ))
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=cpu_power,
            mode='lines',
            name='CPU Power (W)',
            line=dict(color='#F59E0B', width=2),
            fill='tozeroy',
            fillcolor='rgba(245, 158, 11, 0.1)',
        ))
        if total_power:
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=total_power,
                mode='lines',
                name='Total Power (W)',
                line=dict(color='#6366F1', width=3),
            ))
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Power (W)",
            height=height,
        )
        return fig

    @staticmethod
    def energy_per_token(
        timestamps: List[float],
        energy_per_token: List[float],
        title: str = "Energy per Token",
        height: int = 400,
    ) -> go.Figure:
        """Energy per token over time."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=energy_per_token,
            mode='lines',
            name='J/token',
            line=dict(color='#A855F7', width=2),
            fill='tozeroy',
            fillcolor='rgba(168, 85, 247, 0.1)',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Energy (J/token)",
            height=height,
        )
        return fig

    @staticmethod
    def perf_per_watt(
        timestamps: List[float],
        perf_per_watt: List[float],
        title: str = "Performance per Watt",
        height: int = 400,
    ) -> go.Figure:
        """Tokens per Joule over time."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=perf_per_watt,
            mode='lines',
            name='tok/J',
            line=dict(color='#22C55E', width=2),
            fill='tozeroy',
            fillcolor='rgba(34, 197, 94, 0.1)',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Tokens/Joule",
            height=height,
        )
        return fig

    @staticmethod
    def thermal_throttling_timeline(
        timestamps: List[float],
        throttled: List[bool],
        temperature: List[float],
        title: str = "Thermal Throttling Events",
        height: int = 400,
    ) -> go.Figure:
        """Thermal throttling timeline."""
        fig = go.Figure()

        # Temperature
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=temperature,
            mode='lines',
            name='Temperature',
            line=dict(color='#EF4444', width=2),
        ))

        # Throttling events as shaded regions
        in_throttle = False
        start_idx = 0
        for i, (t, th) in enumerate(zip(timestamps, throttled)):
            if th and not in_throttle:
                in_throttle = True
                start_idx = i
            elif not th and in_throttle:
                in_throttle = False
                fig.add_vrect(
                    x0=timestamps[start_idx],
                    x1=t,
                    fillcolor="rgba(239, 68, 68, 0.3)",
                    layer="below",
                    line_width=0,
                )

        if in_throttle:
            fig.add_vrect(
                x0=timestamps[start_idx],
                x1=timestamps[-1],
                fillcolor="rgba(239, 68, 68, 0.3)",
                layer="below",
                line_width=0,
            )

        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Temperature (°C)",
            height=height,
        )
        return fig

    @staticmethod
    def fan_speed_timeline(
        timestamps: List[float],
        fan_speed: List[float],
        title: str = "Fan Speed",
        height: int = 400,
    ) -> go.Figure:
        """Fan speed over time."""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=fan_speed,
            mode='lines',
            name='Fan Speed (%)',
            line=dict(color='#06B6D4', width=2),
            fill='tozeroy',
            fillcolor='rgba(6, 182, 212, 0.1)',
        ))
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Fan Speed (%)",
            yaxis=dict(range=[0, 100]),
            height=height,
        )
        return fig

    @staticmethod
    def thermal_power_combined(
        timestamps: List[float],
        gpu_temp: List[float],
        cpu_temp: List[float],
        gpu_power: List[float],
        cpu_power: List[float],
        title: str = "Thermal & Power",
        height: int = 600,
    ) -> go.Figure:
        """Combined thermal and power chart with dual axes."""
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=("Temperature (°C)", "Power (W)"),
        )

        # Temperature
        fig.add_trace(go.Scatter(
            x=timestamps, y=gpu_temp,
            mode='lines', name='GPU Temp',
            line=dict(color='#EF4444', width=2),
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=timestamps, y=cpu_temp,
            mode='lines', name='CPU Temp',
            line=dict(color='#F59E0B', width=2),
        ), row=1, col=1)

        # Power
        fig.add_trace(go.Scatter(
            x=timestamps, y=gpu_power,
            mode='lines', name='GPU Power',
            line=dict(color='#EF4444', width=2, dash='dash'),
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=timestamps, y=cpu_power,
            mode='lines', name='CPU Power',
            line=dict(color='#F59E0B', width=2, dash='dash'),
        ), row=2, col=1)

        fig.update_layout(title=title, height=height)
        fig.update_yaxes(title_text="°C", row=1, col=1)
        fig.update_yaxes(title_text="W", row=2, col=1)
        fig.update_xaxes(title_text="Time", row=2, col=1)
        return fig