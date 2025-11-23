# Objetivo 1 - Calibración Avanzada de Sensores
## Guía de Ejecución

### 🚀 PASO 1: Iniciar el Servidor Flask

Abre una **consola/terminal** en el directorio `fase 4` y ejecuta:

```bash
python app.py
```

Deberías ver algo como:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
 * WARNING in app.run_simple - This is a development server...
```

**IMPORTANTE:** NO cierres esta consola mientras uses la aplicación.

---

### 🌐 PASO 2: Acceder a la Aplicación

Abre tu navegador web y ve a:

```
http://127.0.0.1:5000/objetivo-1
```

Deberías ver la página de **Objetivo 1: Calibración Avanzada de Sensores** con:
- Contexto del proyecto
- Botón "📥 Cargar y Procesar Datos"
- Secciones vacías debajo (se llenarán cuando cargues los datos)

---

### 📥 PASO 3: Cargar los Datos

1. Haz clic en el botón **"📥 Cargar y Procesar Datos"**
2. Verás un spinner indicando "Procesando datos..."
3. **Espera 5-10 segundos** mientras se cargan los datos

Si todo funciona correctamente, deberías ver:
- ✅ Una serie temporal con 4 líneas (3 sensores + RMCAB)
- ✅ 3 gráficos de scatter plot (Aire2, Aire4, Aire5)
- ✅ Métricas R² y RMSE para cada sensor

---

### ⚙️ PASO 4: Ejecutar Calibración

1. Haz clic en **"⚙️ Ejecutar Calibración Completa"**
2. **Espera 10-15 segundos** (entrena 4 modelos x 3 sensores = 12 entrenamientos)
3. Deberías ver:
   - ✅ Tabla con resultados (R², RMSE, MAE, MAPE)
   - ✅ Alerta con "Mejor Modelo por Sensor"
   - ✅ Gráfico de degradación (Crudo vs Calibrado)
   - ✅ Análisis de conclusiones

---

### 📅 PASO 5: Analizar Rangos Temporales (Opcional)

1. Haz clic en **"📅 Probar Rangos de Tiempo"**
2. **Espera 20-30 segundos** (prueba 4 rangos x 3 sensores = 12 entrenamientos)
3. Deberías ver:
   - ✅ Tabla con "Mejor Rango" por sensor
   - ✅ Interpretación de degradación gradual

---

## 🔍 SOLUCIÓN DE PROBLEMAS

### Problema: "No se carga nada"

**Solución 1:** Verifica la consola del navegador (presiona **F12**)
- Abre "Console" tab
- Busca mensajes en rojo (errores)
- Si ves `[handleInitData] Iniciando carga de datos...`, los logs están funcionando

**Solución 2:** Verifica que el servidor está corriendo
```bash
# En otra consola, ejecuta:
curl http://127.0.0.1:5000/objetivo-1

# Deberías obtener HTML de la página
```

**Solución 3:** Recarga la página (Ctrl+F5 o Cmd+Shift+R)

---

### Problema: "Error: Failed to fetch"

**Significa:** El servidor Flask no está corriendo o hay un error CORS

**Solución:**
1. Verifica que ejecutaste `python app.py`
2. Revisa la consola del servidor para errores
3. Asegúrate de que estás en `http://127.0.0.1:5000` (no en otro puerto)

---

### Problema: "Los gráficos no se muestran"

**Significa:** Plotly no se cargó correctamente o hay un error en los datos

**Solución:**
1. Abre la consola del navegador (F12)
2. Busca errores que digan "Plotly"
3. Intenta recargar la página (Ctrl+F5)

---

### Problema: "Demora mucho tiempo"

**Esto es normal:**
- **Cargar datos:** 5-10 segundos
- **Calibración completa:** 10-15 segundos
- **Pruebas de rangos:** 20-30 segundos

---

## 📊 DATOS ESPERADOS

### Datos Crudos (Sin Calibración)
| Sensor | R² Score | RMSE |
|--------|----------|------|
| Aire2  | ~0.77    | ~5.2 |
| Aire4  | ~0.67    | ~6.2 |
| Aire5  | ~0.81    | ~4.8 |

### Después de Calibración
| Sensor | R² Score | RMSE |
|--------|----------|------|
| Aire2  | ~0.94    | ~1.8 |
| Aire4  | ~0.95    | ~1.5 |
| Aire5  | ~0.94    | ~1.9 |

**Mejora:** +20% a +25% en R²

---

## 🐛 DEBUGGING

Para ver los logs detallados:

1. **Abre consola del navegador:** F12
2. **Abre pestaña "Console"**
3. **Busca mensajes que empiezan con `[Objetivo1]` o `[handleInitData]`**

Ejemplo de logs esperados:
```
[Objetivo1] DOM cargado, inicializando...
[Objetivo1] Event listeners configurados.
[handleInitData] Iniciando carga de datos...
[handleInitData] Llamando a /api/objetivo1/initialize...
[handleInitData] Respuesta recibida: 200
[handleInitData] Datos inicializados: {status: 'success', message: '...', metrics: {...}}
[handleInitData] Cargando timeseries...
[loadTimeseries] Iniciando carga...
[loadTimeseries] Datos recibidos, renderizando gráfico...
[loadTimeseries] Gráfico renderizado exitosamente
```

---

## 📁 ARCHIVOS IMPORTANTES

```
fase 4/
├── app.py                    # Servidor Flask
├── modules/
│   ├── data_processor.py     # Carga datos
│   ├── calibration.py        # Modelos ML
│   └── visualization.py      # Gráficos
├── templates/
│   └── objetivo1.html        # Página interactiva
├── static/
│   └── js/
│       └── objetivo1.js      # JavaScript
└── test_endpoints.py         # Script de prueba
```

---

## ✅ CHECKLIST

- [ ] Ejecuté `python app.py`
- [ ] Abrí http://127.0.0.1:5000/objetivo-1
- [ ] Hice clic en "Cargar y Procesar Datos"
- [ ] Vi gráficos de series de tiempo y scatter plots
- [ ] Hice clic en "Ejecutar Calibración Completa"
- [ ] Vi tabla de resultados y conclusiones
- [ ] La consola del navegador (F12) no muestra errores

---

## 💡 TIPS

1. **Para debugging rápido:** Ejecuta `python test_endpoints.py` en otra consola para verificar que los endpoints funcionan
2. **Para ver todos los datos:** Abre Developer Tools (F12) → Network tab → Haz clic en el botón → Revisa las respuestas
3. **Para guardar resultados:** Los gráficos se pueden descargar como PNG (ícono en la esquina superior derecha del gráfico)

---

**¿Problemas?** Revisa la consola del navegador (F12) y busca errores en rojo. Los logs comienzan con `[Objetivo1]` o `[handleInitData]`.
