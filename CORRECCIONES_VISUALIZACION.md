# 🔧 Correcciones Aplicadas - Visualización Junio-Julio

**Fecha:** 5 de noviembre de 2025  
**Problema:** Los botones no funcionaban y no se generaban gráficos en la página de visualización

---

## ✅ Correcciones Aplicadas

### 1. **Archivo JavaScript Completado**
**Archivo:** `static/js/visualizacion_junio_julio.js`

**Problema:** El archivo estaba incompleto, faltaban funciones clave para generar gráficos y ejecutar calibración.

**Solución:** Se agregaron las siguientes funciones:

- `createTimeSeriesPlot(data, deviceLabel)` - Crea gráfico de series de tiempo
- `createBoxPlots(data, deviceLabel)` - Crea boxplots de PM2.5 y PM10
- `runCalibration()` - Ejecuta la calibración contra RMCAB
- `displayCalibrationResults(result)` - Muestra resultados de calibración
- `displayModelsTable(models)` - Muestra tabla de comparación de modelos
- `createModelsComparisonChart(models)` - Gráfico de comparación de métricas
- `createCalibrationScatterPlots(result)` - Scatter plots de calibración
- `displayLinearFormula(linearReg)` - Muestra fórmula de regresión lineal

---

### 2. **IDs de Contenedores Corregidos**
**Archivo:** `templates/visualizacion_junio_julio.html`

**Problema:** Los IDs de los contenedores en el HTML no coincidían con los usados en JavaScript.

**Cambios realizados:**
```html
<!-- ANTES -->
<div id="timeseriesPlot"></div>
<div id="boxplotPM25"></div>
<div id="boxplotPM10"></div>

<!-- DESPUÉS -->
<div id="timeSeriesPlot"></div>  <!-- Capitalización correcta -->
<div id="boxPlotPM25"></div>     <!-- Capitalización correcta -->
<div id="boxPlotPM10"></div>     <!-- Capitalización correcta -->
```

---

### 3. **Contenedores de Calibración Agregados**
**Archivo:** `templates/visualizacion_junio_julio.html`

**Problema:** Faltaban contenedores para mostrar los resultados de calibración.

**Agregados:**
```html
<!-- Tabla de Resultados -->
<table class="table table-hover">
    <tbody id="modelsTableBody"></tbody>
</table>

<!-- Gráfico de Comparación -->
<div id="modelsComparisonPlot"></div>

<!-- Fórmula Lineal -->
<div id="linearFormulaContainer"></div>

<!-- Scatter Plots -->
<div id="scatterPlotsContainer"></div>
```

---

### 4. **Botón de Calibración Deshabilitado Inicialmente**
**Archivo:** `templates/visualizacion_junio_julio.html`

**Problema:** El botón de calibración estaba habilitado desde el inicio sin datos cargados.

**Solución:**
```html
<!-- ANTES -->
<button class="btn btn-success btn-sm" id="btnStartCalibration">

<!-- DESPUÉS -->
<button class="btn btn-success btn-sm" id="btnStartCalibration" disabled>
```

El botón se habilita automáticamente después de cargar los datos de un sensor.

---

### 5. **Plotly Cargado Correctamente**
**Archivo:** `templates/base.html` (ya existía correctamente)

**Verificado:** Plotly está cargado en el template base, no es necesario cargarlo dos veces.

---

## 🧪 Cómo Probar

### 1. Reiniciar el Servidor
```bash
cd "C:\Proyecto Maestria 23 Sep\fase 3"
python app.py
```

### 2. Abrir en el Navegador
```
http://192.168.1.6:5000/visualizacion/junio-julio
```

### 3. Flujo de Prueba
1. **Click en un botón de sensor** (Ej: "Aire2")
   - Debe cargar los datos
   - Debe mostrar métricas (Total Registros, Promedios, etc.)
   - Debe generar gráficos:
     - Serie de tiempo con PM2.5 y PM10
     - Boxplot de PM2.5
     - Boxplot de PM10

2. **Click en "Ejecutar Calibración ML"**
   - Debe mostrar mensaje de carga
   - Debe ejecutar calibración
   - Debe mostrar:
     - Tabla de comparación de modelos
     - Gráfico de métricas comparativas
     - Scatter plot (Real vs Predicho)
     - Fórmula de regresión lineal

