# 📑 ÍNDICE - OBJETIVO 2: MODELO PREDICTIVO

## 🎯 ¿Por dónde empiezo?

### 🚀 **Quiero ejecutar rápido (5 minutos)**
→ Lee: **README_OBJETIVO2.md**
- Inicio rápido con `python train_predictor.py`
- Verificar archivos generados
- Interpretar resultados básicos

### 📊 **Quiero entender los resultados (15 minutos)**
→ Lee: **RESUMEN_EJECUTIVO_OBJETIVO2.md**
- Qué se entregó
- Tabla de métricas esperadas
- Cómo leer RMSE, MAE, R², MAPE

### 🔬 **Quiero conocer técnicamente el modelo (30 minutos)**
→ Lee: **OBJETIVO_2_MODELO_PREDICTIVO.md**
- Arquitectura LSTM completa
- Flujo de preparación de datos
- Métricas explicadas en detalle
- Validación temporal

### 🧠 **Quiero entender por qué se hizo así (20 minutos)**
→ Lee: **COMO_SE_PENSO_EL_MODELO.md**
- Por qué LSTM vs alternativas
- Por qué 1, 3, 5 horas
- Todas las decisiones justificadas

---

## 📚 Documentos Disponibles

### 1️⃣ **README_OBJETIVO2.md**
**Tipo:** Inicio rápido
**Duración:** 5 minutos
**Para quién:** Usuarios finales

**Contiene:**
- ✅ Instrucciones de ejecución
- ✅ Interpretación de resultados
- ✅ FAQ y solución de errores
- ✅ Checklist de validación

**Inicio:** `python train_predictor.py`

---

### 2️⃣ **RESUMEN_EJECUTIVO_OBJETIVO2.md** (Este documento)
**Tipo:** Resumen ejecutivo
**Duración:** 15 minutos
**Para quién:** Stakeholders, supervisores

**Contiene:**
- ✅ Qué se entregó (componentes)
- ✅ Metodología resumida
- ✅ Resultados esperados (tabla)
- ✅ Evaluación del modelo
- ✅ Impacto práctica
- ✅ Próximos pasos

---

### 3️⃣ **OBJETIVO_2_MODELO_PREDICTIVO.md**
**Tipo:** Documentación técnica completa
**Duración:** 30 minutos (lectura)
**Para quién:** Desarrolladores, científicos de datos

**Contiene:**
- ✅ Arquitectura LSTM con diagramas
- ✅ Preparación de datos paso a paso
- ✅ Explica cada métrica matemáticamente
- ✅ Validación temporal y data leakage
- ✅ Mejoras futuras
- ✅ Ejemplos de secuencias
- ✅ Guía de uso completa

---

### 4️⃣ **COMO_SE_PENSO_EL_MODELO.md**
**Tipo:** Justificación de diseño
**Duración:** 20 minutos
**Para quién:** Revisores, auditores, futuros mejoradores

**Contiene:**
- ✅ Decisión 1: ¿Por qué LSTM?
- ✅ Decisión 2: ¿Por qué 1, 3, 5 horas?
- ✅ Decisión 3: ¿Por qué 24 pasos?
- ✅ Decisión 4: ¿Modelos independientes?
- ✅ Decisión 5: ¿Normalización?
- ✅ Decisión 6: ¿Validación temporal?
- ✅ Decisión 7: ¿Qué métricas?
- ✅ Decisión 8: ¿Qué arquitectura?
- ✅ Decisión 9: ¿Early stopping?
- ✅ Tabla de síntesis

---

## 🗂️ Archivos de Código

### Nuevos archivos creados

```
modules/
├── predictive_model.py              (Implementación LSTM)
│   ├─ TimeSeriesPreprocessor        (Preparación datos)
│   ├─ LSTMPredictor                 (Modelo + entrenamiento)
│   └─ PredictiveModelPipeline       (Orquestación completa)
│
├── data_processor.py                (Modificado mínimamente)
│   ├─ load_real_data()              (PostgreSQL)
│   ├─ load_rmcab_from_csv()         (CSV cache)
│   └─ merge_data()                  (Fusión)
│
└── (calibration.py, visualization.py sin cambios)

app.py                               (Modificado)
├─ POST /api/objetivo2/train-predictor
├─ GET /api/objetivo2/metrics
└─ (endpoints objetivo1 sin cambios)

train_predictor.py                   (Script standalone nuevo)
├─ Ejecuta pipeline completo
├─ Sin necesidad de Flask
└─ Genera resultados en results/

requirements.txt                     (Actualizado)
├─ tensorflow>=2.10.0
├─ keras>=2.10.0
├─ matplotlib>=3.5.0
├─ seaborn>=0.12.0
├─ statsmodels>=0.13.0
└─ joblib>=1.2.0
```

---

## 📊 Archivos de Resultado

Generados después de ejecutar `python train_predictor.py`:

