# GUÍA RÁPIDA DE CORRECCIONES - CALIBRACIÓN PM2.5 y PM10

## ⚠️ ACCIÓN INMEDIATA REQUERIDA

### Paso 1: Crear archivo JavaScript para 2024

Ejecuta el siguiente archivo que ya está creado:
```
C:\Proyecto Maestria 23 Sep\fase 3\run_create_2024.bat
```

O ejecuta manualmente este comando en la terminal:
```cmd
cd "C:\Proyecto Maestria 23 Sep\fase 3"
python create_2024_js.py
```

Esto creará automáticamente `static/js/visualizacion_2024.js` con los ajustes correctos para el año 2024.

### Paso 2: Reiniciar la aplicación Flask

1. Detén el servidor Flask actual (Ctrl+C en la terminal)
2. Inicia nuevamente:
```cmd
cd "C:\Proyecto Maestria 23 Sep\fase 3"
python app.py
```

O usa el batch:
```cmd
iniciar_app.bat
```

## ✅ CORRECCIONES YA APLICADAS

### 1. Timezone Issues Resueltos
**Archivo**: `modules/calibration.py` (líneas 279-295)
- Se removieron timezones de ambos DataFrames antes del merge
- Evita error: "incompatible merge keys datetime64[ns, UTC]"

### 2. Formato Scatter Data Corregido
**Archivo**: `modules/calibration.py` (líneas 612-621)
- Agregados campos `y_test` y `y_pred` para compatibilidad con JavaScript
- Agregado campo `best_model` con el nombre del mejor modelo

### 3. Template Junio-Julio Corregido
**Archivo**: `templates/visualizacion_junio_julio.html`
- Botón "multipleCalibrationBtn" agregado correctamente

### 4. Template 2024 Recreado
**Archivo**: `templates/visualizacion_2024.html`  
- Estructura completamente renovada
- Eliminados bloques duplicados que causaban error Jinja2
- Pestañas de calibración agregadas
- Compatible con visualización multi-contaminante

## 📊 FUNCIONALIDADES IMPLEMENTADAS

### Calibración Múltiple Dispositivos
- ✅ Calibra Aire2, Aire4, Aire5 simultáneamente
- ✅ PM2.5 y PM10 en paralelo
- ✅ 6 modelos ML por contaminante:
  1. Linear Regression
  2. Ridge Regression
  3. Random Forest
  4. SVR (Linear)
  5. SVR (RBF)
  6. SVR (Polynomial)

### Visualización con Pestañas
- ✅ Pestaña por dispositivo (Aire2, Aire4, Aire5)
- ✅ Sub-pestaña por contaminante (PM2.5, PM10)
- ✅ Tabla comparativa de métricas
- ✅ Gráfico de barras (R² y RMSE)
- ✅ Scatter plot (Real vs Predicho)
- ✅ Fórmula de regresión lineal

### Features Automáticas de Calibración
1. **Sensor reading** (PM2.5 o PM10)
2. **Temperatura** (simulada si falta: 8-22°C, promedio 14°C)
3. **Humedad relativa** (simulada si falta: 50-90%, promedio 70%)
4. **Hora del día** (0-23)
5. **Período del día** (0=Madrugada, 1=Mañana, 2=Tarde, 3=Noche)
6. **Día de la semana** (0=Lunes, 6=Domingo)
7. **Es fin de semana** (0=No, 1=Sí)

## 🔍 CÓMO PROBAR

### Visualización Junio-Julio 2025
1. Abrir: http://192.168.1.6:5000/visualizacion/junio-julio
2. Click en **"Calibrar Todos (PM2.5 y PM10)"**
3. Esperar calibración (puede tomar 1-2 minutos)
4. Ver resultados en pestañas separadas por dispositivo
5. Dentro de cada dispositivo, ver PM2.5 y PM10

