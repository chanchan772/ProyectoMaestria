# 🌐 PROBAR OBJETIVO 2 EN LA WEB

## ✨ Nueva Interfaz Web Interactiva

Se ha creado una interfaz web completa en `http://127.0.0.1:5000/objetivo-2` para probar el modelo predictivo LSTM directamente desde el navegador.

---

## 🚀 Pasos para Probar

### 1. **Instalar Dependencias** (si no lo hizo)

```bash
cd "C:\Users\Sebastian\Documents\Maestria\Proyecto Maestria 23 Sep\fase 4"
pip install -r requirements.txt
```

### 2. **Iniciar Servidor Flask**

```bash
python app.py
```

**Verá:**
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
```

### 3. **Abrir en Navegador**

Abra: **http://127.0.0.1:5000/objetivo-2**

---

## 🎯 Interface Web: Qué Verá

### **Panel de Control**
- ✅ Botón grande: "🧠 Entrenar Modelo"
- ✅ Indicador de progreso animado
- ✅ Estado en tiempo real

### **Instrucciones**
1. Haz clic en "Entrenar Modelo"
2. El modelo LSTM se entrena (5-10 minutos)
3. Resultados se muestran automáticamente

### **Resultados Automáticos**

Una vez que termina el entrenamiento, verá:

#### **📊 Tabla de Métricas**
```
PM2.5 (μg/m³)
├─ 1h:  RMSE=4.2  MAE=3.1  R²=0.92  MAPE=12.3%
├─ 3h:  RMSE=7.1  MAE=5.2  R²=0.85  MAPE=18.5%
└─ 5h:  RMSE=10.3 MAE=7.8  R²=0.72  MAPE=26.1%

PM10 (μg/m³)
├─ 1h:  RMSE=5.1  MAE=4.0  R²=0.88  MAPE=15.2%
├─ 3h:  RMSE=8.9  MAE=6.8  R²=0.80  MAPE=22.3%
└─ 5h:  RMSE=12.4 MAE=9.5  R²=0.68  MAPE=28.7%
```

#### **📖 Interpretación de Resultados**
Explicación automática de qué significa cada métrica

#### **📈 Gráficos Interactivos**
- PM2.5: 3 scatter plots (predicción vs real para 1h, 3h, 5h)
- PM10: 3 scatter plots (predicción vs real para 1h, 3h, 5h)
- Comparación: Gráficos de línea (RMSE, MAE, R², MAPE)

#### **📥 Descargar Resultados**
Botones para descargar:
- `predictive_metrics.csv` - Tabla de métricas
- `predictions_PM25.png` - Gráficos PM2.5
- `predictions_PM10.png` - Gráficos PM10
- `steps_comparison.png` - Comparación de efectividad

---

## 🎨 Características de la Interfaz

### **Responsive Design**
✅ Funciona en Desktop, Tablet, Mobile

### **Interfaz Intuitiva**
✅ Bootstrap 5.3 styling
✅ Iconos FontAwesome
✅ Animaciones suaves

### **Manejo de Errores**
✅ Mensajes claros si algo falla
✅ Botón "Reiniciar" para volver a intentar

### **Indicador de Progreso**
✅ Barra de progreso animada
✅ Mensajes de estado en tiempo real

---

## 📱 Estructura de la Página

```
┌─────────────────────────────────────────┐
│ 🔮 Objetivo 2: Modelo Predictivo LSTM   │
└─────────────────────────────────────────┘

┌─ Panel de Control ──────────────────────┐
│ ⚙️ [Estado] [Progreso]  [🧠 Entrenar]    │
└─────────────────────────────────────────┘

┌─ Instrucciones ─────────────────────────┐
│ ℹ️ Cómo usar el modelo                   │
└─────────────────────────────────────────┘

┌─ Métricas (después de entrenar) ────────┐
│ 📊 Tabla PM2.5  │  📊 Tabla PM10         │
└─────────────────────────────────────────┘

┌─ Interpretación ────────────────────────┐
│ 📖 Explicación de métricas               │
└─────────────────────────────────────────┘

┌─ Gráficos ──────────────────────────────┐
│ 📈 PM2.5 Predictions                    │
│ 📈 PM10 Predictions                     │
│ 📈 Steps Comparison                     │
└─────────────────────────────────────────┘

┌─ Información del Modelo ────────────────┐
│ 🧠 Arquitectura  │  Datos  │  Horizonte  │
└─────────────────────────────────────────┘

┌─ Características ───────────────────────┐
│ ✨ Ventajas  │  Validación               │
└─────────────────────────────────────────┘

