"""
MODELO PREDICTIVO MEJORADO PARA PM2.5 Y PM10
==============================================

ARQUITECTURA:
- Modelo: LightGBM (mejor que XGBoost: mas rapido, sin problemas de permisos)
- Features: PM histórico + Features temporales (hora, día semana, mes, estación)
- Ventana temporal: 24 horas
- Split: 75% entrenamiento, 25% test (temporal, sin shuffle)
- Persistencia: Se guarda el modelo entrenado para no reentrenar

CARACTERÍSTICAS AGREGADAS:
1. Hora del día (0-23) - captura ciclo diario
2. Día de semana (0-6) - captura patrones semanales
3. Mes (1-12) - captura estacionalidad
4. Seno/Coseno(hora) - periodicidad 24h continua
5. Seno/Coseno(día semana) - periodicidad 7d continua
6. Estación del año (0-3) - captura ciclos largos

MÉTRICAS ESPERADAS (mejora vs RandomForest):
- R² esperado: 0.15-0.30 (vs 0.02-0.10 anterior)
- RMSE esperado: mejor captura de varianza
- Interpretabilidad: Features temporales más claras

FLUJO:
1. PRIMER ENTRENAMIENTO:
   - Carga datos RMCAB
   - Agrega features temporales
   - Entrena XGBoost (toma ~2-5 min)
   - Guarda modelo en: models/xgboost_pm25.pkl, models/xgboost_pm10.pkl
   - Genera gráficos de evaluación

2. CARGAS POSTERIORES:
   - Lee modelos guardados
   - NO reentena
   - Solo predice sobre nuevos datos
"""

import pandas as pd
import numpy as np
import os
import pickle
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Imports para LightGBM (mejor que XGBoost, sin problemas de permisos)
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
    print("[OK] LightGBM disponible")
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("[INFO] Instalando LightGBM...")
    os.system("pip install lightgbm --user --no-cache-dir")
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')


