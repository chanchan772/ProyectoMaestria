# 🔮 OBJETIVO 2: MODELO PREDICTIVO DE SERIES DE TIEMPO

## 📋 Descripción General

El **Objetivo 2** cambió de una visualización interactiva a un **modelo predictivo de series de tiempo** que predice PM2.5 y PM10 con 1, 3 y 5 horas de anticipación.

### Justificación
Los sensores de bajo costo (Aire2, Aire4, Aire5) tienen considerable desgaste y degradación en el tiempo. Para compensar esto, se implementó un modelo predictivo basado en:
- **Datos reales de RMCAB** (estación de referencia de Bogotá)
- **Variables ambientales** (temperatura y humedad relativa)
- **Arquitectura LSTM** (redes neuronales recurrentes)

---

## 🏗️ Arquitectura del Modelo

### 1. **Modelo Base: LSTM (Long Short-Term Memory)**

```
┌─────────────────────────────────────────────────┐
│  ENTRADA (24 pasos temporales)                  │
│  ├─ PM2.5/PM10 histórico                        │
│  ├─ Temperatura (simulada)                      │
│  └─ Humedad Relativa (simulada)                 │
└─────────────┬───────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────┐
│  LSTM Layer 1 (64 neuronas)                     │
│  ├─ Captures temporal dependencies              │
│  └─ Return sequences para siguiente capa        │
└─────────────┬───────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────┐
│  Dropout (0.2) - Regularización                 │
└─────────────┬───────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────┐
│  LSTM Layer 2 (32 neuronas)                     │
│  └─ Procesa patrones de más alto nivel          │
└─────────────┬───────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────┐
│  Dropout (0.2) - Regularización                 │
└─────────────┬───────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────┐
│  Dense Layer (16 neuronas, ReLU)                │
│  └─ Abstracción final                           │
└─────────────┬───────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────────────────┐
│  Output Layer (1 neurona)                       │
│  └─ Predicción: PM2.5/PM10 (μg/m³)             │
└─────────────────────────────────────────────────┘
```

### 2. **Ventanas Temporales Múltiples**

El modelo entrena **3 modelos independientes** para predecir:
- **+1 hora** adelante
- **+3 horas** adelante
- **+5 horas** adelante

```
Tiempo Real:  ├─ Ventana histórica (24h) ─┤ ├─ Predicción ─┤
              t-24h                        t  t+1h  t+3h  t+5h
```

---

## 📊 Preparación de Datos

### 3.1 Fuentes de Datos

| Componente | Fuente | Tipo | Tratamiento |
|-----------|--------|------|-------------|
| **PM2.5 Referencia** | RMCAB (CSV cache) | Real | Sin cambios |
| **PM10 Referencia** | RMCAB (CSV cache) | Real | Sin cambios |
| **Temperatura** | Simulada | Sintético | Patrón sinusoidal + ruido |
| **Humedad Relativa** | Simulada | Sintético | Patrón inverso a temperatura |

### 3.2 Flujo de Preprocesamiento

```
1. CARGAR DATOS
   ├─ PostgreSQL: Sensores (Aire2, Aire4, Aire5)
   ├─ CSV: RMCAB (pm25_ref, pm10_ref)
   └─ Generar: Temperatura y Humedad

2. LIMPIAR DATOS
   ├─ Eliminar valores NaN
   ├─ Ordenar por timestamp
   └─ Verificar rango suficiente

3. NORMALIZAR (MinMaxScaler: [0, 1])
   ├─ Escalador PM2.5 para objetivo 1
   ├─ Escalador PM10 para objetivo 2
   ├─ Escalador Temperatura
   └─ Escalador Humedad Relativa

4. CREAR SECUENCIAS (ventana deslizante)
   ├─ Input: 24 pasos históricos [PM, Temp, RH]
   ├─ Output: Predicción en t+1, t+3, t+5
   └─ Forma: (muestras, 24, 3)

5. DIVIDIR DATOS
   ├─ Entrenamiento: 75% (respeta orden temporal)
   ├─ Prueba: 25% (datos futuros)
   └─ Sin mezcla para validez temporal
```

### 3.3 Ejemplo de Secuencia

```
Entrada (X):
Time    PM2.5   Temp   RH
t-24h   25.3    18.2   75%
t-23h   24.8    18.5   74%
...
t-1h    27.1    22.3   68%

Salidas (y):
t+1h  → 28.5  (predicción 1 hora)
t+3h  → 30.2  (predicción 3 horas)
t+5h  → 31.8  (predicción 5 horas)
```

---

## 🧠 Entrenamiento del Modelo

### 4.1 Configuración Hiperparámetros

