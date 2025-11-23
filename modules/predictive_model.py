"""
Módulo de Modelo Predictivo de Series de Tiempo para PM2.5 y PM10
Predice contaminación 1, 3 y 5 horas adelante usando DATOS REALES DE RMCAB

Justificación:
- Los sensores Aire2, Aire4, Aire5 están DEGRADADOS y no son confiables
- Usamos RMCAB como ÚNICA fuente de verdad (datos reales de referencia)
- Simulamos Temperatura y Humedad (patrones realistas de Bogotá)

Metodología:
- Arquitectura: LSTM (Long Short-Term Memory) de 2 capas
- Datos de entrada: PM2.5/PM10 histórico (RMCAB) + Temperatura + Humedad (simuladas)
- Predicción: Múltiples pasos adelante (1, 3, 5 horas)
- Modelos: 3 independientes (sin propagación de error)
- Validación: Temporal (75% train, 25% test) + 4 métricas (RMSE, MAE, R², MAPE)

IMPORTANTE:
- NO usa datos de PostgreSQL (sensores degradados)
- NO usa Aire2, Aire4, Aire5 (por eso se hace el modelo)
- USA SOLO datos reales de RMCAB (descargados con Postman → CSV)
"""

import pandas as pd
import numpy as np
import warnings
import os
import json
from datetime import datetime, timedelta
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import seaborn as sns

warnings.filterwarnings('ignore')

# Intentar importar TensorFlow/Keras, si no está disponible usar statsmodels
try:
    from tensorflow import keras
    from tensorflow.keras import layers, Sequential
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.callbacks import EarlyStopping
    KERAS_AVAILABLE = True
except ImportError:
    KERAS_AVAILABLE = False
    print("[WARN] TensorFlow no disponible, usando RandomForest como fallback")


class TimeSeriesPreprocessor:
    """Prepara datos para modelo de series de tiempo"""

    def __init__(self, lookback_window=24, forecast_steps=[1, 3, 5]):
        """
        Args:
            lookback_window: Número de pasos históricos a usar (24 = 24 horas)
            forecast_steps: Lista de pasos adelante a predecir (en horas)
        """
        self.lookback_window = lookback_window
        self.forecast_steps = forecast_steps
        self.scaler_pm25 = MinMaxScaler()
        self.scaler_pm10 = MinMaxScaler()
        self.scaler_temp = MinMaxScaler()
        self.scaler_rh = MinMaxScaler()

    def prepare_data(self, df, target_column='pm25_ref', include_features=None):
        """
        Prepara datos para modelo LSTM

        Args:
            df: DataFrame con columnas [datetime, pm25_ref/pm10_ref, temperature, rh]
            target_column: 'pm25_ref' o 'pm10_ref'
            include_features: Lista de columnas adicionales [temperature, rh]

        Returns:
            X_train, y_train, X_test, y_test, scaler
        """
        if include_features is None:
            include_features = ['temperature', 'rh']

        df = df.copy()
        df = df.sort_values('datetime').reset_index(drop=True)

        # Eliminar NaN
        df = df.dropna(subset=[target_column] + include_features)

        if len(df) < self.lookback_window + max(self.forecast_steps) + 1:
            raise ValueError(
                f"Datos insuficientes: necesita {self.lookback_window + max(self.forecast_steps) + 1} registros, "
                f"tiene {len(df)}"
            )

        print(f"\n[PREP] Preparando datos para {target_column}")
        print(f"   Registros: {len(df)}")
        print(f"   Rango: {df['datetime'].min()} a {df['datetime'].max()}")
        print(f"   Ventana histórica (lookback): {self.lookback_window} pasos")
        print(f"   Pasos de predicción: {self.forecast_steps}")

        # Normalizar datos
        features_list = [target_column] + include_features
        data = df[features_list].values

        # Usar escaladores apropiados según el objetivo
        if target_column == 'pm25_ref':
            self.scaler_pm25.fit(df[[target_column]])
            target_scaled = self.scaler_pm25.transform(df[[target_column]]).flatten()
        else:
            self.scaler_pm10.fit(df[[target_column]])
            target_scaled = self.scaler_pm10.transform(df[[target_column]]).flatten()

        self.scaler_temp.fit(df[['temperature']])
        temp_scaled = self.scaler_temp.transform(df[['temperature']]).flatten()

        self.scaler_rh.fit(df[['rh']])
        rh_scaled = self.scaler_rh.transform(df[['rh']]).flatten()

        # Preparar secuencias
        X, y_multi = [], {step: [] for step in self.forecast_steps}

        for i in range(len(df) - self.lookback_window - max(self.forecast_steps)):
            # Entrada: ventana histórica [lookback] de [target, temp, rh]
            window = np.column_stack([
                target_scaled[i:i+self.lookback_window],
                temp_scaled[i:i+self.lookback_window],
                rh_scaled[i:i+self.lookback_window]
            ])
            X.append(window)

            # Salida: predicciones para múltiples pasos
            idx_target = i + self.lookback_window
            for step in self.forecast_steps:
                y_multi[step].append(target_scaled[idx_target + step - 1])

        X = np.array(X)

        print(f"   Secuencias creadas: {len(X)}")
        print(f"   Forma de X: {X.shape} (muestras, timesteps, features)")

        # Split: 75% entrenamiento, 25% prueba (respetando orden temporal)
        split_idx = int(len(X) * 0.75)
        X_train = X[:split_idx]
        X_test = X[split_idx:]

        y_train = {step: np.array(y_multi[step])[:split_idx] for step in self.forecast_steps}
        y_test = {step: np.array(y_multi[step])[split_idx:] for step in self.forecast_steps}

        print(f"   Entrenamiento: {len(X_train)} | Prueba: {len(X_test)}")

        return X_train, X_test, y_train, y_test, df


