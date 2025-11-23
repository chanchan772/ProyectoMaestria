"""
Módulo avanzado de calibración de sensores usando PyCaret y scikit-learn.
Soporta múltiples rangos de tiempo: Completo, 30d, 15d (optimizado para velocidad).
"""
import pandas as pd
import numpy as np
from datetime import timedelta
import time
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error, mean_absolute_percentage_error
import warnings

warnings.filterwarnings('ignore')

try:
    import pycaret.regression as pycaret_reg
    PYCARET_AVAILABLE = True
except ImportError:
    PYCARET_AVAILABLE = False


class AdvancedSensorCalibrator:
    """Clase para calibrar sensores usando múltiples modelos ML"""

    def __init__(self):
        self.models = {}
        self.results = {}
        self.time_ranges = {
            'completo': None,
            '30dias': 30,
            '15dias': 15,
            '5dias': 5,
            '3dias': 3
        }
        self.pycaret_available = PYCARET_AVAILABLE

    def get_scikit_models(self, simple=False):
        """Retorna modelos de scikit-learn (ultra-optimizados para velocidad)"""
        if simple:
            # Para rangos cortos: solo modelos lineales (más rápido)
            return {
                'Linear Regression': LinearRegression(),
                'Ridge Regression': Ridge(alpha=1.0),
            }
        else:
            # Para rangos largos: modelos completos
            return {
                'Linear Regression': LinearRegression(),
                'Ridge Regression': Ridge(alpha=1.0),
                'Random Forest': RandomForestRegressor(n_estimators=20, random_state=42, n_jobs=1, max_depth=8),
                'Gradient Boosting': GradientBoostingRegressor(n_estimators=20, learning_rate=0.1, random_state=42, subsample=0.7),
            }

    def filter_by_time_range(self, df, days=None):
        """Filtra el dataframe por rango de tiempo (últimos N días)"""
        if days is None:
            return df.copy()

        if len(df) == 0:
            return df

        end_date = df['datetime'].max()
        start_date = end_date - timedelta(days=days)
        return df[(df['datetime'] >= start_date) & (df['datetime'] <= end_date)].copy()

    def prepare_features(self, df, pollutant='pm25'):
        """
        Prepara features para el modelo.

        Args:
            df: DataFrame con datos fusionados
            pollutant: 'pm25' o 'pm10'

        Returns:
            X, y: Features y target
        """
        # Seleccionar columnas según el contaminante
        sensor_col = pollutant  # pm25 o pm10
        ref_col = f'{pollutant}_ref'  # pm25_ref o pm10_ref

        # Target: valor de referencia de RMCAB
        y = df[ref_col].copy()

        # Intentar usar features con temperatura y humedad
        # Si no están disponibles (todos null), usar solo el sensor
        has_temp_rh = (df['temperature'].notna().sum() > 0) and (df['rh'].notna().sum() > 0)

        if has_temp_rh:
            # Usar temperatura y humedad como features
            X = df[[sensor_col, 'temperature', 'rh']].copy()
            X.columns = ['sensor_value', 'temperature', 'rh']
        else:
            # Fallback: usar solo el valor del sensor como feature
            X = df[[sensor_col]].copy()
            X.columns = ['sensor_value']

        # Eliminar NaNs en X e y
        mask = ~(X.isna().any(axis=1) | y.isna())
        X = X[mask].reset_index(drop=True)
        y = y[mask].reset_index(drop=True)

        return X, y

    def evaluate_model(self, model, X_train, X_test, y_train, y_test, model_name):
        """Entrena y evalúa un modelo individual"""
        try:
            # Entrenar
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            # Calcular métricas
            r2 = r2_score(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            mae = mean_absolute_error(y_test, y_pred)

            # MAPE (evitar división por cero)
            mask = y_test != 0
            if mask.sum() > 0:
                mape = mean_absolute_percentage_error(y_test[mask], y_pred[mask]) * 100
            else:
                mape = 0

            return {
                'r2': float(r2),
                'rmse': float(rmse),
                'mae': float(mae),
                'mape': float(mape),
                'n_samples': len(X_test),
                'status': 'success'
            }

        except Exception as e:
            return {
                'r2': None,
                'rmse': None,
                'mae': None,
                'mape': None,
                'error': str(e),
                'status': 'error'
            }

    def calibrate_sensor_by_pollutant(self, df, pollutant='pm25', time_range_days=None):
        """
        Calibra un sensor para un contaminante específico en un rango de tiempo.

        Args:
            df: DataFrame con datos fusionados
            pollutant: 'pm25' o 'pm10'
            time_range_days: Días a usar (None = completo)

        Returns:
            dict con resultados por modelo
        """
        # Filtrar por rango de tiempo
        df_filtered = self.filter_by_time_range(df, days=time_range_days)
        days_label = f"{time_range_days}d" if time_range_days else "completo"

        if len(df_filtered) == 0:
            print(f"[DEBUG] {pollutant} {days_label}: 0 rows after time filter")
            return None

        # Preparar features
        X, y = self.prepare_features(df_filtered, pollutant=pollutant)

        print(f"[DEBUG] {pollutant} {days_label}: X={X.shape[0]}, y={y.shape[0]}")

        if len(X) < 5:
            print(f"[DEBUG] {pollutant} {days_label}: insufficient data ({len(X)} < 5)")
            return None

        # Submuestreo inteligente para datasets grandes (>5000 muestras)
        if len(X) > 5000:
            sample_size = 5000
            sample_idx = np.random.RandomState(42).choice(len(X), sample_size, replace=False)
            X = X.iloc[sample_idx].reset_index(drop=True)
            y = y.iloc[sample_idx].reset_index(drop=True)
            print(f"[DEBUG] {pollutant} {days_label}: submuestreo a {sample_size} (de {X.shape[0]})")

        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42
        )

        # Para rangos cortos (3-5 días), usar solo modelos lineales rápidos
        use_simple = time_range_days in [3, 5] if time_range_days else False

        # Entrenar modelos scikit-learn
        models = self.get_scikit_models(simple=use_simple)
        results = {}

        for model_name, model in models.items():
            result = self.evaluate_model(model, X_train, X_test, y_train, y_test, model_name)
            # Redondear para JSON serialization
            if result['status'] == 'success':
                result['r2'] = round(result['r2'], 4)
                result['rmse'] = round(result['rmse'], 4)
                result['mae'] = round(result['mae'], 4)
                result['mape'] = round(result['mape'], 2)
            results[model_name] = result

        return results

    def calibrate_all_ranges(self, df, pollutant='pm25'):
        """
        Calibra un sensor para todos los rangos de tiempo.

        Returns:
            dict con estructura: {rango_tiempo: {modelo: métricas}}
        """
        all_results = {}
        total_ranges = len(self.time_ranges)

        for idx, (range_name, days) in enumerate(self.time_ranges.items(), 1):
            start_time = time.time()
            print(f"[Calibración] {pollutant.upper()} - {range_name} ({idx}/{total_ranges})...", flush=True)
            results = self.calibrate_sensor_by_pollutant(df, pollutant=pollutant, time_range_days=days)
            elapsed = time.time() - start_time
            print(f"[Calibración] {pollutant.upper()} - {range_name} completado en {elapsed:.2f}s", flush=True)
            all_results[range_name] = results

        return all_results

    def get_best_model_for_range(self, results_by_range):
        """
        Obtiene el mejor modelo para cada rango de tiempo.

        Args:
            results_by_range: dict {rango: {modelo: métricas}}

        Returns:
            dict {rango: (mejor_modelo, métricas)}
        """
        best_by_range = {}

        for range_name, models_results in results_by_range.items():
            if models_results is None:
                continue

            # Filtrar modelos exitosos
            valid = {k: v for k, v in models_results.items() if v.get('status') == 'success' and v.get('r2') is not None}

            if valid:
                best = max(valid.items(), key=lambda x: x[1]['r2'])
                best_by_range[range_name] = {
                    'model': best[0],
                    'r2': best[1]['r2'],
                    'rmse': best[1]['rmse'],
                    'mae': best[1]['mae'],
                    'mape': best[1]['mape'],
                    'n_samples': best[1]['n_samples']
                }

        return best_by_range

    def generate_conclusion(self, best_models_by_range, threshold=0.8):
        """
        Genera conclusión sobre si el sensor cumple con el criterio.

        Args:
            best_models_by_range: dict {rango: mejor_modelo_info}
            threshold: R² mínimo requerido (default 0.8)

        Returns:
            dict con conclusión y estado
        """
        if not best_models_by_range:
            return {
                'status': 'NO CUMPLE',
                'reason': 'No hay datos válidos',
                'recommendation': 'Se requieren datos de temperatura y humedad relativa capturados en tiempo real para realizar una evaluación precisa',
                'r2_values': {}
            }

        r2_values = {k: v['r2'] for k, v in best_models_by_range.items()}

        # Verificar si algún rango alcanza el threshold
        completo_r2 = r2_values.get('completo')

        base_recommendation = 'NOTA IMPORTANTE: Los datos de temperatura y humedad relativa utilizados en este análisis fueron simulados. Para mayor precisión en futuras evaluaciones, se recomienda capturar estos datos directamente de sensores meteorológicos o estaciones de referencia.'

        if completo_r2 is None:
            status = 'NO EVALUADO'
            reason = 'Rango completo no disponible'
        elif completo_r2 >= threshold:
            status = 'CUMPLE'
            reason = f'R² en rango completo: {completo_r2:.4f} >= {threshold}'
        else:
            # Verificar si mejora en rangos cortos
            short_ranges = {k: v for k, v in r2_values.items() if k in ['3dias', '5dias', '15dias']}
            max_short = max(short_ranges.values()) if short_ranges else 0

            if max_short >= threshold:
                status = 'DEGRADACIÓN'
                reason = f'R² completo: {completo_r2:.4f} < {threshold}, pero mejora en rangos cortos (máx: {max_short:.4f})'
            else:
                status = 'NO CUMPLE'
                reason = f'R² completo: {completo_r2:.4f} < {threshold}, sin mejora significativa en rangos cortos'

        return {
            'status': status,
            'reason': reason,
            'recommendation': base_recommendation,
            'r2_values': r2_values,
            'threshold': threshold
        }

    def calibrate_all_sensors_all_ranges(self, df):
        """
        Calibra todos los sensores para todos los contaminantes y rangos.

        Returns:
            dict {pollutant: {sensor: {rango: resultados}}}
        """
        all_results = {}
        total_start = time.time()

        for pollutant in ['pm25', 'pm10']:
            start_time = time.time()
            print(f"\n[CALIBRACIÓN] Iniciando {pollutant.upper()}...", flush=True)
            results = self.calibrate_all_ranges(df, pollutant=pollutant)
            elapsed = time.time() - start_time
            print(f"[CALIBRACIÓN] {pollutant.upper()} completado en {elapsed:.2f}s", flush=True)
            all_results[pollutant] = results

        total_elapsed = time.time() - total_start
        print(f"\n[CALIBRACIÓN] Calibración completa en {total_elapsed:.2f}s ({total_elapsed/60:.2f} minutos)", flush=True)
        return all_results

    def calibrate_all_sensors_independent(self, df):
        """
        Calibra cada sensor de forma INDEPENDIENTE para todos los contaminantes y rangos.

        Returns:
            dict {pollutant: {sensor: {rango: resultados}}}
        """
        all_results = {}
        sensors = df['device_name'].unique() if 'device_name' in df.columns else []

        print(f"\n[CALIBRACIÓN INDEPENDIENTE] Sensores detectados: {list(sensors)}", flush=True)

        total_start = time.time()

        for pollutant in ['pm25', 'pm10']:
            pollutant_results = {}
            start_time = time.time()
            print(f"\n[CALIBRACIÓN] Iniciando {pollutant.upper()}...", flush=True)

            for sensor in sensors:
                sensor_start = time.time()
                print(f"\n[CALIBRACIÓN] {sensor} - {pollutant.upper()}...", flush=True)

                # Filtrar datos para este sensor específico
                df_sensor = df[df['device_name'] == sensor].copy()

                if len(df_sensor) < 10:
                    print(f"[CALIBRACIÓN] {sensor} - {pollutant.upper()}: datos insuficientes ({len(df_sensor)} < 10)")
                    pollutant_results[sensor] = {}
                    continue

                # Calibrar para todos los rangos
                sensor_ranges = self.calibrate_all_ranges(df_sensor, pollutant=pollutant)
                pollutant_results[sensor] = sensor_ranges

                sensor_elapsed = time.time() - sensor_start
                print(f"[CALIBRACIÓN] {sensor} - {pollutant.upper()} completado en {sensor_elapsed:.2f}s", flush=True)

            elapsed = time.time() - start_time
            print(f"[CALIBRACIÓN] {pollutant.upper()} completado en {elapsed:.2f}s", flush=True)
            all_results[pollutant] = pollutant_results

        total_elapsed = time.time() - total_start
        print(f"\n[CALIBRACIÓN INDEPENDIENTE] Completada en {total_elapsed:.2f}s ({total_elapsed/60:.2f} minutos)", flush=True)
        return all_results


# Mantener clase compatible con código anterior
class SensorCalibrator(AdvancedSensorCalibrator):
    """Clase compatible hacia atrás"""
    pass
