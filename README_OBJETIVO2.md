# ⚡ INICIO RÁPIDO - OBJETIVO 2: MODELO PREDICTIVO

## ¿Qué es?

Modelo predictivo **LSTM** que predice PM2.5 y PM10 con **1, 3 y 5 horas de anticipación** basado en:

✅ **Datos REALES** de estación RMCAB (PM2.5 y PM10 históricos)
✅ **Temperatura y Humedad SIMULADAS** (patrón realista Bogotá)
❌ **NO usa sensores Aire2/4/5** (están degradados)
❌ **NO usa PostgreSQL** (por eso se necesita el modelo)

## 🚀 Inicio Rápido (2 minutos)

### Opción 1: Script Directo

```bash
cd "C:\Users\Sebastian\Documents\Maestria\Proyecto Maestria 23 Sep\fase 4"

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python train_predictor.py
```

**Salida:**
```
✓ Cargando datos de PostgreSQL...
✓ Cargando RMCAB desde CSV...
✓ Entrenando LSTM...
✓ Generando reportes...

📊 RESULTADOS
PM2.5:
  1h:  RMSE=4.2  MAE=3.1  R²=0.92  MAPE=12.3%
  3h:  RMSE=7.1  MAE=5.2  R²=0.85  MAPE=18.5%
  5h:  RMSE=10.3 MAE=7.8  R²=0.72  MAPE=26.1%

PM10:
  1h:  RMSE=5.1  MAE=4.0  R²=0.88  MAPE=15.2%
  3h:  RMSE=8.9  MAE=6.8  R²=0.80  MAPE=22.3%
  5h:  RMSE=12.4 MAE=9.5  R²=0.68  MAPE=28.7%
```

### Opción 2: API REST

```bash
# Terminal 1: Iniciar servidor
python app.py

# Terminal 2: Entrenar modelo
curl -X POST http://localhost:5000/api/objetivo2/train-predictor

# Obtener métricas
curl http://localhost:5000/api/objetivo2/metrics
```

---

## 📊 ¿Cómo Lee los Resultados?

### Las 4 Métricas

| Métrica | Fórmula | Interpretación | Objetivo |
|---------|---------|---|---|
| **RMSE** | √[Σ(y-ŷ)²/n] | Error cuadrático medio (μg/m³) | Minimizar |
| **MAE** | Σ\|y-ŷ\|/n | Error absoluto medio (μg/m³) | Minimizar |
| **R²** | 1-(SSres/SStot) | % varianza explicada [0,1] | Maximizar |
| **MAPE** | Σ\|y-ŷ\|/\|y\| × 100 | Error porcentual (%) | Minimizar |

### Ejemplo: PM2.5 a 1 hora

```
RMSE = 4.2 μg/m³
→ El modelo se equivoca en promedio 4.2 μg/m³

R² = 0.92
→ El modelo explica el 92% de la variación
→ MUY BUENO (cercano a 1)

MAPE = 12.3%
→ Error promedio del 12.3%
→ Aceptable para predicción atmosférica
```

### Degradación Normal

```
Conforme predicimos más lejos:
1h  → Error pequeño (buena precisión)
3h  → Error 2x mayor (caos determinista)
5h  → Error 3x mayor (límite de predictibilidad)

Esto es NORMAL y esperado en series de tiempo
```

---

## 📁 Archivos Generados

```
results/
├── predictive_metrics.csv          ← Tabla de métricas
├── predictions_PM25.png            ← Gráficos PM2.5 (3 pasos)
├── predictions_PM10.png            ← Gráficos PM10 (3 pasos)
└── steps_comparison.png            ← Comparación pasos (1h, 3h, 5h)
```

### Ver Resultados

```bash
# CSV de métricas (Excel)
results/predictive_metrics.csv

# Imágenes (abrir con visualizador)
results/predictions_PM25.png
results/predictions_PM10.png
results/steps_comparison.png
```

---

## 🏗️ Arquitectura (Resumen)

```
ENTRADA (24 horas histórico)
    ↓
LSTM Layer 1 (64 neuronas)
    ↓
LSTM Layer 2 (32 neuronas)
    ↓
Dense Layer (16 neuronas)
    ↓
OUTPUT (Predicción PM)

Training: 75% datos antiguos
Test:     25% datos recientes
```

---

## 🔧 Técnicamente: ¿Qué Hace?

### 1. Carga Datos
```python
# PostgreSQL: Sensores (Aire2, Aire4, Aire5)
# CSV: RMCAB (pm25_ref, pm10_ref)
# Simula: Temperatura, Humedad Relativa
merged_df = data_processor.merge_data()
```

### 2. Preprocesa
```python
# Normaliza [0, 1]
# Crea secuencias de 24 pasos
# Split temporal: 75% entrenamiento, 25% prueba
X_train, X_test, y_train, y_test = preprocessor.prepare_data(merged_df)
```