class LSTMPredictor:
    """Modelo LSTM para predicción de series de tiempo múltiples pasos"""

    def __init__(self, lookback_window=24, forecast_steps=[1, 3, 5]):
        self.lookback_window = lookback_window
        self.forecast_steps = forecast_steps
        self.models = {}
        self.training_history = {}
        self.metrics = {}

    def build_model(self, input_shape):
        """Construye modelo LSTM"""
        model = Sequential([
            layers.LSTM(64, activation='relu', return_sequences=True, input_shape=input_shape),
            layers.Dropout(0.2),
            layers.LSTM(32, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(16, activation='relu'),
            layers.Dense(1)
        ])
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse', metrics=['mae'])
        return model

    def train(self, X_train, y_train, X_test, y_test, target_name='PM2.5', epochs=50):
        """Entrena modelo para cada paso de predicción"""
        print(f"\n[TRAIN] Entrenando modelos LSTM para {target_name}")

        input_shape = (X_train.shape[1], X_train.shape[2])

        for step in self.forecast_steps:
            print(f"\n   Paso {step}h - Entrenando...")

            model = self.build_model(input_shape)

            early_stop = EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            )

            history = model.fit(
                X_train, y_train[step],
                epochs=epochs,
                batch_size=8,
                validation_data=(X_test, y_test[step]),
                callbacks=[early_stop],
                verbose=0
            )

            self.models[step] = model
            self.training_history[step] = history

            print(f"      Épocas: {len(history.history['loss'])} | "
                  f"Loss final: {history.history['loss'][-1]:.6f}")

    def predict(self, X_test, y_test_true, scaler, target_name='PM2.5'):
        """Realiza predicciones y evalúa el modelo"""
        print(f"\n[PRED] Evaluando predicciones para {target_name}")

        results = {}
        predictions_scaled = {}

        for step in self.forecast_steps:
            print(f"\n   Paso {step}h:")

            # Predicción
            y_pred_scaled = self.models[step].predict(X_test, verbose=0).flatten()
            predictions_scaled[step] = y_pred_scaled

            # Invertir normalización
            y_pred = scaler.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()
            y_true = scaler.inverse_transform(y_test_true[step].reshape(-1, 1)).flatten()

            # Métricas
            rmse = np.sqrt(mean_squared_error(y_true, y_pred))
            mae = mean_absolute_error(y_true, y_pred)
            r2 = r2_score(y_true, y_pred)

            # MAPE con protección contra división por cero
            mask = y_true != 0
            if mask.sum() > 0:
                mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
            else:
                mape = 0.0

            results[step] = {
                'y_true': y_true,
                'y_pred': y_pred,
                'rmse': float(rmse),
                'mae': float(mae),
                'r2': float(r2),
                'mape': float(mape)
            }

            print(f"      RMSE: {rmse:.2f} μg/m³")
            print(f"      MAE:  {mae:.2f} μg/m³")
            print(f"      R²:   {r2:.4f}")
            print(f"      MAPE: {mape:.2f}%")

        self.metrics = results
        return results


