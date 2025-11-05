# 🚀 Guía Rápida - Correcciones del Modelo Predictivo

## ¿Qué se ha corregido?

Se han implementado **10 mejoras críticas** al sistema de calibración de sensores, enfocadas en:

1. ✅ **Robustez** - Manejo de outliers y valores extremos
2. ✅ **Validación** - Cross-validation y detección de overfitting
3. ✅ **Precisión** - Regularización y optimización de hiperparámetros
4. ✅ **Confiabilidad** - Métricas adicionales (R² ajustado, CV)
5. ✅ **Diagnóstico** - Herramientas de análisis automático

---

## 🏃 Inicio Rápido (5 minutos)

### 1. Verificar instalación
```bash
cd "C:\Proyecto Maestria 23 Sep\fase 3"
python -c "from modules.calibration import get_calibration_models; print('✅ OK')"
```

### 2. Ejecutar diagnóstico
```bash
python test_model_corrections.py
```

### 3. Ver comparación detallada
```bash
python compare_models.py
```

### 4. Probar con tu código existente
```python
# Tu código existente sigue funcionando igual
from modules.calibration import train_and_evaluate_models

result = train_and_evaluate_models(lowcost_df, rmcab_df, pollutant='pm25')

# Ahora con información adicional:
print(f"Outliers eliminados: {result['outliers_removed']}")
print(f"Mejor modelo: {result['best_model']}")

for model in result['results']:
    print(f"{model['model_name']}:")
    print(f"  R² ajustado: {model['r2_adjusted']}")
    print(f"  Overfitting: {model['overfitting']['message']}")
```

---

## 📋 Principales Correcciones

### 1. **Detección de Overfitting** 🔍
```python
# Ahora detecta automáticamente si un modelo está sobreajustado
{
  'overfitting': {
    'status': 'ok',  # o 'overfitting'
    'severity': 'none',  # 'none', 'moderate', 'high'
    'message': 'No se detectó overfitting'
  }
}
```

**¿Por qué es importante?**
- Evita modelos que "memorizan" datos de entrenamiento
- Identifica problemas antes del deployment
- Mejora la confiabilidad de las predicciones

---

### 2. **Validación Cruzada (Cross-Validation)** 🎯
```python
# Evaluación más robusta con 5 folds
{
  'cv_r2_mean': 0.9156,  # R² promedio en 5 folds
  'cv_r2_std': 0.0234     # Desviación estándar (variabilidad)
}
```

**¿Por qué es importante?**
- Evaluación más confiable del modelo
- Detecta si el rendimiento es estable
- Reduce sesgo en la estimación de métricas

---

### 3. **Manejo de Outliers** 📊
```python
# Elimina automáticamente valores atípicos
result = train_and_evaluate_models(
    lowcost_df, 
    rmcab_df,
    remove_outliers_flag=True  # NUEVO
)

print(f"Registros originales: {result['records']}")
print(f"Registros limpios: {result['records_after_cleaning']}")
print(f"Outliers eliminados: {result['outliers_removed']}")
```

**¿Por qué es importante?**
- Outliers pueden distorsionar el entrenamiento
- Mejora la generalización del modelo
- Predicciones más estables

---

### 4. **R² Ajustado** 📐
```python
# Métrica más justa que penaliza modelos complejos
{
  'r2': 0.9245,           # R² tradicional
  'r2_adjusted': 0.9198   # R² ajustado (más realista)
}
```

**¿Por qué es importante?**
- R² simple puede ser engañoso con muchas variables
- R² ajustado penaliza la complejidad innecesaria
- Mejor para comparar modelos con diferentes features

---

### 5. **Regularización Mejorada** 🛡️
```python
# Nuevos modelos con regularización
models = {
    'Ridge Regression': Ridge(alpha=1.0),  # NUEVO
    'Random Forest': RandomForestRegressor(
        max_depth=15,           # Limita profundidad
        min_samples_split=5,    # Regularización
        min_samples_leaf=2      # Regularización
    ),
    'SVR (RBF)': SVR(C=10.0, epsilon=0.1)  # Optimizado
}
```

