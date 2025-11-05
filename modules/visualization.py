"""
Módulo para crear visualizaciones de datos de calidad del aire
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np


# Colores del proyecto
COLORS = {
    'primary_green': '#2d5016',
    'primary_green_light': '#4a7c2c',
    'secondary_blue': '#0077b6',
    'secondary_blue_light': '#00b4d8',
    'accent_teal': '#14b8a6',
    'accent_lime': '#84cc16'
}

# Límites normativos
LIMITS = {
    'pm25': {
        'OMS_2021': 15,
        'Colombia': 25
    },
    'pm10': {
        'OMS_2021': 45,
        'Colombia': 50
    }
}


def create_timeseries_plot(df, pollutant='pm25', title=None):
    """
    Crea gráfico de series de tiempo

    Args:
        df: DataFrame con columnas datetime y contaminante
        pollutant: 'pm25' o 'pm10'
        title: Título del gráfico (opcional)

    Returns:
        plotly.graph_objects.Figure
    """
    if df is None or df.empty:
        # Gráfico vacío
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        return fig

    fig = go.Figure()

    # Si hay múltiples dispositivos/estaciones
    if 'device_name' in df.columns:
        for device in df['device_name'].unique():
            device_data = df[df['device_name'] == device]
            fig.add_trace(go.Scatter(
                x=device_data['datetime'],
                y=device_data[pollutant],
                mode='lines',
                name=device,
                line=dict(width=2)
            ))
    elif 'station' in df.columns:
        for station in df['station'].unique():
            station_data = df[df['station'] == station]
            fig.add_trace(go.Scatter(
                x=station_data['datetime'],
                y=station_data[pollutant],
                mode='lines',
                name=station,
                line=dict(width=2)
            ))
    else:
        fig.add_trace(go.Scatter(
            x=df['datetime'],
            y=df[pollutant],
            mode='lines',
            name=pollutant.upper(),
            line=dict(width=2, color=COLORS['primary_green'])
        ))

    # Agregar límites normativos
    if pollutant in LIMITS:
        # Límite OMS
        fig.add_hline(
            y=LIMITS[pollutant]['OMS_2021'],
            line_dash="dash",
            line_color="orange",
            annotation_text="OMS 2021",
            annotation_position="right"
        )

        # Límite Colombia
        fig.add_hline(
            y=LIMITS[pollutant]['Colombia'],
            line_dash="dash",
            line_color="red",
            annotation_text="Colombia",
            annotation_position="right"
        )

    # Layout
    if not title:
        title = f"Serie de Tiempo - {pollutant.upper()}"

    fig.update_layout(
        title=title,
        xaxis_title="Fecha y Hora",
        yaxis_title=f"Concentración (µg/m³)",
        hovermode='x unified',
        template='plotly_white',
        height=500,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig


def create_boxplot(df, pollutant='pm25', title=None):
    """
    Crea diagrama de caja

    Args:
        df: DataFrame con datos
        pollutant: 'pm25' o 'pm10'
        title: Título del gráfico (opcional)

    Returns:
        plotly.graph_objects.Figure
    """
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        return fig

    fig = go.Figure()

    # Agrupar por dispositivo/estación
    if 'device_name' in df.columns:
        group_col = 'device_name'
    elif 'station' in df.columns:
        group_col = 'station'
    else:
        group_col = None

    if group_col:
        for group in df[group_col].unique():
            group_data = df[df[group_col] == group]
            fig.add_trace(go.Box(
                y=group_data[pollutant],
                name=group,
                boxmean='sd'
            ))
    else:
        fig.add_trace(go.Box(
            y=df[pollutant],
            name=pollutant.upper(),
            boxmean='sd'
        ))

    # Agregar límites normativos
    if pollutant in LIMITS:
        fig.add_hline(
            y=LIMITS[pollutant]['OMS_2021'],
            line_dash="dash",
            line_color="orange",
            annotation_text="OMS 2021"
        )
        fig.add_hline(
            y=LIMITS[pollutant]['Colombia'],
            line_dash="dash",
            line_color="red",
            annotation_text="Colombia"
        )

    if not title:
        title = f"Distribución de {pollutant.upper()}"

    fig.update_layout(
        title=title,
        yaxis_title=f"Concentración (µg/m³)",
        template='plotly_white',
        height=500
    )

    return fig


def create_heatmap(df, pollutant='pm25', title=None):
    """
    Crea mapa de calor por hora del día

    Args:
        df: DataFrame con columna datetime
        pollutant: 'pm25' o 'pm10'
        title: Título del gráfico (opcional)

    Returns:
        plotly.graph_objects.Figure
    """
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        return fig

    # Extraer hora y día de la semana
    df = df.copy()
    df['hour'] = pd.to_datetime(df['datetime']).dt.hour
    df['day_name'] = pd.to_datetime(df['datetime']).dt.day_name()

    # Ordenar días de la semana
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_labels = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

    # Pivot table
    pivot = df.pivot_table(
        values=pollutant,
        index='day_name',
        columns='hour',
        aggfunc='mean'
    )

    # Reordenar días
    pivot = pivot.reindex(day_order)

    # Crear heatmap
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=list(range(24)),
        y=day_labels,
        colorscale='YlOrRd',
        colorbar=dict(title="µg/m³")
    ))

    if not title:
        title = f"Patrón Temporal - {pollutant.upper()} por Hora del Día"

    fig.update_layout(
        title=title,
        xaxis_title="Hora del Día",
        yaxis_title="Día de la Semana",
        template='plotly_white',
        height=500
    )

    return fig


def create_scatter_plot(df, x_col, y_col, title=None):
    """
    Crea diagrama de dispersión

    Args:
        df: DataFrame
        x_col: Columna para eje X
        y_col: Columna para eje Y
        title: Título

    Returns:
        plotly.graph_objects.Figure
    """
    if df is None or df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay datos disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        return fig

    fig = px.scatter(
        df,
        x=x_col,
        y=y_col,
        trendline="ols",
        template='plotly_white'
    )

    if not title:
        title = f"{y_col} vs {x_col}"

    fig.update_layout(
        title=title,
        height=500
    )

    return fig


def create_comparison_plot(results_df):
    """
    Crea gráfico de comparación de modelos

    Args:
        results_df: DataFrame con resultados de modelos

    Returns:
        plotly.graph_objects.Figure
    """
    if results_df is None or results_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No hay resultados disponibles",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        return fig

    # Crear subplots para cada métrica
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('R² (mayor es mejor)', 'RMSE (menor es mejor)',
                       'MAE (menor es mejor)', 'MAPE % (menor es mejor)')
    )

    # R²
    fig.add_trace(
        go.Bar(x=results_df['model_name'], y=results_df['r2'],
               marker_color=COLORS['primary_green'], name='R²'),
        row=1, col=1
    )

    # RMSE
    fig.add_trace(
        go.Bar(x=results_df['model_name'], y=results_df['rmse'],
               marker_color=COLORS['secondary_blue'], name='RMSE'),
        row=1, col=2
    )

    # MAE
    fig.add_trace(
        go.Bar(x=results_df['model_name'], y=results_df['mae'],
               marker_color=COLORS['accent_teal'], name='MAE'),
        row=2, col=1
    )

    # MAPE
    fig.add_trace(
        go.Bar(x=results_df['model_name'], y=results_df['mape'],
               marker_color=COLORS['accent_lime'], name='MAPE'),
        row=2, col=2
    )

    fig.update_layout(
        title_text="Comparación de Modelos de Calibración",
        showlegend=False,
        height=700,
        template='plotly_white'
    )

    return fig


if __name__ == '__main__':
    print("Módulo de visualización cargado correctamente")
