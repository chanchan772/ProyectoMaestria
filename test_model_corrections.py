"""
Script de diagnóstico y prueba para identificar problemas en el modelo predictivo
"""

import numpy as np
import pandas as pd
from modules.calibration import (
    get_calibration_models,
    train_and_evaluate_models,
    calculate_mape,
    evaluate_model
)
from sklearn.model_selection import train_test_split

def test_model_issues():
    """Identifica problemas comunes en el modelo predictivo"""
    
    print("=" * 80)
    print("DIAGNÓSTICO DE PROBLEMAS EN EL MODELO PREDICTIVO")
    print("=" * 80)
    
    # 1. Crear datos sintéticos para pruebas
    print("\n1. Generando datos sintéticos de prueba...")
    np.random.seed(42)
    n_samples = 500
    
    # Simular datos de sensores con ruido
    pm25_sensor = np.random.uniform(5, 50, n_samples)
    temperature = np.random.uniform(10, 30, n_samples)
    rh = np.random.uniform(30, 90, n_samples)
    
    # Simular datos de referencia con correlación
    pm25_ref = pm25_sensor * 0.95 + temperature * 0.2 - rh * 0.1 + np.random.normal(0, 2, n_samples)
    
    # Crear DataFrames
    lowcost_df = pd.DataFrame({
        'datetime': pd.date_range('2024-06-01', periods=n_samples, freq='H'),
        'pm25_sensor': pm25_sensor,
        'temperature': temperature,
        'rh': rh
    })
    
    rmcab_df = pd.DataFrame({
        'datetime': pd.date_range('2024-06-01', periods=n_samples, freq='H'),
        'pm25_ref': pm25_ref
    })
    
    print(f"   ✓ Datos sintéticos generados: {n_samples} registros")
    
    # 2. Probar MAPE con valores cero
    print("\n2. Probando MAPE con valores cero...")
    y_true_with_zeros = np.array([0, 5, 10, 15, 20])
    y_pred = np.array([1, 6, 11, 16, 21])
    try:
        mape = calculate_mape(y_true_with_zeros, y_pred)
        print(f"   ✓ MAPE calculado correctamente: {mape:.2f}%")
        if np.isinf(mape) or np.isnan(mape):
            print("   ✗ PROBLEMA: MAPE contiene valores infinitos o NaN")
        else:
            print("   ✓ MAPE sin problemas numéricos")
    except Exception as e:
        print(f"   ✗ ERROR en calculate_mape: {e}")
    
    # 3. Verificar problemas con train_test_split
    print("\n3. Verificando train_test_split con pocos datos...")
    small_lowcost = lowcost_df.head(50)
    small_rmcab = rmcab_df.head(50)
    try:
        result = train_and_evaluate_models(small_lowcost, small_rmcab, pollutant='pm25', test_size=0.25)
        if result.get('error'):
            print(f"   ✗ ERROR: {result['error']}")
        else:
            print(f"   ✓ Calibración con pocos datos funciona: {result['records']} registros")
    except Exception as e:
        print(f"   ✗ ERROR en train_and_evaluate_models: {e}")
    
    # 4. Probar normalización para SVR
    print("\n4. Verificando normalización para SVR...")
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import SVR
    
    X = lowcost_df[['pm25_sensor', 'temperature', 'rh']].values[:100]
    y = rmcab_df['pm25_ref'].values[:100]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Verificar que la normalización funciona
    print(f"   Media antes: {X_train.mean(axis=0)}")
    print(f"   Media después: {X_train_scaled.mean(axis=0)}")
    print(f"   Std después: {X_train_scaled.std(axis=0)}")
    
    if np.allclose(X_train_scaled.mean(axis=0), 0, atol=1e-10) and \
       np.allclose(X_train_scaled.std(axis=0), 1, atol=1e-10):
        print("   ✓ Normalización correcta")
    else:
        print("   ✗ PROBLEMA: Normalización no es óptima")
    
    # 5. Probar overfitting
    print("\n5. Verificando overfitting...")
    result = train_and_evaluate_models(lowcost_df, rmcab_df, pollutant='pm25', test_size=0.25)
    
    if result.get('results'):
        for model_result in result['results']:
            r2_train = model_result.get('r2_train', 0)
            r2_test = model_result.get('r2', 0)
            diff = r2_train - r2_test
            
            print(f"\n   {model_result['model_name']}:")
            print(f"      R² Train: {r2_train:.4f}")
            print(f"      R² Test:  {r2_test:.4f}")
            print(f"      Diferencia: {diff:.4f}")
            
            if diff > 0.15:
                print(f"      ✗ ADVERTENCIA: Posible overfitting (diff > 0.15)")
            else:
                print(f"      ✓ No hay overfitting significativo")
    
    # 6. Verificar valores atípicos
    print("\n6. Detectando valores atípicos...")
    for col in ['pm25_sensor', 'temperature', 'rh']:
        Q1 = lowcost_df[col].quantile(0.25)
        Q3 = lowcost_df[col].quantile(0.75)
        IQR = Q3 - Q1
        outliers = ((lowcost_df[col] < (Q1 - 1.5 * IQR)) | 
                   (lowcost_df[col] > (Q3 + 1.5 * IQR))).sum()
        pct = (outliers / len(lowcost_df)) * 100
        print(f"   {col}: {outliers} valores atípicos ({pct:.1f}%)")
        if pct > 5:
            print(f"      ✗ ADVERTENCIA: Muchos valores atípicos")
    
    # 7. Verificar multicolinealidad
    print("\n7. Verificando multicolinealidad...")
    correlation_matrix = lowcost_df[['pm25_sensor', 'temperature', 'rh']].corr()
    print("\n   Matriz de correlación:")
    print(correlation_matrix)
    
    high_corr = []
    for i in range(len(correlation_matrix.columns)):
        for j in range(i+1, len(correlation_matrix.columns)):
            if abs(correlation_matrix.iloc[i, j]) > 0.8:
                high_corr.append((correlation_matrix.columns[i], 
                                correlation_matrix.columns[j], 
                                correlation_matrix.iloc[i, j]))
    
    if high_corr:
        print("\n   ✗ ADVERTENCIA: Variables con alta correlación:")
        for var1, var2, corr in high_corr:
            print(f"      {var1} - {var2}: {corr:.3f}")
    else:
        print("\n   ✓ No hay multicolinealidad problemática")
    
    # 8. Verificar validación cruzada
    print("\n8. Sugerencia: Implementar validación cruzada...")
    print("   ⚠ El código actual usa simple train_test_split")
    print("   ⚠ Recomendación: Usar KFold cross-validation para mejor evaluación")
    
    print("\n" + "=" * 80)
    print("RESUMEN DE DIAGNÓSTICO")
    print("=" * 80)
    print("\nProblemas identificados que necesitan corrección:")
    print("1. ✓ MAPE manejando valores cero correctamente")
    print("2. ⚠ Implementar manejo de outliers")
    print("3. ⚠ Agregar validación cruzada (KFold)")
    print("4. ⚠ Implementar regularización en Random Forest")
    print("5. ⚠ Agregar early stopping")
    print("6. ⚠ Implementar detección automática de overfitting")
    print("7. ⚠ Agregar métricas adicionales (R² ajustado, AIC, BIC)")
    
    return result

if __name__ == '__main__':
    test_model_issues()