**¿Por qué es importante?**
- Reduce overfitting
- Mejora generalización
- Modelos más estables

---

### 6. **RobustScaler** 💪
```python
# Más robusto ante outliers que StandardScaler
result = train_and_evaluate_models(
    lowcost_df,
    rmcab_df,
    use_robust_scaler=True  # NUEVO
)
```

**Comparación:**
| Scaler | Centro | Escala | Robustez |
|--------|--------|--------|----------|
| StandardScaler | Media | Std Dev | Baja |
| RobustScaler | Mediana | IQR | Alta ✅ |

---

## 📊 Ejemplo Completo

```python
from modules.data_loader import load_lowcost_data, load_rmcab_data
from modules.calibration import train_and_evaluate_models

# 1. Cargar datos
lowcost_df = load_lowcost_data(
    start_date='2025-06-01',
    end_date='2025-07-31',
    devices=['Aire2']
)

rmcab_df = load_rmcab_data(
    station_code=6,  # Las Ferias
    start_date='2025-06-01',
    end_date='2025-07-31'
)

# 2. Calibrar con todas las mejoras
result = train_and_evaluate_models(
    lowcost_df,
    rmcab_df,
    pollutant='pm25',
    test_size=0.25,
    device_name='Aire2',
    remove_outliers_flag=True,    # Eliminar outliers
    use_robust_scaler=True        # Usar RobustScaler
)

# 3. Analizar resultados
if result['error']:
    print(f"❌ Error: {result['error']}")
else:
    print(f"✅ Calibración exitosa!")
    print(f"\n📊 Resumen de datos:")
    print(f"   Registros originales: {result['records']}")
    print(f"   Registros limpios: {result['records_after_cleaning']}")
    print(f"   Outliers eliminados: {result['outliers_removed']}")
    print(f"\n🏆 Mejor modelo: {result['best_model']}")
    
    print(f"\n📈 Resultados por modelo:")
    for model in result['results']:
        print(f"\n   {model['model_name']}:")
        print(f"      R²: {model['r2']:.4f}")
        print(f"      R² ajustado: {model['r2_adjusted']:.4f}")
        
        if 'cv_r2_mean' in model:
            print(f"      CV R² (±std): {model['cv_r2_mean']:.4f} ± {model['cv_r2_std']:.4f}")
        
        print(f"      RMSE: {model['rmse']:.2f}")
        print(f"      MAE: {model['mae']:.2f}")
        print(f"      MAPE: {model['mape']:.2f}%")
        
        overfitting = model['overfitting']
        status_emoji = "✅" if overfitting['status'] == 'ok' else "⚠️"
        print(f"      Overfitting: {status_emoji} {overfitting['message']}")
```

---

## 🎯 Casos de Uso

### Caso 1: Calibración Básica (sin cambios en tu código)
```python
# Tu código existente funciona igual
result = train_and_evaluate_models(lowcost_df, rmcab_df)
# Ahora con más información automáticamente
```

### Caso 2: Calibración con Limpieza de Datos
```python
result = train_and_evaluate_models(
    lowcost_df,
    rmcab_df,
    remove_outliers_flag=True  # Activa limpieza
)

print(f"Se eliminaron {result['outliers_removed']} outliers")
```

### Caso 3: Calibración Robusta (para datos ruidosos)
```python
result = train_and_evaluate_models(
    lowcost_df,
    rmcab_df,
    remove_outliers_flag=True,
    use_robust_scaler=True  # Más robusto
)
```

### Caso 4: Análisis de Overfitting
```python
result = train_and_evaluate_models(lowcost_df, rmcab_df)

for model in result['results']:
    overfitting = model['overfitting']
    if overfitting['status'] == 'overfitting':
        print(f"⚠️ {model['model_name']}: {overfitting['message']}")
```

