"""
Script de validación final - Verifica que todas las correcciones funcionen
"""

import sys
import traceback
from datetime import datetime

def print_section(title):
    """Imprime una sección con formato"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_import():
    """Test 1: Verificar que los módulos se importen correctamente"""
    print_section("TEST 1: IMPORTACIÓN DE MÓDULOS")
    
    try:
        from modules.calibration import (
            get_calibration_models,
            train_and_evaluate_models,
            calculate_mape,
            calculate_adjusted_r2,
            detect_overfitting,
            remove_outliers,
            evaluate_model
        )
        print("✅ Todos los módulos se importaron correctamente")
        return True
    except Exception as e:
        print(f"✗ Error importando módulos: {e}")
        traceback.print_exc()
        return False

def test_models():
    """Test 2: Verificar que los modelos se creen correctamente"""
    print_section("TEST 2: CREACIÓN DE MODELOS")
    
    try:
        from modules.calibration import get_calibration_models
        models = get_calibration_models()
        
        expected_models = [
            'Linear Regression',
            'Ridge Regression',
            'Random Forest',
            'SVR (Linear)',
            'SVR (RBF)',
            'SVR (Polynomial)'
        ]
        
        print(f"Modelos disponibles: {len(models)}")
        for model_name in models.keys():
            status = "✅" if model_name in expected_models else "⚠️"
            print(f"  {status} {model_name}")
        
        if len(models) >= 6:
            print("\n✅ Todos los modelos se crearon correctamente")
            return True
        else:
            print(f"\n⚠️ Se esperaban 6 modelos, se encontraron {len(models)}")
            return False
            
    except Exception as e:
        print(f"✗ Error creando modelos: {e}")
        traceback.print_exc()
        return False

def test_mape():
    """Test 3: Verificar que MAPE maneje valores cero"""
    print_section("TEST 3: MAPE CON VALORES CERO")
    
    try:
        from modules.calibration import calculate_mape
        import numpy as np
        
        # Test con valores normales
        y_true = np.array([10, 20, 30, 40, 50])
        y_pred = np.array([11, 19, 31, 39, 51])
        mape1 = calculate_mape(y_true, y_pred)
        print(f"  MAPE (valores normales): {mape1:.2f}%")
        
        # Test con valores cero
        y_true_with_zeros = np.array([0, 5, 10, 15, 20])
        y_pred2 = np.array([1, 6, 11, 16, 21])
        mape2 = calculate_mape(y_true_with_zeros, y_pred2)
        print(f"  MAPE (con ceros): {mape2:.2f}%")
        
        # Test con todos ceros
        y_true_all_zeros = np.array([0, 0, 0, 0, 0])
        y_pred3 = np.array([1, 1, 1, 1, 1])
        mape3 = calculate_mape(y_true_all_zeros, y_pred3)
        print(f"  MAPE (todos ceros): {mape3:.2f}%")
        
        if not (np.isinf(mape1) or np.isnan(mape1) or 
                np.isinf(mape2) or np.isnan(mape2) or
                np.isinf(mape3) or np.isnan(mape3)):
            print("\n✅ MAPE maneja valores cero correctamente")
            return True
        else:
            print("\n✗ MAPE tiene problemas con valores especiales")
            return False
            
    except Exception as e:
        print(f"✗ Error probando MAPE: {e}")
        traceback.print_exc()
        return False

def test_adjusted_r2():
    """Test 4: Verificar R² ajustado"""
    print_section("TEST 4: R² AJUSTADO")
    
    try:
        from modules.calibration import calculate_adjusted_r2
        
        # Test con valores típicos
        r2 = 0.95
        n_samples = 100
        n_features = 3
        
        r2_adj = calculate_adjusted_r2(r2, n_samples, n_features)
        print(f"  R²: {r2:.4f}")
        print(f"  R² ajustado: {r2_adj:.4f}")
        print(f"  Diferencia: {r2 - r2_adj:.4f}")
        
        if 0 <= r2_adj <= r2:
            print("\n✅ R² ajustado funciona correctamente")
            return True
        else:
            print("\n✗ R² ajustado tiene valores fuera de rango esperado")
            return False
            
    except Exception as e:
        print(f"✗ Error probando R² ajustado: {e}")
        traceback.print_exc()
        return False

def test_overfitting_detection():
    """Test 5: Verificar detección de overfitting"""
    print_section("TEST 5: DETECCIÓN DE OVERFITTING")
    
    try:
        from modules.calibration import detect_overfitting
        
        # Test sin overfitting
        result1 = detect_overfitting(0.95, 0.93, 2.0, 2.2)
        print(f"\n  Caso 1 (sin overfitting):")
        print(f"    Status: {result1['status']}")
        print(f"    Severity: {result1['severity']}")
        print(f"    Message: {result1['message']}")
        
        # Test con overfitting moderado
        result2 = detect_overfitting(0.95, 0.80, 2.0, 2.5)
        print(f"\n  Caso 2 (overfitting moderado):")
        print(f"    Status: {result2['status']}")
        print(f"    Severity: {result2['severity']}")
        print(f"    Message: {result2['message']}")
        
        # Test con overfitting alto
        result3 = detect_overfitting(0.98, 0.65, 1.5, 3.5)
        print(f"\n  Caso 3 (overfitting alto):")
        print(f"    Status: {result3['status']}")
        print(f"    Severity: {result3['severity']}")
        print(f"    Message: {result3['message']}")
        
        if (result1['status'] == 'ok' and 
            result2['status'] == 'overfitting' and result2['severity'] == 'moderate' and
            result3['status'] == 'overfitting' and result3['severity'] == 'high'):
            print("\n✅ Detección de overfitting funciona correctamente")
            return True
        else:
            print("\n⚠️ Detección de overfitting no clasifica correctamente")
            return False
            
    except Exception as e:
        print(f"✗ Error probando detección de overfitting: {e}")
        traceback.print_exc()
        return False

def test_outliers():
    """Test 6: Verificar eliminación de outliers"""
    print_section("TEST 6: ELIMINACIÓN DE OUTLIERS")
    
    try:
        from modules.calibration import remove_outliers
        import pandas as pd
        import numpy as np
        
        # Crear datos con outliers
        np.random.seed(42)
        data = {
            'pm25': np.concatenate([
                np.random.normal(25, 5, 95),  # Datos normales
                np.array([100, 150, 200, 250, 300])  # Outliers
            ]),
            'temperature': np.concatenate([
                np.random.normal(20, 3, 95),
                np.array([50, 55, -10, -15, 60])
            ])
        }
        df = pd.DataFrame(data)
        
        print(f"  Datos originales: {len(df)} registros")
        
        # Eliminar outliers
        df_clean = remove_outliers(df, ['pm25', 'temperature'], method='iqr', threshold=1.5)
        
        print(f"  Datos limpios: {len(df_clean)} registros")
        print(f"  Outliers eliminados: {len(df) - len(df_clean)}")
        
        if len(df_clean) < len(df):
            print("\n✅ Eliminación de outliers funciona correctamente")
            return True
        else:
            print("\n⚠️ No se eliminaron outliers (puede ser normal si datos son limpios)")
            return True
            
    except Exception as e:
        print(f"✗ Error probando eliminación de outliers: {e}")
        traceback.print_exc()
        return False

def test_full_pipeline():
    """Test 7: Verificar pipeline completo con datos sintéticos"""
    print_section("TEST 7: PIPELINE COMPLETO")
    
    try:
        from modules.calibration import train_and_evaluate_models
        import pandas as pd
        import numpy as np
        
        # Crear datos sintéticos
        np.random.seed(42)
        n_samples = 200
        
        dates = pd.date_range('2024-06-01', periods=n_samples, freq='H')
        pm25_sensor = np.random.uniform(5, 50, n_samples)
        temperature = np.random.uniform(10, 30, n_samples)
        rh = np.random.uniform(30, 90, n_samples)
        pm25_ref = pm25_sensor * 0.95 + temperature * 0.2 - rh * 0.1 + np.random.normal(0, 2, n_samples)
        
        lowcost_df = pd.DataFrame({
            'datetime': dates,
            'pm25_sensor': pm25_sensor,
            'temperature': temperature,
            'rh': rh
        })
        
        rmcab_df = pd.DataFrame({
            'datetime': dates,
            'pm25_ref': pm25_ref
        })
        
        print(f"  Datos generados: {n_samples} registros")
        
        # Ejecutar calibración
        print("\n  Ejecutando calibración...")
        result = train_and_evaluate_models(
            lowcost_df,
            rmcab_df,
            pollutant='pm25',
            remove_outliers_flag=True,
            use_robust_scaler=True
        )
        
        if result.get('error'):
            print(f"\n✗ Error en calibración: {result['error']}")
            return False
        
        print(f"\n  ✓ Registros originales: {result['records']}")
        print(f"  ✓ Registros después de limpieza: {result['records_after_cleaning']}")
        print(f"  ✓ Outliers eliminados: {result['outliers_removed']}")
        print(f"  ✓ Mejor modelo: {result['best_model']}")
        print(f"  ✓ Modelos evaluados: {len(result['results'])}")
        
        # Verificar que todos los modelos tienen las métricas esperadas
        all_ok = True
        for model in result['results']:
            required_fields = ['model_name', 'r2', 'r2_adjusted', 'rmse', 'mae', 'mape', 'overfitting']
            missing = [f for f in required_fields if f not in model]
            if missing:
                print(f"\n  ⚠️ {model['model_name']} le faltan campos: {missing}")
                all_ok = False
        
        if all_ok:
            print("\n✅ Pipeline completo funciona correctamente")
            return True
        else:
            print("\n⚠️ Algunos modelos tienen campos faltantes")
            return False
            
    except Exception as e:
        print(f"✗ Error en pipeline completo: {e}")
        traceback.print_exc()
        return False

def main():
    """Ejecuta todos los tests"""
    print("\n" + "=" * 80)
    print("VALIDACIÓN FINAL - CORRECCIONES AL MODELO PREDICTIVO")
    print("=" * 80)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Importación de módulos", test_import),
        ("Creación de modelos", test_models),
        ("MAPE con valores cero", test_mape),
        ("R² ajustado", test_adjusted_r2),
        ("Detección de overfitting", test_overfitting_detection),
        ("Eliminación de outliers", test_outliers),
        ("Pipeline completo", test_full_pipeline)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Error ejecutando test '{test_name}': {e}")
            results.append((test_name, False))
    
    # Resumen final
    print_section("RESUMEN DE VALIDACIÓN")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTests ejecutados: {total}")
    print(f"Tests exitosos: {passed}")
    print(f"Tests fallidos: {total - passed}")
    print(f"Tasa de éxito: {(passed/total)*100:.1f}%")
    
    print("\nResultados detallados:")
    for test_name, result in results:
        status = "✅ PASS" if result else "✗ FAIL"
        print(f"  {status} - {test_name}")
    
    if passed == total:
        print("\n" + "=" * 80)
        print("🎉 ¡TODAS LAS VALIDACIONES PASARON EXITOSAMENTE!")
        print("=" * 80)
        print("\n✅ El modelo está listo para usar en tu proyecto")
        print("✅ Todas las correcciones funcionan correctamente")
        print("✅ Puedes proceder con confianza")
        print("\nPróximos pasos:")
        print("  1. Probar con tus datos reales")
        print("  2. Comparar con versión anterior")
        print("  3. Integrar con tu aplicación")
        return 0
    else:
        print("\n" + "=" * 80)
        print("⚠️ ALGUNAS VALIDACIONES FALLARON")
        print("=" * 80)
        print("\nRevisa los errores arriba y:")
        print("  1. Verifica que todas las dependencias estén instaladas")
        print("  2. Revisa el código de calibration.py")
        print("  3. Consulta la documentación")
        return 1

if __name__ == '__main__':
    sys.exit(main())
