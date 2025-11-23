"""
Módulo para generar visualizaciones interactivas con Plotly.
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import base64
import io
import json


class DataVisualizer:
    """Clase para generar visualizaciones de datos"""

    @staticmethod
    def plot_timeseries(df, title="Serie de Tiempo"):
        """
        Genera gráfico de serie de tiempo con sensores y RMCAB

        Args:
            df: DataFrame con datos
            title: Título del gráfico

        Returns:
            JSON de Plotly
        """
        fig = go.Figure()

        # Agregar sensores
        for sensor in ['Aire2', 'Aire4', 'Aire5']:
            if sensor in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['datetime'],
                    y=df[sensor],
                    mode='lines',
                    name=sensor,
                    line=dict(width=1.5),
                    opacity=0.8
                ))

        # Agregar RMCAB
        if 'PM25' in df.columns:
            fig.add_trace(go.Scatter(
                x=df['datetime'],
                y=df['PM25'],
                mode='lines',
                name='RMCAB (Referencia)',
                line=dict(color='black', width=2.5, dash='solid')
            ))

        fig.update_layout(
            title=title,
            xaxis_title='Fecha',
            yaxis_title='PM2.5 (μg/m³)',
            hovermode='x unified',
            template='plotly_white',
            height=400,
            margin=dict(l=50, r=50, t=50, b=50)
        )

        return fig.to_json()

    @staticmethod
    def plot_scatter(df, sensor_name, title=None):
        """
        Genera scatter plot: Sensor vs RMCAB

        Args:
            df: DataFrame con datos
            sensor_name: Nombre del sensor
            title: Título del gráfico

        Returns:
            JSON de Plotly
        """
        if title is None:
            title = f'{sensor_name} vs RMCAB'

        # Remover NaNs
        clean_df = df[[sensor_name, 'PM25']].dropna()

        if len(clean_df) == 0:
            return None

        # Crear scatter
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=clean_df['PM25'],
            y=clean_df[sensor_name],
            mode='markers',
            marker=dict(
                size=6,
                color=clean_df['PM25'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title='RMCAB PM2.5')
            ),
            text=[f'RMCAB: {r:.1f}<br>{sensor_name}: {s:.1f}'
                  for r, s in zip(clean_df['PM25'], clean_df[sensor_name])],
            hovertemplate='<b>%{text}</b><extra></extra>',
            name=sensor_name
        ))

        # Agregar línea diagonal (y=x)
        min_val = min(clean_df['PM25'].min(), clean_df[sensor_name].min())
        max_val = max(clean_df['PM25'].max(), clean_df[sensor_name].max())

        fig.add_trace(go.Scatter(
            x=[min_val, max_val],
            y=[min_val, max_val],
            mode='lines',
            name='Línea Perfecta (y=x)',
            line=dict(color='red', dash='dash', width=2)
        ))

        fig.update_layout(
            title=title,
            xaxis_title='RMCAB PM2.5 (μg/m³)',
            yaxis_title=f'{sensor_name} PM2.5 (μg/m³)',
            hovermode='closest',
            template='plotly_white',
            height=400,
            showlegend=True,
            margin=dict(l=50, r=50, t=50, b=50)
        )

        # Hacer que los ejes sean iguales
        fig.update_xaxes(scaleanchor="y", scaleratio=1)
        fig.update_yaxes(scaleanchor="x", scaleratio=1)

        return fig.to_json()

    @staticmethod
    def plot_sensor_comparison(df, title="Comparación de Sensores Individuales"):
        """
        Genera gráficos individuales de cada sensor vs RMCAB

        Args:
            df: DataFrame con datos
            title: Título general

        Returns:
            dict con gráficos JSON
        """
        graphs = {}
        sensors = ['Aire2', 'Aire4', 'Aire5']

        for sensor in sensors:
            if sensor in df.columns:
                graph_json = DataVisualizer.plot_scatter(df, sensor, f'{sensor} vs RMCAB')
                if graph_json:
                    graphs[sensor] = graph_json

        return graphs

    @staticmethod
    def create_metrics_table(results):
        """
        Crea tabla HTML con resultados de calibración

        Args:
            results: dict con resultados de calibración

        Returns:
            HTML string
        """
        html = '<div class="table-responsive"><table class="table table-sm table-hover">'
        html += '<thead class="table-light"><tr>'
        html += '<th>Sensor</th><th>Modelo</th><th>R²</th><th>RMSE</th><th>MAE</th><th>MAPE (%)</th>'
        html += '</tr></thead><tbody>'

        for sensor, models in results.items():
            if models is None:
                continue

            first_row = True
            for model_name, metrics in models.items():
                if metrics.get('error'):
                    continue

                row_class = 'table-light' if first_row else ''
                html += f'<tr class="{row_class}">'

                if first_row:
                    html += f'<td rowspan="{len([m for m in models.items() if not m[1].get("error")])}">'
                    html += f'<strong>{sensor}</strong></td>'
                    first_row = False

                html += f'<td>{model_name}</td>'
                html += f'<td>{metrics.get("r2", "-")}</td>'
                html += f'<td>{metrics.get("rmse", "-")}</td>'
                html += f'<td>{metrics.get("mae", "-")}</td>'
                html += f'<td>{metrics.get("mape", "-")}</td>'
                html += '</tr>'

        html += '</tbody></table></div>'
        return html

    @staticmethod
    def create_degradation_summary(degradation_data):
        """
        Crea resumen visual de degradación

        Args:
            degradation_data: dict con datos de degradación

        Returns:
            JSON de gráfico Plotly
        """
        sensors = list(degradation_data.keys())
        raw_r2 = [degradation_data[s]['raw_r2'] for s in sensors]
        cal_r2 = [degradation_data[s]['calibrated_r2'] for s in sensors]

        fig = go.Figure(data=[
            go.Bar(name='R² Crudo (Sin Calibración)', x=sensors, y=raw_r2),
            go.Bar(name='R² Calibrado', x=sensors, y=cal_r2)
        ])

        fig.update_layout(
            title='Mejora con Calibración',
            barmode='group',
            xaxis_title='Sensor',
            yaxis_title='R² Score',
            template='plotly_white',
            height=350,
            margin=dict(l=50, r=50, t=50, b=50)
        )

        return fig.to_json()
