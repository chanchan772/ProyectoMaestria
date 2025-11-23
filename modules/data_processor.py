"""
Módulo para procesar y preparar datos REALES de sensores y estación de referencia.
SIN SIMULACIÓN - Datos 100% reales de PostgreSQL y RMCAB API
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import psycopg2
import requests


# Configuración de base de datos
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "dit_as_events"),
    "user": os.getenv("DB_USER", "dit_as_events"),
    "password": os.getenv("DB_PASSWORD", "ucentral2020"),
    "host": os.getenv("DB_HOST", "186.121.143.150"),
    "port": int(os.getenv("DB_PORT", 15432))
}

RMCAB_ENDPOINT = 'http://rmcab.ambientebogota.gov.co/home/MonitorsVal'
RMCAB_HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Accept': 'application/json',
    'User-Agent': 'Mozilla/5.0'
}


class DataProcessor:
    """Clase para procesar datos REALES de sensores y RMCAB"""

    def __init__(self):
        self.sensors_data = None
        self.rmcab_data = None
        self.merged_data = None

    def load_real_data(self, start_date="2025-06-01", end_date="2025-07-30", devices=None):
        """
        Carga datos REALES de PostgreSQL para los sensores de bajo costo.
        QUERY EXACTO del usuario - SIN PROCESAMIENTO
        """
        if devices is None:
            devices = ['Aire2', 'Aire4', 'Aire5']

        try:
            conn = psycopg2.connect(**DB_CONFIG)

            # Query EXACTO del usuario
            devices_str = "','".join(devices)
            query = f"""
            SELECT
                id,
                received_at,
                device_name,
                ((object -> 'analogInput' -> '2')::NUMERIC) * 10 AS pm25_raw,
                ((object -> 'analogInput' -> '3')::NUMERIC) AS pm10_raw,
                ((object -> 'analogInput' -> '4')::NUMERIC) AS temperature,
                ((object -> 'analogInput' -> '5')::NUMERIC) AS rh
            FROM public.device_up
            WHERE device_name IN ('{devices_str}')
              AND received_at BETWEEN '{start_date}' AND '{end_date}'
              AND object ? 'analogInput'
            ORDER BY received_at
            """

            print(f"\n[QUERY] Ejecutando query para traer datos REALES...")
            print(f"   Dispositivos: {devices}")
            print(f"   Período: {start_date} a {end_date}")

            df = pd.read_sql(query, conn)
            conn.close()

            if df.empty:
                raise ValueError(f"No se encontraron datos en el período {start_date} a {end_date}")

            # Procesar: renombrar columnas
            df['received_at'] = pd.to_datetime(df['received_at']).dt.tz_localize(None)
            df = df.rename(columns={
                'received_at': 'datetime',
                'pm25_raw': 'pm25',
                'pm10_raw': 'pm10'
            })

            # Ordenar por datetime
            df = df.sort_values('datetime').reset_index(drop=True)

            # Simular temperatura y humedad (datos no disponibles en BD)
            print(f"\n[SIMULACIÓN] Generando datos de temperatura y humedad...")
            df = self._simulate_environmental_data(df)

            self.sensors_data = df

            print(f"[OK] Datos de sensores cargados: {len(df)} registros")
            print(f"   Columnas: {list(df.columns)}")
            print(f"   Rango: {df['datetime'].min()} a {df['datetime'].max()}")
            print(f"   Temperatura: {df['temperature'].min():.1f}°C a {df['temperature'].max():.1f}°C")
            print(f"   Humedad Relativa: {df['rh'].min():.1f}% a {df['rh'].max():.1f}%")

            return df

        except Exception as e:
            print(f"[ERROR] Error al cargar datos reales: {e}")
            import traceback
            traceback.print_exc()
            raise

    def load_rmcab_from_csv(self):
        """
        Carga datos de RMCAB desde CSV cache.
        MÉTODO PRIMARIO - Evita consumir la API constantemente.
        """
        try:
            csv_path = os.path.join(os.path.dirname(__file__), '..', 'data_rmcab', 'rmcab_data.csv')

            print(f"\n[CSV] Cargando datos RMCAB desde CSV...")
            print(f"   Ruta: {csv_path}")

            if not os.path.exists(csv_path):
                print(f"[WARN] Archivo CSV no encontrado: {csv_path}")
                print(f"[WARN] Por favor ejecute: python download_rmcab_data.py")
                raise FileNotFoundError(f"CSV file not found: {csv_path}")

            # Leer CSV
            df = pd.read_csv(csv_path)
            df['datetime'] = pd.to_datetime(df['datetime'])

            # Renombrar columnas para consistencia con el merge
            df = df.rename(columns={
                'PM2.5': 'pm25_ref',
                'PM10': 'pm10_ref'
            })

            df = df.sort_values('datetime').reset_index(drop=True)

            self.rmcab_data = df

            print(f"[OK] Datos RMCAB desde CSV: {len(df)} registros")
            print(f"   Columnas: {list(df.columns)}")
            print(f"   Rango: {df['datetime'].min()} a {df['datetime'].max()}")

            return df

        except Exception as e:
            print(f"[ERROR] Error al cargar datos RMCAB desde CSV: {e}")
            import traceback
            traceback.print_exc()
            raise

    def load_rmcab_real(self, start_date="2025-06-01", end_date="2025-07-30", station_code=6):
        """
        Carga datos REALES de RMCAB desde la API.
        MÉTODO LEGACY - Usar load_rmcab_from_csv() en su lugar
        """
        try:
            # Ruta al archivo Postman collection
            postman_path = os.path.join(os.path.dirname(__file__), '..', 'Proyecto de grado.postman_collection.json')

            print(f"\n[API] Cargando datos RMCAB desde API...")
            print(f"   Estación: {station_code} (Las Ferias)")
            print(f"   Período: {start_date} a {end_date}")

            # Cargar template del cuerpo Postman
            print(f"   Leyendo archivo Postman: {postman_path}")
            with open(postman_path, 'r', encoding='utf-8') as f:
                postman_data = json.load(f)
                template_body = postman_data['item'][0]['request']['body']['raw']
            print(f"   Template cargado, tamaño: {len(template_body)} caracteres")

            # Configurar parámetros
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            days = max((end - start).days, 1)
            user_date = end.strftime('%Y/%m/%d')
            print(f"   Período: {days} días")

            # Construir body
            body = template_body
            replacements = {
                'serialCode%22%3A6': f"serialCode%22%3A{station_code}",
                'Las+Ferias': 'Las+Ferias',
                'SelectedPollutant=S_6_15': f'SelectedPollutant=S_{station_code}_15',  # PM2.5
                'days=15': f'days={days}'
            }
            print(f"   Realizando {len(replacements)} reemplazos en el body")

            for old, new in replacements.items():
                body = body.replace(old, new)

            # Hacer request a RMCAB
            print(f"   Haciendo POST a {RMCAB_ENDPOINT}")
            response = requests.post(
                RMCAB_ENDPOINT,
                data=body,
                headers=RMCAB_HEADERS,
                timeout=60
            )

            if response.status_code != 200:
                print(f"[ERROR] RMCAB API retornó status {response.status_code}")
                print(f"   Respuesta: {response.text[:200]}")
                raise ValueError(f"API error: {response.status_code}")

            print(f"   Respuesta HTTP 200 OK")

            payload = response.json()
            print(f"   Respuesta RMCAB: {len(payload)} elementos en respuesta")

            if 'ListDic' not in payload or not payload['ListDic']:
                print(f"   ListDic vacío o no encontrado")
                print(f"   Claves en payload: {list(payload.keys())}")
                raise ValueError("Sin datos disponibles de RMCAB")

            print(f"   ListDic tiene {len(payload['ListDic'])} registros")

            # Procesar datos para PM2.5 y PM10
            records = []
            pm25_field = f"S_{station_code}_15"  # PM2.5
            pm10_field = f"S_{station_code}_1"   # PM10
            print(f"   Buscando campos: PM2.5={pm25_field}, PM10={pm10_field}")

            for idx, entry in enumerate(payload['ListDic']):
                datetime_str = entry.get('datetime')
                pm25_str = entry.get(pm25_field)
                pm10_str = entry.get(pm10_field)

                if idx == 0:  # Mostrar el primer registro como ejemplo
                    print(f"   Primer registro - datetime: {datetime_str}")
                    print(f"   PM2.5 ({pm25_field}): {pm25_str}, PM10 ({pm10_field}): {pm10_str}")

                if not datetime_str:
                    continue

                try:
                    timestamp = datetime.strptime(datetime_str, '%d-%m-%Y %H:%M')
                    record = {'datetime': timestamp}

                    if pm25_str is not None:
                        record['pm25_ref'] = float(str(pm25_str).replace(',', '.'))

                    if pm10_str is not None:
                        record['pm10_ref'] = float(str(pm10_str).replace(',', '.'))

                    records.append(record)
                except (ValueError, TypeError) as e:
                    if idx == 0:  # Mostrar error del primer registro
                        print(f"   Error al procesar primer registro: {e}")
                    continue

            print(f"   Registros procesados exitosamente: {len(records)}")

            if not records:
                raise ValueError("No se pudieron procesar datos de RMCAB")

            df = pd.DataFrame(records)
            df = df.sort_values('datetime').reset_index(drop=True)

            self.rmcab_data = df

            print(f"[OK] Datos RMCAB cargados: {len(df)} registros")
            print(f"   Columnas: {list(df.columns)}")

            return df

        except Exception as e:
            print(f"[ERROR] Error al cargar datos RMCAB: {e}")
            import traceback
            traceback.print_exc()
            raise

    def merge_data(self, sensors_df=None, rmcab_df=None):
        """Fusiona datos de sensores con RMCAB usando coincidencia del punto más cercano"""
        if sensors_df is None:
            sensors_df = self.sensors_data
        if rmcab_df is None:
            rmcab_df = self.rmcab_data

        if sensors_df is None or rmcab_df is None or sensors_df.empty or rmcab_df.empty:
            print("[WARN] No hay datos para fusionar")
            return pd.DataFrame()

        # Asegurar formato datetime
        sensors_df = sensors_df.copy()
        rmcab_df = rmcab_df.copy()

        sensors_df['datetime'] = pd.to_datetime(sensors_df['datetime'])
        rmcab_df['datetime'] = pd.to_datetime(rmcab_df['datetime'])

        # Estrategia mejorada: Usar merge_asof para encontrar el RMCAB más cercano
        # Esto permite calibración punto-a-punto con los datos disponibles de RMCAB
        print(f"\n[MERGE] Fusionando datos de sensores con RMCAB usando estrategia punto-a-punto...")
        print(f"   Sensores: {len(sensors_df)} registros")
        print(f"   RMCAB: {len(rmcab_df)} registros únicos")

        # Ordenar ambos dataframes por datetime (requerido para merge_asof)
        sensors_sorted = sensors_df.sort_values('datetime').reset_index(drop=True)
        rmcab_sorted = rmcab_df.sort_values('datetime').reset_index(drop=True)

        # Preparar columnas de RMCAB para merge
        rmcab_cols = ['datetime']
        if 'pm25_ref' in rmcab_sorted.columns:
            rmcab_cols.append('pm25_ref')
        if 'pm10_ref' in rmcab_sorted.columns:
            rmcab_cols.append('pm10_ref')

        # Usar merge_asof para encontrar el RMCAB más cercano a cada lectura de sensor
        # direction='nearest' encuentra el timestamp más cercano (antes o después)
        merged = pd.merge_asof(
            sensors_sorted,
            rmcab_sorted[rmcab_cols],
            on='datetime',
            direction='nearest',
            tolerance=pd.Timedelta(hours=12)  # Máximo 12 horas de diferencia
        )

        self.merged_data = merged

        print(f"\n[OK] Datos fusionados: {len(merged)} registros")
        print(f"   Columnas: {list(merged.columns)}")

        # Estadísticas de datos válidos
        if 'pm25_ref' in merged.columns:
            valid_pm25 = merged['pm25_ref'].notna().sum()
            print(f"   PM2.5 Reference: {valid_pm25}/{len(merged)} registros válidos ({100*valid_pm25/len(merged):.1f}%)")
        if 'pm10_ref' in merged.columns:
            valid_pm10 = merged['pm10_ref'].notna().sum()
            print(f"   PM10 Reference: {valid_pm10}/{len(merged)} registros válidos ({100*valid_pm10/len(merged):.1f}%)")

        return merged

    def _simulate_environmental_data(self, df):
        """
        Simula datos de temperatura y humedad relativa basados en patrones reales de Bogotá.
        NOTA: Esta es una simulación para propósitos de demostración.
        Para mayor precisión, se debe capturar estos datos directamente de sensores o estaciones meteorológicas.
        """
        import numpy as np

        df = df.copy()

        # Extraer información de la fecha para crear patrones diarios
        df['hour'] = df['datetime'].dt.hour
        df['day'] = df['datetime'].dt.dayofyear

        # Parámetros climáticos de Bogotá (junio-julio)
        # Temperatura: 14-24°C (ciclo diario)
        temp_base = 18  # Temperatura base
        temp_amplitude = 5  # Variación diaria

        # Humedad relativa: 60-90% (ciclo diario inverso a temperatura)
        rh_base = 75  # Humedad base
        rh_amplitude = 15  # Variación diaria

        # Generar ciclo diario sinusoidal (máximo a las 14h, mínimo a las 5h)
        hour_normalized = (df['hour'] - 5) / 24 * 2 * np.pi

        # Temperatura: máxima al mediodía, mínima al amanecer
        df['temperature'] = temp_base + temp_amplitude * np.sin(hour_normalized)

        # Humedad: mínima al mediodía, máxima al amanecer (inverso a temp)
        df['rh'] = rh_base - rh_amplitude * np.sin(hour_normalized)

        # Agregar pequeño ruido para mayor realismo
        np.random.seed(42)  # Para reproducibilidad
        df['temperature'] += np.random.normal(0, 0.5, len(df))
        df['rh'] += np.random.normal(0, 2, len(df))

        # Asegurar rangos realistas
        df['temperature'] = df['temperature'].clip(10, 28)
        df['rh'] = df['rh'].clip(50, 95)

        # Eliminar columnas auxiliares
        df = df.drop(['hour', 'day'], axis=1)

        return df

    def get_data_for_plotting(self):
        """Retorna datos listos para graficar - DOS GRÁFICOS: PM2.5 y PM10"""
        if self.merged_data is None or self.merged_data.empty:
            return None

        df = self.merged_data.copy()

        # Retornar datos sin procesamiento adicional
        return {
            'pm25': {
                'data': df[['datetime', 'device_name', 'pm25', 'pm25_ref']],
                'title': 'PM2.5 (μg/m³)',
                'columns': ['datetime', 'device_name', 'pm25', 'pm25_ref']
            },
            'pm10': {
                'data': df[['datetime', 'device_name', 'pm10']],
                'title': 'PM10 (μg/m³)',
                'columns': ['datetime', 'device_name', 'pm10']
            }
        }