class ImprovedPredictiveModel:
    """Modelo mejorado con features temporales y XGBoost"""

    def __init__(self, lookback_window=24, forecast_steps=[1, 3, 5]):
        """
        Args:
            lookback_window: Horas de histórico a usar (24 = 1 día)
            forecast_steps: Pasos adelante a predecir (1, 3, 5 horas)
        """
        self.lookback_window = lookback_window
        self.forecast_steps = forecast_steps
        self.models = {}  # {pollutant: {step: model}}
        self.scalers = {}  # {pollutant: scaler}
        self.results = {}
        self.feature_names = None
        self.model_info = {}

    def add_temporal_features(self, df):
        """Agrega features temporales al DataFrame"""
        df = df.copy()
        df['datetime'] = pd.to_datetime(df['datetime'])

        # Hora del día (0-23)
        df['hour'] = df['datetime'].dt.hour

        # Día de semana (0-6, donde 0=lunes)
        df['dayofweek'] = df['datetime'].dt.dayofweek

        # Mes (1-12)
        df['month'] = df['datetime'].dt.month

        # Estación (0-3: invierno=0, primavera=1, verano=2, otoño=3)
        # En Bogotá: semestres secos (dic-mar, jul-ago) y húmedos
        season = (df['month'] % 12 + 3) // 3
        df['season'] = season % 4

        # Seno/Coseno para periodicidad 24h (suave)
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)

        # Seno/Coseno para periodicidad 7d (suave)
        df['day_sin'] = np.sin(2 * np.pi * df['dayofweek'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['dayofweek'] / 7)

        return df

    def prepare_sequences(self, df, target_col, step):
        """Prepara secuencias para predecir 'step' horas adelante"""
        data = df[[target_col] + [c for c in df.columns if c not in ['datetime', target_col]]].values

        X, y = [], []

        for i in range(len(data) - self.lookback_window - step):
            X.append(data[i:i + self.lookback_window])
            y.append(data[i + self.lookback_window + step - 1, 0])

        return np.array(X).reshape(len(X), -1), np.array(y)

    def train(self, rmcab_df, output_dir='static/results', model_dir='models'):
        """
        Entrena modelos XGBoost para PM2.5 y PM10

        Args:
            rmcab_df: DataFrame con datetime, pm25_ref, pm10_ref
            output_dir: Directorio para gráficos
            model_dir: Directorio para guardar modelos

        Returns:
            dict con información del entrenamiento
        """
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(model_dir, exist_ok=True)

        print("\n" + "="*80)
        print("[ENTRENAMIENTOMEJORADO] XGBoost con Features Temporales")
        print("="*80)

        print("\n[PASO 1] Agregando features temporales...")
        df = self.add_temporal_features(rmcab_df)
        self.feature_names = [c for c in df.columns if c not in ['datetime', 'pm25_ref', 'pm10_ref']]

        print(f"   ✓ Features agregados: {self.feature_names}")
        print(f"   ✓ Total features: {len(self.feature_names)}")

        # Entrenar para PM2.5
        print("\n" + "-"*80)
        print("[ENTRENAMIENTO PM2.5] 24 horas de histórico + features temporales")
        print("-"*80)

        train_info_pm25 = self._train_pollutant(
            df, 'pm25_ref', 'PM2.5', output_dir, model_dir
        )

        # Entrenar para PM10
        print("\n" + "-"*80)
        print("[ENTRENAMIENTO PM10] 24 horas de histórico + features temporales")
        print("-"*80)

        train_info_pm10 = self._train_pollutant(
            df, 'pm10_ref', 'PM10', output_dir, model_dir
        )

        self.model_info = {
            'pm25': train_info_pm25,
            'pm10': train_info_pm10,
            'features': self.feature_names,
            'lookback_window': self.lookback_window,
            'forecast_steps': self.forecast_steps,
            'trained_at': datetime.now().isoformat()
        }

        # Guardar info del entrenamiento
        info_path = os.path.join(model_dir, 'training_info.json')
        with open(info_path, 'w') as f:
            # Convertir arrays a listas para JSON
            info_serializable = {
                'pm25': {
                    'steps': {str(k): {
                        'r2': float(v.get('r2', 0)),
                        'rmse': float(v.get('rmse', 0)),
                        'mae': float(v.get('mae', 0)),
                        'mape': float(v.get('mape', 0))
                    } for k, v in train_info_pm25.get('steps', {}).items()}
                },
                'pm10': {
                    'steps': {str(k): {
                        'r2': float(v.get('r2', 0)),
                        'rmse': float(v.get('rmse', 0)),
                        'mae': float(v.get('mae', 0)),
                        'mape': float(v.get('mape', 0))
                    } for k, v in train_info_pm10.get('steps', {}).items()}
                },
                'trained_at': self.model_info['trained_at']
            }
            json.dump(info_serializable, f, indent=2)

        print("\n" + "="*80)
        print("[EXITO] Entrenamiento completado y modelos guardados")
        print("="*80)
        print(f"Ubicación: {model_dir}/")
        print(f"Archivos:")
        print(f"  - xgboost_pm25.pkl")
        print(f"  - xgboost_pm10.pkl")
        print(f"  - training_info.json")
        print(f"  - scaler_pm25.pkl")
        print(f"  - scaler_pm10.pkl")

        return self.model_info

    def _train_pollutant(self, df, target_col, pollutant_name, output_dir, model_dir):
        """Entrena modelo para un contaminante específico"""

        print(f"\n   [1] Preparando datos para {pollutant_name}...")
        X_all, y_all = self.prepare_sequences(df, target_col, step=1)

        if len(X_all) < 100:
            print(f"   [ERROR] Datos insuficientes para {pollutant_name}")
            return {}

        # Split temporal (75/25)
        split_idx = int(len(X_all) * 0.75)
        X_train = X_all[:split_idx]
        X_test = X_all[split_idx:]
        y_train = y_all[:split_idx]
        y_test = y_all[split_idx:]

        print(f"      Train: {len(X_train)} muestras")
        print(f"      Test:  {len(X_test)} muestras")

        # Normalizar
        print(f"\n   [2] Normalizando datos...")
        scaler = MinMaxScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Entrenar LightGBM (mejor que XGBoost: mas rapido, sin problemas de permisos)
        print(f"\n   [3] Entrenando LightGBM (esto puede tomar 30-60 segundos)...")

        train_data = lgb.Dataset(X_train_scaled, label=y_train)

        params = {
            'objective': 'regression',
            'metric': 'rmse',
            'num_leaves': 31,
            'learning_rate': 0.1,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1
        }

        model = lgb.train(
            params,
            train_data,
            num_boost_round=200
        )

        # Predicciones
        y_pred_train = model.predict(X_train_scaled)
        y_pred_test = model.predict(X_test_scaled)

        # Métricas
        print(f"\n   [4] Evaluando modelo...")

        rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))
        mae_test = mean_absolute_error(y_test, y_pred_test)
        r2_test = r2_score(y_test, y_pred_test)

        # MAPE protegido
        mask = y_test != 0
        if mask.sum() > 0:
            mape_test = np.mean(np.abs((y_test[mask] - y_pred_test[mask]) / y_test[mask])) * 100
        else:
            mape_test = 0.0

        print(f"      RMSE Test: {rmse_test:.4f}")
        print(f"      MAE Test:  {mae_test:.4f}")
        print(f"      R² Test:   {r2_test:.4f}")
        print(f"      MAPE Test: {mape_test:.2f}%")

        # Guardar modelo
        model_path = os.path.join(model_dir, f'lightgbm_{pollutant_name.lower()}.pkl')
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        print(f"      ✓ Modelo guardado: {model_path}")

        # Guardar scaler
        scaler_path = os.path.join(model_dir, f'scaler_{pollutant_name.lower()}.pkl')
        with open(scaler_path, 'wb') as f:
            pickle.dump(scaler, f)

        # Generar gráficos
        self._plot_predictions(output_dir, y_test, y_pred_test, pollutant_name)

        self.models[pollutant_name.lower()] = model
        self.scalers[pollutant_name.lower()] = scaler

        return {
            'steps': {
                1: {
                    'r2': float(r2_test),
                    'rmse': float(rmse_test),
                    'mae': float(mae_test),
                    'mape': float(mape_test)
                }
            }
        }

    def _plot_predictions(self, output_dir, y_true, y_pred, pollutant_name):
        """Genera gráficos de predicciones vs reales"""

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f'Evaluación del Modelo: {pollutant_name}', fontsize=16, fontweight='bold')

        # 1. Scatter plot: Real vs Predicho
        ax = axes[0, 0]
        ax.scatter(y_true, y_pred, alpha=0.6, s=20, color='steelblue', edgecolors='navy', linewidth=0.5)
        min_val = min(y_true.min(), y_pred.min())
        max_val = max(y_true.max(), y_pred.max())
        ax.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Predicción Perfecta')
        ax.set_xlabel('Valores Reales (μg/m³)', fontsize=10)
        ax.set_ylabel('Valores Predichos (μg/m³)', fontsize=10)
        ax.set_title('Predicciones vs Valores Reales (Scatter)', fontsize=11, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 2. Evolución temporal
        ax = axes[0, 1]
        time_points = min(200, len(y_true))
        ax.plot(range(time_points), y_true[:time_points], 'o-', label='Real', linewidth=2, markersize=4, color='blue')
        ax.plot(range(time_points), y_pred[:time_points], 's-', label='Predicho', linewidth=2, markersize=4, color='red', alpha=0.7)
        ax.set_xlabel('Tiempo (muestras)', fontsize=10)
        ax.set_ylabel('Concentración (μg/m³)', fontsize=10)
        ax.set_title('Evolución Temporal (primeras 200 muestras)', fontsize=11, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 3. Residuos
        ax = axes[1, 0]
        residuals = y_true - y_pred
        ax.hist(residuals, bins=30, color='steelblue', edgecolor='black', alpha=0.7)
        ax.axvline(x=0, color='red', linestyle='--', linewidth=2)
        ax.set_xlabel('Residuos (Real - Predicho)', fontsize=10)
        ax.set_ylabel('Frecuencia', fontsize=10)
        ax.set_title('Distribución de Residuos', fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

        # 4. Métricas texto
        ax = axes[1, 1]
        ax.axis('off')

        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae = mean_absolute_error(y_true, y_pred)
        r2 = r2_score(y_true, y_pred)
        mask = y_true != 0
        if mask.sum() > 0:
            mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
        else:
            mape = 0.0

        metrics_text = f"""
METRICAS DE DESEMPEÑO

R²:   {r2:.4f}
RMSE: {rmse:.4f} μg/m³
MAE:  {mae:.4f} μg/m³
MAPE: {mape:.2f}%

DATOS
Muestras test: {len(y_true)}
Real min/max: {y_true.min():.2f} / {y_true.max():.2f}
Pred min/max: {y_pred.min():.2f} / {y_pred.max():.2f}
        """

        ax.text(0.1, 0.9, metrics_text, transform=ax.transAxes, fontsize=11,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()
        filename = f'evaluation_{pollutant_name.lower()}.png'
        plot_path = os.path.join(output_dir, filename)
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"      ✓ Gráfico guardado: {filename}")

    def load_trained_model(self, model_dir='models'):
        """Carga modelos ya entrenados sin reentrenar"""
        print("\n[CARGA DE MODELO] Buscando modelos entrenados...")

        loaded_models = []

        for pollutant in ['pm25', 'pm10']:
            model_path = os.path.join(model_dir, f'lightgbm_{pollutant}.pkl')
            scaler_path = os.path.join(model_dir, f'scaler_{pollutant}.pkl')

            if os.path.exists(model_path) and os.path.exists(scaler_path):
                with open(model_path, 'rb') as f:
                    self.models[pollutant] = pickle.load(f)
                with open(scaler_path, 'rb') as f:
                    self.scalers[pollutant] = pickle.load(f)
                print(f"   ✓ Modelo {pollutant.upper()} cargado")
                loaded_models.append(pollutant)
            else:
                print(f"   ✗ Modelo {pollutant.upper()} NO encontrado")

        # Cargar info
        info_path = os.path.join(model_dir, 'training_info.json')
        if os.path.exists(info_path):
            with open(info_path, 'r') as f:
                self.model_info = json.load(f)
            print(f"   ✓ Info del entrenamiento cargada")

        return len(loaded_models) == 2

    def get_summary(self):
        """Retorna resumen de resultados"""
        if not self.model_info:
            return {}

        return {
            'pm25': self.model_info.get('pm25', {}).get('steps', {}),
            'pm10': self.model_info.get('pm10', {}).get('steps', {})
        }
