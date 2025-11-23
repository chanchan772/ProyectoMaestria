# -*- coding: utf-8 -*-
import sys
import io

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from flask import Flask, render_template, jsonify, request
from modules.data_processor import DataProcessor
from modules.calibration import SensorCalibrator
from modules.visualization import DataVisualizer
from modules.predictive_model import PredictiveModelPipeline
from modules.advanced_predictive_model import AdvancedPredictiveModel
from dotenv import load_dotenv
import json
import os

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Instancias globales para procesar datos
data_processor = None
calibrator = None
predictive_model = None
advanced_model = None

def initialize_data():
    """Inicializa datos REALES de PostgreSQL y CSV RMCAB cache - SIN API CALLS"""
    global data_processor, calibrator
    data_processor = DataProcessor()
    calibrator = SensorCalibrator()

    print("\n" + "="*70)
    print("[INICIO] CARGANDO DATOS DESDE POSTGRESQL Y CSV CACHE")
    print("="*70)

    # Cargar datos de sensores desde PostgreSQL
    print("\n[PASO 1] Cargando datos de sensores desde PostgreSQL...")
    data_processor.load_real_data(start_date='2025-06-01', end_date='2025-07-30')

    # Cargar datos de RMCAB desde CSV (no desde API)
    print("\n[PASO 2] Cargando datos de RMCAB desde CSV cache...")
    data_processor.load_rmcab_from_csv()

    # Fusionar
    print("\n[PASO 3] Fusionando datos de sensores y RMCAB...")
    data_processor.merge_data()

    print("\n" + "="*70)
    print("[OK] DATOS CARGADOS EXITOSAMENTE - LISTO PARA GRAFICAR")
    print("="*70 + "\n")

    return data_processor.merged_data

# Rutas principales
@app.route('/')
def index():
    return render_template('index.html', title='Inicio')

@app.route('/tecnologias')
def tecnologias():
    return render_template('tecnologias.html', title='Tecnologías')

@app.route('/modelos')
def modelos():
    return render_template('modelos.html', title='Modelos')

@app.route('/definiciones')
def definiciones():
    return render_template('definiciones.html', title='Definiciones')

@app.route('/acerca-de')
def acerca_de():
    return render_template('acerca_de.html', title='Acerca de')

@app.route('/objetivo-1')
def objetivo_1():
    return render_template('objetivo1.html', title='Objetivo 1')

@app.route('/objetivo-2')
def objetivo_2():
    return render_template('objetivo2.html', title='Objetivo 2')

@app.route('/objetivo-3')
def objetivo_3():
    return render_template('objetivo3.html', title='Objetivo 3')

# ==================== API ENDPOINTS ====================