```python
# Arquitectura
LSTM_Layer1 = 64 neuronas
LSTM_Layer2 = 32 neuronas
Dense_Layer = 16 neuronas
Dropout = 0.2 (20% de neuronas desactivadas)

# Optimización
Optimizador: Adam
Learning Rate: 0.001
Función Pérdida: MSE (Mean Squared Error)
Métrica: MAE (Mean Absolute Error)

# Entrenamiento
Épocas Máximas: 50
Batch Size: 8
Early Stopping: 10 épocas sin mejoría
Validación: 25% del conjunto de entrenamiento
```

### 4.2 Proceso de Entrenamiento

```
Para cada Paso (1h, 3h, 5h):
  ├─ Crear modelo LSTM nuevo
  ├─ Compilar con Adam optimizer
  ├─ Entrenar en datos entrenamiento
  ├─ Validar en datos prueba
  ├─ Early stopping si no hay mejoría
  └─ Guardar mejor modelo

Tiempo estimado: 5-10 minutos (depende de datos)
```

### 4.3 Regularización (Prevenir Overfitting)

| Técnica | Parámetro | Efecto |
|---------|-----------|--------|
| **Dropout** | 0.2 | Desactiva 20% neuronas aleatoriamente |
| **Early Stopping** | patience=10 | Detiene si no mejora validación |
| **Split Temporal** | 75/25 | Evita data leakage |

---

## 📈 Evaluación del Modelo

### 5.1 Métricas de Efectividad

#### **RMSE (Root Mean Squared Error)**
```
RMSE = √[Σ(y_true - y_pred)² / n]

→ Mide error promedio en escala original (μg/m³)
→ Penaliza más errores grandes
→ Objetivo: Minimizar (valores bajos son mejores)

Interpretación:
  RMSE < 5   = Excelente predicción
  RMSE 5-10  = Buena predicción
  RMSE > 15  = Predicción débil
```

#### **MAE (Mean Absolute Error)**
```
MAE = Σ|y_true - y_pred| / n

→ Error promedio absoluto (μg/m³)
→ Más robusto a outliers que RMSE
→ Objetivo: Minimizar

Interpretación:
  MAE = 3 μg/m³ significa:
  En promedio, el modelo se equivoca ~3 μg/m³
```

#### **R² (Coeficiente de Determinación)**
```
R² = 1 - (SS_res / SS_tot)

→ Proporción de varianza explicada por modelo [0, 1]
→ Comparación con baseline (media simple)
→ Objetivo: Maximizar (cercano a 1)

Interpretación:
  R² = 0.95  = Explica 95% de variación (excelente)
  R² = 0.80  = Explica 80% de variación (bueno)
  R² = 0.50  = Explica 50% de variación (mediocre)
  R² < 0     = Peor que predecir siempre la media
```

#### **MAPE (Mean Absolute Percentage Error)**
```
MAPE = Σ|y_true - y_pred| / |y_true| × 100%

→ Error porcentual promedio
→ Útil para valores con diferentes escalas
→ Objetivo: Minimizar

Interpretación:
  MAPE = 10% = En promedio, error del 10%
  MAPE = 25% = En promedio, error del 25%
```

### 5.2 Tabla de Resultados Esperados

```
Métrica    1h Adelante    3h Adelante    5h Adelante
───────────────────────────────────────────────────
RMSE       3-6 μg/m³      6-10 μg/m³     10-15 μg/m³
MAE        2-4 μg/m³      4-7 μg/m³      7-12 μg/m³
R²         0.85-0.95      0.75-0.88      0.60-0.80
MAPE       8-15%          12-22%         18-30%
```

**Nota**: Los valores empeoran conforme aumenta el horizonte de predicción (máxima entropía).

---

## 🔧 Implementación Técnica

### 6.1 Estructura de Archivos

```
fase 4/
├── modules/
│   ├── data_processor.py          # Carga datos RMCAB
│   ├── calibration.py             # Calibración sensores
│   ├── visualization.py           # Gráficos
│   └── predictive_model.py        # ← NUEVO: Modelo LSTM
├── app.py                         # Flask con endpoints
├── train_predictor.py             # ← NUEVO: Script standalone
├── requirements.txt               # Dependencias actualizadas
└── results/
    ├── predictive_metrics.csv     # Tabla de métricas
    ├── predictions_PM25.png       # Gráficos PM2.5
    ├── predictions_PM10.png       # Gráficos PM10
    └── steps_comparison.png       # Comparación pasos
```

### 6.2 Clases Principales

