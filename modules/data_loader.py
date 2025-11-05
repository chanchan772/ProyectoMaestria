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



POSTMAN_BODY_TEMPLATE = None
POSTMAN_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), '..', 'Proyecto de grado.postman_collection.json')
RMCAB_ENDPOINT = os.getenv('RMCAB_ENDPOINT', 'http://rmcab.ambientebogota.gov.co/home/MonitorsVal')
RMCAB_HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0'
}
RMCAB_STATION_INFO = {
    6: {
        'name': 'Las Ferias',
        'short_name': 'Ferias'
    }
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



def _load_postman_body_template():
    global POSTMAN_BODY_TEMPLATE

    if POSTMAN_BODY_TEMPLATE:
        return POSTMAN_BODY_TEMPLATE

    if not os.path.exists(POSTMAN_TEMPLATE_PATH):
        print(f"Archivo Postman no encontrado: {POSTMAN_TEMPLATE_PATH}")
        return None

    try:
        with open(POSTMAN_TEMPLATE_PATH, 'r', encoding='utf-8') as template_file:
            postman_data = json.load(template_file)
            POSTMAN_BODY_TEMPLATE = postman_data['item'][0]['request']['body']['raw']
    except (KeyError, IndexError, json.JSONDecodeError) as exc:
        print(f"No se pudo cargar el template de Postman: {exc}")
        return None

    return POSTMAN_BODY_TEMPLATE


def _build_rmcab_request_body(template, station_code, station_name, pollutant_channel, user_date, days):
    safe_name = station_name.replace(' ', '+')
    short_name = RMCAB_STATION_INFO.get(station_code, {}).get('short_name', station_name.split(' ')[0])
    safe_short = short_name.replace(' ', '+')

    body = template
    replacements = {
        '%22serialCode%22%3A6': f"%22serialCode%22%3A{station_code}",
        'serialCode%22%3A6': f"serialCode%22%3A{station_code}",
        'Las+Ferias': safe_name,
        '%22name%22%3A%22Las+Ferias%22': f"%22name%22%3A%22{safe_name}%22",
        '%22StationTag%22%3A%226%22': f"%22StationTag%22%3A%22{station_code}%22",
        'StationTag%22%3A%226': f"StationTag%22%3A%22{station_code}",
        '%22ShortName%22%3A%22Ferias%22': f"%22ShortName%22%3A%22{safe_short}%22",
        'SelectedPollutant=S_6_1': f"SelectedPollutant=S_{station_code}_{pollutant_channel}",
        'UserDate=2025%2F07%2F30': f"UserDate={user_date.replace('/', '%2F')}",
        'days=15': f"days={days}"
    }

    for old, new in replacements.items():
        body = body.replace(old, new)

    return body


def _fetch_rmcab_pollutant_series(template, station_code, station_name, pollutant_channel, user_date, days):
    body = _build_rmcab_request_body(template, station_code, station_name, pollutant_channel, user_date, days)

    try:
        response = requests.post(RMCAB_ENDPOINT, data=body, headers=RMCAB_HEADERS, timeout=60)
    except requests.RequestException as exc:
        print(f"Error de red solicitando RMCAB ({station_code}-{pollutant_channel}): {exc}")
        return pd.DataFrame()

    if response.status_code != 200:
        print(f"Respuesta no exitosa de RMCAB ({station_code}-{pollutant_channel}): {response.status_code}")
        return pd.DataFrame()

    try:
        payload = response.json()
    except json.JSONDecodeError as exc:
        print(f"Error interpretando respuesta de RMCAB ({station_code}-{pollutant_channel}): {exc}")
        return pd.DataFrame()

    if 'ListDic' not in payload or not payload['ListDic']:
        return pd.DataFrame()

    series_info = payload.get('series', [])
    pollutant_field = f"S_{station_code}_{pollutant_channel}"
    pollutant_label = next((serie.get('name') for serie in series_info if serie.get('field') == pollutant_field), None)

    if not pollutant_label:
        pollutant_label = 'PM10' if pollutant_channel == 1 else 'PM2.5'

    records = []

    for entry in payload['ListDic']:
        datetime_str = entry.get('datetime')
        value_str = entry.get(pollutant_field)

        if not datetime_str or value_str is None:
            continue

        try:
            value = float(str(value_str).replace(',', '.'))
            timestamp = datetime.strptime(datetime_str, '%d-%m-%Y %H:%M')
            records.append({
                'datetime': timestamp,
                'station': station_name,
                'pollutant': pollutant_label,
                'value': value
            })
        except (ValueError, TypeError):
            continue

    return pd.DataFrame(records)

def load_rmcab_data(station_code=6, start_date='2024-06-01', end_date='2024-07-31'):
    """
    Carga datos de RMCAB desde la API

    Args:
        station_code: Codigo de estacion RMCAB (default: 6 = Las Ferias)
        start_date: Fecha inicial (formato YYYY-MM-DD)
        end_date: Fecha final (formato YYYY-MM-DD)

    Returns:
        DataFrame con columnas: datetime, station, pm25, pm10
    """
    try:
        template = _load_postman_body_template()
        if not template:
            return None

        station_meta = RMCAB_STATION_INFO.get(station_code, {})
        station_name = station_meta.get('name', f'Estacion {station_code}')

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        if end <= start:
            end = start + timedelta(days=1)

        days = max((end - start).days, 1)
        user_date = end.strftime('%Y/%m/%d')

        datasets = []
        for pollutant_channel in (1, 15):
            df_pollutant = _fetch_rmcab_pollutant_series(
                template,
                station_code,
                station_name,
                pollutant_channel,
                user_date,
                days
            )
            if df_pollutant is not None and not df_pollutant.empty:
                datasets.append(df_pollutant)

        if not datasets:
            print('No se pudieron obtener datos de RMCAB')
            return pd.DataFrame()

        combined = pd.concat(datasets, ignore_index=True)

        pivot = combined.pivot_table(
            index='datetime',
            columns='pollutant',
            values='value',
            aggfunc='first'
        ).reset_index()

        column_mapping = {}
        for col in pivot.columns:
            if isinstance(col, str):
                normalized = col.lower().replace(' ', '').replace('.', '')
                if normalized == 'pm25':
                    column_mapping[col] = 'pm25'
                elif normalized == 'pm10':
                    column_mapping[col] = 'pm10'

        if column_mapping:
            pivot = pivot.rename(columns=column_mapping)

        if 'pm25' not in pivot.columns:
            pivot['pm25'] = None
        if 'pm10' not in pivot.columns:
            pivot['pm10'] = None

        pivot['station'] = f'RMCAB_{station_code}'

        return pivot.sort_values('datetime')
    except Exception as exc:
        print(f"Error cargando datos de RMCAB: {exc}")
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