@app.route('/api/objetivo1/initialize', methods=['POST'])
def api_initialize_objective1():
    """Inicializa los datos para Objetivo 1"""
    try:
        global data_processor
        df = initialize_data()

        return jsonify({
            'status': 'success',
            'message': 'Datos cargados correctamente',
            'records': len(df),
            'columns': list(df.columns)
        })
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/objetivo1/charts', methods=['GET'])
def api_charts():
    """Retorna DOS gráficos: PM2.5 y PM10 con datos REALES"""
    try:
        if data_processor is None or data_processor.merged_data is None:
            initialize_data()

        df = data_processor.merged_data.copy()

        # Crear columna de datetime redondeado para RMCAB (horas cerradas)
        df['datetime_rmcab'] = df['datetime'].dt.round('H').astype(str)

        # Convertir datetime a string para JSON
        df['datetime'] = df['datetime'].astype(str)

        # Construir datos PM2.5 (seleccionar solo columnas disponibles)
        pm25_cols = ['datetime', 'datetime_rmcab', 'device_name', 'pm25']
        if 'pm25_ref' in df.columns:
            pm25_cols.append('pm25_ref')
        if 'pm10_ref' in df.columns:
            pm25_cols.append('pm10_ref')

        # Construir datos PM10 (seleccionar solo columnas disponibles)
        pm10_cols = ['datetime', 'datetime_rmcab', 'device_name', 'pm10']
        if 'pm10_ref' in df.columns:
            pm10_cols.append('pm10_ref')

        # Retornar DOS gráficos: PM2.5 y PM10
        return jsonify({
            'status': 'success',
            'pm25': {
                'title': 'PM2.5 (μg/m³) - Sensores vs RMCAB',
                'data': json.loads(df[pm25_cols].to_json(orient='records'))
            },
            'pm10': {
                'title': 'PM10 (μg/m³) - Sensores vs RMCAB',
                'data': json.loads(df[pm10_cols].to_json(orient='records'))
            }
        })
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/objetivo1/raw-data', methods=['GET'])
def api_raw_data():
    """Retorna los datos CRUDOS tal como vienen de la BD y API"""
    try:
        if data_processor is None or data_processor.merged_data is None:
            initialize_data()

        df = data_processor.merged_data.copy()
        df['datetime'] = df['datetime'].astype(str)

        return jsonify({
            'status': 'success',
            'datos_reales': json.loads(df.to_json(orient='records')),
            'total_registros': len(df),
            'dispositivos': sorted(df['device_name'].unique().tolist()),
            'columnas': list(df.columns)
        })
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/objetivo1/calibration', methods=['POST'])
def api_calibration():
    """Ejecuta calibración INDEPENDIENTE por sensor para PM2.5 y PM10"""
    try:
        print("\n[API] Iniciando calibración INDEPENDIENTE por sensor...")

        if data_processor is None or data_processor.merged_data is None:
            initialize_data()

        df = data_processor.merged_data.copy()

        # Ejecutar calibración INDEPENDIENTE por sensor
        all_results = calibrator.calibrate_all_sensors_independent(df)

        # Procesar resultados: Convertir estructura de {pollutant: {sensor: {range: results}}} a lo que JavaScript espera
        calibration_summary = {}

        for pollutant in ['pm25', 'pm10']:
            print(f"\n[API] Procesando resultados {pollutant.upper()}...")
            sensors_data = all_results.get(pollutant, {})

            # Reestructurar para que sea {range: {model: metrics}} globalmente
            # Pero también guardar la información por sensor
            global_results = {}

            for sensor, sensor_ranges in sensors_data.items():
                for range_name, range_results in sensor_ranges.items():
                    if range_name not in global_results:
                        global_results[range_name] = {}
                    # Agregar resultados de este sensor para este rango
                    global_results[range_name][f"{sensor}_{sensor}_"] = range_results

            calibration_summary[pollutant] = {
                'all_results': sensors_data,  # Guardar estructura original por sensor
                'global_results': global_results,  # Para compatibilidad backwards
                'by_sensor': sensors_data  # Explícitamente por sensor
            }

        print(f"[API] Calibración INDEPENDIENTE completada exitosamente")

        return jsonify({
            'status': 'success',
            'message': 'Calibración completada',
            'data': calibration_summary
        })

    except Exception as e:
        print(f"[ERROR] Error en calibración: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/objetivo1/calibration-by-range', methods=['POST'])
def api_calibration_by_range():
    """Ejecuta calibración para un pollutant y rango de tiempo específico"""
    try:
        req_data = request.get_json()
        pollutant = req_data.get('pollutant', 'pm25')  # pm25 o pm10
        time_range = req_data.get('time_range', 'completo')  # completo, 30dias, 15dias, 5dias, 3dias

        print(f"\n[API] Calibración por rango: {pollutant.upper()} - {time_range}")

        if data_processor is None or data_processor.merged_data is None:
            initialize_data()

        df = data_processor.merged_data.copy()

        # Mapeo de rangos a días
        time_ranges_map = {
            'completo': None,
            '30dias': 30,
            '15dias': 15,
            '5dias': 5,
            '3dias': 3
        }

        days = time_ranges_map.get(time_range)

        # Ejecutar calibración
        results = calibrator.calibrate_sensor_by_pollutant(df, pollutant=pollutant, time_range_days=days)

        if results is None:
            return jsonify({
                'status': 'error',
                'message': f'No hay datos suficientes para {pollutant} en rango {time_range}'
            }), 400

        # Obtener el mejor modelo para este rango
        best_models = calibrator.get_best_model_for_range({time_range: results})

        return jsonify({
            'status': 'success',
            'pollutant': pollutant,
            'time_range': time_range,
            'all_models_results': results,
            'best_model': best_models.get(time_range)
        })

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== ENDPOINTS MODELO PREDICTIVO ====================

@app.route('/api/objetivo2/train-improved', methods=['POST'])
def api_train_improved():
    """
    ENTRENA MODELO HIBRIDO AVANZADO: REGRESSION + CLASSIFICATION
    CON FEATURES METEOROLOGICAS MEJORADAS + FEATURES TEMPORALES

    Solo se ejecuta UNA VEZ. Guarda el modelo entrenado.
    Las siguientes ejecuciones cargan el modelo guardado (sin reentrenar).
    """
    try:
        global advanced_model

        print("\n" + "="*80)
        print("[ENTRENAMIENTO AVANZADO] LightGBM Regression + Classification")
        print("[HIBRIDO] Features Meteorológicas + Features Temporales + Features Derivadas")
        print("="*80)

        # Cargar datos RMCAB
        print("\n[PASO 1/3] Cargando datos REALES de RMCAB (TODO EL AÑO 2025)...")
        processor = DataProcessor()
        rmcab_df = processor.load_rmcab_from_csv()

        if rmcab_df is None or rmcab_df.empty:
            raise ValueError("No se pudieron cargar datos de RMCAB")

        total_records = len(rmcab_df)
        date_min = rmcab_df['datetime'].min()
        date_max = rmcab_df['datetime'].max()

        print(f"   ✓ Registros: {total_records}")
        print(f"   ✓ Período: {date_min} a {date_max}")

        # Crear modelo avanzado híbrido
        print("\n[PASO 2/3] Entrenando modelo LightGBM HIBRIDO (Regression + Classification)...")
        print("   ✓ Generando features meteorológicas realistas (HR, Temp, Presión, Viento)")
        print("   ✓ Agregando features derivadas (deltas, moving averages)")
        print("   ✓ Agregando features temporales (hora, dia, mes, estación)")
        print("   ✓ Entrenando 4 modelos LightGBM: PM2.5 Reg, PM2.5 Clf, PM10 Reg, PM10 Clf")

        advanced_model = AdvancedPredictiveModel(lookback_window=24)

        # Entrenar y guardar
        model_info = advanced_model.train(
            rmcab_df,
            output_dir='static/results',
            model_dir='models'
        )

        summary = advanced_model.get_summary()

        # Mensaje final
        print("\n[PASO 3/3] Generando gráficos avanzados de evaluación...")
        print("\n" + "="*80)
        print("[EXITO] Modelo HIBRIDO entrenado, guardado y evaluado")
        print("="*80)
        print("\nModelos guardados:")
        print("  ✓ models/lightgbm_reg_pm25.pkl (Regression PM2.5)")
        print("  ✓ models/lightgbm_reg_pm10.pkl (Regression PM10)")
        print("  ✓ models/lightgbm_clf_pm25.pkl (Classification PM2.5)")
        print("  ✓ models/lightgbm_clf_pm10.pkl (Classification PM10)")
        print("\nGráficos generados:")
        print("  ✓ static/results/advanced_evaluation_pm25.png (Regression + Classification + Residuos + Métricas)")
        print("  ✓ static/results/advanced_evaluation_pm10.png (Regression + Classification + Residuos + Métricas)")
        print(f"\nProximas ejecuciones: Cargarán los modelos guardados (sin reentrenar)")

        print("\n[DEBUG] Summary being returned:")
        import json
        print(json.dumps(summary, indent=2, default=str))

        return jsonify({
            'status': 'success',
            'message': 'Modelo HIBRIDO entrenado, guardado y evaluado exitosamente',
            'model_type': 'LightGBM Regression + Classification (HIBRIDO)',
            'data_info': {
                'total_records': total_records,
                'period_start': str(date_min),
                'period_end': str(date_max)
            },
            'results': summary,
            'files_generated': [
                'results/advanced_evaluation_pm25.png',
                'results/advanced_evaluation_pm10.png'
            ]
        })

    except Exception as e:
        print(f"[ERROR] Error en entrenamiento: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/objetivo2/load-model', methods=['GET'])
def api_load_model():
    """
    CARGA EL MODELO HIBRIDO YA ENTRENADO (sin reentrenar)

    Se ejecuta automaticamente cuando se accede a la página.
    Si el modelo no existe, retorna instrucción de entrenar primero.
    """
    try:
        global advanced_model

        print("\n[CARGA DE MODELO] Buscando modelo HIBRIDO entrenado...")

        advanced_model = AdvancedPredictiveModel()
        model_loaded = advanced_model.load_trained_model(model_dir='models')

        if model_loaded:
            summary = advanced_model.get_summary()
            print("\n[OK] Modelo HIBRIDO cargado exitosamente")

            return jsonify({
                'status': 'success',
                'message': 'Modelo HIBRIDO cargado exitosamente (no se reentrenó)',
                'model_info': advanced_model.model_info,
                'results': summary
            })
        else:
            print("\n[INFO] Modelo no encontrado - requiere entrenamiento previo")

            return jsonify({
                'status': 'not_trained',
                'message': 'No hay modelo HIBRIDO entrenado. Ejecuta primero el entrenamiento.',
                'action': 'Haz clic en "Entrenar Modelo" para entrenar una sola vez.'
            }), 200

    except Exception as e:
        print(f"[ERROR] Error al cargar modelo: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/objetivo2/train-predictor', methods=['POST'])
def api_train_predictor():
    """ENDPOINT ANTIGUO - Mantiene compatibilidad"""
    # Redirige al nuevo endpoint mejorado
    return api_train_improved()


@app.route('/api/objetivo2/metrics', methods=['GET'])
def api_predictor_metrics():
    """Retorna métricas del modelo predictivo"""
    try:
        if advanced_model is None:
            return jsonify({
                'status': 'error',
                'message': 'Modelo no entrenado. Primero ejecuta /api/objetivo2/train-improved'
            }), 400

        summary = advanced_model.get_summary()

        return jsonify({
            'status': 'success',
            'metrics': summary
        })

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/objetivo2/validation-data', methods=['GET'])
def api_validation_data():
    """Retorna datos de validacion para tablas comparativas"""
    try:
        import random

        # Leer datos de validacion
        pm25_file = os.path.join('models', 'validation_pm2.5.json')
        pm10_file = os.path.join('models', 'validation_pm10.json')

        validation_result = {}

        for pollutant, filepath in [('pm25', pm25_file), ('pm10', pm10_file)]:
            if not os.path.exists(filepath):
                continue

            with open(filepath, 'r') as f:
                data = json.load(f)

            real = data['real']
            predicho = data['predicho']

            # Calcular errores
            errors = [abs(r - p) for r, p in zip(real, predicho)]

            # OPCION A: 100 muestras aleatorias
            indices = list(range(len(real)))
            sample_indices = random.sample(indices, min(100, len(indices)))
            opcion_a = [
                {
                    'idx': i,
                    'real': round(real[i], 2),
                    'predicho': round(predicho[i], 2),
                    'error': round(errors[i], 2),
                    'error_pct': round((errors[i] / (abs(real[i]) + 0.1) * 100), 2)
                }
                for i in sorted(sample_indices)
            ]

            # OPCION B: Primeras 50
            opcion_b = [
                {
                    'idx': i,
                    'real': round(real[i], 2),
                    'predicho': round(predicho[i], 2),
                    'error': round(errors[i], 2),
                    'error_pct': round((errors[i] / (abs(real[i]) + 0.1) * 100), 2)
                }
                for i in range(min(50, len(real)))
            ]

            # OPCION C: Tabla resumen con percentiles
            sorted_real = sorted(real)
            sorted_pred = sorted(predicho)
            sorted_errors = sorted(errors)

            def percentile(data, p):
                idx = int(len(data) * p / 100)
                return round(data[min(idx, len(data)-1)], 2)

            opcion_c = {
                'real': {
                    'min': round(min(real), 2),
                    'q1': percentile(sorted_real, 25),
                    'q2': percentile(sorted_real, 50),
                    'q3': percentile(sorted_real, 75),
                    'max': round(max(real), 2),
                    'mean': round(sum(real) / len(real), 2)
                },
                'predicho': {
                    'min': round(min(predicho), 2),
                    'q1': percentile(sorted_pred, 25),
                    'q2': percentile(sorted_pred, 50),
                    'q3': percentile(sorted_pred, 75),
                    'max': round(max(predicho), 2),
                    'mean': round(sum(predicho) / len(predicho), 2)
                },
                'error': {
                    'min': round(min(errors), 2),
                    'q1': percentile(sorted_errors, 25),
                    'q2': percentile(sorted_errors, 50),
                    'q3': percentile(sorted_errors, 75),
                    'max': round(max(errors), 2),
                    'mean': round(sum(errors) / len(errors), 2)
                }
            }

            validation_result[pollutant] = {
                'opcion_a': opcion_a,
                'opcion_b': opcion_b,
                'opcion_c': opcion_c,
                'total_samples': len(real)
            }

        return jsonify({
            'status': 'success',
            'validation': validation_result
        })

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/results/<filename>', methods=['GET'])
def download_result(filename):
    """Descarga archivos de resultados"""
    try:
        import os
        from flask import send_from_directory

        # Validar nombre de archivo
        allowed_files = ['predictive_metrics.csv', 'predictions_PM25.png',
                         'predictions_PM10.png', 'steps_comparison.png']

        if filename not in allowed_files:
            return jsonify({'status': 'error', 'message': 'Archivo no permitido'}), 403

        # Buscar archivo en static/results o results
        if os.path.exists(f'static/results/{filename}'):
            return send_from_directory('static/results', filename, as_attachment=True)
        elif os.path.exists(f'results/{filename}'):
            return send_from_directory('results', filename, as_attachment=True)
        else:
            return jsonify({'status': 'error', 'message': 'Archivo no encontrado'}), 404

    except Exception as e:
        print(f"[ERROR] Error al descargar: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Manejadores de errores
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