---

## 🔍 Scripts de Diagnóstico

### test_model_corrections.py
Verifica que todas las correcciones funcionen correctamente:
- ✅ MAPE con valores cero
- ✅ Normalización correcta
- ✅ Detección de overfitting
- ✅ Identificación de outliers
- ✅ Validación cruzada

```bash
python test_model_corrections.py
```

### compare_models.py
Genera reporte comparativo completo:
```bash
python compare_models.py
```

---

## ❓ FAQ - Preguntas Frecuentes

### ¿Es retrocompatible?
✅ **Sí**, tu código existente funciona sin cambios. Las mejoras son automáticas.

### ¿Puedo desactivar la eliminación de outliers?
✅ **Sí**, usa `remove_outliers_flag=False` (por defecto es True).

### ¿Cuántos datos necesito como mínimo?
📊 Mínimo **60 registros** después del merge y limpieza.

### ¿La validación cruzada es obligatoria?
⚡ No, solo se ejecuta si hay **≥100 registros** en entrenamiento.

### ¿Qué pasa si tengo pocos datos?
✅ El sistema lo detecta y ajusta automáticamente (sin CV si <100 registros).

### ¿Cómo sé si hay overfitting?
🔍 Revisa `model['overfitting']['status']` en los resultados.

### ¿Qué modelo debo usar?
🏆 El sistema selecciona automáticamente el mejor (menor RMSE).

---

## 📚 Documentación Adicional

- **MEJORAS_MODELO_PREDICTIVO.md** - Documentación técnica completa
- **test_model_corrections.py** - Script de diagnóstico
- **compare_models.py** - Reporte de comparación
- **modules/calibration.py** - Código fuente con comentarios

---

## 🎓 Para tu Tesis

### Nuevos Puntos a Destacar

1. **Validación Cruzada**
   - "Se implementó validación cruzada K-Fold (k=5) para evaluar de forma más robusta el rendimiento de los modelos"

2. **Detección de Overfitting**
   - "Se desarrolló un sistema automático de detección de sobreajuste basado en la diferencia de métricas entre entrenamiento y test"

3. **Manejo de Outliers**
   - "Se implementaron dos métodos de detección de valores atípicos: IQR (Interquartile Range) y Z-Score"

4. **Regularización**
   - "Se aplicaron técnicas de regularización (Ridge L2, limitación de profundidad en Random Forest) para mejorar la generalización"

5. **Métricas Robustas**
   - "Se incluyó R² ajustado que penaliza la complejidad del modelo, proporcionando una evaluación más justa"

---

## ✅ Checklist de Implementación

Antes de usar en producción:

- [x] ✅ Código implementado y probado
- [x] ✅ Documentación completa
- [x] ✅ Scripts de diagnóstico
- [ ] ⏳ Pruebas con datos reales
- [ ] ⏳ Comparación con versión anterior
- [ ] ⏳ Actualización del frontend
- [ ] ⏳ Validación con expertos

---

## 🚀 Próximos Pasos

1. **Ejecutar diagnóstico**
   ```bash
   python test_model_corrections.py
   ```

2. **Ver comparación**
   ```bash
   python compare_models.py
   ```

3. **Probar con tus datos**
   ```python
   # Tu código aquí
   ```

4. **Revisar documentación técnica**
   - Leer: MEJORAS_MODELO_PREDICTIVO.md

5. **Integrar con frontend** (si es necesario)
   - Mostrar nuevas métricas en la UI
   - Visualizar información de overfitting
   - Mostrar outliers eliminados

---

## 💡 Soporte

¿Problemas o dudas?

1. Revisa **MEJORAS_MODELO_PREDICTIVO.md**
2. Ejecuta **test_model_corrections.py**
3. Consulta los comentarios en **calibration.py**

---

**¡Tu modelo predictivo ahora es más robusto, confiable y científicamente riguroso! 🎉**

Fecha: 5 de noviembre de 2025  
Versión: 2.0