#### **TimeSeriesPreprocessor**
```python
class TimeSeriesPreprocessor:
    """Prepara datos para LSTM"""

    def __init__(lookback_window=24, forecast_steps=[1,3,5])
    def prepare_data(df, target_column, include_features)
        → Retorna: X_train, X_test, y_train, y_test
```

#### **LSTMPredictor**
```python
class LSTMPredictor:
    """Entrena y predice con LSTM"""

    def build_model(input_shape)
        → Crea arquitectura LSTM
    def train(X_train, y_train, X_test, y_test)
        → Entrena modelo
    def predict(X_test, y_test_true, scaler)
        → Realiza predicciones + métricas
```

#### **PredictiveModelPipeline**
```python
class PredictiveModelPipeline:
    """Orquesta todo el flujo"""

    def train_and_evaluate(merged_df, output_dir)
        → Ejecuta pipeline completo
        → Genera reportes y gráficos
```

---

## 🚀 Cómo Usar

### 7.1 Instalación de Dependencias

```bash
# En la carpeta fase 4/
pip install -r requirements.txt

# Principales librerías agregadas:
# - tensorflow>=2.10.0  (LSTM)
# - matplotlib>=3.5.0   (gráficos)
# - seaborn>=0.12.0     (visualización)
# - statsmodels>=0.13.0 (ARIMA fallback)
```

### 7.2 Ejecución Opción 1: Script Standalone

```bash
# En carpeta fase 4/
python train_predictor.py

# Salida:
# ✓ Carga datos de PostgreSQL
# ✓ Carga RMCAB desde CSV
# ✓ Entrena modelo LSTM
# ✓ Genera gráficos y métricas
```

### 7.3 Ejecución Opción 2: API REST

```bash
# Iniciar servidor
python app.py

# En otra terminal o cliente HTTP:

# 1. Entrenar modelo
POST http://localhost:5000/api/objetivo2/train-predictor

# Respuesta:
{
  "status": "success",
  "results": {
    "pm25": {
      "1": {"rmse": 4.2, "mae": 3.1, "r2": 0.92, "mape": 12.3},
      "3": {"rmse": 7.1, "mae": 5.2, "r2": 0.85, "mape": 18.5},
      "5": {"rmse": 10.3, "mae": 7.8, "r2": 0.72, "mape": 26.1}
    },
    "pm10": {...}
  }
}

# 2. Obtener métricas
GET http://localhost:5000/api/objetivo2/metrics
```

### 7.4 Salida Generada

```
results/
├── predictive_metrics.csv
│   Contaminante, Paso, RMSE, MAE, R², MAPE
│   PM2.5,1,4.2,3.1,0.92,12.3
│   PM2.5,3,7.1,5.2,0.85,18.5
│   PM2.5,5,10.3,7.8,0.72,26.1
│   PM10,1,5.1,4.0,0.88,15.2
│   ...
│
├── predictions_PM25.png
│   - 3 gráficos scatter: Valor Real vs Predicho
│   - Para cada paso (1h, 3h, 5h)
│   - Con R² y RMSE en títulos
│
├── predictions_PM10.png
│   - Idem PM2.5
│
└── steps_comparison.png
    - 4 gráficos de línea
    - RMSE, MAE, R², MAPE vs Pasos
    - Comparación PM2.5 vs PM10
```

---

## 📚 Metodología: Paso a Paso

### 8.1 Metodología de Entrenamiento

```
FASE 1: PREPARACIÓN
├─ 1.1 Cargar datos reales (PostgreSQL + CSV)
├─ 1.2 Limpiar valores NaN
├─ 1.3 Simular temperatura/humedad
└─ 1.4 Verificar integridad datos

FASE 2: NORMALIZACIÓN
├─ 2.1 Crear escaladores MinMaxScaler
├─ 2.2 Escalar todas las variables [0,1]
├─ 2.3 Guardar escaladores para inverse_transform
└─ 2.4 Verificar rango normalizado

FASE 3: SECUENCIACIÓN
├─ 3.1 Crear ventanas deslizantes (24 pasos)
├─ 3.2 Generar outputs para t+1, t+3, t+5
├─ 3.3 Verificar forma (muestras, timesteps, features)
└─ 3.4 Split 75/25 respetando orden temporal

FASE 4: MODELADO
├─ 4.1 Construir arquitectura LSTM
├─ 4.2 Compilar con optimizer Adam
├─ 4.3 Para cada paso (1h, 3h, 5h):
│      ├─ Entrenar modelo
│      ├─ Monitorear validación
│      ├─ Aplicar early stopping
│      └─ Guardar mejor modelo
└─ 4.4 Verificar convergencia

FASE 5: EVALUACIÓN
├─ 5.1 Predicción en conjunto prueba
├─ 5.2 Desnormalizar predicciones
├─ 5.3 Calcular 4 métricas (RMSE, MAE, R², MAPE)
├─ 5.4 Analizar patrones de error
└─ 5.5 Generar reportes

FASE 6: VISUALIZACIÓN
├─ 6.1 Gráficos scatter (Real vs Predicho)
├─ 6.2 Gráficos de línea (Comparación pasos)
├─ 6.3 Exportar CSV de métricas
└─ 6.4 Guardar con alta resolución (300 DPI)
```

