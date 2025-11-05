"""
Módulo para cargar datos de sensores de bajo costo y RMCAB
"""

import pandas as pd
import psycopg2
import requests
import json
import os
from datetime import datetime, timedelta


# Configuración de base de datos
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "dit_as_events"),
    "user": os.getenv("DB_USER", "dit_as_events"),
    "password": os.getenv("DB_PASSWORD", "ucentral2020"),
    "host": os.getenv("DB_HOST", "186.121.143.150"),
    "port": int(os.getenv("DB_PORT", 15432))
}


def load_lowcost_data(start_date='2024-06-01', end_date='2024-07-31', devices=None):
    """
    Carga datos de sensores de bajo costo desde PostgreSQL

    Args:
        start_date: Fecha inicial (formato YYYY-MM-DD)
        end_date: Fecha final (formato YYYY-MM-DD)
        devices: Lista de dispositivos (default: ['Aire2', 'Aire4', 'Aire5'])

    Returns:
        DataFrame con columnas: datetime, device_name, pm25, pm10, temperature, rh
    """
    if devices is None:
        devices = ['Aire2', 'Aire4', 'Aire5']

    try:
        # Conectar a PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)

        # Construir lista de dispositivos para SQL
        devices_str = "','".join(devices)

        # Query SQL
        query = f"""
        SELECT
            id,
            received_at,
            device_name,
            ((object -> 'analogInput' -> '2')::NUMERIC) * 10 AS pm25_raw,
            ((object -> 'analogInput' -> '1')::NUMERIC) * 10 AS pm10_raw,
            ((object -> 'analogInput' -> '3')::NUMERIC) AS temperature,
            ((object -> 'analogInput' -> '4')::NUMERIC) AS rh
        FROM public.device_up
        WHERE device_name IN ('{devices_str}')
          AND received_at BETWEEN '{start_date}' AND '{end_date}'
          AND object ? 'analogInput'
        ORDER BY received_at
        """

        # Cargar datos
        df = pd.read_sql(query, conn)
        conn.close()

        # Procesar datos
        if not df.empty:
            df['received_at'] = pd.to_datetime(df['received_at'])
            df = df.rename(columns={
                'received_at': 'datetime',
                'pm25_raw': 'pm25',
                'pm10_raw': 'pm10'
            })

            # Resample a promedios horarios
            df_hourly = df.groupby(['device_name', pd.Grouper(key='datetime', freq='H')]).agg({
                'pm25': 'mean',
                'pm10': 'mean',
                'temperature': 'mean',
                'rh': 'mean'
            }).reset_index()

            return df_hourly
        else:
            print("No se encontraron datos para el período especificado")
            return pd.DataFrame()

    except Exception as e:
        print(f"Error cargando datos de sensores: {e}")
        return None


def load_rmcab_data(station_code=6, start_date='2024-06-01', end_date='2024-07-31'):
    """
    Carga datos de RMCAB desde la API

    Args:
        station_code: Código de estación RMCAB (default: 6 = Las Ferias)
        start_date: Fecha inicial (formato YYYY-MM-DD)
        end_date: Fecha final (formato YYYY-MM-DD)

    Returns:
        DataFrame con columnas: datetime, station, pm25, pm10
    """
    try:
        # Cargar template de Postman
        postman_file = os.path.join(os.path.dirname(__file__), '..', 'Proyecto de grado.postman_collection.json')

        if not os.path.exists(postman_file):
            print(f"Archivo Postman no encontrado: {postman_file}")
            return None

        with open(postman_file, 'r', encoding='utf-8') as f:
            postman_data = json.load(f)

        # Extraer URL y headers del template
        request_item = postman_data['item'][0]['request']
        url_template = request_item['url']['raw']

        # Configurar parámetros
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        days = (end - start).days

        # Construir URLs para PM25 y PM10
        urls = {
            'pm25': url_template.replace('{{variable}}', '112').replace('{{station}}', str(station_code)),
            'pm10': url_template.replace('{{variable}}', '114').replace('{{station}}', str(station_code))
        }

        data_frames = []

        for pollutant, url in urls.items():
            url = url.replace('{{days}}', str(days)).replace('{{date}}', end.strftime('%Y/%m/%d'))

            response = requests.get(url, timeout=60)

            if response.status_code == 200:
                data = response.json()

                if 'data' in data and len(data['data']) > 0:
                    df = pd.DataFrame(data['data'])
                    df['pollutant'] = pollutant
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    df['value'] = pd.to_numeric(df['value'], errors='coerce')
                    data_frames.append(df)

        if data_frames:
            # Combinar PM25 y PM10
            df_combined = pd.concat(data_frames)

            # Pivot para tener PM25 y PM10 como columnas
            df_pivot = df_combined.pivot_table(
                index='datetime',
                columns='pollutant',
                values='value',
                aggfunc='first'
            ).reset_index()

            df_pivot = df_pivot.rename(columns={'pm25': 'pm25', 'pm10': 'pm10'})
            df_pivot['station'] = f'RMCAB_{station_code}'

            return df_pivot
        else:
            print("No se pudieron obtener datos de RMCAB")
            return pd.DataFrame()

    except Exception as e:
        print(f"Error cargando datos de RMCAB: {e}")
        return None


def merge_datasets(lowcost_df, rmcab_df, tolerance='1H'):
    """
    Combina datos de sensores de bajo costo con RMCAB

    Args:
        lowcost_df: DataFrame de sensores de bajo costo
        rmcab_df: DataFrame de RMCAB
        tolerance: Tolerancia de tiempo para merge (default: 1 hora)

    Returns:
        DataFrame combinado
    """
    try:
        if lowcost_df is None or rmcab_df is None:
            return None

        if lowcost_df.empty or rmcab_df.empty:
            return pd.DataFrame()

        # Asegurar que datetime sea el índice
        lowcost_df = lowcost_df.set_index('datetime')
        rmcab_df = rmcab_df.set_index('datetime')

        # Merge con pd.merge_asof (join por tiempo más cercano)
        merged_df = pd.merge_asof(
            lowcost_df.sort_index(),
            rmcab_df.sort_index(),
            left_index=True,
            right_index=True,
            tolerance=pd.Timedelta(tolerance),
            suffixes=('_sensor', '_ref')
        )

        return merged_df.reset_index()

    except Exception as e:
        print(f"Error combinando datasets: {e}")
        return None


if __name__ == '__main__':
    # Test de funciones
    print("Cargando datos de sensores de bajo costo...")
    lowcost = load_lowcost_data()
    if lowcost is not None:
        print(f"Registros cargados: {len(lowcost)}")
        print(lowcost.head())

    print("\nCargando datos de RMCAB...")
    rmcab = load_rmcab_data()
    if rmcab is not None:
        print(f"Registros cargados: {len(rmcab)}")
        print(rmcab.head())