### Visualización Año 2024
1. Abrir: http://192.168.1.6:5000/visualizacion/2024
2. Click en **"Calibrar Todos (PM2.5 y PM10)"**
3. Mismo proceso que arriba pero con datos de todo 2024
4. Usa estación RMCAB "Min Ambiente" (código 9)

## 🐛 SOLUCIÓN A ERRORES COMUNES

### Error: "comparisonSection is not defined"
**Causa**: JavaScript antiguo sin funciones actualizadas
**Solución**: Ejecutar `run_create_2024.bat` para regenerar el JS

### Error: "incompatible merge keys datetime64[ns, UTC]"
**Causa**: Timezones incompatibles entre DataFrames
**Solución**: Ya corregido en calibration.py (líneas 279-295)

### Gráficos no aparecen
**Causa**: Formato scatter data incompatible
**Solución**: Ya corregido en calibration.py (líneas 612-621)

### Template con bloques duplicados
**Causa**: Archivo visualizacion_2024.html con estructura incorrecta
**Solución**: Ya corregido - archivo completamente reescrito

## 📝 MÉTRICAS DE CALIBRACIÓN

### R² (Coeficiente de Determinación)
- **Rango**: 0 a 1
- **Ideal**: Cercano a 1
- **Interpretación**: % de varianza explicada por el modelo

### RMSE (Root Mean Square Error)
- **Rango**: 0 a ∞
- **Ideal**: Lo más bajo posible
- **Interpretación**: Error promedio en µg/m³

### MAE (Mean Absolute Error)
- **Rango**: 0 a ∞
- **Ideal**: Lo más bajo posible
- **Interpretación**: Error absoluto promedio en µg/m³

### MAPE (Mean Absolute Percentage Error)
- **Rango**: 0% a ∞%
- **Ideal**: Menos de 20%
- **Interpretación**: Error porcentual promedio

### Overfitting
- **OK**: Diferencia R² train-test < 0.1
- **Moderado**: Diferencia entre 0.1 y 0.2
- **Alto**: Diferencia > 0.2

## 📅 DIFERENCIAS ENTRE PÁGINAS

### Junio-Julio 2025
- **Fechas**: 2025-06-01 a 2025-07-31
- **RMCAB**: Las Ferias (código 6)
- **Período**: 2 meses
- **URL**: /visualizacion/junio-julio

### Año Completo 2024
- **Fechas**: 2024-01-01 a 2024-12-31
- **RMCAB**: Min Ambiente (código 9)
- **Período**: 12 meses
- **URL**: /visualizacion/2024

## ⚙️ CONFIGURACIÓN DE CALIBRACIÓN

```python
# Split de datos
train_size = 0.75  # 75% entrenamiento
test_size = 0.25   # 25% prueba
random_state = 42  # Reproducibilidad

# Eliminación de outliers
method = 'IQR'
threshold = 2.0

# Escalado
scaler = RobustScaler()  # Para SVR y Ridge
# StandardScaler para otros modelos

# Validación cruzada
cv_folds = 5  # Solo si n_samples >= 100
```

## 🎯 PRÓXIMOS PASOS SUGERIDOS

1. ✅ Ejecutar `run_create_2024.bat`
2. ✅ Reiniciar Flask
3. ✅ Probar calibración en junio-julio
4. ✅ Probar calibración en 2024
5. 📊 Comparar resultados entre períodos
6. 📈 Analizar mejor modelo por dispositivo
7. 💾 Opcional: Guardar modelos entrenados para uso futuro

## 🆘 SOPORTE

Si algo no funciona:
1. Verificar que app.py esté corriendo
2. Verificar en consola Flask los logs de calibración
3. Abrir DevTools del navegador (F12) y ver consola JavaScript
4. Revisar archivo `CAMBIOS_CALIBRACION.md` para más detalles técnicos

---

**Última actualización**: 2025-11-05
**Versión**: 3.0
**Estado**: ✅ Listo para usar (ejecutar run_create_2024.bat)
