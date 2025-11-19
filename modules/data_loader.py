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
        'short_name': 'Ferias',
        'channels': {'pm10': 1, 'pm25': 15}
    },
    17: {
        'name': 'MinAmbiente',
        'short_name': 'MinAmb',
        'channels': {'pm10': 1, 'pm25': [15, 4, 8, 2, 3, 5, 6, 7, 9, 10, 11, 12, 13, 14, 16, 17, 18, 19, 20]}  # Probar múltiples canales
    }
}

LAST_LOW_COST_QUERY = ""


def get_last_lowcost_query(default_message='(sin consulta registrada)'):
    return LAST_LOW_COST_QUERY or default_message


def load_lowcost_data(start_date='2024-06-01', end_date='2024-07-31', devices=None, aggregate=True, filter_by_keys=True):
    """
    Carga datos de sensores de bajo costo desde PostgreSQL

    Args:
        start_date: Fecha inicial (formato YYYY-MM-DD)
        end_date: Fecha final (formato YYYY-MM-DD)
        devices: Lista de dispositivos (opcional). Si es None, incluye todos.

    Returns:
        DataFrame con columnas: datetime, device_name, pm25, pm10, temperature, rh
    """
    if isinstance(devices, str):
        devices = [devices]
    if devices:
        devices = [str(dev).strip() for dev in devices if dev]
        if not devices:
            devices = None

    try:
        # Conectar a PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)

        filters = []
        params = [start_date, end_date]

        if devices:
            placeholders = ','.join(['%s'] * len(devices))
            filters.append(f"device_name IN ({placeholders})")
            params.extend(devices)

        if filter_by_keys:
            key_filter = """
                (
                    object ? 'analogInput'
                    OR object ? 'PM_2P5'
                    OR object ? 'PM2_5'
                    OR object ? 'PM25'
                    OR object ? 'pm25'
                    OR object ? 'PM_10'
                    OR object ? 'PM10'
                    OR object ? 'pm10'
                )
            """
            filters.append(key_filter)

        # Excluir dispositivos cuyo nombre contenga 'Prototipo'
        filters.append("COALESCE(device_name, '') NOT ILIKE '%prototipo%'")

        where_clause = " AND ".join(["received_at BETWEEN %s AND %s"] + filters)

        query = f"""
        SELECT
            id,
            received_at,
            device_name,
            CASE
                WHEN object ? 'analogInput' THEN ((object -> 'analogInput' -> '2')::NUMERIC) * 10
                WHEN object ? 'PM_2P5' THEN NULLIF(object ->> 'PM_2P5', '')::NUMERIC
                WHEN object ? 'PM2_5' THEN NULLIF(object ->> 'PM2_5', '')::NUMERIC
                WHEN object ? 'PM25' THEN NULLIF(object ->> 'PM25', '')::NUMERIC
                WHEN object ? 'pm25' THEN NULLIF(object ->> 'pm25', '')::NUMERIC
                ELSE NULL
            END AS pm25_raw,
            CASE
                WHEN object ? 'analogInput' THEN ((object -> 'analogInput' -> '1')::NUMERIC) * 10
                WHEN object ? 'PM_10' THEN NULLIF(object ->> 'PM_10', '')::NUMERIC
                WHEN object ? 'PM10' THEN NULLIF(object ->> 'PM10', '')::NUMERIC
                WHEN object ? 'pm10' THEN NULLIF(object ->> 'pm10', '')::NUMERIC
                ELSE NULL
            END AS pm10_raw,
            CASE
                WHEN object ? 'analogInput' THEN (object -> 'analogInput' -> '3')::NUMERIC
                WHEN object ? 'temperature' THEN NULLIF(object ->> 'temperature', '')::NUMERIC
                WHEN object ? 'Temperature' THEN NULLIF(object ->> 'Temperature', '')::NUMERIC
                WHEN object ? 'temp' THEN NULLIF(object ->> 'temp', '')::NUMERIC
                ELSE NULL
            END AS temperature,
            CASE
                WHEN object ? 'analogInput' THEN (object -> 'analogInput' -> '4')::NUMERIC
                WHEN object ? 'rh' THEN NULLIF(object ->> 'rh', '')::NUMERIC
                WHEN object ? 'RH' THEN NULLIF(object ->> 'RH', '')::NUMERIC
                WHEN object ? 'humidity' THEN NULLIF(object ->> 'humidity', '')::NUMERIC
                WHEN object ? 'Humidity' THEN NULLIF(object ->> 'Humidity', '')::NUMERIC
                ELSE NULL
            END AS rh
        FROM public.device_up
        WHERE {where_clause}
        ORDER BY received_at DESC
        """
        global LAST_LOW_COST_QUERY
        # Registrar la consulta completa para depuración (aunque falle la ejecución)
        try:
            with conn.cursor() as cur:
                LAST_LOW_COST_QUERY = cur.mogrify(query, params).decode('utf-8').strip()
        except Exception as dbg_exc:
            # Si falla mogrify (p. ej., desajuste de parámetros), conserva query y params crudos
            LAST_LOW_COST_QUERY = f"-- mogrify_failed: {dbg_exc}\n{query}\n-- params: {params}"

        # Cargar datos
        df = pd.read_sql(query, conn, params=params)
        conn.close()

        if df.empty:
            print("No se encontraron datos para el período especificado")
            return pd.DataFrame()

        df['received_at'] = pd.to_datetime(df['received_at']).dt.tz_localize(None)
        if 'device_name' not in df.columns:
            df['device_name'] = 'Desconocido'
        else:
            df['device_name'] = df['device_name'].fillna('Desconocido')
        df = df.rename(columns={
            'received_at': 'datetime',
            'pm25_raw': 'pm25_sensor',
            'pm10_raw': 'pm10_sensor'
        })

        if not aggregate:
            return df.sort_values('datetime').reset_index(drop=True)

        df_hourly = df.groupby(['device_name', pd.Grouper(key='datetime', freq='H')]).agg({
            'pm25_sensor': 'mean',
            'pm10_sensor': 'mean',
            'temperature': 'mean',
            'rh': 'mean'
        }).reset_index()

        return df_hourly

    except Exception as e:
        import traceback
        print(f"Error cargando datos de sensores: {e}")
        traceback.print_exc()
        return None



