"""
Módulo para calcular estadísticas y métricas
"""

import pandas as pd
import numpy as np


def calculate_statistics(df, pollutants=['pm25', 'pm10']):
    """
    Calcula estadísticas descriptivas

    Args:
        df: DataFrame con datos
        pollutants: Lista de contaminantes a analizar

    Returns:
        dict: Diccionario con estadísticas
    """
    if df is None or df.empty:
        return {}

    stats = {}

    # Estadísticas por contaminante
    for pollutant in pollutants:
        if pollutant not in df.columns:
            continue

        data = df[pollutant].dropna()

        if len(data) == 0:
            continue

        stats[pollutant] = {
            'count': int(len(data)),
            'mean': round(float(data.mean()), 2),
            'std': round(float(data.std()), 2),
            'min': round(float(data.min()), 2),
            'max': round(float(data.max()), 2),
            'p25': round(float(data.quantile(0.25)), 2),
            'p50': round(float(data.median()), 2),
            'p75': round(float(data.quantile(0.75)), 2),
            'p95': round(float(data.quantile(0.95)), 2)
        }

    # Estadísticas generales
    stats['general'] = {
        'total_records': int(len(df)),
        'date_range': {
            'start': str(df['datetime'].min()) if 'datetime' in df.columns else None,
            'end': str(df['datetime'].max()) if 'datetime' in df.columns else None
        }
    }

    # Contar dispositivos/estaciones
    if 'device_name' in df.columns:
        stats['general']['devices'] = df['device_name'].unique().tolist()
        stats['general']['num_devices'] = int(df['device_name'].nunique())
    elif 'station' in df.columns:
        stats['general']['stations'] = df['station'].unique().tolist()
        stats['general']['num_stations'] = int(df['station'].nunique())

    return stats


def calculate_compliance(df, pollutant='pm25', limits=None):
    """
    Calcula cumplimiento de límites normativos

    Args:
        df: DataFrame con datos
        pollutant: Contaminante a evaluar
        limits: Dict con límites (default: OMS y Colombia)

    Returns:
        dict: Porcentajes de cumplimiento
    """
    if limits is None:
        if pollutant == 'pm25':
            limits = {'OMS_2021': 15, 'Colombia': 25}
        elif pollutant == 'pm10':
            limits = {'OMS_2021': 45, 'Colombia': 50}
        else:
            return {}

    if df is None or df.empty or pollutant not in df.columns:
        return {}

    data = df[pollutant].dropna()
    total = len(data)

    if total == 0:
        return {}

    compliance = {}

    for limit_name, limit_value in limits.items():
        exceeds = (data > limit_value).sum()
        compliance[limit_name] = {
            'limit': limit_value,
            'exceeds': int(exceeds),
            'compliance_pct': round((1 - exceeds / total) * 100, 2),
            'exceedance_pct': round((exceeds / total) * 100, 2)
        }

    return compliance


def calculate_correlation(df1, df2, pollutant='pm25'):
    """
    Calcula correlación entre dos datasets

    Args:
        df1: DataFrame 1 (ej: sensores)
        df2: DataFrame 2 (ej: referencia)
        pollutant: Contaminante

    Returns:
        dict: Coeficiente de correlación y p-value
    """
    from scipy.stats import pearsonr

    try:
        # Merge por datetime
        merged = pd.merge(
            df1[['datetime', pollutant]],
            df2[['datetime', pollutant]],
            on='datetime',
            suffixes=('_1', '_2')
        ).dropna()

        if len(merged) < 10:
            return {'error': 'Datos insuficientes para calcular correlación'}

        corr, pvalue = pearsonr(merged[f'{pollutant}_1'], merged[f'{pollutant}_2'])

        return {
            'correlation': round(corr, 4),
            'p_value': round(pvalue, 6),
            'n': int(len(merged)),
            'significant': pvalue < 0.05
        }

    except Exception as e:
        return {'error': str(e)}


def get_aqi_category(value, pollutant='pm25'):
    """
    Obtiene categoría de ICA según valor de contaminante

    Args:
        value: Valor de concentración (µg/m³)
        pollutant: 'pm25' o 'pm10'

    Returns:
        dict: Categoría, color y descripción
    """
    if pollutant == 'pm25':
        breakpoints = [
            (0, 12, 'Buena', 'good', '#00e400'),
            (12.1, 37.5, 'Aceptable', 'moderate', '#ffff00'),
            (37.6, 55.4, 'Dañina a grupos sensibles', 'unhealthy_sensitive', '#ff7e00'),
            (55.5, 150.4, 'Dañina', 'unhealthy', '#ff0000'),
            (150.5, 250.4, 'Muy dañina', 'very_unhealthy', '#8f3f97'),
            (250.5, float('inf'), 'Peligrosa', 'hazardous', '#7e0023')
        ]
    elif pollutant == 'pm10':
        breakpoints = [
            (0, 54, 'Buena', 'good', '#00e400'),
            (55, 154, 'Aceptable', 'moderate', '#ffff00'),
            (155, 254, 'Dañina a grupos sensibles', 'unhealthy_sensitive', '#ff7e00'),
            (255, 354, 'Dañina', 'unhealthy', '#ff0000'),
            (355, 424, 'Muy dañina', 'very_unhealthy', '#8f3f97'),
            (425, float('inf'), 'Peligrosa', 'hazardous', '#7e0023')
        ]
    else:
        return {'error': 'Contaminante no reconocido'}

    for min_val, max_val, category, code, color in breakpoints:
        if min_val <= value <= max_val:
            return {
                'value': value,
                'category': category,
                'code': code,
                'color': color,
                'range': f'{min_val}-{max_val}'
            }

    return {'error': 'Valor fuera de rango'}


def calculate_daily_averages(df, pollutants=['pm25', 'pm10']):
    """
    Calcula promedios diarios

    Args:
        df: DataFrame con datetime y contaminantes
        pollutants: Lista de contaminantes

    Returns:
        DataFrame con promedios diarios
    """
    if df is None or df.empty or 'datetime' not in df.columns:
        return pd.DataFrame()

    df = df.copy()
    df['date'] = pd.to_datetime(df['datetime']).dt.date

    agg_dict = {p: 'mean' for p in pollutants if p in df.columns}

    if not agg_dict:
        return pd.DataFrame()

    daily = df.groupby('date').agg(agg_dict).reset_index()

    return daily


if __name__ == '__main__':
    print("Módulo de métricas cargado correctamente")

    # Test de función AQI
    test_value = 30
    result = get_aqi_category(test_value, 'pm25')
    print(f"PM2.5 = {test_value} µg/m³ → {result}")
