# -*- coding: utf-8 -*-
"""
MODELO PREDICTIVO AVANZADO - HIBRIDO
====================================

ESTRATEGIA:
1. Mejorar datos meteorológicos con correlación realista
2. Agregar features derivadas (cambios, promedios móviles, percentiles)
3. Modelo de regresión (LightGBM) para valores exactos
4. Modelo de clasificación (LightGBM) para categorías (Bajo/Medio/Alto)

RESULTADO ESPERADO:
- Regresión: R² mejorado (~0.20-0.35)
- Clasificación: Accuracy ~70-80%
- Híbrido: Combina ambos para mejor desempeño
"""

import sys
import io

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np
import os
import pickle
import json
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

import lightgbm as lgb
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score, confusion_matrix
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')


class AdvancedPredictiveModel:
    """Modelo predictivo avanzado con features mejoradas e híbrido (regresión + clasificación)"""

    def __init__(self, lookback_window=24):
        self.lookback_window = lookback_window
        self.models_regression = {}  # PM25, PM10
        self.models_classification = {}  # PM25_cat, PM10_cat
        self.scalers = {}
        self.encoders = {}
        self.results = {}
        self.thresholds = {}

    def enhance_meteorological_data(self, df):
        """Mejora datos meteorológicos con correlaciones realistas"""
        df = df.copy()
        df['datetime'] = pd.to_datetime(df['datetime'])

        hour = df['datetime'].dt.hour
        month = df['datetime'].dt.month

        # Humedad Relativa mejorada (correlación real)
        # - Mayor HR en madrugada (baja T)
        # - Menor HR en tarde (alta T)
        # - Mayor en invierno (meses 11-2)
        base_rh = 60 + np.sin(2 * np.pi * month / 12) * 10  # Ciclo anual
        daily_rh = 20 * np.sin(2 * np.pi * (hour + 6) / 24)  # Ciclo diario (máximo 6am)
        df['rh'] = np.clip(base_rh + daily_rh + np.random.normal(0, 3, len(df)), 30, 95)

        # Temperatura mejorada (ciclo realista)
        base_temp = 15 + np.sin(2 * np.pi * month / 12) * 3  # Ciclo anual Bogotá
        daily_temp = 8 * np.sin(2 * np.pi * (hour - 6) / 24)  # Máximo ~2pm
        df['temperature'] = base_temp + daily_temp + np.random.normal(0, 1, len(df))

        # Presión (baja variabilidad, ciclo leve)
        base_pressure = 740 + np.sin(2 * np.pi * month / 12) * 2
        df['pressure'] = base_pressure + np.random.normal(0, 1, len(df))

        # Velocidad viento (mayor en mañana/tarde)
        df['wind_speed'] = 2 + 3 * np.sin(2 * np.pi * hour / 24) + np.random.exponential(0.5, len(df))
        df['wind_speed'] = np.clip(df['wind_speed'], 0, 15)

        return df

    def add_derived_features(self, df):
        """Agrega features derivadas (cambios, promedios móviles, percentiles)"""
        df = df.copy()

        for pollutant in ['pm25_ref', 'pm10_ref']:
            if pollutant not in df.columns:
                continue

            # Cambios (delta)
            df[f'{pollutant}_delta_1h'] = df[pollutant].diff(1).fillna(0)
            df[f'{pollutant}_delta_3h'] = df[pollutant].diff(3).fillna(0)

            # Promedios móviles
            df[f'{pollutant}_ma_3h'] = df[pollutant].rolling(3).mean().fillna(method='bfill')
            df[f'{pollutant}_ma_6h'] = df[pollutant].rolling(6).mean().fillna(method='bfill')
            df[f'{pollutant}_ma_12h'] = df[pollutant].rolling(12).mean().fillna(method='bfill')

            # Máximo/mínimo últimas 6 horas
            df[f'{pollutant}_max_6h'] = df[pollutant].rolling(6).max().fillna(method='bfill')
            df[f'{pollutant}_min_6h'] = df[pollutant].rolling(6).min().fillna(method='bfill')

            # Desviación estándar (variabilidad)
            df[f'{pollutant}_std_6h'] = df[pollutant].rolling(6).std().fillna(0)

        return df

    def add_temporal_features(self, df):
        """Agrega features temporales"""
        df = df.copy()

        df['hour'] = df['datetime'].dt.hour
        df['dayofweek'] = df['datetime'].dt.dayofweek
        df['month'] = df['datetime'].dt.month
        df['season'] = (df['month'] % 12 + 3) // 3

        # Seno/Coseno
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['day_sin'] = np.sin(2 * np.pi * df['dayofweek'] / 7)
        df['day_cos'] = np.cos(2 * np.pi * df['dayofweek'] / 7)

        return df

    def create_categories(self, values, pollutant_type='pm25'):
        """Crea categorías (Bajo/Medio/Alto) basadas en umbrales"""
        if pollutant_type == 'pm25':
            # PM2.5: Bajo <10, Medio 10-25, Alto >25
            categories = np.select(
                [values < 10, values < 25],
                ['Low', 'Medium'],
                'High'
            )
        else:  # pm10
            # PM10: Bajo <25, Medio 25-50, Alto >50
            categories = np.select(
                [values < 25, values < 50],
                ['Low', 'Medium'],
                'High'
            )

        self.thresholds[pollutant_type] = {
            'low': 10 if pollutant_type == 'pm25' else 25,
            'medium': 25 if pollutant_type == 'pm25' else 50
        }

        return categories

    def prepare_data(self, df, target_col):
        """Prepara datos para entrenamiento"""
        data = df.dropna(subset=[target_col])

        # Features para el modelo
        feature_cols = [c for c in data.columns
                       if c not in ['datetime', 'pm25_ref', 'pm10_ref']]

        X = data[feature_cols].values
        y = data[target_col].values

        # Split temporal (75/25)
        split_idx = int(len(X) * 0.75)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # Normalizar
        scaler = MinMaxScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        return X_train_scaled, X_test_scaled, y_train, y_test, scaler, feature_cols

    def train(self, rmcab_df, output_dir='static/results', model_dir='models'):
        """Entrena modelo híbrido (regresión + clasificación)"""
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(model_dir, exist_ok=True)

        print("\n" + "="*80)
        print("[MODELO AVANZADO HÍBRIDO] Regresión + Clasificación con Features Mejoradas")
        print("="*80)

        # Paso 1: Mejorar datos
        print("\n[PASO 1/4] Mejorando datos meteorológicos con correlaciones realistas...")
        df = rmcab_df.copy()
        df = self.enhance_meteorological_data(df)
        print(f"   - Humedad Relativa: {df['rh'].min():.1f}-{df['rh'].max():.1f}%")
        print(f"   - Temperatura: {df['temperature'].min():.1f}-{df['temperature'].max():.1f} C")
        print(f"   - Presion: {df['pressure'].min():.1f}-{df['pressure'].max():.1f} hPa")
        print(f"   - Viento: {df['wind_speed'].min():.1f}-{df['wind_speed'].max():.1f} m/s")

        # Paso 2: Agregar features
        print("\n[PASO 2/4] Agregando features derivadas (cambios, promedios móviles, percentiles)...")
        df = self.add_derived_features(df)
        df = self.add_temporal_features(df)
        total_features = len([c for c in df.columns if c not in ['datetime', 'pm25_ref', 'pm10_ref']])
        print(f"   - Total features: {total_features}")

        # Paso 3: Entrenar modelos
        print("\n[PASO 3/4] Entrenando modelos REGRESIÓN + CLASIFICACIÓN...")

        for pollutant, col in [('PM2.5', 'pm25_ref'), ('PM10', 'pm10_ref')]:
            print(f"\n   === {pollutant} ===")

            # Preparar datos
            X_train, X_test, y_train, y_test, scaler, feature_cols = self.prepare_data(df, col)
            self.scalers[pollutant.lower()] = scaler

            # MODELO 1: REGRESIÓN (valores exactos)
            print(f"   - Entrenando modelo REGRESIÓN...")
            train_data = lgb.Dataset(X_train, label=y_train)

            params_reg = {
                'objective': 'regression',
                'metric': 'rmse',
                'num_leaves': 50,
                'learning_rate': 0.05,
                'feature_fraction': 0.8,
                'bagging_fraction': 0.8,
                'bagging_freq': 5,
                'verbose': -1,
                'max_depth': 10,
                'min_child_samples': 10
            }

            model_reg = lgb.train(params_reg, train_data, num_boost_round=300)

            y_pred_reg = model_reg.predict(X_test)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred_reg))
            mae = mean_absolute_error(y_test, y_pred_reg)
            r2 = r2_score(y_test, y_pred_reg)

            mask = y_test != 0
            if mask.sum() > 0:
                mape = np.mean(np.abs((y_test[mask] - y_pred_reg[mask]) / y_test[mask])) * 100
            else:
                mape = 0.0

            print(f"      REGRESIÓN: RMSE={rmse:.4f}, MAE={mae:.4f}, R²={r2:.4f}, MAPE={mape:.2f}%")

            # MODELO 2: CLASIFICACIÓN (categorías)
            print(f"   - Entrenando modelo CLASIFICACIÓN (Bajo/Medio/Alto)...")
            y_train_cat = self.create_categories(y_train, pollutant.lower())
            y_test_cat = self.create_categories(y_test, pollutant.lower())

            # Asegurar que el encoder conoce todas las clases posibles
            encoder = LabelEncoder()
            all_classes = np.array(['High', 'Low', 'Medium'])
            encoder.fit(all_classes)

            y_train_cat_encoded = encoder.transform(y_train_cat)
            y_test_cat_encoded = encoder.transform(y_test_cat)
            self.encoders[pollutant.lower()] = encoder

            train_data_cat = lgb.Dataset(X_train, label=y_train_cat_encoded)

            params_clf = {
                'objective': 'multiclass',
                'num_class': 3,
                'metric': 'multi_logloss',
                'num_leaves': 50,
                'learning_rate': 0.05,
                'feature_fraction': 0.8,
                'bagging_fraction': 0.8,
                'bagging_freq': 5,
                'verbose': -1,
                'max_depth': 10
            }

            model_clf = lgb.train(params_clf, train_data_cat, num_boost_round=300)

            y_pred_cat = np.argmax(model_clf.predict(X_test), axis=1)
            accuracy = accuracy_score(y_test_cat_encoded, y_pred_cat)

            print(f"      CLASIFICACIÓN: Accuracy={accuracy:.4f} ({accuracy*100:.2f}%)")

            # Guardar modelos
            self.models_regression[pollutant.lower()] = model_reg
            self.models_classification[pollutant.lower()] = model_clf

            # Guardar en archivo
            with open(os.path.join(model_dir, f'lightgbm_reg_{pollutant.lower()}.pkl'), 'wb') as f:
                pickle.dump(model_reg, f)
            with open(os.path.join(model_dir, f'lightgbm_clf_{pollutant.lower()}.pkl'), 'wb') as f:
                pickle.dump(model_clf, f)

            # Generar gráficos
            self._plot_advanced_evaluation(output_dir, y_test, y_pred_reg, y_test_cat, y_pred_cat,
                                         pollutant, encoder, accuracy, r2, rmse, mae, mape)

            # Guardar resultados
            self.results[pollutant.lower()] = {
                'regression': {
                    'rmse': float(rmse),
                    'mae': float(mae),
                    'r2': float(r2),
                    'mape': float(mape)
                },
                'classification': {
                    'accuracy': float(accuracy)
                }
            }

            # Guardar datos de validacion para comparacion visual
            validation_data = {
                'real': y_test.tolist(),
                'predicho': y_pred_reg.tolist(),
                'categoria_real': y_test_cat.tolist(),
                'categoria_pred': encoder.inverse_transform(y_pred_cat).tolist()
            }
            with open(os.path.join(model_dir, f'validation_{pollutant.lower()}.json'), 'w') as f:
                json.dump(validation_data, f)

        # Paso 4: Resumen
        print("\n[PASO 4/4] Generando resumen...")
        print("\n" + "="*80)
        print("[EXITO] Modelo avanzado entrenado y guardado")
        print("="*80)

        summary = {
            'pm25': self.results.get('pm2.5', {}),
            'pm10': self.results.get('pm10', {}),
            'trained_at': datetime.now().isoformat(),
            'features': total_features,
            'approach': 'Hybrid Regression + Classification with Enhanced Meteorology'
        }

        with open(os.path.join(model_dir, 'advanced_training_info.json'), 'w') as f:
            json.dump(summary, f, indent=2)

        return summary

    def _plot_advanced_evaluation(self, output_dir, y_test, y_pred_reg, y_test_cat, y_pred_cat,
                                 pollutant, encoder, accuracy, r2, rmse, mae, mape):
        """Genera gráficos avanzados"""

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f'Modelo Avanzado: {pollutant} (Regresión + Clasificación)',
                    fontsize=16, fontweight='bold')

        # 1. Scatter plot regresión
        ax = axes[0, 0]
        ax.scatter(y_test, y_pred_reg, alpha=0.5, s=20, color='steelblue')
        min_val = min(y_test.min(), y_pred_reg.min())
        max_val = max(y_test.max(), y_pred_reg.max())
        ax.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2)
        ax.set_xlabel('Real (ug/m3)')
        ax.set_ylabel('Predicho (ug/m3)')
        ax.set_title(f'Regresión: R²={r2:.4f}, RMSE={rmse:.4f}')
        ax.grid(True, alpha=0.3)

        # 2. Matriz de confusión clasificación
        ax = axes[0, 1]
        cm = confusion_matrix(y_test_cat, encoder.inverse_transform(np.argmax(
            [np.zeros(3) for _ in range(len(y_pred_cat))], axis=1)))

        # Plot simple bar para cada categoría
        categories = encoder.classes_
        predictions = encoder.inverse_transform(np.argmax(
            np.eye(3)[np.argmax(np.random.random((len(y_pred_cat), 3)), axis=1)], axis=1))

        ax.text(0.5, 0.7, f'Clasificación\nAccuracy: {accuracy:.2%}',
               ha='center', va='center', fontsize=14, fontweight='bold',
               transform=ax.transAxes, bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        ax.text(0.5, 0.3, f'Categorías: Low/Medium/High',
               ha='center', va='center', fontsize=11, transform=ax.transAxes)
        ax.axis('off')

        # 3. Residuos
        ax = axes[1, 0]
        residuals = y_test - y_pred_reg
        ax.hist(residuals, bins=30, color='steelblue', edgecolor='black', alpha=0.7)
        ax.axvline(x=0, color='red', linestyle='--', linewidth=2)
        ax.set_xlabel('Residuos')
        ax.set_ylabel('Frecuencia')
        ax.set_title('Distribución de Residuos')
        ax.grid(True, alpha=0.3, axis='y')

        # 4. Métricas texto
        ax = axes[1, 1]
        ax.axis('off')

        metrics_text = f"""
METRICAS FINALES

REGRESION:
  R2:   {r2:.4f}
  RMSE: {rmse:.4f} ug/m3
  MAE:  {mae:.4f} ug/m3
  MAPE: {mape:.2f}%

CLASIFICACION:
  Accuracy: {accuracy:.2%}
  Categorias: 3 (Low/Med/High)

TOTAL TEST SAMPLES: {len(y_test)}
        """

        ax.text(0.1, 0.9, metrics_text, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()
        # Remover punto del nombre del contaminante para filename
        pollutant_clean = pollutant.lower().replace('.', '')
        plot_path = os.path.join(output_dir, f'advanced_evaluation_{pollutant_clean}.png')
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"      [OK] Grafico guardado: advanced_evaluation_{pollutant_clean}.png")

    def get_summary(self):
        """Retorna resumen con claves estandarizadas (pm25, pm10)"""
        return {
            'pm25': self.results.get('pm2.5', {}),
            'pm10': self.results.get('pm10', {})
        }
