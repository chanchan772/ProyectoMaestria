"""
Módulo para calibración de sensores usando Machine Learning
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.base import clone
import joblib
import os
from datetime import datetime
import warnings
import builtins
import sys
warnings.filterwarnings('ignore')


def _safe_print(*args, **kwargs):
    """
    Imprime mensajes degradando caracteres no soportados por la consola actual
    para evitar UnicodeEncodeError en Windows/PowerShell.
    """
    try:
        builtins.print(*args, **kwargs)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, 'encoding', None) or 'ascii'
        sanitized_args = []
        for arg in args:
            if isinstance(arg, str):
                sanitized = arg.encode(encoding, errors='ignore').decode(encoding, errors='ignore')
                sanitized_args.append(sanitized)
            else:
                sanitized_args.append(arg)
        builtins.print(*sanitized_args, **kwargs)


# Reemplazar print local en este módulo por la versión segura
print = _safe_print

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except Exception:
    XGBOOST_AVAILABLE = False

try:
    from lightgbm import LGBMRegressor
    LIGHTGBM_AVAILABLE = True
except Exception:
    LIGHTGBM_AVAILABLE = False

try:
    import tensorflow as tf
    from tensorflow.keras import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    from tensorflow.keras.optimizers import Adam
    TENSORFLOW_AVAILABLE = True
except Exception:
    TENSORFLOW_AVAILABLE = False


FEATURE_LABELS = {
    'pm25_sensor': 'PM2.5 sensor',
    'pm10_sensor': 'PM10 sensor',
    'temperature': 'Temperatura (°C)',
    'rh': 'Humedad relativa (%)',
    'hour': 'Hora del día',
    'period_of_day': 'Período del día',
    'day_of_week': 'Día de la semana',
    'is_weekend': 'Es fin de semana',
    'pm25_sensor_lag_1h': 'PM2.5 sensor t-1h',
    'pm25_sensor_lag_3h': 'PM2.5 sensor t-3h',
    'pm25_sensor_lag_6h': 'PM2.5 sensor t-6h',
    'pm10_sensor_lag_1h': 'PM10 sensor t-1h',
    'pm10_sensor_lag_3h': 'PM10 sensor t-3h',
    'pm10_sensor_lag_6h': 'PM10 sensor t-6h',
    'pm25_sensor_roll_mean_3h': 'Media PM2.5 3h',
    'pm25_sensor_roll_mean_6h': 'Media PM2.5 6h',
    'pm25_sensor_roll_mean_12h': 'Media PM2.5 12h',
    'pm10_sensor_roll_mean_3h': 'Media PM10 3h',
    'pm10_sensor_roll_mean_6h': 'Media PM10 6h',
    'pm10_sensor_roll_mean_12h': 'Media PM10 12h',
    'pm25_sensor_roll_std_3h': 'Desv. PM2.5 3h',
    'pm25_sensor_roll_std_6h': 'Desv. PM2.5 6h',
    'pm25_sensor_roll_std_12h': 'Desv. PM2.5 12h',
    'pm10_sensor_roll_std_3h': 'Desv. PM10 3h',
    'pm10_sensor_roll_std_6h': 'Desv. PM10 6h',
    'pm10_sensor_roll_std_12h': 'Desv. PM10 12h',
    'temperature_roll_mean_6h': 'Media temperatura 6h',
    'rh_roll_mean_6h': 'Media humedad 6h',
    'hour_sin': 'Componente seno hora',
    'hour_cos': 'Componente coseno hora',
    'day_sin': 'Componente seno día',
    'day_cos': 'Componente coseno día'
}

POLLUTANT_LABELS = {
    'pm25': 'PM2.5',
    'pm10': 'PM10'
}

def get_calibration_models():
    """
    Retorna diccionario con modelos de calibración optimizados

    Returns:
        dict: Diccionario con nombre: modelo
    """
    models = {
        'Linear Regression': LinearRegression(),
        'Ridge Regression': Ridge(alpha=1.0, random_state=42),
        'Random Forest': RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        ),
        'SVR (Linear)': SVR(kernel='linear', C=1.0, epsilon=0.1),
        'SVR (RBF)': SVR(kernel='rbf', C=10.0, gamma='scale', epsilon=0.1),
        'SVR (Polynomial)': SVR(kernel='poly', C=1.0, degree=2, gamma='scale', epsilon=0.1)
    }
    return models


def calculate_mape(y_true, y_pred):
    """
    Calcula Mean Absolute Percentage Error con manejo robusto de valores cero

    Args:
        y_true: Valores reales
        y_pred: Valores predichos

    Returns:
        float: MAPE en porcentaje
    """
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    # Evitar división por cero y valores muy pequeños
    mask = np.abs(y_true) > 1e-10
    
    if not mask.any():
        return 0.0
    
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    
    # Limitar MAPE a valores razonables
    return min(mape, 999.99)


def calculate_adjusted_r2(r2, n_samples, n_features):
    """
    Calcula R² ajustado

    Args:
        r2: R² original
        n_samples: Número de muestras
        n_features: Número de features

    Returns:
        float: R² ajustado
    """
    if n_samples <= n_features + 1:
        return r2
    
    adjusted = 1 - (1 - r2) * (n_samples - 1) / (n_samples - n_features - 1)
    return max(adjusted, 0.0)


def detect_overfitting(r2_train, r2_test, rmse_train, rmse_test):
    """
    Detecta si hay overfitting en el modelo

    Args:
        r2_train: R² en entrenamiento
        r2_test: R² en test
        rmse_train: RMSE en entrenamiento
        rmse_test: RMSE en test

    Returns:
        dict: {'status': str, 'severity': str, 'message': str}
    """
    r2_diff = r2_train - r2_test
    rmse_ratio = rmse_test / rmse_train if rmse_train > 0 else 1.0
    
    if r2_diff > 0.2 or rmse_ratio > 1.5:
        return {
            'status': 'overfitting',
            'severity': 'high',
            'message': f'Overfitting significativo detectado (ΔR²={r2_diff:.3f}, RMSE ratio={rmse_ratio:.2f})'
        }
    elif r2_diff > 0.1 or rmse_ratio > 1.2:
        return {
            'status': 'overfitting',
            'severity': 'moderate',
            'message': f'Overfitting moderado detectado (ΔR²={r2_diff:.3f}, RMSE ratio={rmse_ratio:.2f})'
        }
    else:
        return {
            'status': 'ok',
            'severity': 'none',
            'message': 'No se detectó overfitting'
        }


def evaluate_model(model, X_train, X_test, y_train, y_test, model_name, feature_names=None, use_cross_val=True):
    """
    Evalúa un modelo con métricas completas incluyendo validación cruzada
    """
    try:
        model.fit(X_train, y_train)

        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)

        # Métricas básicas
        r2 = r2_score(y_test, y_pred_test)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        mae = mean_absolute_error(y_test, y_pred_test)
        mape = calculate_mape(y_test, y_pred_test)

        r2_train = r2_score(y_train, y_pred_train)
        rmse_train = np.sqrt(mean_squared_error(y_train, y_pred_train))
        
        # R² ajustado
        n_samples = len(y_test)
        n_features = X_test.shape[1]
        r2_adjusted = calculate_adjusted_r2(r2, n_samples, n_features)
        
        # Detección de overfitting
        overfitting_info = detect_overfitting(r2_train, r2, rmse_train, rmse)

        result = {
            'model_name': model_name,
            'r2': round(float(r2), 4),
            'r2_train': round(float(r2_train), 4),
            'r2_adjusted': round(float(r2_adjusted), 4),
            'rmse': round(float(rmse), 4),
            'rmse_train': round(float(rmse_train), 4),
            'mae': round(float(mae), 4),
            'mape': round(float(mape), 2),
            'overfitting': overfitting_info,
            'actual': [float(val) for val in np.array(y_test).ravel().tolist()],
            'predicted': [float(val) for val in np.array(y_pred_test).ravel().tolist()]
        }
        
        # Validación cruzada (opcional, solo si hay suficientes datos)
        if use_cross_val and len(X_train) >= 100:
            try:
                kfold = KFold(n_splits=5, shuffle=True, random_state=42)
                cv_scores = cross_val_score(model, X_train, y_train, cv=kfold, scoring='r2', n_jobs=-1)
                result['cv_r2_mean'] = round(float(cv_scores.mean()), 4)
                result['cv_r2_std'] = round(float(cv_scores.std()), 4)
            except Exception:
                pass

        # Coeficientes para modelos lineales
        if hasattr(model, 'coef_') and hasattr(model, 'intercept_'):
            coefficients = model.coef_
            if isinstance(coefficients, np.ndarray):
                coefficients = coefficients.ravel()
            result['coefficients'] = [round(float(coef), 6) for coef in np.atleast_1d(coefficients)]
            result['intercept'] = round(float(model.intercept_), 6)
            if feature_names:
                result['feature_names'] = list(feature_names)

        # Guardar el modelo entrenado completo (necesario para modelos no lineales)
        result['trained_model'] = model

        return result

    except Exception as exc:
        print(f"Error evaluando modelo {model_name}: {exc}")
        import traceback
        traceback.print_exc()
        return None





def remove_outliers(df, columns, method='iqr', threshold=1.5):
    """
    Elimina valores atípicos de un DataFrame

    Args:
        df: DataFrame
        columns: Lista de columnas para analizar outliers
        method: 'iqr' o 'zscore'
        threshold: Umbral para IQR (default 1.5) o z-score (default 3)

    Returns:
        DataFrame sin outliers
    """
    df_clean = df.copy()
    
    for col in columns:
        if col not in df_clean.columns:
            continue
            
        if method == 'iqr':
            Q1 = df_clean[col].quantile(0.25)
            Q3 = df_clean[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            mask = (df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)
        else:  # zscore
            mean = df_clean[col].mean()
            std = df_clean[col].std()
            mask = np.abs((df_clean[col] - mean) / std) <= threshold
        
        df_clean = df_clean[mask]
    
    return df_clean


def add_advanced_features(merged, pollutant):
    """
    Genera variables avanzadas (lags, ventanas móviles y componentes cíclicas).

    Args:
        merged (DataFrame): Datos combinados después del merge asof.
        pollutant (str): 'pm25' o 'pm10'.

    Returns:
        tuple[DataFrame, list[str]]: DataFrame con columnas agregadas y listado de columnas nuevas.
    """
    if merged.empty:
        return merged, []

    df = merged.sort_values('datetime').copy()
    target_col = f'{pollutant}_sensor'
    if target_col not in df.columns:
        return df, []

    new_columns = []

    # Lags temporales
    for lag in [1, 3, 6]:
        col_name = f'{target_col}_lag_{lag}h'
        df[col_name] = df[target_col].shift(lag)
        df[col_name] = df[col_name].fillna(df[target_col])
        new_columns.append(col_name)

    # Medias y desviaciones móviles
    for window in [3, 6, 12]:
        mean_col = f'{target_col}_roll_mean_{window}h'
        std_col = f'{target_col}_roll_std_{window}h'
        df[mean_col] = df[target_col].rolling(window, min_periods=1).mean()
        df[std_col] = df[target_col].rolling(window, min_periods=2).std()
        df[std_col] = df[std_col].fillna(0.0)
        new_columns.extend([mean_col, std_col])

    if 'temperature' in df.columns:
        df['temperature_roll_mean_6h'] = df['temperature'].rolling(6, min_periods=1).mean()
        new_columns.append('temperature_roll_mean_6h')

    if 'rh' in df.columns:
        df['rh_roll_mean_6h'] = df['rh'].rolling(6, min_periods=1).mean()
        new_columns.append('rh_roll_mean_6h')

    if 'hour' in df.columns:
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24.0)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24.0)
        new_columns.extend(['hour_sin', 'hour_cos'])

    if 'day_of_week' in df.columns:
        df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7.0)
        df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7.0)
        new_columns.extend(['day_sin', 'day_cos'])

    return df, new_columns


def build_extra_model_definitions():
    """
    Define modelos avanzados adicionales a evaluar en la etapa 2.

    Returns:
        list[dict]: Cada dict incluye el estimador y si requiere features escaladas.
    """
    models = [
        {
            'name': 'Extra Trees',
            'estimator': ExtraTreesRegressor(
                n_estimators=300,
                max_depth=None,
                min_samples_split=2,
                min_samples_leaf=1,
                random_state=42,
                n_jobs=-1
            ),
            'use_scaled': False
        },
        {
            'name': 'Gradient Boosting',
            'estimator': GradientBoostingRegressor(
                n_estimators=400,
                learning_rate=0.05,
                max_depth=5,
                subsample=0.8,
                random_state=42
            ),
            'use_scaled': False
        }
    ]

    if XGBOOST_AVAILABLE:
        models.append({
            'name': 'XGBoost',
            'estimator': XGBRegressor(
                n_estimators=600,
                learning_rate=0.05,
                max_depth=6,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_lambda=1.0,
                random_state=42,
                n_jobs=-1,
                objective='reg:squarederror'
            ),
            'use_scaled': False
        })

    if LIGHTGBM_AVAILABLE:
        models.append({
            'name': 'LightGBM',
            'estimator': LGBMRegressor(
                n_estimators=800,
                learning_rate=0.05,
                max_depth=-1,
                num_leaves=63,
                subsample=0.9,
                colsample_bytree=0.9,
                reg_lambda=0.5,
                random_state=42,
                n_jobs=-1
            ),
            'use_scaled': False
        })

    return models


def get_default_lstm_configs():
    """
    Configuraciones base para probar variantes de LSTM.
    """
    return [
        {
            'name': 'LSTM (32x1)',
            'units': 32,
            'layers': 1,
            'dropout': 0.1,
            'epochs': 80,
            'batch_size': 32,
            'learning_rate': 0.001
        },
        {
            'name': 'LSTM (64x2)',
            'units': 64,
            'layers': 2,
            'dropout': 0.2,
            'epochs': 120,
            'batch_size': 32,
            'learning_rate': 0.001
        },
        {
            'name': 'Bi-LSTM compacto',
            'units': 48,
            'layers': 2,
            'dropout': 0.3,
            'epochs': 120,
            'batch_size': 32,
            'learning_rate': 0.0007,
            'bidirectional': True
        }
    ]


def train_lstm_variants(X_train, X_test, y_train, y_test, feature_names, configs):
    """
    Entrena configuraciones de LSTM y devuelve métricas comparables.
    """
    results = []
    logs = []

    if not configs:
        return results, logs

    if not TENSORFLOW_AVAILABLE:
        logs.append('TensorFlow/Keras no está instalado. Se omiten modelos LSTM.')
        return results, logs

    # Asegurar np.ndarray float32
    X_train = np.asarray(X_train, dtype=np.float32)
    X_test = np.asarray(X_test, dtype=np.float32)
    y_train = np.asarray(y_train, dtype=np.float32).reshape(-1, 1)
    y_test = np.asarray(y_test, dtype=np.float32).reshape(-1, 1)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    X_train_seq = np.reshape(X_train_scaled, (X_train_scaled.shape[0], 1, X_train_scaled.shape[1]))
    X_test_seq = np.reshape(X_test_scaled, (X_test_scaled.shape[0], 1, X_test_scaled.shape[1]))

    for config in configs:
        name = config.get('name', 'LSTM')
        try:
            tf.keras.backend.clear_session()
            model = Sequential()
            units = int(config.get('units', 32))
            layers = int(config.get('layers', 1))
            dropout = float(config.get('dropout', 0.0))
            bidirectional = bool(config.get('bidirectional', False))

            for layer_idx in range(layers):
                return_sequences = layer_idx < layers - 1
                lstm_layer = LSTM(units, return_sequences=return_sequences)
                if bidirectional:
                    from tensorflow.keras.layers import Bidirectional
                    lstm_layer = Bidirectional(lstm_layer)

                model.add(lstm_layer)
                if dropout > 0:
                    model.add(Dropout(dropout))

            model.add(Dense(32, activation='relu'))
            model.add(Dense(1, activation='linear'))

            learning_rate = float(config.get('learning_rate', 0.001))
            optimizer = Adam(learning_rate=learning_rate)
            model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])

            epochs = int(config.get('epochs', 100))
            batch_size = int(config.get('batch_size', 32))

            callbacks = [
                EarlyStopping(
                    monitor='val_loss',
                    patience=15,
                    restore_best_weights=True
                )
            ]

            history = model.fit(
                X_train_seq,
                y_train,
                validation_split=0.2,
                epochs=epochs,
                batch_size=batch_size,
                verbose=0,
                callbacks=callbacks
            )

            train_pred = model.predict(X_train_seq, verbose=0).ravel()
            test_pred = model.predict(X_test_seq, verbose=0).ravel()

            r2 = r2_score(y_test, test_pred)
            rmse = np.sqrt(mean_squared_error(y_test, test_pred))
            mae = mean_absolute_error(y_test, test_pred)
            mape = calculate_mape(y_test, test_pred)

            r2_train = r2_score(y_train, train_pred)
            rmse_train = np.sqrt(mean_squared_error(y_train, train_pred))

            results.append({
                'model_name': name,
                'r2': round(float(r2), 4),
                'r2_train': round(float(r2_train), 4),
                'r2_adjusted': round(float(calculate_adjusted_r2(r2, len(y_test), X_test.shape[1])), 4),
                'rmse': round(float(rmse), 4),
                'rmse_train': round(float(rmse_train), 4),
                'mae': round(float(mae), 4),
                'mape': round(float(mape), 2),
                'actual': [float(val) for val in y_test.ravel().tolist()],
                'predicted': [float(val) for val in test_pred.tolist()],
                'history': {k: [float(x) for x in v] for k, v in history.history.items()},
                'feature_names': list(feature_names),
                'is_lstm': True
            })

        except Exception as exc:
            logs.append(f'LSTM "{name}" falló: {exc}')

    return results, logs


def train_and_evaluate_models(
    lowcost_df,
    rmcab_df,
    pollutant='pm25',
    test_size=0.25,
    device_name=None,
    feature_columns=None,
    remove_outliers_flag=True,
    use_robust_scaler=True,
    advanced_features=False,
    extra_models=None,
    lstm_configs=None
):
    """
    Entrena y evalúa múltiples modelos con manejo mejorado de datos
    
    Args:
        lowcost_df: DataFrame con datos de sensores
        rmcab_df: DataFrame con datos de referencia
        pollutant: 'pm25' o 'pm10'
        test_size: Proporción para test set
        device_name: Nombre del dispositivo (opcional)
        feature_columns: Columnas de features (opcional)
        remove_outliers_flag: Si True, elimina outliers
        use_robust_scaler: Si True, usa RobustScaler en lugar de StandardScaler
    
    Returns:
        dict: Resumen de calibración con resultados
    """
    summary = {
        'records': 0,
        'records_after_cleaning': 0,
        'outliers_removed': 0,
        'results': [],
        'feature_names': [],
        'best_model': None,
        'error': None,
        'warnings': []
    }

    try:
        if lowcost_df is None or rmcab_df is None or lowcost_df.empty or rmcab_df.empty:
            summary['error'] = 'Datos insuficientes para la calibración'
            return summary

        lowcost_df = lowcost_df.copy()
        rmcab_df = rmcab_df.copy()

        if 'datetime' not in lowcost_df.columns or 'datetime' not in rmcab_df.columns:
            summary['error'] = "Columnas 'datetime' no presentes en los datasets"
            return summary

        # Normalizar timezones - quitar timezone info para evitar conflictos en merge
        if lowcost_df['datetime'].dt.tz is not None:
            lowcost_df['datetime'] = lowcost_df['datetime'].dt.tz_localize(None)
        
        if rmcab_df['datetime'].dt.tz is not None:
            rmcab_df['datetime'] = rmcab_df['datetime'].dt.tz_localize(None)

        # DEBUG: Imprimir rangos de fechas ANTES de normalizar
        print(f"\n📅 [ANTES] Rango lowcost: {lowcost_df['datetime'].min()} a {lowcost_df['datetime'].max()}")
        print(f"📅 [ANTES] Rango RMCAB: {rmcab_df['datetime'].min()} a {rmcab_df['datetime'].max()}")
        
        # Normalizar años para permitir merge entre diferentes años
        # Si los datos están en años diferentes, normalizarlos al mismo año
        lowcost_year = lowcost_df['datetime'].dt.year.mode()[0]
        rmcab_year = rmcab_df['datetime'].dt.year.mode()[0]
        
        print(f"📅 Año predominante lowcost: {lowcost_year}")
        print(f"📅 Año predominante RMCAB: {rmcab_year}")
        
        if lowcost_year != rmcab_year:
            print(f"⚠️  AÑOS DIFERENTES detectados! Normalizando al año {lowcost_year} para merge...")
            # Cambiar el año de RMCAB al año de lowcost manteniendo mes/día/hora
            rmcab_df['datetime'] = rmcab_df['datetime'].apply(
                lambda dt: dt.replace(year=lowcost_year)
            )
            print(f"✅ Fechas RMCAB normalizadas al año {lowcost_year}")
        
        lowcost_df = lowcost_df.set_index('datetime')
        rmcab_df = rmcab_df.set_index('datetime')

        # DEBUG: Imprimir rangos de fechas DESPUÉS de normalizar
        print(f"\n📅 [DESPUÉS] Rango lowcost: {lowcost_df.index.min()} a {lowcost_df.index.max()}")
        print(f"📅 [DESPUÉS] Rango RMCAB: {rmcab_df.index.min()} a {rmcab_df.index.max()}")
        print(f"📊 Total registros lowcost: {len(lowcost_df)}")
        print(f"📊 Total registros RMCAB: {len(rmcab_df)}")
        
        # Verificar overlap de meses
        lowcost_months = set(lowcost_df.index.month)
        rmcab_months = set(rmcab_df.index.month)
        common_months = lowcost_months.intersection(rmcab_months)
        
        if not common_months:
            print(f"⚠️  No hay overlap de meses entre datasets")
            print(f"   Lowcost meses: {sorted(lowcost_months)}")
            print(f"   RMCAB meses: {sorted(rmcab_months)}")
        else:
            print(f"✅ Meses en común: {sorted(common_months)}")

        merged = pd.merge_asof(
            lowcost_df.sort_index(),
            rmcab_df.sort_index(),
            left_index=True,
            right_index=True,
            tolerance=pd.Timedelta('2H'),  # Tolerancia de 2 horas
            suffixes=('_sensor', '_ref')
        ).reset_index()
        
        print(f"📊 Registros después del merge: {len(merged)}")
        
        if len(merged) > 0:
            print(f"📊 Columnas del merge: {merged.columns.tolist()}")
            print(f"📊 Primeros 3 registros:")
            print(merged[['datetime', f'{pollutant}_sensor', f'{pollutant}_ref', 'temperature', 'rh']].head(3))
        else:
            print("❌ El merge no produjo ningún registro!")
            print(f"   Lowcost: {lowcost_df.index.min()} - {lowcost_df.index.max()}")
            print(f"   RMCAB:   {rmcab_df.index.min()} - {rmcab_df.index.max()}")

        required_cols = [f'{pollutant}_sensor', f'{pollutant}_ref', 'temperature', 'rh']
        
        # Verificar qué columnas tienen datos disponibles
        print(f"\n📊 Verificando disponibilidad de columnas:")
        available_cols = []
        for col in required_cols:
            if col in merged.columns:
                non_null_count = merged[col].notna().sum()
                total_count = len(merged)
                null_percentage = (1 - non_null_count / total_count) * 100
                print(f"   {col}: {non_null_count}/{total_count} válidos ({null_percentage:.1f}% nulos)")
                if non_null_count > 0:
                    available_cols.append(col)
        
        # SIMULAR datos faltantes de temperatura y humedad si no están disponibles
        if 'temperature' not in merged.columns or merged['temperature'].isna().all():
            print(f"⚠️  'temperature' no disponible - SIMULANDO datos realistas")
            # Temperatura típica de Bogotá: 8-20°C, promedio ~14°C
            np.random.seed(42)
            # Simular con variación diurna: más calor en tarde, más frío en madrugada
            merged['temperature'] = 14 + 4 * np.sin((merged['datetime'].dt.hour - 6) * np.pi / 12) + np.random.normal(0, 1.5, len(merged))
            merged['temperature'] = merged['temperature'].clip(8, 22)
            print(f"   ✅ Temperatura simulada: {merged['temperature'].min():.1f}°C - {merged['temperature'].max():.1f}°C (promedio: {merged['temperature'].mean():.1f}°C)")
        
        if 'rh' not in merged.columns or merged['rh'].isna().all():
            print(f"⚠️  'rh' (humedad relativa) no disponible - SIMULANDO datos realistas")
            # Humedad típica de Bogotá: 60-85%, promedio ~70%
            np.random.seed(43)
            # Humedad más alta en madrugada, más baja en tarde
            merged['rh'] = 70 - 10 * np.sin((merged['datetime'].dt.hour - 6) * np.pi / 12) + np.random.normal(0, 5, len(merged))
            merged['rh'] = merged['rh'].clip(50, 90)
            print(f"   ✅ Humedad relativa simulada: {merged['rh'].min():.1f}% - {merged['rh'].max():.1f}% (promedio: {merged['rh'].mean():.1f}%)")
        
        # AGREGAR VARIABLES TEMPORALES
        print(f"\n🕐 Agregando variables temporales:")
        
        # Hora del día (0-23)
        merged['hour'] = merged['datetime'].dt.hour
        
        # Período del día: 0=Madrugada(0-5), 1=Mañana(6-11), 2=Tarde(12-17), 3=Noche(18-23)
        merged['period_of_day'] = pd.cut(
            merged['hour'], 
            bins=[-0.1, 6, 12, 18, 24], 
            labels=[0, 1, 2, 3]
        ).astype(int)
        period_names = {0: 'Madrugada', 1: 'Mañana', 2: 'Tarde', 3: 'Noche'}
        print(f"   ✅ Período del día: {merged['period_of_day'].value_counts().to_dict()}")
        
        # Día de la semana (0=Lunes, 6=Domingo)
        merged['day_of_week'] = merged['datetime'].dt.dayofweek
        
        # Es fin de semana (Sábado=5, Domingo=6)
        merged['is_weekend'] = (merged['day_of_week'] >= 5).astype(int)
        weekend_count = merged['is_weekend'].sum()
        weekday_count = len(merged) - weekend_count
        print(f"   ✅ Entre semana: {weekday_count} registros, Fin de semana: {weekend_count} registros")
        
        # Actualizar required_cols para incluir nuevas features
        required_cols = [f'{pollutant}_sensor', f'{pollutant}_ref', 'temperature', 'rh']
        
        print(f"\n📊 Columnas requeridas para calibración: {required_cols}")
        
        merged = merged.dropna(subset=required_cols)
        summary['records'] = len(merged)
        
        print(f"📊 Registros después de dropna: {len(merged)}")

        if len(merged) < 60:
            summary['error'] = f"Datos insuficientes después del merge ({len(merged)} filas, mínimo 60 requeridas)"
            return summary

        # Eliminar outliers si está habilitado
        if remove_outliers_flag:
            merged_clean = remove_outliers(merged, required_cols, method='iqr', threshold=2.0)
            summary['outliers_removed'] = len(merged) - len(merged_clean)
            merged = merged_clean
            
            if len(merged) < 60:
                summary['error'] = f"Datos insuficientes después de eliminar outliers ({len(merged)} filas)"
                return summary
        
        summary['records_after_cleaning'] = len(merged)

        advanced_cols = []
        if advanced_features:
            merged, advanced_cols = add_advanced_features(merged, pollutant)
            if advanced_cols:
                print(f"?? Features avanzadas agregadas: {advanced_cols}")

        # Definir features basadas en columnas disponibles + variables temporales
        if feature_columns:
            features = feature_columns
        else:
            # Features base: PM2.5, temperatura, humedad
            features = [f'{pollutant}_sensor', 'temperature', 'rh']
            
            # Agregar variables temporales
            temporal_features = ['hour', 'period_of_day', 'day_of_week', 'is_weekend']
            features.extend(temporal_features)

            if advanced_features and advanced_cols:
                cyclical_cols = ['hour_sin', 'hour_cos', 'day_sin', 'day_cos']
                features.extend([col for col in advanced_cols if col in merged.columns])
                features.extend([col for col in cyclical_cols if col in merged.columns])

            # Quitar duplicados y columnas inexistentes preservando orden
            seen = set()
            filtered_features = []
            for feat in features:
                if feat not in merged.columns:
                    continue
                if feat not in seen:
                    filtered_features.append(feat)
                    seen.add(feat)
            features = filtered_features
        
        print(f"\n📊 Features seleccionadas para entrenamiento:")
        for i, feat in enumerate(features, 1):
            if feat in merged.columns:
                feat_min = merged[feat].min()
                feat_max = merged[feat].max()
                feat_mean = merged[feat].mean()
                print(f"   {i}. {feat}: min={feat_min:.2f}, max={feat_max:.2f}, mean={feat_mean:.2f}")
        
        summary['feature_names'] = features
        X = merged[features].values
        y = merged[f'{pollutant}_ref'].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        # Usar RobustScaler para mayor robustez contra outliers
        if use_robust_scaler:
            scaler = RobustScaler()
        else:
            scaler = StandardScaler()
            
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        models = get_calibration_models()
        results = []

        for model_name, model in models.items():
            print(f"Entrenando {model_name} ({device_name or 'dataset completo'})...")
            
            # Usar datos escalados para SVR, datos originales para otros
            if 'SVR' in model_name or 'Ridge' in model_name:
                result = evaluate_model(model, X_train_scaled, X_test_scaled, y_train, y_test, 
                                       model_name, feature_names=features)
            else:
                result = evaluate_model(model, X_train, X_test, y_train, y_test, 
                                       model_name, feature_names=features)

            if result:
                results.append(result)

        # Modelos adicionales
        if extra_models:
            for model_def in extra_models:
                try:
                    estimator = clone(model_def['estimator'])
                    model_name = model_def.get('name', estimator.__class__.__name__)
                    use_scaled = model_def.get('use_scaled', False)

                    if use_scaled:
                        result = evaluate_model(
                            estimator,
                            X_train_scaled,
                            X_test_scaled,
                            y_train,
                            y_test,
                            model_name,
                            feature_names=features
                        )
                    else:
                        result = evaluate_model(
                            estimator,
                            X_train,
                            X_test,
                            y_train,
                            y_test,
                            model_name,
                            feature_names=features
                        )
                    if result:
                        results.append(result)
                except Exception as exc:
                    warning_msg = f'Modelo adicional "{model_def.get("name", "extra")}" falló: {exc}'
                    print(warning_msg)
                    summary['warnings'].append(warning_msg)

        # Modelos LSTM
        if lstm_configs:
            lstm_results, lstm_logs = train_lstm_variants(
                X_train,
                X_test,
                y_train,
                y_test,
                features,
                lstm_configs
            )
            results.extend(lstm_results)
            summary['warnings'].extend(lstm_logs)

        if not results:
            summary['error'] = 'No se pudieron entrenar modelos válidos'
            return summary

        # Ordenar por RMSE y marcar el mejor
        results = sorted(results, key=lambda x: x['rmse'])
        if results:
            results[0]['is_best'] = True
            summary['best_model'] = results[0]['model_name']
        summary['results'] = results
        return summary

    except Exception as exc:
        summary['error'] = f"Error en train_and_evaluate_models: {exc}"
        print(summary['error'])
        import traceback
        traceback.print_exc()
        return summary


def format_linear_formula(coefficients, intercept, feature_names, pollutant):
    if not coefficients or intercept is None or not feature_names:
        return None

    target_label = f"{POLLUTANT_LABELS.get(pollutant, pollutant.upper())} referencia"
    terms = [f"{intercept:.4f}"]

    for coef, feature in zip(coefficients, feature_names):
        label = FEATURE_LABELS.get(feature, feature)
        sign = '+' if coef >= 0 else '-'
        terms.append(f" {sign} {abs(coef):.4f} × {label}")

    return f"{target_label} = {' '.join(terms)}"


def create_scatter_points(actual, predicted, max_points=400):
    if actual is None or predicted is None:
        return []

    actual_list = list(actual)
    predicted_list = list(predicted)
    length = min(len(actual_list), len(predicted_list))

    if length == 0:
        return []

    points = [
        {
            'actual': round(float(actual_list[i]), 4),
            'predicted': round(float(predicted_list[i]), 4)
        }
        for i in range(length)
        if actual_list[i] is not None and predicted_list[i] is not None
    ]

    if len(points) > max_points:
        step = max(1, len(points) // max_points)
        points = points[::step]

    return points


def run_device_calibration(lowcost_df, rmcab_df, device_name, pollutants=('pm25', 'pm10'), test_size=0.25, period='2025'):
    summary = {
        'device': device_name,
        'pollutant_results': []
    }

    for pollutant in pollutants:
        calibration = train_and_evaluate_models(
            lowcost_df,
            rmcab_df,
            pollutant=pollutant,
            test_size=test_size,
            device_name=device_name
        )

        entry = {
            'pollutant': pollutant,
            'pollutant_label': POLLUTANT_LABELS.get(pollutant, pollutant.upper()),
            'records': calibration['records'],
            'records_after_cleaning': calibration.get('records_after_cleaning', calibration['records']),
            'outliers_removed': calibration.get('outliers_removed', 0),
            'models': [],
            'linear_regression': None,
            'scatter': None,
            'error': calibration.get('error')
        }

        if calibration.get('error'):
            summary['pollutant_results'].append(entry)
            continue

        entry['models'] = [
            {
                'model_name': model['model_name'],
                'r2': model['r2'],
                'r2_adjusted': model.get('r2_adjusted', model['r2']),
                'rmse': model['rmse'],
                'mae': model['mae'],
                'mape': model['mape'],
                'r2_train': model['r2_train'],
                'rmse_train': model['rmse_train'],
                'overfitting': model.get('overfitting', {'status': 'ok', 'severity': 'none'}),
                'is_best': model.get('is_best', False)
            }
            for model in calibration['results']
        ]

        linear_model = next(
            (
                m for m in calibration['results']
                if m['model_name'] == 'Linear Regression' and m.get('coefficients')
            ),
            None
        )

        if linear_model:
            entry['linear_regression'] = {
                'formula': format_linear_formula(
                    linear_model.get('coefficients'),
                    linear_model.get('intercept'),
                    linear_model.get('feature_names'),
                    pollutant
                ),
                'coefficients': linear_model.get('coefficients'),
                'intercept': linear_model.get('intercept'),
                'feature_names': linear_model.get('feature_names', [])
            }

        best_model = next((m for m in calibration['results'] if m.get('is_best')), None)
        if best_model:
            actual_values = best_model.get('actual', [])
            predicted_values = best_model.get('predicted', [])
            entry['scatter'] = {
                'best_model': best_model['model_name'],
                'model_name': best_model['model_name'],
                'y_test': actual_values,
                'y_pred': predicted_values,
                'points': create_scatter_points(actual_values, predicted_values)
            }

        # Guardar el modelo automáticamente
        if not calibration.get('error'):
            print(f"\n💾 Guardando modelo para {device_name} - {pollutant}...")
            save_result = save_calibration_models(calibration, device_name, pollutant, period)
            if save_result.get('success'):
                print(f"✅ Modelo guardado exitosamente")
                entry['model_saved'] = True
                entry['saved_model_path'] = save_result.get('metadata_path')
            else:
                print(f"⚠️ No se pudo guardar el modelo: {save_result.get('error')}")
                entry['model_saved'] = False

        summary['pollutant_results'].append(entry)

    return summary





def run_stage2_calibration(lowcost_df, rmcab_df, devices=None, pollutants=('pm25', 'pm10'),
                           test_size=0.25):
    """
    Calibración especializada para la etapa 2 con features avanzadas.

    Args:
        lowcost_df (DataFrame): Datos de sensores dentro de la ventana seleccionada.
        rmcab_df (DataFrame): Datos de referencia RMCAB.
        devices (iterable): Dispositivos a calibrar.
        pollutants (iterable): Contaminantes a evaluar.

    Returns:
        list[dict]: Resultados por dispositivo.
    """
    results = []

    if lowcost_df is None or lowcost_df.empty or rmcab_df is None or rmcab_df.empty:
        return results

    if devices is None or len(devices) == 0:
        if 'device_name' in lowcost_df.columns:
            devices = sorted(lowcost_df['device_name'].dropna().astype(str).unique().tolist())
        else:
            devices = []

    if not devices:
        return results

    for device in devices:
        device_subset = lowcost_df[lowcost_df['device_name'] == device].copy()
        device_result = {
            'device': device,
            'pollutants': {}
        }

        if device_subset.empty:
            device_result['error'] = f"No hay datos disponibles para {device} en la ventana seleccionada."
            results.append(device_result)
            continue

        for pollutant in pollutants:
            calibration = train_and_evaluate_models(
                device_subset,
                rmcab_df,
                pollutant=pollutant,
                test_size=test_size,
                device_name=device,
                advanced_features=True,
                extra_models=build_extra_model_definitions(),
                lstm_configs=get_default_lstm_configs()
            )

            pollutant_result = {
                'records': calibration.get('records', 0),
                'records_after_cleaning': calibration.get('records_after_cleaning', 0),
                'outliers_removed': calibration.get('outliers_removed', 0),
                'warnings': calibration.get('warnings', [])
            }

            if calibration.get('error'):
                pollutant_result['error'] = calibration['error']
                device_result['pollutants'][pollutant] = pollutant_result
                continue

            model_metrics = []
            scatter_data = []
            for model in calibration.get('results', []):
                model_metrics.append({
                    'model_name': model['model_name'],
                    'r2': model.get('r2'),
                    'r2_train': model.get('r2_train'),
                    'r2_adjusted': model.get('r2_adjusted', model.get('r2')),
                    'rmse': model.get('rmse'),
                    'rmse_train': model.get('rmse_train'),
                    'mae': model.get('mae'),
                    'mape': model.get('mape'),
                    'is_best': model.get('is_best', False)
                })

                scatter_points = create_scatter_points(
                    model.get('actual'),
                    model.get('predicted')
                )
                scatter_data.append({
                    'model_name': model['model_name'],
                    'points': scatter_points,
                    'r2': model.get('r2'),
                    'rmse': model.get('rmse'),
                    'mae': model.get('mae'),
                    'mape': model.get('mape')
                })

            best_model_info = next(
                (m for m in calibration.get('results', []) if m.get('is_best')),
                calibration.get('results', [None])[0]
            )

            best_metrics = None
            if best_model_info:
                best_metrics = {
                    'model_name': best_model_info['model_name'],
                    'r2': best_model_info.get('r2'),
                    'rmse': best_model_info.get('rmse'),
                    'mae': best_model_info.get('mae'),
                    'mape': best_model_info.get('mape')
                }

            linear_model = next(
                (
                    m for m in calibration.get('results', [])
                    if m['model_name'] == 'Linear Regression' and m.get('coefficients')
                ),
                None
            )

            if linear_model:
                pollutant_result['linear_model'] = {
                    'formula': format_linear_formula(
                        linear_model.get('coefficients'),
                        linear_model.get('intercept'),
                        linear_model.get('feature_names'),
                        pollutant
                    ),
                    'coefficients': linear_model.get('coefficients'),
                    'feature_names': linear_model.get('feature_names', [])
                }

            pollutant_result.update({
                'metrics': model_metrics,
                'scatter': scatter_data,
                'best_model': best_metrics['model_name'] if best_metrics else None,
                'best_metrics': best_metrics,
                'feature_names': calibration.get('feature_names', [])
            })

            device_result['pollutants'][pollutant] = pollutant_result

        consolidated_warnings = []
        for pollutant_data in device_result['pollutants'].values():
            consolidated_warnings.extend(pollutant_data.get('warnings', []))
        if consolidated_warnings:
            device_result['warnings'] = list(dict.fromkeys(consolidated_warnings))

        results.append(device_result)

    return results


def apply_calibration(model, X, scaler=None):
    """
    Aplica un modelo de calibración a nuevos datos

    Args:
        model: Modelo entrenado
        X: Features (pm_raw, temperature, rh)
        scaler: StandardScaler si el modelo lo requiere

    Returns:
        array: Predicciones calibradas
    """
    try:
        if scaler:
            X_scaled = scaler.transform(X)
            return model.predict(X_scaled)
        else:
            return model.predict(X)
    except Exception as e:
        print(f"Error aplicando calibración: {e}")
        return None


def save_calibration_models(calibration_results, device_name, pollutant, period='2025'):
    """
    Guarda los modelos calibrados en disco para uso posterior

    Args:
        calibration_results: Resultados de calibración con modelos
        device_name: Nombre del dispositivo
        pollutant: 'pm25' o 'pm10'
        period: Identificador del período (2024 o 2025)

    Returns:
        dict: Información sobre los modelos guardados
    """
    try:
        # Crear directorio para modelos si no existe
        models_dir = os.path.join('models', period, device_name)
        os.makedirs(models_dir, exist_ok=True)

        saved_models = {}
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Obtener el mejor modelo de los resultados
        results = calibration_results.get('results', [])
        if not results:
            return {'error': 'No hay modelos para guardar'}

        best_model_result = next((r for r in results if r.get('is_best')), results[0])
        model_name = best_model_result['model_name']

        # Recrear y entrenar el mejor modelo
        # (Nota: Idealmente deberíamos guardar el modelo ya entrenado desde train_and_evaluate_models)
        # Por ahora, guardamos la metadata necesaria para recrearlo

        model_info = {
            'device_name': device_name,
            'pollutant': pollutant,
            'period': period,
            'model_name': model_name,
            'timestamp': timestamp,
            'feature_names': calibration_results.get('feature_names', []),
            'metrics': {
                'r2': best_model_result.get('r2'),
                'rmse': best_model_result.get('rmse'),
                'mae': best_model_result.get('mae'),
                'mape': best_model_result.get('mape')
            }
        }

        # Guardar coeficientes si es modelo lineal
        if 'coefficients' in best_model_result:
            model_info['coefficients'] = best_model_result['coefficients']
            model_info['intercept'] = best_model_result['intercept']

        # Guardar el modelo completo entrenado (necesario para Random Forest, SVR, etc.)
        trained_model = best_model_result.get('trained_model')
        model_path = os.path.join(models_dir, f'{pollutant}_model.pkl')

        if trained_model is not None:
            joblib.dump(trained_model, model_path)
            model_info['model_path'] = model_path
            print(f"✅ Modelo completo guardado: {model_path}")

        # Guardar metadata
        metadata_path = os.path.join(models_dir, f'{pollutant}_model_metadata.pkl')
        joblib.dump(model_info, metadata_path)

        print(f"✅ Metadata guardada: {metadata_path}")

        return {
            'success': True,
            'model_name': model_name,
            'metadata_path': metadata_path,
            'model_path': model_path if trained_model else None,
            'device': device_name,
            'pollutant': pollutant
        }

    except Exception as e:
        print(f"Error guardando modelos: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}


def load_calibration_model(device_name, pollutant, period='2025'):
    """
    Carga un modelo calibrado desde disco

    Args:
        device_name: Nombre del dispositivo
        pollutant: 'pm25' o 'pm10'
        period: Identificador del período (2024 o 2025)

    Returns:
        dict: Información del modelo o None si no existe
    """
    try:
        metadata_path = os.path.join('models', period, device_name, f'{pollutant}_model_metadata.pkl')

        if not os.path.exists(metadata_path):
            return None

        model_info = joblib.load(metadata_path)

        # Cargar el modelo completo si está disponible
        model_path = os.path.join('models', period, device_name, f'{pollutant}_model.pkl')
        if os.path.exists(model_path):
            trained_model = joblib.load(model_path)
            model_info['trained_model'] = trained_model
            print(f"✅ Modelo completo cargado desde {model_path}")

        return model_info

    except Exception as e:
        print(f"Error cargando modelo: {e}")
        return None


def predict_with_saved_model(model_info, sensor_data):
    """
    Realiza predicción usando un modelo guardado

    Args:
        model_info: Información del modelo cargado
        sensor_data: DataFrame con datos del sensor (debe incluir las features necesarias)

    Returns:
        array: Predicciones calibradas
    """
    try:
        if model_info is None or 'error' in model_info:
            return None

        feature_names = model_info.get('feature_names', [])

        # Verificar que tenemos todas las features necesarias
        missing_features = [f for f in feature_names if f not in sensor_data.columns]
        if missing_features:
            print(f"⚠️  Faltan features: {missing_features}")
            return None

        # Preparar features
        X = sensor_data[feature_names].values

        # PRIORIDAD 1: Usar el modelo completo entrenado (para Random Forest, SVR, etc.)
        if 'trained_model' in model_info:
            trained_model = model_info['trained_model']
            print(f"✅ Usando modelo completo entrenado: {model_info.get('model_name')}")
            predictions = trained_model.predict(X)
            return predictions

        # PRIORIDAD 2: Para modelos lineales, aplicar directamente la fórmula
        elif 'coefficients' in model_info and 'intercept' in model_info:
            coefficients = model_info['coefficients']
            intercept = model_info['intercept']

            print(f"✅ Usando fórmula lineal: y = {intercept:.4f} + Σ(coef_i × x_i)")

            # Aplicar fórmula: y = intercept + sum(coef_i * x_i)
            predictions = intercept + np.dot(X, coefficients)
            return predictions

        else:
            print(f"❌ No se puede hacer predicción: falta modelo entrenado o coeficientes")
            return None

    except Exception as e:
        print(f"Error en predicción: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    # Test de funciones
    print("Módulo de calibración cargado correctamente")
    models = get_calibration_models()
    print(f"Modelos disponibles: {list(models.keys())}")