class FallbackPredictor:
    """Predictor usando scikit-learn cuando LSTM no está disponible"""

    def __init__(self, lookback_window=24, forecast_steps=[1, 3, 5]):
        from sklearn.ensemble import RandomForestRegressor
        self.lookback_window = lookback_window
        self.forecast_steps = forecast_steps
        self.models = {}
        self.training_history = {}

    def train(self, X_train, y_train, X_test, y_test, target_name='PM2.5', epochs=50):
        """Entrena modelos Random Forest para cada paso de predicción"""
        from sklearn.ensemble import RandomForestRegressor

        print(f"\n[TRAIN-FALLBACK] Entrenando modelos RandomForest para {target_name}")

        # Reshape X_train/X_test de (samples, timesteps, features) a (samples, features*timesteps)
        X_train_flat = X_train.reshape(X_train.shape[0], -1)
        X_test_flat = X_test.reshape(X_test.shape[0], -1)

        for step in self.forecast_steps:
            print(f"   Paso {step}h - Entrenando RandomForest...")

            rf = RandomForestRegressor(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )

            rf.fit(X_train_flat, y_train[step])
            self.models[step] = rf

            train_score = rf.score(X_train_flat, y_train[step])
            test_score = rf.score(X_test_flat, y_test[step])
            print(f"      Train R²: {train_score:.4f} | Test R²: {test_score:.4f}")

    def predict(self, X_test, y_test_true, scaler, target_name='PM2.5'):
        """Realiza predicciones y evalúa el modelo"""
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

        print(f"\n[PRED-FALLBACK] Evaluando predicciones para {target_name}")

        # Reshape X_test
        X_test_flat = X_test.reshape(X_test.shape[0], -1)

        results = {}
        predictions_scaled = {}

        for step in self.forecast_steps:
            print(f"\n   Paso {step}h:")

            # Predicción
            y_pred_scaled = self.models[step].predict(X_test_flat)
            predictions_scaled[step] = y_pred_scaled

            # Inverse scaling
            y_pred = scaler.inverse_transform(y_pred_scaled.reshape(-1, 1)).flatten()
            y_true = scaler.inverse_transform(y_test_true[step].reshape(-1, 1)).flatten()

            # Métricas
            rmse = np.sqrt(mean_squared_error(y_true, y_pred))
            mae = mean_absolute_error(y_true, y_pred)
            r2 = r2_score(y_true, y_pred)

            # MAPE con protección contra división por cero
            mask = y_true != 0
            if mask.sum() > 0:
                mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
            else:
                mape = 0.0

            results[step] = {
                'y_true': y_true,
                'y_pred': y_pred,
                'rmse': float(rmse),
                'mae': float(mae),
                'r2': float(r2),
                'mape': float(mape)
            }

            print(f"      RMSE: {rmse:.2f} μg/m³")
            print(f"      MAE:  {mae:.2f} μg/m³")
            print(f"      R²:   {r2:.4f}")
            print(f"      MAPE: {mape:.2f}%")

        return results