```
results/
├── predictive_metrics.csv
│   Tabla con todas las métricas:
│   Contaminante, Paso, RMSE, MAE, R², MAPE
│
├── predictions_PM25.png
│   3 scatter plots (1h, 3h, 5h)
│   Real vs Predicho
│
├── predictions_PM10.png
│   3 scatter plots (1h, 3h, 5h)
│   Real vs Predicho
│
└── steps_comparison.png
    4 line plots:
    RMSE, MAE, R², MAPE vs Pasos
    PM2.5 vs PM10
```

---

## 🔄 Flujo de Lectura Recomendado

### Opción A: "Quiero usar esto ahora"
```
1. README_OBJETIVO2.md                (5 min)
   └─ python train_predictor.py
2. Ver results/predictive_metrics.csv (2 min)
3. Ver PNG de gráficos              (3 min)
───────────────────────────────────────
TOTAL: 10 minutos
```

### Opción B: "Quiero entender qué se hizo"
```
1. RESUMEN_EJECUTIVO_OBJETIVO2.md     (15 min)
2. COMO_SE_PENSO_EL_MODELO.md         (20 min)
3. README_OBJETIVO2.md                (5 min)
4. Ejecutar python train_predictor.py (10 min)
───────────────────────────────────────
TOTAL: 50 minutos
```

### Opción C: "Quiero conocer todo en detalle"
```
1. RESUMEN_EJECUTIVO_OBJETIVO2.md     (15 min)
2. OBJETIVO_2_MODELO_PREDICTIVO.md    (30 min)
3. COMO_SE_PENSO_EL_MODELO.md         (20 min)
4. README_OBJETIVO2.md                (5 min)
5. Analizar código: modules/predictive_model.py
6. Ejecutar y revisar resultados      (10 min)
───────────────────────────────────────
TOTAL: ~90 minutos (recomendado dedicarle tiempo)
```

---

## 🎓 Vocabulario Clave

Si encuentras términos no familiares:

| Término | Definición | Documento |
|---------|-----------|-----------|
| **LSTM** | Red neuronal con memoria para series | OBJETIVO_2 |
| **RMSE** | Error cuadrático medio | OBJETIVO_2 |
| **MAE** | Error absoluto medio | OBJETIVO_2 |
| **R²** | Proporción varianza explicada | OBJETIVO_2 |
| **MAPE** | Error porcentual | OBJETIVO_2 |
| **Normalización** | Escalar datos a [0,1] | OBJETIVO_2 |
| **Data Leakage** | Ver futuro en entrenamiendo | COMO_SE_PENSO |
| **Early Stopping** | Detener entrenamiento si no mejora | COMO_SE_PENSO |
| **Dropout** | Desactivar neuronas (regularización) | COMO_SE_PENSO |
| **Validación temporal** | Respetar orden cronológico | OBJETIVO_2 |

---

## ✅ Verificación Rápida

¿Están todos los archivos?

```bash
# En carpeta: fase 4/

# Código
modules/predictive_model.py          ✓ Existe
app.py                               ✓ Modificado
train_predictor.py                   ✓ Nuevo
requirements.txt                     ✓ Actualizado

# Documentación
README_OBJETIVO2.md                  ✓ Nuevo
RESUMEN_EJECUTIVO_OBJETIVO2.md      ✓ Nuevo
OBJETIVO_2_MODELO_PREDICTIVO.md     ✓ Nuevo
COMO_SE_PENSO_EL_MODELO.md          ✓ Nuevo
INDICE_OBJETIVO2.md                 ✓ Este archivo
```

---

## 🚀 Quickstart (30 segundos)

```bash
# En carpeta: fase 4/

# 1. Instalar
pip install -r requirements.txt

# 2. Ejecutar
python train_predictor.py

# 3. Ver resultados
# Abrir: results/predictive_metrics.csv
#        results/predictions_PM25.png
```

---

## 📞 ¿Tienes dudas?

### Sobre CÓMO EJECUTAR
→ **README_OBJETIVO2.md** (Sección "Inicio Rápido")

### Sobre QUÉ ES EL MODELO
→ **RESUMEN_EJECUTIVO_OBJETIVO2.md** (Sección "Metodología")

### Sobre CÓMO INTERPRETAR RESULTADOS
→ **RESUMEN_EJECUTIVO_OBJETIVO2.md** (Sección "Evaluación del Modelo")

### Sobre DETALLES TÉCNICOS
→ **OBJETIVO_2_MODELO_PREDICTIVO.md** (Toda la documentación)

### Sobre POR QUÉ FUNCIONA ASÍ
→ **COMO_SE_PENSO_EL_MODELO.md** (Cada decisión explicada)

### Sobre SOLUCIONAR ERRORES
→ **README_OBJETIVO2.md** (Sección "Si Hay Errores")

---

## 📈 Tus Próximos Pasos

1. [ ] Leer documento apropiado (arriba)
2. [ ] Ejecutar `python train_predictor.py`
3. [ ] Revisar `results/predictive_metrics.csv`
4. [ ] Analizar gráficos PNG
5. [ ] Documentar hallazgos
6. [ ] Presentar resultados

---

**Bienvenido al Objetivo 2: Modelo Predictivo**

*Fecha: 2025-11-20*
*Estado: ✅ Completo y listo para usar*
