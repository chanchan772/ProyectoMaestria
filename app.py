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
from modules.data_loader import load_lowcost_data, load_rmcab_data
from modules.calibration import get_calibration_models, train_and_evaluate_models
from modules.visualization import create_timeseries_plot, create_boxplot, create_heatmap
from modules.metrics import calculate_statistics

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
    """Página de visualización Junio-Julio 2024"""
    return render_template('visualizacion_junio_julio.html')

@app.route('/visualizacion/2024')
def visualizacion_2024():
    """Página de visualización Periodo Completo 2024"""
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
        results = train_and_evaluate_models(lowcost_data, rmcab_data)

        return jsonify({
            'success': True,
            'results': results
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

        # Cargar datos del dispositivo
        lowcost_data = load_lowcost_data(start_date, end_date, [device_name])

        # Cargar datos de RMCAB
        rmcab_data = load_rmcab_data(6, start_date, end_date)  # Las Ferias

        if lowcost_data is None or rmcab_data is None:
            return jsonify({'error': 'No se pudieron cargar los datos'}), 404

        # Ejecutar calibración
        results = train_and_evaluate_models(lowcost_data, rmcab_data, pollutant)

        return jsonify({
            'success': True,
            'device': device_name,
            'pollutant': pollutant,
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    app.run(host='0.0.0.0', port=port, debug=debug)