class PredictiveModelPipeline:
    """Pipeline completo de modelo predictivo"""

    def __init__(self, lookback_window=24, forecast_steps=[1, 3, 5]):
        self.lookback_window = lookback_window
        self.forecast_steps = forecast_steps
        self.preprocessor = TimeSeriesPreprocessor(lookback_window, forecast_steps)
        self.models = {}
        self.results = {}

    def train_and_evaluate(self, rmcab_df, output_dir='static/results'):
        """
        Pipeline completo de entrenamiento y evaluación

        IMPORTANTE: Recibe datos de RMCAB (NO PostgreSQL, NO sensores degradados)

        Args:
            rmcab_df: DataFrame con columnas [datetime, pm25_ref, pm10_ref, temperature, rh]
                      (pm25_ref y pm10_ref son REALES de RMCAB)
                      (temperature y rh están simuladas)
            output_dir: Directorio para guardar resultados
        """

        print("\n" + "="*70)
        print("[PIPELINE] Modelo Predictivo LSTM - DATOS DE RMCAB SOLAMENTE")
        print("="*70)
        print("\n⚠️  IMPORTANTE:")
        print("   ├─ Datos REALES: PM2.5 y PM10 de RMCAB (estación referencia)")
        print("   ├─ Datos SIMULADOS: Temperatura y Humedad Relativa")
        print("   ├─ Sensores Aire2/4/5: NO USADOS (están degradados)")
        print("   └─ PostgreSQL: NO UTILIZADO")

        # Crear directorio de resultados
        # Si viene de Flask, usar static/results; si no, usar ../results
        if not os.path.isabs(output_dir):
            # Resolver ruta relativa correctamente
            if os.path.exists('static'):
                output_dir = 'static/results'
            else:
                output_dir = '../results'

        os.makedirs(output_dir, exist_ok=True)

        # Entrenamiento para PM2.5
        print("\n" + "-"*70)
        print("OBJETIVO: Predecir PM2.5 (datos REALES de RMCAB)")
        print("-"*70)

        X_train_pm25, X_test_pm25, y_train_pm25, y_test_pm25, df_pm25 = \
            self.preprocessor.prepare_data(rmcab_df, 'pm25_ref', ['temperature', 'rh'])

        if KERAS_AVAILABLE:
            model_pm25 = LSTMPredictor(self.lookback_window, self.forecast_steps)
            model_pm25.train(X_train_pm25, y_train_pm25, X_test_pm25, y_test_pm25,
                           target_name='PM2.5', epochs=50)
            results_pm25 = model_pm25.predict(
                X_test_pm25, y_test_pm25,
                self.preprocessor.scaler_pm25,
                target_name='PM2.5'
            )
        else:
            print("[WARN] LSTM no disponible, usando RandomForest como fallback...")
            model_pm25 = FallbackPredictor(self.lookback_window, self.forecast_steps)
            model_pm25.train(X_train_pm25, y_train_pm25, X_test_pm25, y_test_pm25,
                           target_name='PM2.5', epochs=50)
            results_pm25 = model_pm25.predict(
                X_test_pm25, y_test_pm25,
                self.preprocessor.scaler_pm25,
                target_name='PM2.5'
            )

        self.models['pm25'] = model_pm25
        self.results['pm25'] = results_pm25

        # Entrenamiento para PM10
        print("\n" + "-"*70)
        print("OBJETIVO: Predecir PM10 (datos REALES de RMCAB)")
        print("-"*70)

        X_train_pm10, X_test_pm10, y_train_pm10, y_test_pm10, df_pm10 = \
            self.preprocessor.prepare_data(rmcab_df, 'pm10_ref', ['temperature', 'rh'])

        if KERAS_AVAILABLE:
            model_pm10 = LSTMPredictor(self.lookback_window, self.forecast_steps)
            model_pm10.train(X_train_pm10, y_train_pm10, X_test_pm10, y_test_pm10,
                           target_name='PM10', epochs=50)
            results_pm10 = model_pm10.predict(
                X_test_pm10, y_test_pm10,
                self.preprocessor.scaler_pm10,
                target_name='PM10'
            )
        else:
            print("[WARN] LSTM no disponible, usando RandomForest como fallback...")
            model_pm10 = FallbackPredictor(self.lookback_window, self.forecast_steps)
            model_pm10.train(X_train_pm10, y_train_pm10, X_test_pm10, y_test_pm10,
                           target_name='PM10', epochs=50)
            results_pm10 = model_pm10.predict(
                X_test_pm10, y_test_pm10,
                self.preprocessor.scaler_pm10,
                target_name='PM10'
            )

        self.models['pm10'] = model_pm10
        self.results['pm10'] = results_pm10

        # Generar reportes
        self._generate_reports(output_dir, results_pm25, results_pm10)

        return self.results

    def _generate_reports(self, output_dir, results_pm25, results_pm10):
        """Genera reportes y gráficos de resultados"""

        print("\n" + "="*70)
        print("[REPORTES] Generando reportes de resultados")
        print("="*70)

        # Crear tabla de métricas
        metrics_data = []

        for pollutant, results in [('PM2.5', results_pm25), ('PM10', results_pm10)]:
            for step in self.forecast_steps:
                if step in results:
                    metrics_data.append({
                        'Contaminante': pollutant,
                        'Paso (horas)': step,
                        'RMSE': results[step]['rmse'],
                        'MAE': results[step]['mae'],
                        'R²': results[step]['r2'],
                        'MAPE (%)': results[step]['mape']
                    })

        metrics_df = pd.DataFrame(metrics_data)
        metrics_csv = os.path.join(output_dir, 'predictive_metrics.csv')
        metrics_df.to_csv(metrics_csv, index=False)
        print(f"\n✓ Métricas guardadas: {metrics_csv}")
        print(metrics_df.to_string(index=False))

        # Crear gráficos de predicciones
        self._plot_predictions(output_dir, results_pm25, 'PM2.5')
        self._plot_predictions(output_dir, results_pm10, 'PM10')

        # Crear gráfico de comparación de pasos
        self._plot_steps_comparison(output_dir, results_pm25, results_pm10)

    def _plot_predictions(self, output_dir, results, pollutant_name):
        """Grafica predicciones vs valores reales"""
        if not results:
            print(f"[WARN] No hay resultados para {pollutant_name}, saltando gráfico")
            return

        print(f"\n[PLOT] Generando gráfico de predicciones para {pollutant_name}...")
        try:
            fig, axes = plt.subplots(1, 3, figsize=(15, 4))
            fig.suptitle(f'Predicciones de {pollutant_name} por Ventana Temporal', fontsize=14, fontweight='bold')

            for idx, step in enumerate(self.forecast_steps):
                if step not in results:
                    continue

                ax = axes[idx]
                y_true = results[step]['y_true']
                y_pred = results[step]['y_pred']

                # Gráfico de dispersión
                ax.scatter(y_true, y_pred, alpha=0.6, s=30, color='steelblue', edgecolors='navy', linewidth=0.5)

                # Línea de referencia (y=x)
                min_val = min(y_true.min(), y_pred.min())
                max_val = max(y_true.max(), y_pred.max())
                ax.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, alpha=0.7, label='Predicción Perfecta')

                ax.set_xlabel('Valor Real (μg/m³)', fontsize=10)
                ax.set_ylabel('Valor Predicho (μg/m³)', fontsize=10)
                ax.set_title(f'{step}h Adelante | R²={results[step]["r2"]:.3f} | RMSE={results[step]["rmse"]:.2f}', fontsize=10)
                ax.grid(True, alpha=0.3)
                ax.legend(fontsize=9)

            plt.tight_layout()
            # Nombres sin puntos: predictions_PM25.png, predictions_PM10.png
            filename = f'predictions_{pollutant_name.replace(".", "").replace(" ", "")}.png'
            plot_path = os.path.join(output_dir, filename)
            plt.savefig(plot_path, dpi=300, bbox_inches='tight')
            plt.close()
            print(f"✓ Gráfico guardado: {plot_path}")
        except Exception as e:
            print(f"[ERROR] Fallo al generar gráfico de {pollutant_name}: {e}")
            import traceback
            traceback.print_exc()
            plt.close()

    def _plot_steps_comparison(self, output_dir, results_pm25, results_pm10):
        """Gráfico comparando efectividad de diferentes pasos"""

        metrics = ['rmse', 'mae', 'r2', 'mape']
        fig, axes = plt.subplots(1, 4, figsize=(16, 4))
        fig.suptitle('Comparación de Métricas por Ventana Temporal', fontsize=14, fontweight='bold')

        pollutants = [('PM2.5', results_pm25), ('PM10', results_pm10)]

        for metric_idx, metric in enumerate(metrics):
            ax = axes[metric_idx]

            for pollutant_name, results in pollutants:
                if not results:
                    continue

                values = [results[step].get(metric, 0) for step in self.forecast_steps]
                ax.plot(self.forecast_steps, values, marker='o', linewidth=2, label=pollutant_name, markersize=8)

            ax.set_xlabel('Horas Adelante', fontsize=10)
            ax.set_ylabel(metric.upper(), fontsize=10)
            ax.set_title(metric.upper(), fontsize=11, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.set_xticks(self.forecast_steps)
            ax.legend(fontsize=9)

        plt.tight_layout()
        plot_path = os.path.join(output_dir, 'steps_comparison.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✓ Gráfico guardado: {plot_path}")

    def get_summary(self):
        """Retorna resumen de resultados"""
        summary = {
            'pm25': {},
            'pm10': {}
        }

        for pollutant in ['pm25', 'pm10']:
            if pollutant in self.results and self.results[pollutant]:
                for step in self.forecast_steps:
                    if step in self.results[pollutant]:
                        result = self.results[pollutant][step]
                        summary[pollutant][step] = {
                            'rmse': float(result['rmse']),
                            'mae': float(result['mae']),
                            'r2': float(result['r2']),
                            'mape': float(result['mape'])
                        }

        return summary
