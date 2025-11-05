# 📅 Períodos de Datos - Configuración del Sistema

## 📊 Resumen de Períodos

El sistema está configurado con **2 períodos de análisis** independientes, cada uno con su estación RMCAB de referencia correspondiente.

---

## 1️⃣ **Junio-Julio 2025**

### 📍 Periodo
- **Inicio:** 1 de junio de 2025
- **Fin:** 31 de julio de 2025
- **Duración:** 61 días

### 📡 Dispositivos Disponibles

#### Sensores de Bajo Costo
1. **Aire2** - Sensor PMS5003
2. **Aire4** - Sensor PMS5003
3. **Aire5** - Sensor PMS5003

#### Estación de Referencia
- **RMCAB - Las Ferias**
  - Código: 6
  - Tipo: Estación oficial de referencia
  - Ubicación: Localidad de Suba, Bogotá

### 🎯 Uso
- Análisis de periodo corto (2 meses)
- Calibración de sensores contra Las Ferias
- Comparación de 5 modelos de ML
- Evaluación de efectividad

### 🔗 Ruta
```
/visualizacion/junio-julio
```

---

## 2️⃣ **Periodo Completo 2024**

### 📍 Periodo
- **Inicio:** 1 de enero de 2024
- **Fin:** 31 de diciembre de 2024
- **Duración:** 366 días (año bisiesto)

### 📡 Dispositivos Disponibles

#### Sensores de Bajo Costo
1. **Aire2** - Sensor PMS5003
2. **Aire4** - Sensor PMS5003
3. **Aire5** - Sensor PMS5003

#### Estación de Referencia
- **RMCAB - Min Ambiente**
  - Código: 9
  - Tipo: Estación oficial de referencia
  - Ubicación: Centro de Bogotá

### 🎯 Uso
- Análisis de periodo largo (año completo)
- Calibración de sensores contra Min Ambiente
- Detección de patrones estacionales
- Evaluación de rendimiento anual

### 🔗 Ruta
```
/visualizacion/2024
```

---

## 🔄 ¿Por Qué 2 Estaciones Diferentes?

### **Las Ferias (Jun-Jul 2025)**
- ✅ Datos más recientes
- ✅ Periodo corto y controlado
- ✅ Mayor densidad de mediciones
- ✅ Ideal para validación inicial

### **Min Ambiente (2024)**
- ✅ Datos históricos completos
- ✅ Periodo largo para patrones estacionales
- ✅ Mayor cantidad de datos
- ✅ Ideal para análisis robusto

---

## 📊 Comparación de Períodos

| Característica | Jun-Jul 2025 | Periodo 2024 |
|---------------|--------------|--------------|
| **Duración** | 61 días | 366 días |
| **Estación RMCAB** | Las Ferias (6) | Min Ambiente (9) |
| **Sensores** | Aire2, 4, 5 | Aire2, 4, 5 |
| **Uso Principal** | Validación corta | Análisis anual |
| **Ventaja** | Datos recientes | Datos extensos |

---

## 🔧 Configuración Técnica

### Fechas en JavaScript

**Junio-Julio 2025:**
```javascript
start_date: '2025-06-01'
end_date: '2025-07-31'
station_code: 6  // Las Ferias
```

**Periodo 2024:**
```javascript
start_date: '2024-01-01'
end_date: '2024-12-31'
station_code: 9  // Min Ambiente
```

### Endpoints API

**Cargar datos de sensor:**
```http
POST /api/load-device-data
{
  "device_name": "Aire2",
  "start_date": "2025-06-01",  // o "2024-01-01"
  "end_date": "2025-07-31"      // o "2024-12-31"
}
```

**Cargar datos RMCAB:**
```http
POST /api/load-rmcab-data
{
  "station_code": 6,             // Las Ferias (2025) o 9 (Min Ambiente 2024)
  "start_date": "2025-06-01",
  "end_date": "2025-07-31"
}
```

**Calibrar sensor:**
```http
POST /api/calibrate-device
{
  "device_name": "Aire2",
  "start_date": "2025-06-01",
  "end_date": "2025-07-31",
  "pollutant": "pm25"
}
```

---

## 🎓 Para Tu Tesis

### Demo Junio-Julio 2025
**Objetivo:** Mostrar calibración en periodo corto
1. Seleccionar Aire2
2. Cargar datos Jun-Jul 2025
3. Ejecutar calibración contra Las Ferias
4. Mostrar resultados de 5 modelos
5. Explicar efectividad

### Demo Periodo 2024
**Objetivo:** Mostrar análisis anual completo
1. Seleccionar Aire4
2. Cargar datos año 2024
3. Ejecutar calibración contra Min Ambiente
4. Analizar patrones estacionales
5. Comparar con periodo corto

---

## 📝 Archivos Modificados

### Templates
- ✅ `templates/visualizacion_junio_julio.html` → 2025, solo Las Ferias
- ✅ `templates/visualizacion_2024.html` → 2024, solo Min Ambiente
- ✅ `templates/base.html` → Navbar actualizado

### JavaScript
- ✅ `static/js/visualizacion_junio_julio.js` → Fechas 2025-06-01 a 2025-07-31
- ✅ `static/js/visualizacion_2024.js` → Fechas 2024-01-01 a 2024-12-31

### Backend
- ✅ `app.py` → Comentarios actualizados

---

## ✅ Checklist de Verificación

### Junio-Julio 2025
- [x] Título muestra "2025"
- [x] Fechas en JS: 2025-06-01 a 2025-07-31
- [x] Solo muestra 4 dispositivos (3 sensores + Las Ferias)
- [x] No muestra Min Ambiente

### Periodo 2024
- [x] Título muestra "2024"
- [x] Fechas en JS: 2024-01-01 a 2024-12-31
- [x] Solo muestra 4 dispositivos (3 sensores + Min Ambiente)
- [x] No muestra Las Ferias

---

## 🔍 Cómo Verificar

### Test 1: Junio-Julio 2025
```bash
# Navegar a http://localhost:5000/visualizacion/junio-julio
# Deberías ver:
✅ Título: "Visualización Junio-Julio 2025"
✅ Subtítulo: "1 junio - 31 julio 2025"
✅ 4 cards: Aire2, Aire4, Aire5, RMCAB Las Ferias
❌ NO debe aparecer Min Ambiente
```

### Test 2: Periodo 2024
```bash
# Navegar a http://localhost:5000/visualizacion/2024
# Deberías ver:
✅ Título: "Visualización Periodo Completo 2024"
✅ Subtítulo: "1 enero - 31 diciembre 2024"
✅ 4 cards: Aire2, Aire4, Aire5, RMCAB Min Ambiente
❌ NO debe aparecer Las Ferias
```

---

## 💡 Notas Importantes

### Calibración
- La calibración se hace **contra la estación RMCAB del mismo periodo**
- Jun-Jul 2025: Sensores vs Las Ferias
- 2024: Sensores vs Min Ambiente

### Datos Históricos
- Los sensores (Aire2, 4, 5) deben tener datos en **ambos periodos**
- Las Ferias: datos en jun-jul 2025
- Min Ambiente: datos en año 2024

### Merge de Datos
- El sistema hace merge temporal con tolerancia de 1 hora
- Si las fechas no coinciden exactamente, busca la más cercana
- Mínimo 100 registros coincidentes para calibración válida

---

**Configuración actualizada y lista para usar! ✅**

Fecha de última actualización: 4 de noviembre de 2025
