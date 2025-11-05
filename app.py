"""
Aplicación Web - Monitoreo de Calidad del Aire
Proyecto de Maestría en Analítica de Datos - Universidad Central
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
from dotenv import load_dotenv
import json

# Cargar variables de entorno
load_dotenv()

# Inicializar Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Importar módulos personalizados
from modules.data_loader import load_lowcost_data, load_rmcab_data, RMCAB_STATION_INFO
from modules.calibration import get_calibration_models, train_and_evaluate_models, run_device_calibration
from modules.visualization import create_timeseries_plot, create_boxplot, create_heatmap
from modules.metrics import calculate_statistics

DEVICE_LABELS = {
    'Aire2': 'Sensor Aire2',
    'Aire4': 'Sensor Aire4',
    'Aire5': 'Sensor Aire5'
}

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

            calibration = run_device_calibration(device_data, rmcab_data, device, tuple(pollutants))
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

        calibration = run_device_calibration(device_data, rmcab_data, device_name, (pollutant,))
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
                calibration = run_device_calibration(device_data, rmcab_data, device_name, tuple(pollutants))
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
