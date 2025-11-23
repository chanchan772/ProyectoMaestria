# 📊 Flujo de Datos REALES - Objetivo 1

## 🔄 Cómo fluyen los datos desde la BD hasta los gráficos

### 1️⃣ **SENSORES DE BAJO COSTO (Aire2, Aire4, Aire5)**

```
PostgreSQL Database (device_up table)
  ↓
  Query con índices REALES:
  - analogInput → '2' = PM2.5 (multiplicado por 10)
  - analogInput → '1' = PM10
  - analogInput → '3' = Temperature
  - analogInput → '4' = RH
  ↓
load_real_data()
  ↓
  - Agrupa por HORA (redondeando a la hora más cercana)
  - Promedia datos por hora Y dispositivo
  - Pivota para tener columnas: Aire2, Aire4, Aire5
  - Rellena valores faltantes (forward/backward fill)
  ↓
self.sensors_data = DataFrame con columnas:
  [datetime, Aire2, Aire4, Aire5]
```

### 2️⃣ **ESTACIÓN DE REFERENCIA RMCAB (Las Ferias)**

```
RMCAB API Endpoint
  (http://rmcab.ambientebogota.gov.co/home/MonitorsVal)
  ↓
load_rmcab_real()
  ↓
  - Usa Postman template del archivo JSON
  - Construye request para canal PM2.5 (S_6_15)
  - Envía POST request con parámetros de fecha/estación
  ↓
API Response (JSON)
  ↓
  - Extrae campo datetime y valor PM2.5
  - Procesa formato: DD-MM-YYYY HH:MM
  - Crea DataFrame con datos horarios
  ↓
self.rmcab_data = DataFrame con columnas:
  [datetime, PM25]
```

### 3️⃣ **FUSIÓN DE DATOS**

```
sensors_data (Aire2, Aire4, Aire5)
  ↓
merge_data()
  ↓
  Intento 1: Inner Join exacto por datetime
  Intento 2: Si falla, usa merge_asof() con
            tolerance de 1 hora (nearest)
  ↓
merged_data = DataFrame con columnas:
  [datetime, Aire2, Aire4, Aire5, PM25]
```

### 4️⃣ **ENVÍO AL FRONTEND**

```
/api/objetivo1/timeseries (GET)
  ↓
app.py retorna:
  {
    "status": "success",
    "data": [
      {
        "datetime": "2025-06-22T10:00:00",
        "Aire2": 25.3,
        "Aire4": 24.8,
        "Aire5": 26.1,
        "PM25": 28.5  ← DATO REAL DE RMCAB
      },
      ...
    ]
  }
```

### 5️⃣ **RENDERIZADO EN GRÁFICO**

```
JavaScript (objetivo1.js)
  ↓
loadTimeseries()
  ↓
  - Extrae cada sensor: Aire2, Aire4, Aire5
  - Extrae referencia: PM25 (RMCAB)
  - Crea trazas para Plotly
  ↓
Plotly.newPlot()
  ↓
📊 Gráfico con 4 líneas:
   - Aire2 (color 1)
   - Aire4 (color 2)
   - Aire5 (color 3)
   - RMCAB (negro, línea sólida)
```

---

## ✅ Verificación: ¿Está usando datos REALES?

Si ves esto en la consola del servidor cuando inicias:

```
📡 Intentando cargar datos REALES de PostgreSQL y RMCAB...
✅ Datos de sensores cargados: 500 registros
   Columnas: ['datetime', 'Aire2', 'Aire4', 'Aire5']
✅ Datos RMCAB cargados: 450 registros
✅ Datos fusionados: 450 registros
```

**→ ¡Estás usando datos REALES!** ✅

Si ves esto:

```
⚠️ Error al cargar datos reales: ...
📊 Usando datos de ejemplo como respaldo...
```

**→ Está usando datos simulados** (falla en BD o API) ⚠️

---

## 🔍 Debugging: Verificar estructura de datos

Para ver exactamente qué datos se están usando:

1. **Abre consola del servidor** (donde ejecutaste `python app.py`)
2. **Busca logs que empiezan con:**
   - `✅ Datos de sensores cargados`
   - `✅ Datos RMCAB cargados`
   - `✅ Datos fusionados`

3. **En el navegador (F12 → Network):**
   - Haz clic en "Cargar y Procesar Datos"
   - Busca request a `/api/objetivo1/timeseries`
   - En "Response", verifica que `data` contiene:
     ```json
     {
       "datetime": "...",
       "Aire2": número,
       "Aire4": número,
       "Aire5": número,
       "PM25": número  ← De RMCAB
     }
     ```

---

## 📋 Resumen de fuentes de datos

| Elemento | Fuente | Tipo |
|----------|--------|------|
| **Aire2, Aire4, Aire5** | PostgreSQL (device_up) | REAL |
| **PM25 (RMCAB)** | API RMCAB | REAL |
| **Índices** | Query exacto con analogInput 2,1,3,4 | REAL |
| **Período** | 2025-06-01 a 2025-07-30 | REAL |

---

## ⚠️ Si los gráficos muestran números raros

1. **Verifica la consola del servidor** para ver si hay errores
2. **Comprueba credenciales en `.env`**:
   - Host: 186.121.143.150:15432
   - Usuario: dit_as_events
   - Contraseña: ucentral2020
3. **Verifica conexión a BD**: `psql -h 186.121.143.150 -U dit_as_events -d dit_as_events`
4. **Verifica API RMCAB**: Accede a `http://rmcab.ambientebogota.gov.co` en navegador