def find_dense_window(lowcost_df, window_days=10, devices=None):
    """
    Encuentra la ventana deslizante de 'window_days' días con mayor densidad de datos.

    Args:
        lowcost_df (DataFrame): Datos horarios de sensores de bajo costo.
        window_days (int): Duración de la ventana en días (default: 10).
        devices (list[str], opcional): Lista de dispositivos a priorizar.

    Returns:
        dict | None: Información de la mejor ventana encontrada.
    """
    if lowcost_df is None or lowcost_df.empty:
        return None

    df = lowcost_df.copy()
    if 'datetime' not in df.columns:
        return None

    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    df = df.dropna(subset=['datetime'])
    if df.empty:
        return None

    if devices:
        df = df[df['device_name'].isin(devices)]
        if df.empty:
            return None

    # Normalizar hora y ordenar
    df['datetime'] = df['datetime'].dt.floor('H')
    df = df.sort_values('datetime')

    start_ts = df['datetime'].min().normalize()
    end_ts = df['datetime'].max()

    if pd.isna(start_ts) or pd.isna(end_ts):
        return None

    window_duration = pd.Timedelta(days=window_days)
    if end_ts - start_ts < pd.Timedelta(hours=1):
        return None

    last_start = (end_ts - window_duration).floor('D')
    if last_start < start_ts:
        last_start = start_ts

    start_candidates = pd.date_range(start_ts, last_start, freq='D')
    if len(start_candidates) == 0:
        start_candidates = pd.DatetimeIndex([start_ts])

    best_window = None
    priority_devices = devices or df['device_name'].unique().tolist()

    for candidate_start in start_candidates:
        candidate_end = candidate_start + window_duration - pd.Timedelta(hours=1)
        mask = (df['datetime'] >= candidate_start) & (df['datetime'] <= candidate_end)
        subset = df.loc[mask]
        total_records = len(subset)
        if total_records == 0:
            continue

        per_device_counts = subset['device_name'].value_counts()
        # Cobertura mínima de dispositivos prioritarios
        coverage_min = None
        if priority_devices:
            coverage_series = per_device_counts.reindex(priority_devices).fillna(0)
            coverage_min = coverage_series.min()

        # Registrar conteos por contaminante y dispositivo
        pollutant_counts = {}
        for device in priority_devices:
            device_subset = subset[subset['device_name'] == device]
            if device_subset.empty:
                pollutant_counts[device] = {'pm25': 0, 'pm10': 0}
                continue

            pm25_count = int(device_subset['pm25_sensor'].notna().sum()) if 'pm25_sensor' in device_subset.columns else 0
            pm10_count = int(device_subset['pm10_sensor'].notna().sum()) if 'pm10_sensor' in device_subset.columns else 0
            pollutant_counts[device] = {
                'pm25': pm25_count,
                'pm10': pm10_count
            }

        candidate = {
            'start': candidate_start,
            'end': candidate_end,
            'subset': subset.copy(),
            'total_records': int(total_records),
            'per_device_counts': per_device_counts.astype(int).to_dict(),
            'pollutant_counts': pollutant_counts,
            'hours_covered': int(subset['datetime'].nunique()),
            'coverage_min': float(coverage_min) if coverage_min is not None else None
        }

        if best_window is None:
            best_window = candidate
            continue

        # Priorizar mayor número total de registros
        if candidate['total_records'] > best_window['total_records']:
            best_window = candidate
            continue

        if candidate['total_records'] == best_window['total_records']:
            # Desempatar por cobertura mínima de dispositivos prioritarios
            cand_cov = candidate['coverage_min'] or 0
            best_cov = best_window['coverage_min'] or 0
            if cand_cov > best_cov:
                best_window = candidate
                continue
            # Como último recurso, elegir la ventana cronológicamente más temprana
            if cand_cov == best_cov and candidate_start < best_window['start']:
                best_window = candidate

    return best_window


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
        print(f"      ❌ Error de red: {exc}")
        return pd.DataFrame()

    if response.status_code != 200:
        print(f"      ❌ Status code: {response.status_code}")
        return pd.DataFrame()

    try:
        payload = response.json()
    except json.JSONDecodeError as exc:
        print(f"      ❌ Error JSON: {exc}")
        return pd.DataFrame()

    if 'ListDic' not in payload or not payload['ListDic']:
        print(f"      ⚠️  ListDic vacío o inexistente")
        return pd.DataFrame()

    series_info = payload.get('series', [])
    pollutant_field = f"S_{station_code}_{pollutant_channel}"

    # Buscar el nombre del contaminante en la respuesta
    pollutant_label = next((serie.get('name') for serie in series_info if serie.get('field') == pollutant_field), None)

    if not pollutant_label:
        pollutant_label = 'PM10' if pollutant_channel == 1 else 'PM2.5'
        print(f"      ℹ️  Usando label por defecto: {pollutant_label}")
    else:
        print(f"      ℹ️  Label de API: '{pollutant_label}'")

    records = []

    for entry in payload['ListDic']:
        datetime_str = entry.get('datetime')
        value_str = entry.get(pollutant_field)

        if not datetime_str or value_str is None:
            continue

        try:
            value = float(str(value_str).replace(',', '.'))
            # Convertir a datetime sin timezone
            timestamp = datetime.strptime(datetime_str, '%d-%m-%Y %H:%M')
            records.append({
                'datetime': timestamp,
                'station': station_name,
                'pollutant': pollutant_label,
                'value': value
            })
        except (ValueError, TypeError):
            continue

    print(f"      ✅ Procesados {len(records)} registros válidos")
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
        channels = station_meta.get('channels', {'pm10': 1, 'pm25': 15})

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        if end <= start:
            end = start + timedelta(days=1)

        days = max((end - start).days, 1)
        user_date = end.strftime('%Y/%m/%d')

        print(f"\n📡 Cargando datos RMCAB para {station_name} (código {station_code})")
        print(f"   Periodo: {start_date} a {end_date} ({days} días)")
        print(f"   Canales: PM10={channels['pm10']}, PM2.5={channels['pm25']}")

        datasets = []
        for pollutant_name, pollutant_channel_config in channels.items():
            # Si el canal es una lista, probar cada uno hasta encontrar datos
            if isinstance(pollutant_channel_config, list):
                print(f"   Buscando {pollutant_name.upper()} en canales: {pollutant_channel_config}")
                found = False
                for pollutant_channel in pollutant_channel_config:
                    print(f"      Probando canal {pollutant_channel}...")
                    df_pollutant = _fetch_rmcab_pollutant_series(
                        template,
                        station_code,
                        station_name,
                        pollutant_channel,
                        user_date,
                        days
                    )
                    if df_pollutant is not None and not df_pollutant.empty and len(df_pollutant) > 0:
                        print(f"   ✅ {pollutant_name.upper()} encontrado en canal {pollutant_channel}: {len(df_pollutant)} registros")
                        datasets.append(df_pollutant)
                        # Actualizar la configuración con el canal que funcionó
                        RMCAB_STATION_INFO[station_code]['channels'][pollutant_name] = pollutant_channel
                        found = True
                        break
                if not found:
                    print(f"   ⚠️  {pollutant_name.upper()}: No se encontró en ningún canal")
            else:
                # Canal único
                print(f"   Consultando {pollutant_name.upper()} (canal {pollutant_channel_config})...")
                df_pollutant = _fetch_rmcab_pollutant_series(
                    template,
                    station_code,
                    station_name,
                    pollutant_channel_config,
                    user_date,
                    days
                )
                if df_pollutant is not None and not df_pollutant.empty:
                    print(f"   ✅ {pollutant_name.upper()}: {len(df_pollutant)} registros")
                    datasets.append(df_pollutant)
                else:
                    print(f"   ⚠️  {pollutant_name.upper()}: Sin datos")

        if not datasets:
            print('❌ No se pudieron obtener datos de RMCAB')
            return pd.DataFrame()

        combined = pd.concat(datasets, ignore_index=True)
        print(f"   Total combinado: {len(combined)} registros")

        pivot = combined.pivot_table(
            index='datetime',
            columns='pollutant',
            values='value',
            aggfunc='first'
        ).reset_index()

        print(f"   Columnas después del pivot: {list(pivot.columns)}")

        column_mapping = {}
        for col in pivot.columns:
            if isinstance(col, str):
                normalized = col.lower().replace(' ', '').replace('.', '').replace('μ', '')
                if 'pm25' in normalized or 'pm2' in normalized:
                    column_mapping[col] = 'pm25_ref'  # Usar sufijo _ref para consistencia con calibración
                elif 'pm10' in normalized:
                    column_mapping[col] = 'pm10_ref'  # Usar sufijo _ref para consistencia con calibración

        if column_mapping:
            print(f"   Renombrando columnas: {column_mapping}")
            pivot = pivot.rename(columns=column_mapping)

        if 'pm25_ref' not in pivot.columns:
            print(f"   ⚠️  Agregando columna pm25_ref vacía")
            pivot['pm25_ref'] = None
        if 'pm10_ref' not in pivot.columns:
            print(f"   ⚠️  Agregando columna pm10_ref vacía")
            pivot['pm10_ref'] = None

        pivot['station'] = f'RMCAB_{station_code}'

        print(f"   ✅ Datos finales: {len(pivot)} registros")
        print(f"   PM2.5 no nulos: {pivot['pm25_ref'].notna().sum()}")
        print(f"   PM10 no nulos: {pivot['pm10_ref'].notna().sum()}")

        return pivot.sort_values('datetime')
    except Exception as exc:
        print(f"❌ Error cargando datos de RMCAB: {exc}")
        import traceback
        traceback.print_exc()
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


