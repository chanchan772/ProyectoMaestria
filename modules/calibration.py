"""
Módulo para calibración de sensores usando Machine Learning
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


def get_calibration_models():
    """
    Retorna diccionario con modelos de calibración

    Returns:
        dict: Diccionario con nombre: modelo
    """
    models = {
        'Linear Regression': LinearRegression(),
        'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        'SVR (Linear)': SVR(kernel='linear', C=1.0),
        'SVR (RBF)': SVR(kernel='rbf', C=1.0, gamma='scale'),
        'SVR (Polynomial)': SVR(kernel='poly', C=1.0, degree=2, gamma='scale')
    }
    return models


def calculate_mape(y_true, y_pred):
    """
    Calcula Mean Absolute Percentage Error

    Args:
        y_true: Valores reales
        y_pred: Valores predichos

    Returns:
        float: MAPE en porcentaje
    """
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    mask = y_true != 0  # Evitar división por cero
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


def evaluate_model(model, X_train, X_test, y_train, y_test, model_name):
    """
    Entrena y evalúa un modelo

    Args:
        model: Modelo de sklearn
        X_train, X_test: Features de entrenamiento y prueba
        y_train, y_test: Target de entrenamiento y prueba
        model_name: Nombre del modelo

    Returns:
        dict: Diccionario con métricas
    """
    try:
        # Entrenar modelo
        model.fit(X_train, y_train)

        # Predicciones
        y_pred_train = model.predict(X_train)
        y_pred_test = model.predict(X_test)

        # Métricas en conjunto de prueba
        r2 = r2_score(y_test, y_pred_test)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        mae = mean_absolute_error(y_test, y_pred_test)
        mape = calculate_mape(y_test, y_pred_test)

        # Métricas en conjunto de entrenamiento (para detectar overfitting)
        r2_train = r2_score(y_train, y_pred_train)
        rmse_train = np.sqrt(mean_squared_error(y_train, y_pred_train))

        results = {
            'model_name': model_name,
            'r2': round(r2, 4),
            'r2_train': round(r2_train, 4),
            'rmse': round(rmse, 4),
            'rmse_train': round(rmse_train, 4),
            'mae': round(mae, 4),
            'mape': round(mape, 2),
            'model': model,
            'predictions': y_pred_test
        }

        return results

    except Exception as e:
        print(f"Error evaluando modelo {model_name}: {e}")
        return None


def train_and_evaluate_models(lowcost_df, rmcab_df, pollutant='pm25', test_size=0.25):
    """
    Entrena y evalúa múltiples modelos de calibración

    Args:
        lowcost_df: DataFrame de sensores de bajo costo
        rmcab_df: DataFrame de RMCAB (datos de referencia)
        pollutant: Contaminante a calibrar ('pm25' o 'pm10')
        test_size: Proporción del conjunto de prueba

    Returns:
        list: Lista de diccionarios con resultados de cada modelo
    """
    try:
        # Validar DataFrames
        if lowcost_df is None or rmcab_df is None:
            print("Error: DataFrames vacíos")
            return []

        if lowcost_df.empty or rmcab_df.empty:
            print("Error: DataFrames sin datos")
            return []

        # Combinar datasets (merge por timestamp)
        lowcost_df = lowcost_df.copy()
        rmcab_df = rmcab_df.copy()

        # Asegurar columna datetime
        if 'datetime' not in lowcost_df.columns:
            print("Error: columna 'datetime' no encontrada en lowcost_df")
            return []

        if 'datetime' not in rmcab_df.columns:
            print("Error: columna 'datetime' no encontrada en rmcab_df")
            return []

        # Merge por datetime más cercano
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

        # Filtrar filas completas
        required_cols = [f'{pollutant}_sensor', f'{pollutant}_ref', 'temperature', 'rh']
        merged = merged.dropna(subset=required_cols)

        if len(merged) < 100:
            print(f"Error: Datos insuficientes después del merge ({len(merged)} filas)")
            return []

        # Preparar features y target
        X = merged[[f'{pollutant}_sensor', 'temperature', 'rh']].values
        y = merged[f'{pollutant}_ref'].values

        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        # Normalizar features (importante para SVR)
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Obtener modelos
        models = get_calibration_models()

        # Entrenar y evaluar cada modelo
        results = []

        for model_name, model in models.items():
            print(f"Entrenando {model_name}...")

            # Usar datos escalados para SVR, sin escalar para los demás
            if 'SVR' in model_name:
                result = evaluate_model(
                    model, X_train_scaled, X_test_scaled, y_train, y_test, model_name
                )
            else:
                result = evaluate_model(
                    model, X_train, X_test, y_train, y_test, model_name
                )

            if result:
                results.append(result)

        # Ordenar por RMSE (menor es mejor)
        results = sorted(results, key=lambda x: x['rmse'])

        # Identificar mejor modelo
        if results:
            best = results[0]
            print(f"\n✅ Mejor modelo: {best['model_name']}")
            print(f"   R²: {best['r2']:.4f}")
            print(f"   RMSE: {best['rmse']:.4f} µg/m³")
            print(f"   MAE: {best['mae']:.4f} µg/m³")
            print(f"   MAPE: {best['mape']:.2f}%")

        return results

    except Exception as e:
        print(f"Error en train_and_evaluate_models: {e}")
        import traceback
        traceback.print_exc()
        return []


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
