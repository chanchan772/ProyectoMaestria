"""
Módulo para calibración de sensores usando Machine Learning
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, KFold
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler, RobustScaler
import warnings
warnings.filterwarnings('ignore')


FEATURE_LABELS = {
    'pm25_sensor': 'PM2.5 sensor',
    'pm10_sensor': 'PM10 sensor',
    'temperature': 'Temperatura (°C)',
    'rh': 'Humedad relativa (%)'
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


def train_and_evaluate_models(lowcost_df, rmcab_df, pollutant='pm25', test_size=0.25, device_name=None, 
                              feature_columns=None, remove_outliers_flag=True, use_robust_scaler=True):
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
        'error': None
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

        lowcost_df = lowcost_df.set_index('datetime')
        rmcab_df = rmcab_df.set_index('datetime')

        merged = pd.merge_asof(
            lowcost_df.sort_index(),
            rmcab_df.sort_index(),
            left_index=True,
            right_index=True,
            tolerance=pd.Timedelta('1H'),
            suffixes=('_sensor', '_ref')
        ).reset_index()

        required_cols = [f'{pollutant}_sensor', f'{pollutant}_ref', 'temperature', 'rh']
        merged = merged.dropna(subset=required_cols)
        summary['records'] = len(merged)

        if len(merged) < 60:
            summary['error'] = f"Datos insuficientes después del merge ({len(merged)} filas)"
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

        features = feature_columns or [f'{pollutant}_sensor', 'temperature', 'rh']
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

        if not results:
            summary['error'] = 'No se pudieron entrenar modelos válidos'
            return summary

        # Ordenar por RMSE y marcar el mejor
        results = sorted(results, key=lambda x: x['rmse'])
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


def run_device_calibration(lowcost_df, rmcab_df, device_name, pollutants=('pm25', 'pm10'), test_size=0.25):
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
                'rmse': model['rmse'],
                'mae': model['mae'],
                'mape': model['mape'],
                'r2_train': model['r2_train'],
                'rmse_train': model['rmse_train'],
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
            entry['scatter'] = {
                'model_name': best_model['model_name'],
                'points': create_scatter_points(
                    best_model.get('actual'),
                    best_model.get('predicted')
                )
            }

        summary['pollutant_results'].append(entry)

    return summary





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


if __name__ == '__main__':
    # Test de funciones
    print("Módulo de calibración cargado correctamente")
    models = get_calibration_models()
    print(f"Modelos disponibles: {list(models.keys())}")
