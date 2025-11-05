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


def create_calibration_scatter(y_true, y_pred, model_name, pollutant='PM2.5'):
    """
    Crea scatter plot de calibración (real vs predicho)

    Args:
        y_true: Valores reales
        y_pred: Valores predichos
        model_name: Nombre del modelo
        pollutant: Nombre del contaminante

    Returns:
        plotly.graph_objects.Figure
    """
    fig = go.Figure()

    # Scatter plot
    fig.add_trace(go.Scatter(
        x=y_true,
        y=y_pred,
        mode='markers',
        name='Predicciones',
        marker=dict(
            color=COLORS['primary_green'],
            size=6,
            opacity=0.6
        ),
        text=[f'Real: {r:.2f}<br>Pred: {p:.2f}' for r, p in zip(y_true, y_pred)],
        hovertemplate='%{text}<extra></extra>'
    ))

    # Línea perfecta (y = x)
    min_val = min(min(y_true), min(y_pred))
    max_val = max(max(y_true), max(y_pred))

    fig.add_trace(go.Scatter(
        x=[min_val, max_val],
        y=[min_val, max_val],
        mode='lines',
        name='Predicción Perfecta',
        line=dict(color='red', dash='dash', width=2)
    ))

    # Calcular R²
    from sklearn.metrics import r2_score
    r2 = r2_score(y_true, y_pred)

    fig.update_layout(
        title=f'{model_name} - {pollutant}<br><sub>R² = {r2:.4f}</sub>',
        xaxis_title=f'{pollutant} Real (µg/m³)',
        yaxis_title=f'{pollutant} Predicho (µg/m³)',
        template='plotly_white',
        height=500,
        showlegend=True
    )

    # Hacer cuadrado el gráfico
    fig.update_xaxes(scaleanchor="y", scaleratio=1)

    return fig


def create_residuals_plot(y_true, y_pred, model_name):
    """
    Crea gráfico de residuales

    Args:
        y_true: Valores reales
        y_pred: Valores predichos
        model_name: Nombre del modelo

    Returns:
        plotly.graph_objects.Figure
    """
    residuals = y_true - y_pred

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=y_pred,
        y=residuals,
        mode='markers',
        name='Residuales',
        marker=dict(
            color=COLORS['secondary_blue'],
            size=6,
            opacity=0.6
        )
    ))

    # Línea en cero
    fig.add_hline(y=0, line_dash="dash", line_color="red")

    fig.update_layout(
        title=f'Residuales - {model_name}',
        xaxis_title='Valores Predichos (µg/m³)',
        yaxis_title='Residuales (µg/m³)',
        template='plotly_white',
        height=400
    )

    return fig


def create_before_after_comparison(df_original, df_calibrated, device_name, pollutant='pm25'):
    """
    Crea comparación antes/después de calibración

    Args:
        df_original: DataFrame con datos originales
        df_calibrated: DataFrame con datos calibrados
        device_name: Nombre del dispositivo
        pollutant: Contaminante

    Returns:
        plotly.graph_objects.Figure
    """
    fig = go.Figure()

    # Datos originales
    fig.add_trace(go.Scatter(
        x=df_original['datetime'],
        y=df_original[f'{pollutant}_sensor'],
        mode='lines',
        name=f'{device_name} - Sin Calibrar',
        line=dict(color='gray', width=1),
        opacity=0.7
    ))

    # Datos calibrados
    fig.add_trace(go.Scatter(
        x=df_calibrated['datetime'],
        y=df_calibrated[f'{pollutant}_calibrated'],
        mode='lines',
        name=f'{device_name} - Calibrado',
        line=dict(color=COLORS['primary_green'], width=2)
    ))

    # Datos de referencia
    fig.add_trace(go.Scatter(
        x=df_calibrated['datetime'],
        y=df_calibrated[f'{pollutant}_ref'],
        mode='lines',
        name='RMCAB (Referencia)',
        line=dict(color='red', width=1.5, dash='dot')
    ))

    # Límites normativos
    if pollutant in LIMITS:
        fig.add_hline(
            y=LIMITS[pollutant]['OMS_2021'],
            line_dash="dash",
            line_color="orange",
            annotation_text="OMS 2021",
            annotation_position="right"
        )

    fig.update_layout(
        title=f'Comparación Antes/Después - {device_name}',
        xaxis_title='Fecha y Hora',
        yaxis_title=f'Concentración {pollutant.upper()} (µg/m³)',
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


def create_model_effectiveness_summary(results_list):
    """
    Crea resumen visual de efectividad de modelos

    Args:
        results_list: Lista de resultados de calibración

    Returns:
        plotly.graph_objects.Figure
    """
    from plotly.subplots import make_subplots

    # Convertir a DataFrame
    df = pd.DataFrame(results_list)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'R² por Modelo (↑ mejor)',
            'RMSE por Modelo (↓ mejor)',
            'MAE por Modelo (↓ mejor)',
            'MAPE por Modelo (↓ mejor)'
        ),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "bar"}]]
    )

    # Colores por modelo
    colors = [COLORS['primary_green'], COLORS['secondary_blue'], COLORS['accent_teal'],
              '#fbbf24', '#f87171']

    # R²
    fig.add_trace(
        go.Bar(x=df['model_name'], y=df['r2'], marker_color=colors, name='R²',
               text=df['r2'].round(4), textposition='outside'),
        row=1, col=1
    )

    # RMSE
    fig.add_trace(
        go.Bar(x=df['model_name'], y=df['rmse'], marker_color=colors, name='RMSE',
               text=df['rmse'].round(2), textposition='outside'),
        row=1, col=2
    )

    # MAE
    fig.add_trace(
        go.Bar(x=df['model_name'], y=df['mae'], marker_color=colors, name='MAE',
               text=df['mae'].round(2), textposition='outside'),
        row=2, col=1
    )

    # MAPE
    fig.add_trace(
        go.Bar(x=df['model_name'], y=df['mape'], marker_color=colors, name='MAPE',
               text=df['mape'].round(2), textposition='outside'),
        row=2, col=2
    )

    fig.update_layout(
        title_text="Efectividad de Modelos de Calibración",
        showlegend=False,
        height=800,
        template='plotly_white'
    )

    # Actualizar ejes
    fig.update_xaxes(tickangle=-45)

    return fig


if __name__ == '__main__':
    print("Módulo de visualización cargado correctamente")