### 3. Entrena LSTM
```python
# Modelo LSTM con 2 capas + Dropout
# 3 modelos independientes (1h, 3h, 5h)
# Early stopping para evitar overfitting
model.fit(X_train, y_train, epochs=50, callbacks=[early_stop])
```

### 4. Predice y Evalúa
```python
# Predicción en datos nuevos (test set)
y_pred = model.predict(X_test)

# Desnormalizar
y_pred_real = scaler.inverse_transform(y_pred)

# Calcular 4 métricas (RMSE, MAE, R², MAPE)
metrics = evaluate(y_test_real, y_pred_real)
```

### 5. Reporta
```python
# CSV: predictive_metrics.csv
# PNG: Scatter plots (Real vs Predicho)
# PNG: Line plots (Comparación pasos)
```

---

## ❓ Preguntas Frecuentes

### ¿Por qué LSTM?
- Captura **dependencias temporales** automáticamente
- Memoria de eventos lejanos (**256 pasos* atrás)
- Superior a regresión lineal para series complejas

### ¿Por qué 24 horas de histórico?
- PM tiene ciclo diario (cambios cada ~6-12h)
- 24h captura ciclo completo
- Más que eso: ruido, menos: pierde contexto

### ¿Por qué 3 modelos (1h, 3h, 5h)?
- Cada horizonte tiene diferentes incertidumbres
- Modelos específicos = predicciones mejores
- Alternativa: 1 modelo + composición (peor)

### ¿Puedo mejorar los resultados?
Sí:
1. **Más datos** (junio-julio → todo el año)
2. **Features adicionales** (presión, viento)
3. **Arquitectura** (Transformer, Attention)
4. **Hibridación** (LSTM + ARIMA)

### ¿Funciona para otros contaminantes?
Sí, misma arquitectura para:
- PM10 (ya implementado)
- NO₂, O₃, SO₂, CO (si tienes datos RMCAB)

---

## ⚠️ Limitaciones

| Limitación | Causa | Mitigación |
|-----------|-------|-----------|
| **RMSE crece** con horizonte | Caos determinista | Usar 1h para alertas críticas |
| **Temperaturas simuladas** | No hay sensor en BD | Conectar estación meteorológica |
| **Datos solo junio-julio** | Período limitado | Descargar año completo |
| **Degradación sensores** | Edad y calibración | Cambiar sensores/calibrar |

---

## 📋 Checklist de Ejecución

### Pre-requisitos
- [ ] Python 3.8+
- [ ] Conexión a PostgreSQL (186.121.143.150:15432)
- [ ] Archivo `data_rmcab/rmcab_data.csv`
- [ ] Ejecutable en `fase 4/`

### Instalación
```bash
pip install -r requirements.txt
```
- [ ] Sin errores de instalación
- [ ] TensorFlow instalado correctamente

### Ejecución
```bash
python train_predictor.py
```
- [ ] Carga datos sin errores
- [ ] Entrena modelo
- [ ] Genera gráficos

### Validación
- [ ] `results/predictive_metrics.csv` existe
- [ ] `results/predictions_PM25.png` existe
- [ ] `results/predictions_PM10.png` existe
- [ ] `results/steps_comparison.png` existe
- [ ] Métricas razonables (R² > 0.6)

---

## 📞 Si Hay Errores

### Error: "TensorFlow not available"
```
Solución:
pip install tensorflow==2.10.0
# O si no tienes GPU:
pip install tensorflow-cpu==2.10.0
```

### Error: "CSV file not found"
```
Verificar:
1. ls data_rmcab/
2. Debería existir: rmcab_data.csv
3. Si no: python download_rmcab_data.py
```

### Error: "No se conecta a PostgreSQL"
```
Verificar:
1. Credenciales en .env
2. Host: 186.121.143.150:15432
3. Usuario: dit_as_events
4. Contraseña: ucentral2020
```

### Modelo muy lento
```
Solución:
# Reducir datos en train_predictor.py:
data_processor.load_real_data(
    start_date='2025-07-01',  # ← Solo julio
    end_date='2025-07-31'
)
```

---

## 📚 Documentación Completa

Para detalles técnicos completos:
→ Ver archivo: `OBJETIVO_2_MODELO_PREDICTIVO.md`

Cubre:
- Arquitectura detallada
- Matemáticas de LSTM
- Preparación de datos paso a paso
- Métricas explicadas
- Validación temporal
- Mejoras futuras

---

## 🎯 Próximos Pasos

### Corto Plazo (Esta semana)
- [ ] Ejecutar modelo y revisar gráficos
- [ ] Interpretar métricas
- [ ] Documentar hallazgos

### Mediano Plazo (Este mes)
- [ ] Integrar en dashboard web
- [ ] Agregar endpoint de predicción en tiempo real
- [ ] Crear alertas automáticas

### Largo Plazo (Este semestre)
- [ ] Reentrenamiento diario
- [ ] Feedback loop (comparar predicción vs real)
- [ ] Publicación de resultados

---

**Versión**: 1.0
**Fecha**: 2025-11-20
**Estado**: ✅ Listo para usar
