"""
Script para descargar datos de RMCAB directamente desde el API de MonitorsVal
Guarda los datos en CSV para uso posterior sin consumir la API constantemente
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import os
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Configuración
RMCAB_URL = 'http://rmcab.ambientebogota.gov.co/home/MonitorsVal'
STATION_CODE = 6  # Las Ferias
START_DATE = '2025-06-01'
END_DATE = '2025-07-30'
OUTPUT_DIR = 'data_rmcab'
POSTMAN_FILE = 'Proyecto de grado.postman_collection.json'

# Headers para simular browser
HEADERS = {
    'Accept': '*/*',
    'Accept-Language': 'es-ES,es;q=0.9,it;q=0.8',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'http://rmcab.ambientebogota.gov.co',
    'Referer': 'http://rmcab.ambientebogota.gov.co/home/map',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 OPR/124.0.0.0',
    'X-Requested-With': 'XMLHttpRequest'
}

def get_postman_request_body():
    """Extrae el template del body del archivo Postman"""
    try:
        postman_path = os.path.join(os.path.dirname(__file__), POSTMAN_FILE)
        logging.info(f'Leyendo Postman collection desde: {postman_path}')

        if not os.path.exists(postman_path):
            logging.error(f'Archivo Postman no encontrado: {postman_path}')
            return None

        with open(postman_path, 'r', encoding='utf-8') as f:
            postman_data = json.load(f)

        # Extraer el body del primer request
        if 'item' in postman_data and len(postman_data['item']) > 0:
            request_obj = postman_data['item'][0].get('request', {})
            body_obj = request_obj.get('body', {})
            template_body = body_obj.get('raw', '')

            if template_body:
                logging.info(f'Template extraído correctamente (tamaño: {len(template_body)} caracteres)')
                return template_body

        logging.warning('No se encontró body en Postman collection')
        return None
    except Exception as e:
        logging.error(f'Error al leer Postman: {e}')
        return None

def download_pollutant(pollutant_name, selected_pollutant_code, days=60):
    """
    Descarga datos de un contaminante específico usando el template de Postman
    pollutant_name: 'PM2.5' o 'PM10'
    selected_pollutant_code: 'S_6_15' para PM2.5, 'S_6_1' para PM10
    """
    logging.info(f'[*] Descargando datos de {pollutant_name}...')

    try:
        # Obtener template del body
        template_body = get_postman_request_body()
        if not template_body:
            logging.error(f'No se pudo obtener template para {pollutant_name}')
            return None

        # Calcular período
        end_date_obj = datetime.strptime(END_DATE, '%Y-%m-%d')
        user_date = end_date_obj.strftime('%Y/%m/%d')

        # Reemplazar parámetros en el template
        body = template_body
        body = body.replace(f'SelectedPollutant=S_6_15', f'SelectedPollutant={selected_pollutant_code}')
        body = body.replace(f'SelectedPollutant=S_6_1', f'SelectedPollutant={selected_pollutant_code}')
        body = body.replace('days=15', f'days={days}')
        body = body.replace('serialCode%22%3A6', f'serialCode%22%3A{STATION_CODE}')

        logging.info(f'[*] Enviando request a RMCAB para {pollutant_name}...')
        response = requests.post(RMCAB_URL, data=body, headers=HEADERS, timeout=60)

        logging.info(f'[*] Status HTTP: {response.status_code}')

        if response.status_code != 200:
            logging.error(f'[ERROR] Status {response.status_code}')
            logging.error(f'[ERROR] Response: {response.text[:500]}')
            return None

        # Parsear JSON
        try:
            json_response = response.json()
            logging.info(f'[*] JSON parseado exitosamente')
        except json.JSONDecodeError as e:
            logging.error(f'[ERROR] JSON inválido: {e}')
            logging.error(f'[ERROR] Primeros 500 chars: {response.text[:500]}')
            return None

        # Extraer datos
        if 'ListDic' not in json_response or not json_response['ListDic']:
            logging.warning(f'[WARN] Sin datos en ListDic para {pollutant_name}')
            logging.info(f'[*] Claves en respuesta: {list(json_response.keys())}')
            return pd.DataFrame()

        logging.info(f'[*] Procesando {len(json_response["ListDic"])} registros...')
        records = []
        for idx, entry in enumerate(json_response['ListDic']):
            datetime_str = entry.get('datetime')
            value_str = entry.get(selected_pollutant_code)

            if datetime_str and value_str is not None:
                try:
                    timestamp = datetime.strptime(datetime_str, '%d-%m-%Y %H:%M')
                    value = float(str(value_str).replace(',', '.'))
                    records.append({
                        'datetime': timestamp,
                        'pollutant': pollutant_name,
                        'value': value
                    })
                except (ValueError, TypeError) as e:
                    if idx == 0:
                        logging.debug(f'[DEBUG] Error al procesar: {e}')
                    continue

        if not records:
            logging.warning(f'[WARN] No se procesaron registros para {pollutant_name}')
            return pd.DataFrame()

        df = pd.DataFrame(records)
        df = df.sort_values('datetime').reset_index(drop=True)

        logging.info(f'[OK] {pollutant_name}: {len(df)} registros descargados')
        return df

    except requests.exceptions.RequestException as e:
        logging.error(f'[ERROR] Request error para {pollutant_name}: {e}')
        return None
    except Exception as e:
        logging.error(f'[ERROR] Excepción para {pollutant_name}: {e}')
        import traceback
        traceback.print_exc()
        return None

def main():
    """Función principal"""

    # Crear directorio de datos si no existe
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    logging.info('Iniciando descarga de datos RMCAB...')
    logging.info(f'Período: {START_DATE} a {END_DATE}')
    logging.info(f'Estación: Las Ferias (código {STATION_CODE})')

    # Descargar PM2.5
    df_pm25 = download_pollutant('PM2.5', 'S_6_15', days=60)
    if df_pm25 is None or df_pm25.empty:
        logging.error('Error al descargar PM2.5')
        return False

    # Descargar PM10
    df_pm10 = download_pollutant('PM10', 'S_6_1', days=60)
    if df_pm10 is None or df_pm10.empty:
        logging.error('Error al descargar PM10')
        return False

    # Combinar datos
    df_combined = pd.concat([df_pm25, df_pm10], ignore_index=True)

    # Pivotar para tener PM2.5 y PM10 en columnas
    df_pivot = df_combined.pivot_table(
        index='datetime',
        columns='pollutant',
        values='value',
        aggfunc='first'
    ).reset_index()

    # Guardar en CSV
    output_file = os.path.join(OUTPUT_DIR, 'rmcab_data.csv')
    df_pivot.to_csv(output_file, index=False)

    logging.info(f'[OK] Datos guardados en {output_file}')
    logging.info(f'Total de registros: {len(df_pivot)}')
    logging.info(f'Período: {df_pivot["datetime"].min()} a {df_pivot["datetime"].max()}')

    return True

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