def align_lowcost_with_reference(lowcost_df, reference_times, tolerance_minutes=30):
    """
    Selecciona el registro de cada sensor más cercano a cada timestamp de referencia.

    Args:
        lowcost_df (DataFrame): Medidas de sensores (sin agregar).
        reference_times (Iterable[datetime]): Timestamps de referencia (RMCAB).
        tolerance_minutes (int): Ventana máxima para considerar una coincidencia.

    Returns:
        DataFrame con columnas alineadas a los timestamps de referencia.
    """
    if lowcost_df is None or lowcost_df.empty or not reference_times:
        return pd.DataFrame()

    reference_sorted = sorted(pd.to_datetime(reference_times))
    if not reference_sorted:
        return pd.DataFrame()

    ref_df = pd.DataFrame({'reference_datetime': reference_sorted})
    tolerance = pd.Timedelta(minutes=tolerance_minutes)
    aligned_frames = []

    for device, device_df in lowcost_df.groupby('device_name'):
        device_sorted = device_df.sort_values('datetime')
        merged = pd.merge_asof(
            ref_df,
            device_sorted,
            left_on='reference_datetime',
            right_on='datetime',
            direction='nearest',
            tolerance=tolerance
        )

        if merged.empty:
            continue

        merged = merged.dropna(subset=['device_name'])
        if merged.empty:
            continue

        merged = merged.rename(columns={'datetime': 'sensor_datetime'})
        merged['datetime'] = merged['reference_datetime']
        merged['device_name'] = merged['device_name'].astype(str)
        aligned_frames.append(merged)

    if not aligned_frames:
        return pd.DataFrame()

    result = pd.concat(aligned_frames, ignore_index=True)
    if 'reference_datetime' in result.columns:
        result = result.drop(columns=['reference_datetime'])

    preferred_order = [
        'datetime',
        'device_name',
        'pm25_sensor',
        'pm10_sensor',
        'temperature',
        'rh',
        'sensor_datetime'
    ]
    for column in preferred_order:
        if column not in result.columns:
            result[column] = pd.NA

    return result[preferred_order]


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