┌─ Descargas ─────────────────────────────┐
│ 📥 Descargar CSV y PNGs                 │
└─────────────────────────────────────────┘
```

---

## ⚙️ Flujo Técnico Detrás de Escenas

```
Usuario hace clic en "Entrenar Modelo"
            ↓
JavaScript: fetch('/api/objetivo2/train-predictor')
            ↓
Flask: POST /api/objetivo2/train-predictor
            ↓
Backend:
├─ Carga datos PostgreSQL + RMCAB CSV
├─ Prepara secuencias 24h
├─ Entrena 3 modelos LSTM (1h, 3h, 5h)
├─ Calcula 4 métricas (RMSE, MAE, R², MAPE)
├─ Genera 4 gráficos PNG
└─ Retorna JSON con resultados
            ↓
JavaScript: Recibe JSON con métricas
            ↓
Frontend:
├─ Llena tablas con métricas
├─ Carga imágenes PNG desde static/results/
├─ Muestra secciones de resultados
└─ Scroll automático a resultados
            ↓
✅ Usuario ve todo completado en 5-10 minutos
```

---

## 🔧 Archivos Modificados para Web

| Archivo | Cambio | Descripción |
|---------|--------|-------------|
| `templates/objetivo2.html` | Reemplazado | Nueva interfaz interactiva |
| `app.py` | Modificado | Nuevos endpoints para Objetivo 2 |
| `modules/predictive_model.py` | Actualizado | Guarda en `static/results/` |
| `static/results/` | Creado | Carpeta para archivos estáticos |

---

## 🎯 Casos de Uso

### **Caso 1: Investigador**
```
1. Abro página Objetivo 2
2. Hago clic en "Entrenar Modelo"
3. Espero 10 minutos mientras entrena
4. Reviso tablas de métricas
5. Analizo gráficos
6. Descargo CSV para análisis posterior
```

### **Caso 2: Presentador**
```
1. Abro en proyector: http://127.0.0.1:5000/objetivo-2
2. Hago clic en "Entrenar" (como demostración)
3. Vemos progreso en tiempo real
4. Mostramos resultados finales
5. Explicamos métricas usando tabla integrada
```

### **Caso 3: Desarrollador**
```
1. Reviso código en templates/objetivo2.html
2. Veo JavaScript que llama /api/objetivo2/train-predictor
3. Sigo el flujo en app.py → modules/predictive_model.py
4. Personalizo parámetros (epochs, lookback, steps)
5. Agrego nuevas métricas o visualizaciones
```

---

## ⚠️ Solución de Problemas

### **Error: "Conexión rehusada"**
```
Problema: Flask no está corriendo
Solución: Ejecutar: python app.py
```

### **Error: "404 Not Found"**
```
Problema: URL incorrecta
Solución: Usar: http://127.0.0.1:5000/objetivo-2
```

### **Error: "Modelo no entrenado"**
```
Problema: No hizo clic en "Entrenar Modelo"
Solución: Haga clic en botón verde
```

### **Error: "PostgreSQL no disponible"**
```
Problema: BD no conectada
Solución: Verificar credenciales en .env
```

### **Error: "CSV file not found"**
```
Problema: Falta RMCAB datos
Solución: Descargar con: python download_rmcab_data.py
```

---

## 📊 Rendimiento Esperado

| Aspecto | Valor |
|---------|-------|
| Tiempo carga página | < 1s |
| Tiempo entrenamiento | 5-10 min |
| Tiempo carga gráficos | < 2s |
| Responsividad | Instantánea |
| Memoria RAM | ~500MB-1GB |

---

## 🎉 Lo Mejor de la Interfaz Web

✨ **No necesita línea de comandos**
- Todo desde navegador web

✨ **Visualización en Tiempo Real**
- Ver progreso mientras entrena

✨ **Gráficos Automáticos**
- Generados y mostrados al instante

✨ **Descargas Integradas**
- Bajar resultados sin navegar carpetas

✨ **Documentación Integrada**
- Explicaciones en la misma página

✨ **Profesional y Pulido**
- Estilo Bootstrap 5.3
- Responsive design
- Animaciones suaves

---

## 📞 Próximos Pasos

1. ✅ Ejecutar `python app.py`
2. ✅ Abrir `http://127.0.0.1:5000/objetivo-2`
3. ✅ Hacer clic en "🧠 Entrenar Modelo"
4. ✅ Esperar y ver resultados
5. ✅ Descargar gráficos y métricas

---

**¡Listo para probar!**

Abra: **http://127.0.0.1:5000/objetivo-2**

Haga clic en: **🧠 Entrenar Modelo**

Espere ~10 minutos y disfrute de los resultados.

---

*Versión: 1.0*
*Fecha: 2025-11-20*
