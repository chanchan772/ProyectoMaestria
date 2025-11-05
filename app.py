"""
Aplicación Web - Monitoreo de Calidad del Aire
Proyecto de Maestría en Analítica de Datos - Universidad Central
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
from dotenv import load_dotenv
import json
import pandas as pd
import numpy as np

# Cargar variables de entorno
load_dotenv()

# Inicializar Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Importar módulos personalizados
from modules.data_loader import load_lowcost_data, load_rmcab_data, RMCAB_STATION_INFO
from modules.calibration import (get_calibration_models, train_and_evaluate_models, run_device_calibration,
                                  load_calibration_model, predict_with_saved_model)
from modules.visualization import create_timeseries_plot, create_boxplot, create_heatmap
from modules.metrics import calculate_statistics

DEVICE_LABELS = {
    'Aire2': 'Sensor Aire2',
    'Aire4': 'Sensor Aire4',
    'Aire5': 'Sensor Aire5'
}


def safe_number(value, decimals=4):
    """
    Normaliza valores numericos evitando NaN o infinitos antes de serializar.
    """
    try:
        if value is None:
            return None
        if isinstance(value, bool):
            return float(value)
        if not np.isfinite(value):
            return None
        return round(float(value), decimals)
    except Exception:
        return None

# =======================
# RUTAS PRINCIPALES
# =======================

@app.route('/')
def index():
    """Página principal del proyecto"""
    return render_template('index.html')

@app.route('/modelos')
def modelos():
    """Página de modelos de calibración y predicción"""
    return render_template('modelos.html')

@app.route('/definiciones')
def definiciones():
    """Página de definiciones técnicas y conceptos"""
    return render_template('definiciones.html')

@app.route('/acerca-de')
def acerca_de():
    """Página sobre el equipo y el proyecto"""
    return render_template('acerca_de.html')

@app.route('/visualizacion/junio-julio')
def visualizacion_junio_julio():
    """Página de visualización Junio-Julio 2025 (Sensores + Las Ferias)"""
    return render_template('visualizacion_junio_julio.html')

@app.route('/visualizacion/2024')
def visualizacion_2024():
    """Página de visualización Periodo Completo 2024 (Sensores + Min Ambiente)"""
    return render_template('visualizacion_2024.html')

# =======================
# API ENDPOINTS
# =======================

@app.route('/api/load-lowcost-data', methods=['POST'])
def api_load_lowcost():
    """Carga datos de sensores de bajo costo desde PostgreSQL"""
    try:
        data = load_lowcost_data()
        if data is None or data.empty:
            return jsonify({'error': 'No se encontraron datos'}), 404

        # Convertir a formato JSON
        data_json = data.to_json(orient='records', date_format='iso')
        return jsonify({
            'success': True,
            'records': len(data),
            'data': json.loads(data_json)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calibration-summary', methods=['POST'])
def api_calibration_summary():
    """Genera un resumen de calibración para todos los sensores solicitados"""
    try:
        payload = request.json or {}
        start_date = payload.get('start_date', '2025-06-01')
        end_date = payload.get('end_date', '2025-07-31')
        devices = payload.get('devices') or ['Aire2', 'Aire4', 'Aire5']
        pollutants = payload.get('pollutants') or ['pm25', 'pm10']
        station_code = payload.get('station_code', 6)

        lowcost_data = load_lowcost_data(start_date, end_date, devices)
        rmcab_data = load_rmcab_data(station_code, start_date, end_date)

        if (
            lowcost_data is None or rmcab_data is None or
            lowcost_data.empty or rmcab_data.empty
        ):
            return jsonify({
                'success': False,
                'error': 'No se pudieron cargar los datos necesarios para la calibración'
            }), 400

        sensor_summaries = []
        for device in devices:
            device_data = lowcost_data[lowcost_data['device_name'] == device].copy()

            if device_data.empty:
                sensor_summaries.append({
                    'device': device,
                    'label': DEVICE_LABELS.get(device, device),
                    'pollutant_results': [],
                    'error': 'No hay datos disponibles para el periodo seleccionado'
                })
                continue

            # Determinar período basado en las fechas
            period = '2025' if '2025' in start_date else '2024'
            calibration = run_device_calibration(device_data, rmcab_data, device, tuple(pollutants), period=period)
            calibration['label'] = DEVICE_LABELS.get(device, device)
            sensor_summaries.append(calibration)

        reference_info = RMCAB_STATION_INFO.get(station_code, {})

        return jsonify({
            'success': True,
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'reference': {
                'station_code': station_code,
                'station_name': reference_info.get('name', f'RMCAB {station_code}')
            },
            'sensors': sensor_summaries
        })

    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/api/load-rmcab-data', methods=['POST'])
def api_load_rmcab():
    """Carga datos de RMCAB desde la API"""
    try:
        station_code = request.json.get('station_code', 6)  # Default: Las Ferias
        data = load_rmcab_data(station_code)

        if data is None or data.empty:
            return jsonify({'error': 'No se encontraron datos'}), 404

        data_json = data.to_json(orient='records', date_format='iso')
        return jsonify({
            'success': True,
            'records': len(data),
            'data': json.loads(data_json)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calibrate', methods=['POST'])
def api_calibrate():
    """Ejecuta el proceso de calibración con múltiples modelos"""
    try:
        # Cargar datos
        lowcost_data = load_lowcost_data()
        rmcab_data = load_rmcab_data()

        if lowcost_data is None or rmcab_data is None:
            return jsonify({'error': 'No se pudieron cargar los datos'}), 404

        # Ejecutar calibración
        calibration = train_and_evaluate_models(lowcost_data, rmcab_data)

        if calibration.get('error'):
            return jsonify({'success': False, 'error': calibration['error']}), 400

        return jsonify({
            'success': True,
            'records': calibration.get('records', 0),
            'best_model': calibration.get('best_model'),
            'results': calibration.get('results', [])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics', methods=['POST'])
def api_statistics():
    """Calcula estadísticas descriptivas de los datos"""
    try:
        data_type = request.json.get('data_type', 'lowcost')

        if data_type == 'lowcost':
            data = load_lowcost_data()
        else:
            data = load_rmcab_data()

        if data is None or data.empty:
            return jsonify({'error': 'No se encontraron datos'}), 404

        stats = calculate_statistics(data)

        return jsonify({
            'success': True,
            'statistics': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/visualize', methods=['POST'])
def api_visualize():
    """Genera visualizaciones de datos"""
    try:
        plot_type = request.json.get('plot_type', 'timeseries')
        data_type = request.json.get('data_type', 'lowcost')

        # Cargar datos
        if data_type == 'lowcost':
            data = load_lowcost_data()
        else:
            data = load_rmcab_data()

        if data is None or data.empty:
            return jsonify({'error': 'No se encontraron datos'}), 404

        # Generar visualización
        if plot_type == 'timeseries':
            fig = create_timeseries_plot(data)
        elif plot_type == 'boxplot':
            fig = create_boxplot(data)
        elif plot_type == 'heatmap':
            fig = create_heatmap(data)
        else:
            return jsonify({'error': 'Tipo de gráfico no válido'}), 400

        # Convertir a JSON
        fig_json = fig.to_json()

        return jsonify({
            'success': True,
            'plot': json.loads(fig_json)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/load-device-data', methods=['POST'])
def api_load_device_data():
    """Carga datos de un dispositivo específico"""
    try:
        device_name = request.json.get('device_name')
        start_date = request.json.get('start_date', '2024-06-01')
        end_date = request.json.get('end_date', '2024-07-31')

        data = load_lowcost_data(start_date, end_date, [device_name])

        if data is None or data.empty:
            return jsonify({'error': f'No se encontraron datos para {device_name}'}), 404

        data_json = data.to_json(orient='records', date_format='iso')
        return jsonify({
            'success': True,
            'device': device_name,
            'records': len(data),
            'data': json.loads(data_json)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calibrate-device', methods=['POST'])
def api_calibrate_device():
    """Ejecuta calibración para un dispositivo específico"""
    try:
        device_name = request.json.get('device_name')
        start_date = request.json.get('start_date', '2024-06-01')
        end_date = request.json.get('end_date', '2024-07-31')
        pollutant = request.json.get('pollutant', 'pm25')

        if not device_name:
            return jsonify({'error': 'Debe proporcionar el nombre del dispositivo'}), 400

        lowcost_data = load_lowcost_data(start_date, end_date, [device_name])
        rmcab_data = load_rmcab_data(6, start_date, end_date)  # Las Ferias

        if (
            lowcost_data is None or rmcab_data is None or
            lowcost_data.empty or rmcab_data.empty
        ):
            return jsonify({'error': 'No se pudieron cargar los datos'}), 404

        device_data = lowcost_data[lowcost_data['device_name'] == device_name].copy()
        if device_data.empty:
            return jsonify({'error': 'El dispositivo no tiene datos en el periodo indicado'}), 404

        # Determinar período basado en las fechas
        period = '2025' if '2025' in start_date else '2024'
        calibration = run_device_calibration(device_data, rmcab_data, device_name, (pollutant,), period=period)
        pollutant_results = calibration.get('pollutant_results', [])
        pollutant_entry = pollutant_results[0] if pollutant_results else None

        if not pollutant_entry or pollutant_entry.get('error'):
            message = pollutant_entry.get('error') if pollutant_entry else 'No se obtuvieron resultados de calibración'
            return jsonify({'error': message}), 400

        return jsonify({
            'success': True,
            'device': device_name,
            'pollutant': pollutant,
            'records': pollutant_entry.get('records', 0),
            'results': pollutant_entry.get('models', []),
            'linear_regression': pollutant_entry.get('linear_regression'),
            'scatter': pollutant_entry.get('scatter')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calibrate-multiple-devices', methods=['POST'])
def api_calibrate_multiple_devices():
    """Ejecuta calibración para múltiples dispositivos con múltiples contaminantes"""
    try:
        devices = request.json.get('devices', ['Aire2', 'Aire4', 'Aire5'])
        start_date = request.json.get('start_date', '2024-06-01')
        end_date = request.json.get('end_date', '2024-07-31')
        pollutants = request.json.get('pollutants', ['pm25'])  # Soportar múltiples contaminantes

        print(f"\n{'='*60}")
        print(f"CALIBRACIÓN MÚLTIPLE INICIADA")
        print(f"{'='*60}")
        print(f"Dispositivos: {devices}")
        print(f"Periodo: {start_date} a {end_date}")
        print(f"Contaminantes: {pollutants}")

        # Cargar datos de todos los sensores
        print(f"\n📊 Cargando datos de sensores...")
        lowcost_data = load_lowcost_data(start_date, end_date, devices)
        print(f"✅ Datos lowcost cargados: {len(lowcost_data) if lowcost_data is not None and not lowcost_data.empty else 0} registros")
        
        print(f"\n📊 Cargando datos de RMCAB...")
        rmcab_data = load_rmcab_data(6, start_date, end_date)  # Las Ferias
        print(f"✅ Datos RMCAB cargados: {len(rmcab_data) if rmcab_data is not None and not rmcab_data.empty else 0} registros")

        if (
            lowcost_data is None or rmcab_data is None or
            lowcost_data.empty or rmcab_data.empty
        ):
            error_msg = 'No se pudieron cargar los datos'
            print(f"❌ ERROR: {error_msg}")
            return jsonify({'error': error_msg}), 404

        # Calibrar cada dispositivo
        results_by_device = {}
        
        for device_name in devices:
            print(f"\n{'='*60}")
            print(f"📡 Calibrando {device_name}...")
            print(f"{'='*60}")
            
            device_data = lowcost_data[lowcost_data['device_name'] == device_name].copy()
            
            if device_data.empty:
                error_msg = f'No hay datos para {device_name} en el periodo indicado'
                print(f"⚠️  {error_msg}")
                results_by_device[device_name] = {
                    'success': False,
                    'error': error_msg
                }
                continue

            print(f"📊 Registros de {device_name}: {len(device_data)}")

            try:
                # Determinar período basado en las fechas
                period = '2025' if '2025' in start_date else '2024'
                calibration = run_device_calibration(device_data, rmcab_data, device_name, tuple(pollutants), period=period)
                pollutant_results = calibration.get('pollutant_results', [])

                if not pollutant_results or any(pr.get('error') for pr in pollutant_results):
                    errors = [pr.get('error') for pr in pollutant_results if pr.get('error')]
                    message = '; '.join(errors) if errors else 'No se obtuvieron resultados'
                    print(f"❌ Error en calibración de {device_name}: {message}")
                    results_by_device[device_name] = {
                        'success': False,
                        'error': message
                    }
                else:
                    print(f"✅ {device_name} calibrado exitosamente")
                    print(f"   - Contaminantes: {len(pollutant_results)}")
                    for pr in pollutant_results:
                        print(f"   - {pr.get('pollutant_label')}: {pr.get('records', 0)} registros, {len(pr.get('models', []))} modelos")
                    
                    results_by_device[device_name] = {
                        'success': True,
                        'device': device_name,
                        'pollutant_results': pollutant_results
                    }
            except Exception as device_error:
                error_msg = str(device_error)
                print(f"❌ Excepción en {device_name}: {error_msg}")
                import traceback
                traceback.print_exc()
                results_by_device[device_name] = {
                    'success': False,
                    'error': error_msg
                }

        # Verificar si al menos uno tuvo éxito
        success_count = sum(1 for r in results_by_device.values() if r.get('success'))
        
        print(f"\n{'='*60}")
        print(f"RESUMEN DE CALIBRACIÓN")
        print(f"{'='*60}")
        print(f"Exitosos: {success_count}/{len(devices)}")
        for device, result in results_by_device.items():
            status = "✅" if result.get('success') else "❌"
            print(f"{status} {device}: {result.get('error', 'OK')}")
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': success_count > 0,
            'devices_calibrated': success_count,
            'total_devices': len(devices),
            'results_by_device': results_by_device
        })
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ ERROR GENERAL: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

@app.route('/api/predict-with-calibration', methods=['POST'])
def api_predict_with_calibration():
    """
    Realiza predicción con modelo calibrado para una fecha específica y compara con RMCAB
    Soporta dos modos:
    - Modo 1: Con datos reales del sensor (automático)
    - Modo 2: Con valores manuales ingresados por el usuario (cuando no hay datos)
    """
    import sys

    try:
        payload = request.json or {}
        device_name = payload.get('device_name')
        pollutant = payload.get('pollutant', 'pm25')
        target_date = payload.get('target_date')  # Formato: YYYY-MM-DD
        period = payload.get('period', '2025')
        station_code = payload.get('station_code', 6)

        # Valores manuales (opcionales)
        manual_values = payload.get('manual_values')  # {'pm25_sensor': 15.5, 'temperature': 14.0, 'rh': 70.0}

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"PREDICCIÓN CON MODELO CALIBRADO", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"Dispositivo: {device_name}", file=sys.stderr)
        print(f"Contaminante: {pollutant}", file=sys.stderr)
        print(f"Fecha objetivo: {target_date}", file=sys.stderr)
        print(f"Período: {period}", file=sys.stderr)
        print(f"Modo: {'Manual' if manual_values else 'Datos Reales'}", file=sys.stderr)

        # Validar parámetros
        if not device_name or not target_date:
            return jsonify({'error': 'Faltan parámetros requeridos (device_name, target_date)'}), 400

        # Cargar modelo calibrado
        print(f"\n📂 Cargando modelo calibrado...", file=sys.stderr)
        model_info = load_calibration_model(device_name, pollutant, period)

        if model_info is None:
            return jsonify({
                'error': f'No se encontró modelo calibrado para {device_name} - {pollutant} ({period}). Ejecuta primero la calibración.'
            }), 404

        print(f"✅ Modelo cargado: {model_info.get('model_name')}", file=sys.stderr)
        print(f"   Features: {model_info.get('feature_names')}", file=sys.stderr)

        from datetime import datetime, timedelta
        import numpy as np
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')

        # Intentar cargar datos reales del sensor
        sensor_start_date = target_dt.strftime('%Y-%m-%d')
        sensor_end_date = (target_dt + timedelta(days=1)).strftime('%Y-%m-%d')
        rmcab_start_date = (target_dt - timedelta(days=1)).strftime('%Y-%m-%d')
        rmcab_end_date = (target_dt + timedelta(days=1)).strftime('%Y-%m-%d')

        sensor_data = None
        use_manual_mode = False

        if manual_values:
            # MODO MANUAL: Usuario proveyó valores
            use_manual_mode = True
            print(f"\n🔧 Usando valores manuales provisto por el usuario")
        else:
            # MODO AUTOMÁTICO: Intentar cargar datos reales
            print(f"\n📊 Intentando cargar datos del sensor para {target_date}...")
            try:
                sensor_data = load_lowcost_data(sensor_start_date, sensor_end_date, [device_name])
                if sensor_data is not None and not sensor_data.empty:
                    sensor_data = sensor_data[sensor_data['datetime'].dt.date == target_dt.date()].copy()
                    if sensor_data.empty:
                        sensor_data = None
            except Exception as e:
                print(f"⚠️ No se pudieron cargar datos reales: {e}")
                sensor_data = None

            if sensor_data is None or sensor_data.empty:
                print(f"⚠️ No hay datos reales disponibles")
                # Sugerir usar modo manual
                return jsonify({
                    'error': f'No hay datos del sensor {device_name} para la fecha {target_date}',
                    'suggestion': 'use_manual_mode',
                    'message': 'No hay datos reales disponibles. Por favor ingresa valores manualmente.'
                }), 404
            else:
                print(f"✅ Datos del sensor cargados: {len(sensor_data)} registros")
                print(f"   Columnas en datos reales: {sensor_data.columns.tolist()}")

        # Crear DataFrame con datos (reales o manuales)
        if use_manual_mode:
            # Crear 24 registros horarios con valores manuales
            hours = pd.date_range(
                start=f'{target_date} 00:00:00',
                end=f'{target_date} 23:00:00',
                freq='H'
            )

            sensor_data = pd.DataFrame({
                'datetime': hours,
                f'{pollutant}_sensor': [manual_values.get(f'{pollutant}_sensor', 15.0)] * 24,
                'temperature': [manual_values.get('temperature', 14.0)] * 24,
                'rh': [manual_values.get('rh', 70.0)] * 24
            })

            print(f"✅ Creados {len(sensor_data)} registros con valores manuales:")
            print(f"   PM2.5: {manual_values.get(f'{pollutant}_sensor')} µg/m³")
            print(f"   Temperatura: {manual_values.get('temperature')} °C")
            print(f"   Humedad: {manual_values.get('rh')} %")

        # Agregar variables temporales si no existen
        if 'hour' not in sensor_data.columns:
            sensor_data['hour'] = sensor_data['datetime'].dt.hour
        if 'period_of_day' not in sensor_data.columns:
            sensor_data['period_of_day'] = pd.cut(
                sensor_data['hour'],
                bins=[-0.1, 6, 12, 18, 24],
                labels=[0, 1, 2, 3]
            ).astype(int)
        if 'day_of_week' not in sensor_data.columns:
            sensor_data['day_of_week'] = sensor_data['datetime'].dt.dayofweek
        if 'is_weekend' not in sensor_data.columns:
            sensor_data['is_weekend'] = (sensor_data['day_of_week'] >= 5).astype(int)

        # Verificar que tenemos todas las features necesarias
        feature_names = model_info.get('feature_names', [])

        print(f"\n🔍 Verificando features:")
        print(f"   Features requeridas por el modelo: {feature_names}")
        print(f"   Columnas disponibles en sensor_data: {sensor_data.columns.tolist()}")

        missing_features = [f for f in feature_names if f not in sensor_data.columns]

        if missing_features:
            print(f"❌ Faltan features: {missing_features}")
            print(f"   Datos de sensor_data (primeras 3 filas):")
            print(sensor_data.head(3))
            return jsonify({
                'error': f'Faltan features en los datos del sensor: {missing_features}',
                'required_features': feature_names,
                'available_columns': sensor_data.columns.tolist(),
                'suggestion': f'El modelo fue entrenado con {pollutant} pero faltan columnas necesarias'
            }), 400

        # Realizar predicción
        print(f"\n🔮 Realizando predicción...")
        predictions = predict_with_saved_model(model_info, sensor_data)

        if predictions is None:
            return jsonify({
                'error': 'No se pudo realizar la predicción con el modelo'
            }), 500

        print(f"✅ Predicciones realizadas: {len(predictions)} valores")

        # Agregar predicciones al DataFrame
        sensor_data['predicted'] = predictions

        # Cargar datos de RMCAB para comparación
        print(f"\n📊 Cargando datos de RMCAB para comparación...")
        rmcab_data = load_rmcab_data(station_code, rmcab_start_date, rmcab_end_date)

        if rmcab_data is None or rmcab_data.empty:
            print(f"⚠️ No hay datos de RMCAB para {target_date}")
            rmcab_available = False
        else:
            # Filtrar solo el día específico
            filtered_rmcab = rmcab_data[rmcab_data['datetime'].dt.date == target_dt.date()].copy()

            if filtered_rmcab.empty:
                shifted_rmcab = rmcab_data.copy()
                shifted_rmcab['datetime'] = shifted_rmcab['datetime'] - pd.Timedelta(days=1)
                filtered_rmcab = shifted_rmcab[shifted_rmcab['datetime'].dt.date == target_dt.date()].copy()
                if not filtered_rmcab.empty:
                    print("INFO: Ajustando RMCAB restando 1 día por desfase en la fuente")

            rmcab_data = filtered_rmcab
            rmcab_available = not rmcab_data.empty
            if rmcab_available:
                print(f"✅ Datos RMCAB cargados: {len(rmcab_data)} registros")

        # Preparar resultados
        results = []
        for idx, row in sensor_data.iterrows():
            result_entry = {
                'datetime': row['datetime'].isoformat(),
                'sensor_raw': safe_number(row.get(f'{pollutant}_sensor')),
                'predicted': safe_number(row.get('predicted')),
                'temperature': safe_number(row.get('temperature'), decimals=2) if 'temperature' in row else None,
                'rh': safe_number(row.get('rh'), decimals=2) if 'rh' in row else None
            }

            # Buscar valor de RMCAB correspondiente
            if rmcab_available:
                # Buscar en RMCAB el registro más cercano (tolerancia de 1 hora)
                time_diff = abs(rmcab_data['datetime'] - row['datetime'])
                closest_idx = time_diff.idxmin()

                if time_diff.loc[closest_idx] <= pd.Timedelta('1H'):
                    rmcab_value = rmcab_data.loc[closest_idx, f'{pollutant}_ref']
                    result_entry['rmcab_reference'] = safe_number(rmcab_value)

                    # Calcular error
                    predicted_value = row.get('predicted')
                    if predicted_value is not None and np.isfinite(predicted_value) and np.isfinite(rmcab_value):
                        error = predicted_value - rmcab_value
                        abs_error = abs(error)
                    else:
                        abs_error = None
                    result_entry['error'] = safe_number(abs_error)
                    if rmcab_value > 0 and np.isfinite(rmcab_value) and abs_error is not None:
                        result_entry['error_percentage'] = safe_number((abs_error / rmcab_value) * 100, decimals=2)
                    else:
                        result_entry['error_percentage'] = None
                else:
                    result_entry['rmcab_reference'] = None
            else:
                result_entry['rmcab_reference'] = None

            results.append(result_entry)

        # Calcular estadísticas de error si hay datos de RMCAB
        error_stats = None
        if rmcab_available:
            valid_results = [
                r for r in results
                if r.get('rmcab_reference') is not None
                and r.get('predicted') is not None
                and r.get('sensor_raw') is not None
            ]
            if valid_results:
                errors = [r['error'] for r in valid_results if r.get('error') is not None]
                mean_error = np.mean(errors) if errors else None
                max_error = np.max(errors) if errors else None
                min_error = np.min(errors) if errors else None
                predictions_vals = [r['predicted'] for r in valid_results]
                rmcab_vals = [r['rmcab_reference'] for r in valid_results]

                from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
                import numpy as np

                # Calcular también error del sensor sin calibrar
                sensor_raw_vals = [r['sensor_raw'] for r in valid_results]
                rmse_raw = np.sqrt(mean_squared_error(rmcab_vals, sensor_raw_vals))
                mae_raw = mean_absolute_error(rmcab_vals, sensor_raw_vals)
                r2_raw = r2_score(rmcab_vals, sensor_raw_vals)

                rmse_calibrated = np.sqrt(mean_squared_error(rmcab_vals, predictions_vals))
                mae_calibrated = mean_absolute_error(rmcab_vals, predictions_vals)
                r2_calibrated = r2_score(rmcab_vals, predictions_vals)

                rmse_improvement_pct = 0
                if np.isfinite(rmse_raw) and rmse_raw > 0 and np.isfinite(rmse_calibrated):
                    rmse_improvement_pct = safe_number((rmse_raw - rmse_calibrated) / rmse_raw * 100, decimals=2)

                mae_improvement_pct = 0
                if np.isfinite(mae_raw) and mae_raw > 0 and np.isfinite(mae_calibrated):
                    mae_improvement_pct = safe_number((mae_raw - mae_calibrated) / mae_raw * 100, decimals=2)

                error_stats = {
                    'rmse': safe_number(rmse_calibrated),
                    'mae': safe_number(mae_calibrated),
                    'r2': safe_number(r2_calibrated),
                    'mean_error': safe_number(mean_error),
                    'max_error': safe_number(max_error),
                    'min_error': safe_number(min_error),
                    'comparisons_count': len(valid_results),
                    # Métricas sin calibrar
                    'rmse_raw': safe_number(rmse_raw),
                    'mae_raw': safe_number(mae_raw),
                    'r2_raw': safe_number(r2_raw),
                    # Mejora porcentual
                    'rmse_improvement_pct': rmse_improvement_pct,
                    'mae_improvement_pct': mae_improvement_pct
                }

        # Calcular estadísticas descriptivas
        descriptive_stats = {
            'sensor_raw': {
                'mean': safe_number(sensor_data[f'{pollutant}_sensor'].mean()),
                'median': safe_number(sensor_data[f'{pollutant}_sensor'].median()),
                'std': safe_number(sensor_data[f'{pollutant}_sensor'].std()),
                'min': safe_number(sensor_data[f'{pollutant}_sensor'].min()),
                'max': safe_number(sensor_data[f'{pollutant}_sensor'].max())
            },
            'predicted': {
                'mean': safe_number(sensor_data['predicted'].mean()),
                'median': safe_number(sensor_data['predicted'].median()),
                'std': safe_number(sensor_data['predicted'].std()),
                'min': safe_number(sensor_data['predicted'].min()),
                'max': safe_number(sensor_data['predicted'].max())
            }
        }

        if rmcab_available:
            valid_rmcab_vals = [r['rmcab_reference'] for r in results if r.get('rmcab_reference') is not None]
            if valid_rmcab_vals:
                descriptive_stats['rmcab'] = {
                    'mean': safe_number(np.mean(valid_rmcab_vals)),
                    'median': safe_number(np.median(valid_rmcab_vals)),
                    'std': safe_number(np.std(valid_rmcab_vals)),
                    'min': safe_number(np.min(valid_rmcab_vals)),
                    'max': safe_number(np.max(valid_rmcab_vals))
                }

        print(f"\n{'='*60}")
        print(f"PREDICCIÓN COMPLETADA")
        print(f"{'='*60}")
        print(f"Registros predichos: {len(results)}")
        if error_stats:
            print(f"RMSE: {error_stats['rmse']}")
            print(f"MAE: {error_stats['mae']}")
            print(f"R²: {error_stats['r2']}")
            print(f"Mejora RMSE: {error_stats.get('rmse_improvement_pct', 0)}%")
            print(f"Mejora MAE: {error_stats.get('mae_improvement_pct', 0)}%")
        print(f"{'='*60}\n")

        return jsonify({
            'success': True,
            'device_name': device_name,
            'pollutant': pollutant,
            'target_date': target_date,
            'period': period,
            'mode': 'manual' if use_manual_mode else 'real_data',
            'model_info': {
                'model_name': model_info.get('model_name'),
                'metrics': model_info.get('metrics'),
                'feature_names': feature_names
            },
            'predictions': results,
            'error_stats': error_stats,
            'descriptive_stats': descriptive_stats,
            'rmcab_available': rmcab_available,
            'records_count': len(results)
        })

    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ ERROR EN PREDICCIÓN: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

# =======================
# MANEJO DE ERRORES
# =======================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# =======================
# INICIAR APLICACIÓN
# =======================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    # Desactivar reloader para evitar interrupciones durante calibración
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False)
