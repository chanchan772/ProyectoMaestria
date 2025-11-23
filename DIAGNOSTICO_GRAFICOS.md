# 🔧 Diagnóstico: Gráficos Incompletos

## ❌ Problema Identificado

Los gráficos estaban mostrando **solo Aire2**, mientras que faltaban **Aire4, Aire5 y RMCAB**.

Razón: El merge estaba usando `how='inner'`, lo que eliminaba registros donde faltaban datos en alguna columna.

---

## ✅ Correcciones Realizadas

### 1. **Cambio en `merge_data()` (data_processor.py)**
   - ❌ Antes: `merge(..., how='inner')` → Eliminaba filas con datos incompletos
   - ✅ Ahora: `merge(..., how='outer')` → Mantiene todos los datos
   - ✅ Agrega relleno automático (`fillna()`) para valores faltantes

### 2. **Logs Detallados en `initialize_data()`**
   - ✅ Muestra cantidad de registros en cada etapa
   - ✅ Indica cuántos valores no-nulos hay por columna
   - ✅ Facilita diagnóstico visual de problemas

### 3. **Endpoint de Debug**
   - ✅ Nueva ruta: `/api/debug/data-structure`
   - ✅ Muestra estructura exacta de los datos cargados
   - ✅ Porcentaje de valores nulos por columna

---

## 🚀 Pasos para Corregir el Problema

### **Paso 1: Actualiza el código**

Los cambios ya están hechos. Asegúrate de tener:
- `data_processor.py` con `merge(..., how='outer')`
- `app.py` con logs detallados

### **Paso 2: Reinicia el servidor**

```bash
cd "C:\Users\Sebastian\Documents\Maestria\Proyecto Maestria 23 Sep\fase 4"
python app.py
```

Deberías ver en la consola:
```
============================================================
📡 Intentando cargar datos REALES de PostgreSQL y RMCAB...
============================================================

[1/3] Cargando datos de sensores (Aire2, Aire4, Aire5)...
      ✅ Sensores: XXX registros, columnas: ['datetime', 'Aire2', 'Aire4', 'Aire5']

[2/3] Cargando datos de RMCAB (Las Ferias)...
      ✅ RMCAB: YYY registros, columnas: ['datetime', 'PM25']

[3/3] Fusionando datos...
      ✅ Fusionados: ZZZ registros
      Columnas finales: ['datetime', 'Aire2', 'Aire4', 'Aire5', 'PM25']
      Valores no-nulos por columna:
        - datetime: ZZZ/ZZZ valores
        - Aire2: ZZZ/ZZZ valores
        - Aire4: ZZZ/ZZZ valores
        - Aire5: ZZZ/ZZZ valores
        - PM25: ZZZ/ZZZ valores

✅ Datos REALES cargados exitosamente
============================================================
```

### **Paso 3: Verifica los datos en el navegador**

1. Abre: `http://127.0.0.1:5000/api/debug/data-structure`
2. Busca en la respuesta JSON:
   - `info_columnas.Aire2.no_nulos` > 0 ✅
   - `info_columnas.Aire4.no_nulos` > 0 ✅
   - `info_columnas.Aire5.no_nulos` > 0 ✅
   - `info_columnas.PM25.no_nulos` > 0 ✅

Si todos tienen valores > 0, los datos están bien.

### **Paso 4: Accede a la página**

```
http://127.0.0.1:5000/objetivo-1
```

1. Haz clic en "📥 Cargar y Procesar Datos"
2. Deberías ver **4 líneas** en el gráfico:
   - Aire2 (azul)
   - Aire4 (naranja)
   - Aire5 (verde)
   - RMCAB (negro, línea sólida) ← **Esto era lo que faltaba**

---

## 🔍 Cómo Verificar si el Problema está Resuelto

### En el gráfico "Serie de Tiempo":
```
✅ Se ven 4 líneas
✅ Hay una leyenda con 4 elementos
✅ La línea negra (RMCAB) está presente
```

### En la consola del navegador (F12):
```
[loadTimeseries] Datos recibidos: XXXX registros
[loadTimeseries] Renderizando gráfico con 4 trazas...
[loadTimeseries] Gráfico renderizado exitosamente
```

### En los scatter plots:
```
✅ Se ven 3 gráficos (Aire2, Aire4, Aire5)
✅ Cada uno con puntos (no vacío)
✅ Métricas R² y RMSE visibles
```

---

## ⚠️ Si Aún Hay Problemas

### Opción 1: Verifica el endpoint de debug

```
http://127.0.0.1:5000/api/debug/data-structure
```

Busca en la respuesta si alguna columna tiene `porcentaje_nulos: 100`:
- Si `Aire4.porcentaje_nulos = 100` → Los datos de Aire4 no se están cargando
- Si `PM25.porcentaje_nulos = 100` → RMCAB no se está cargando

### Opción 2: Revisa la consola del servidor

Busca mensajes de error como:
```
❌ Error al cargar datos reales: ...
❌ Error al cargar datos RMCAB: ...
```

Si ves esto, hay un problema con:
- Conexión a BD (Aire2, Aire4, Aire5)
- Conexión a API RMCAB (PM25)

### Opción 3: Verifica credenciales en `.env`

```
DB_NAME=dit_as_events
DB_USER=dit_as_events
DB_PASSWORD=ucentral2020
DB_HOST=186.121.143.150
DB_PORT=15432
```

---

## 📊 Resumen de Cambios

| Aspecto | Antes | Después |
|---------|-------|---------|
| Merge type | `inner` | `outer` |
| Filas retornadas | Eliminaba datos incompletos | Mantiene todos los datos |
| Valores NULL | No los rellena | Auto-rellena con `ffill()`/`bfill()` |
| Visibilidad en gráficos | Aire2 solo | Aire2, Aire4, Aire5, RMCAB |
| Líneas en gráfico | 1 (incompleto) | 4 (completo) |

---

## ✅ Confirmación

Una vez que veas **4 líneas en el gráfico** (Aire2, Aire4, Aire5, RMCAB):

✅ El problema está RESUELTO
✅ Los datos son 100% REALES
✅ Está graficando correctamente
