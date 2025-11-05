# Cambios Realizados para Corregir la Calibración

## Fecha: 2025-11-05

### Problema Principal
1. Error "comparisonSection is not defined" en JavaScript
2. Gráficos de calibración no se mostraban
3. Error de merge con timezones incompatibles: "incompatible merge keys [0] datetime64[ns, UTC]"
4. Formato de scatter data incompatible entre backend y frontend

### Cambios Realizados

#### 1. `modules/calibration.py`

**Línea 279-295**: Agregado normalización de timezones
```python
# Normalizar timezones - quitar timezone info para evitar conflictos en merge
if lowcost_df['datetime'].dt.tz is not None:
    lowcost_df['datetime'] = lowcost_df['datetime'].dt.tz_localize(None)

if rmcab_df['datetime'].dt.tz is not None:
    rmcab_df['datetime'] = rmcab_df['datetime'].dt.tz_localize(None)
```

**Línea 612-621**: Corregido formato de scatter data
```python
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
```

#### 2. `templates/visualizacion_junio_julio.html`

**Línea 119**: Cambiado ID del botón de calibración múltiple
```html
<button class="btn btn-primary btn-lg" id="multipleCalibrationBtn">
    <i class="bi bi-cpu-fill"></i> Calibrar Todos (PM2.5 y PM10)
</button>
```

#### 3. `templates/visualizacion_2024.html`

**ARCHIVO COMPLETO REEMPLAZADO** con estructura correcta:
- Eliminados bloques duplicados de `{% block extra_css %}`, `{% block content %}`, `{% block extra_js %}`
- Agregado estructura similar a visualizacion_junio_julio.html
- Incluye secciones: multiSensorSection, dataSection, calibrationSection
- Fechas cambiadas a 2024-01-01 hasta 2024-12-31
- Estación RMCAB cambiada a "Min Ambiente" (código 9)

### Funcionalidades Implementadas

1. **Calibración Múltiple**: Calibra los 3 sensores (Aire2, Aire4, Aire5) con PM2.5 y PM10 simultáneamente
2. **Pestañas por Dispositivo**: Muestra resultados de cada sensor en pestañas separadas
3. **Sub-pestañas por Contaminante**: Dentro de cada dispositivo, pestañas para PM2.5 y PM10
4. **6 Modelos ML**: Linear Regression, Ridge, Random Forest, SVR (Linear, RBF, Polynomial)
5. **Gráficos Automáticos**:
   - Tabla comparativa de métricas
   - Gráfico de barras (R² y RMSE)
   - Scatter plot (Real vs Predicho)
   - Fórmula de regresión lineal

6. **Features de Calibración**:
   - PM sensor (PM2.5 o PM10)
   - Temperatura (simulada si no disponible)
   - Humedad relativa (simulada si no disponible)
   - Hora del día (0-23)
   - Período del día (Madrugada, Mañana, Tarde, Noche)
   - Día de la semana (0-6)
   - Es fin de semana (0/1)

### Archivos Pendientes

#### `static/js/visualizacion_2024.js`
**NECESITA SER ACTUALIZADO** para coincidir con visualizacion_junio_julio.js:

1. Cambiar DATE_RANGE:
```javascript
const DATE_RANGE = {
    start: '2024-01-01',
    end: '2024-12-31'
};
```

2. Cambiar DEVICE_CONFIG:
```javascript
const DEVICE_CONFIG = {
    Aire2: { type: 'sensor', label: 'Sensor Aire2' },
    Aire4: { type: 'sensor', label: 'Sensor Aire4' },
    Aire5: { type: 'sensor', label: 'Sensor Aire5' },
    RMCAB_MinAmb: { type: 'rmcab', label: 'RMCAB Min Ambiente', station: 9 }
};
```

3. Cambiar DEVICE_ORDER:
```javascript
const DEVICE_ORDER = ['Aire2', 'Aire4', 'Aire5', 'RMCAB_MinAmb'];
```

4. Copiar todas las funciones de visualizacion_junio_julio.js:
   - runMultipleCalibration()
   - displayMultipleCalibrationResults()
   - createMultiPollutantContent()
   - renderDeviceMultiPollutantGraphs()
   - showComparisonView()
   - loadDeviceData()

### Cómo Probar

1. **Página Junio-Julio 2025**:
   - URL: http://192.168.1.6:5000/visualizacion/junio-julio
   - Click en "Calibrar Todos (PM2.5 y PM10)"
   - Debería calibrar Aire2, Aire4, Aire5
   - Ver resultados en pestañas con sub-pestañas PM2.5/PM10

2. **Página Año 2024**:
   - URL: http://192.168.1.6:5000/visualizacion/2024
   - Click en "Calibrar Todos (PM2.5 y PM10)"
   - Mismo comportamiento pero con datos de todo 2024
   - Usar estación RMCAB Min Ambiente (código 9)

### Notas Importantes

1. **No cambiar fechas**: Las fechas están correctas (2025 para junio-julio, 2024 para año completo)
2. **Simulación de RH y Temperatura**: Si no hay datos reales, se simulan valores realistas
3. **Variables temporales**: Se agregan automáticamente para mejorar la calibración
4. **75/25 split**: Entrenamiento 75%, prueba 25% (random_state=42)
5. **Outliers**: Se eliminan usando IQR con threshold=2.0

### Estado Actual

✅ Calibración backend funcionando correctamente
✅ Template junio-julio corregido
✅ Template 2024 corregido
⚠️ JavaScript 2024 necesita actualización (copiar de junio-julio.js)
✅ Gráficos scatter funcionando
✅ Timezone issues resueltos
✅ Formato scatter data corregido

### Siguiente Paso

**COPIAR** el contenido de `visualizacion_junio_julio.js` a `visualizacion_2024.js` y cambiar solo:
- DATE_RANGE
- DEVICE_CONFIG (cambiar RMCAB_LasFer por RMCAB_MinAmb con station: 9)
- DEVICE_ORDER
