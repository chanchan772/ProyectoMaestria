# 📋 Plan: Página Visualización 2024 Completo

**Fecha:** 5 de noviembre de 2025 - 06:25 AM  
**Objetivo:** Replicar funcionalidad de junio-julio pero para todo 2024 con PM2.5 y PM10

---

## ✅ Archivos a Modificar/Crear

### 1. **HTML Template** - `templates/visualizacion_2024.html`
- ✅ Ya existe, necesita actualización
- Cambiar de diseño con cards a diseño con botones rápidos
- Cambiar fechas a 2024-01-01 → 2024-12-31
- Mantener misma estructura que junio-julio

### 2. **JavaScript** - `static/js/visualizacion_2024.js`  
- ✅ Ya existe, necesita reemplazo completo
- Cambiar DATE_RANGE a 2024
- Soportar PM2.5 y PM10
- Calibración múltiple con pestañas
- Misma lógica que junio-julio

### 3. **Ruta en app.py**
- ✅ Ya existe `/visualizacion/2024`
- Verificar que funcione correctamente

### 4. **API Endpoint para calibración**
- ✅ Ya existe `/api/calibrate-multiple-devices`
- Acepta `pollutants` como parámetro
- Funciona con PM2.5 y PM10

---

## 🎯 Funcionalidades Requeridas

### Vista de Datos
- [x] Botones rápidos: Aire2, Aire4, Aire5, RMCAB Las Ferias
- [x] Botón "Comparar 4 Sensores"
- [x] Gráficos de serie temporal
- [x] Métricas: Registros, PM2.5 avg, PM10 avg, temp, humedad

### Calibración Individual
- [x] Botón "Ejecutar Calibración ML" por sensor
- [x] Calibración con PM2.5 y PM10
- [x] Mostrar resultados en tablas
- [x] Gráficos de comparación de modelos
- [x] Scatter plots

### Calibración Múltiple
- [x] Botón "Calibrar Todos los Sensores"
- [x] Procesar Aire2, Aire4, Aire5 simultáneamente
- [x] Pestañas por dispositivo
- [x] Sub-pestañas por contaminante (PM2.5 / PM10)
- [x] Indicadores de éxito/error

### Features del Modelo
- [x] PM2.5 / PM10 sensor
- [x] Temperatura (simulada si falta)
- [x] Humedad relativa (simulada si falta)  
- [x] Hora del día
- [x] Período del día
- [x] Día de la semana
- [x] Fin de semana

### Modelos de ML
- [x] Linear Regression
- [x] Ridge Regression
- [x] Random Forest
- [x] SVR (Linear)
- [x] SVR (RBF)
- [x] SVR (Polynomial)

---

## 📊 Diferencias con Junio-Julio

| Aspecto | Junio-Julio 2025 | 2024 Completo |
|---------|-----------------|---------------|
| **Fechas** | 2025-06-01 a 2025-07-31 | 2024-01-01 a 2024-12-31 |
| **Contaminantes** | Solo PM2.5 | PM2.5 y PM10 |
| **Registros esperados** | ~400 por sensor | ~8,000-10,000 por sensor |
| **Pestañas** | 1 nivel (dispositivo) | 2 niveles (dispositivo → contaminante) |

---

## 🔧 Cambios Técnicos

### JavaScript
```javascript
// Antes (junio-julio)
const DATE_RANGE = {
    start: '2025-06-01',
    end: '2025-07-31'
};
const POLLUTANTS = ['pm25'];

// Después (2024)
const DATE_RANGE = {
    start: '2024-01-01',
    end: '2024-12-31'
};
const POLLUTANTS = ['pm25', 'pm10'];
```

### Backend (ya funciona)
```python
@app.route('/api/calibrate-multiple-devices', methods=['POST'])
def api_calibrate_multiple_devices():
    pollutants = request.json.get('pollutants', ['pm25', 'pm10'])
    # Ya soporta múltiples contaminantes
```

---

## 📂 Estructura de Pestañas

```
Calibración Múltiple 2024
├─ [✅ Aire2]
│  ├─ PM2.5
│  │  ├─ Métricas (registros, outliers)
│  │  ├─ Tabla de 6 modelos
│  │  ├─ Gráfico comparación
│  │  └─ Scatter plot
│  └─ PM10
│     ├─ Métricas
│     ├─ Tabla de 6 modelos
│     ├─ Gráfico comparación
│     └─ Scatter plot
├─ [✅ Aire4]
│  ├─ PM2.5
│  └─ PM10
└─ [✅ Aire5]
   ├─ PM2.5
   └─ PM10
```

---

## ⚠️ Consideraciones

### Datos
- **Año 2024:** Verificar que hay datos disponibles en la BD
- **Meses:** Enero a Diciembre (12 meses vs 2 meses)
- **Volumen:** ~6x más datos que junio-julio

### Rendimiento
- **Calibración más lenta:** 3 dispositivos × 2 contaminantes × 6 modelos = 36 entrenamientos
- **Estimado:** 3-5 minutos para calibración completa
- **Solución:** Mensaje de loading claro con progreso

### Simulación de Variables
- Temperatura: 8-22°C (Bogotá)
- Humedad: 50-90% (Bogotá)
- Patrón diurno sinusoidal

---

## 🚀 Pasos de Implementación

1. ✅ Actualizar `visualizacion_2024.html` con estructura de junio-julio
2. ✅ Reemplazar `visualizacion_2024.js` con nueva versión
3. ✅ Cambiar DATE_RANGE a 2024
4. ✅ Agregar soporte para PM10
5. ✅ Implementar pestañas de dos niveles
6. ✅ Probar calibración individual
7. ✅ Probar calibración múltiple
8. ✅ Validar gráficos

---

## 📝 Testing

### Pruebas Necesarias
- [ ] Cargar Aire2 → Ver PM2.5 y PM10
- [ ] Cargar RMCAB → Ver PM2.5 y PM10
- [ ] Comparar 4 sensores → Ver todos juntos
- [ ] Calibrar Aire2 → PM2.5 y PM10 en pestañas
- [ ] Calibrar Todos → 3 pestañas principales, 2 sub-pestañas cada una
- [ ] Verificar métricas correctas
- [ ] Verificar scatter plots

---

## 📚 Documentación para la Tesis

### Puntos Clave
1. **"Análisis de año completo 2024"**
   - 12 meses de datos continuos
   - Captura variabilidad estacional

2. **"Calibración multi-contaminante"**
   - PM2.5 y PM10 simultáneamente
   - Modelos independientes por contaminante

3. **"Comparación de rendimiento anual"**
   - R² promedio por mes
   - Estacionalidad en precisión del modelo

---

**Estado:** 🔨 EN IMPLEMENTACIÓN  
**Progreso:** 40% (HTML y JS base creados, falta actualizar)  
**Siguiente:** Actualizar HTML y JS completamente