### 8.2 Validación Temporal (Data Leakage Prevention)

```
PROBLEMA COMÚN: Data Leakage
┌──────────────────────────────────┐
│ Si mezclamos datos:              │
│ Train: Mix de primeras y últimas │
│ Test: Also mix                   │
│ → Modelo aprende "trampas"       │
│ → Métricas artificialmente altas  │
└──────────────────────────────────┘

SOLUCIÓN IMPLEMENTADA: Respeto Temporal
┌─────────────────────────────────┐
│ Test (25%)                       │
│ ├─ Datos más recientes          │
│ └─ Predice futuro del modelo    │
├─────────────────────────────────┤
│ Train (75%)                      │
│ ├─ Datos más antiguos           │
│ └─ Modelo aprende pasado        │
└─────────────────────────────────┘

→ Split temporal es CRUCIAL para series
→ Evita que modelo vea "el futuro"
→ Métricas representan valor real
```

---

## 📊 Análisis de Resultados

### 9.1 ¿Qué Significan los Resultados?

#### Escenario 1: Modelo Excelente ✅
```
RMSE = 3-5 μg/m³
R²   = 0.90-0.95
MAPE = 10-15%

→ Modelo es muy preciso
→ Puede reemplazar sensores degradados
→ Error pequeño vs magnitud de contaminación
```

#### Escenario 2: Modelo Aceptable ⚠️
```
RMSE = 8-12 μg/m³
R²   = 0.75-0.85
MAPE = 20-25%

→ Modelo es útil pero con margen
→ Recomendable para alertas tempranas
→ Requiere validación adicional
```

#### Escenario 3: Modelo Débil ❌
```
RMSE = > 15 μg/m³
R²   = < 0.60
MAPE = > 30%

→ Modelo no es confiable
→ Requiere más datos o mejor arquitectura
→ Considerar features adicionales
```

### 9.2 Degración Esperada por Paso

**Es NORMAL que la precisión disminuya:**

```
Efecto de Horizonte (Lyapunov Chaos)
├─ 1h:   RMSE = 4 μg/m³  (Alta precisión)
├─ 3h:   RMSE = 8 μg/m³  (50% más error)
└─ 5h:  RMSE = 12 μg/m³ (200% más error)

Razón:
├─ Perturbaciones pequeñas se amplifican
├─ Incertidumbre crece exponencialmente
└─ Máximo horizonte ~24-48h para PM
```

---

## 🔬 Mejoras Futuras

### Variaciones Posibles:

1. **Agregar Features Adicionales**
   ```
   - Presión atmosférica
   - Velocidad del viento
   - Dirección del viento
   - Radiación solar
   ```

2. **Arquitecturas Alternativas**
   ```
   - GRU (más rápido que LSTM)
   - Attention mechanisms
   - Transformer (estado del arte)
   - ARIMA (más interpretable)
   - Prophet (Facebook)
   ```

3. **Mejoras de Validación**
   ```
   - Cross-validation temporal
   - Bootstrap del error
   - Intervalos de confianza
   - Análisis de residuos
   ```

4. **Deployment**
   ```
   - Reentrenamiento diario
   - Monitoreo en tiempo real
   - Alertas automáticas
   - API para móviles
   ```

---

## 🎯 Conclusión

El modelo predictivo LSTM proporciona:

✅ **Predicciones 1, 3, 5 horas adelante**
✅ **Métricas cuantificables (RMSE, MAE, R², MAPE)**
✅ **Compensación para sensores degradados**
✅ **Alertas tempranas de contaminación**
✅ **Base para aplicaciones en tiempo real**

**Archivos clave:**
- `modules/predictive_model.py` - Implementación
- `train_predictor.py` - Ejecución standalone
- `app.py` - Integración API REST
- `results/` - Gráficos y métricas

---

## 📞 Soporte

Para errores o preguntas:
1. Verificar conexión a PostgreSQL
2. Verificar archivo `data_rmcab/rmcab_data.csv`
3. Revisar logs en consola
4. Consultar `DATOS_REALES_FLUJO.md` para fuentes de datos

---

*Documento generado: 2025-11-20*
*Versión: 1.0*