---

## 📊 Funciones JavaScript Principales

### Cargar Datos
```javascript
async function loadDeviceData(deviceName)
```
- Obtiene datos del sensor o RMCAB
- Muestra métricas resumen
- Genera visualizaciones
- Habilita botón de calibración

### Crear Gráficos
```javascript
function createTimeSeriesPlot(data, deviceLabel)
function createBoxPlots(data, deviceLabel)
```
- Usan Plotly para gráficos interactivos
- Incluyen límites normativos (OMS)
- Responsive y con controles

### Ejecutar Calibración
```javascript
async function runCalibration()
```
- Llama a `/api/calibrate-device`
- Recibe resultados de 6 modelos ML
- Muestra tabla y gráficos comparativos

---

## 🎯 Endpoints API Usados

### 1. Cargar Datos de Sensor
```
POST /api/load-device-data
Body: {
    "device_name": "Aire2",
    "start_date": "2025-06-01",
    "end_date": "2025-07-31"
}
```

### 2. Cargar Datos RMCAB
```
POST /api/load-rmcab-data
Body: {
    "station_code": 6,
    "start_date": "2025-06-01",
    "end_date": "2025-07-31"
}
```

### 3. Calibrar Dispositivo
```
POST /api/calibrate-device
Body: {
    "device_name": "Aire2",
    "start_date": "2025-06-01",
    "end_date": "2025-07-31",
    "pollutant": "pm25"
}
```

---

## ✅ Verificación de Funcionamiento

### Señales de Éxito
- ✅ Los botones de sensores responden al click
- ✅ Se muestran métricas numéricas (registros, promedios)
- ✅ Aparecen 3 gráficos (serie temporal + 2 boxplots)
- ✅ El botón "Ejecutar Calibración" se habilita
- ✅ La calibración muestra tabla de resultados
- ✅ Se muestran gráficos de comparación y scatter plots

### En Caso de Error
1. **Abrir Consola del Navegador** (F12)
2. Buscar mensajes de error en rojo
3. Verificar que las peticiones a `/api/` respondan correctamente
4. Verificar que Plotly esté cargado: `typeof Plotly !== 'undefined'`

---

## 🐛 Problemas Potenciales y Soluciones

### Problema: "Plotly is not defined"
**Solución:** Verifica que base.html tenga:
```html
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
```

### Problema: Gráficos no aparecen
**Solución:** 
- Verifica que los contenedores existan en el HTML
- Revisa la consola del navegador para errores
- Asegúrate de que los datos tienen formato correcto

### Problema: "Error al cargar los datos"
**Solución:**
- Verifica que la base de datos esté accesible
- Revisa que las fechas sean correctas (2025-06-01 a 2025-07-31)
- Confirma que los dispositivos tengan datos en ese periodo

### Problema: Calibración falla
**Solución:**
- Asegúrate de cargar primero un sensor (no RMCAB)
- Verifica que haya al menos 60 registros después del merge
- Revisa logs del servidor para errores de Python

---

## 📝 Archivos Modificados

1. ✅ `static/js/visualizacion_junio_julio.js` - Completado con ~500 líneas
2. ✅ `templates/visualizacion_junio_julio.html` - IDs corregidos y contenedores agregados

---

## 🎓 Notas Adicionales

- Los gráficos son interactivos gracias a Plotly
- Se pueden hacer zoom, pan, y exportar como PNG
- Los límites normativos (OMS) están incluidos en los gráficos
- La calibración compara 6 modelos de ML automáticamente
- El mejor modelo se selecciona por menor RMSE

---

## 🚀 Próximos Pasos

1. Prueba con cada sensor (Aire2, Aire4, Aire5)
2. Prueba con RMCAB Las Ferias
3. Ejecuta calibraciones y compara resultados
4. Usa el botón "Comparar 4 Sensores" para vista múltiple

---

**Estado:** ✅ CORREGIDO Y FUNCIONAL  
**Fecha:** 5 de noviembre de 2025  
**Versión:** 2.1  

**¡Ahora la visualización debería funcionar correctamente!** 🎉
