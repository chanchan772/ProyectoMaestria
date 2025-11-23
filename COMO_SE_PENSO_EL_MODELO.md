# 🧠 CÓMO SE PENSÓ EL MODELO PREDICTIVO

Una explicación conceptual de las decisiones de diseño.

---

## 📌 Problema Original

```
SITUACIÓN:
├─ Sensores Aire2, Aire4, Aire5 → DEGRADADOS
├─ Incertidumbre en mediciones → ALTA
├─ Necesidad: Predecir PM futuro → ANTICIPARSE
└─ Objetivo cambió: Mejor que visual → MODELO PREDICTIVO
```

**Pregunta Central:**
> ¿Podemos predecir PM2.5 y PM10 1, 3, 5 horas adelante con datos de la estación de referencia (RMCAB)?

---

## 🤔 Decisión 1: ¿Por qué usar LSTM?

### Alternativas Consideradas

```
┌─────────────────────────┬────────────────┬──────────────┬────────────────┐
│ Método                  │ Ventajas       │ Desventajas  │ Vio Seleccion  │
├─────────────────────────┼────────────────┼──────────────┼────────────────┤
│ Regresión Lineal        │ Simple         │ Asume lineal │ ❌             │
│ Polinomial              │ Flexible       │ Overfitting  │ ❌             │
│ ARIMA                   │ Interpretable  │ Estacionario │ ⚠️ Fallback   │
│ Prophet (Facebook)      │ Automático     │ Menos potente│ ⚠️ Fallback   │
│ LSTM ✓                  │ Temporal       │ Complejo     │ ✅ ELEGIDO    │
│ Transformer             │ Estado arte    │ Datos 1000s  │ ⚠️ Futuro     │
└─────────────────────────┴────────────────┴──────────────┴────────────────┘
```

### Razones LSTM Elegido

```
1. CAPTURA DEPENDENCIAS TEMPORALES LARGAS

   Problema: PM hoy depende de:
   ├─ PM ayer        (12h antes)
   ├─ Viento ayer    (12h antes)
   ├─ Presión 3 días (72h antes)
   └─ Ciclo semanal  (168h antes)

   Solución LSTM:
   ├─ Celda recurrente = MEMORIA
   ├─ Gates (input/forget/output) = FILTRO INTELIGENTE
   └─ Puede aprender "olvida PM hace 3 meses, recuerda hace 2 días"

2. SIN SUPUESTOS RESTRICTIVOS

   Regresión: Asume linealidad
   ├─ PM2.5 = α + β×Temp + γ×RH
   ├─ ¿Y si relación es cuadrática?
   └─ ¿Y si depende de interacciones?

   LSTM: Aprende relaciones complejas automáticamente
   └─ "Descubre" si es lineal, polinomial, caótica, etc.

3. MANEJA ENTRADA MULTIVARIABLE NATURALMENTE

   Input:
   ├─ PM2.5 (histórico)
   ├─ Temperatura (histórico)
   └─ Humedad Relativa (histórico)

   → Todo entra simultáneamente
   → Captura interacciones automáticamente

4. TOLERA DATOS IMPERFECTOS

   Si falta un punto:
   ├─ Regresión: Se "rompe"
   └─ LSTM: Interpola implícitamente

   Si hay ruido:
   ├─ Regresión: Sensible
   └─ LSTM: Robusto (filtro recurrente)
```

---

## 🤔 Decisión 2: ¿Ventanas de 1, 3, 5 horas?

### Por qué no 24, 48, 72 horas?

```
HORIZONTE vs PREDICTIBILIDAD

La atmósfera tiene "límite de predictibilidad"
(similar a efecto mariposa)

Horizonte (h) │ Incertidumbre │ Fiabilidad │ Uso
──────────────┼───────────────┼────────────┼──────────────
1h            │ Baja          │ ✅ Alta    │ Alertas críticas
3h            │ Media         │ ✅ Buena   │ Planificación
5h            │ Media-Alta    │ ⚠️ Media   │ Tendencias
12h           │ Alta          │ ❌ Baja    │ Poco útil
24h+          │ Muy Alta      │ ❌ Muy baja│ Inútil
```

### Razón de estos horizontes

```
CICLO DIARIO DE PM2.5

24h = Ciclo completo:
├─ 05:00 - Mínimo  (inversión térmica)
├─ 14:00 - Máximo  (calentamiento)
├─ 19:00 - Caída   (mezcla vertical)
└─ 24:00 - Ciclo repite

Estrategia:
├─ 1h  → Captura cambios rápidos (tráfico, emisiones)
├─ 3h  → Captura variabilidad media (dispersión)
└─ 5h  → Captura tendencia (ciclo parcial)

No hay razón de ir más allá
└─ Error crece exponencialmente > 5h
```

---

## 🤔 Decisión 3: ¿24 pasos históricos?

### Window Size

```
WINDOW PEQUEÑO (6h)
├─ ✅ Más muestras para entrenar
├─ ❌ Pierde contexto (falta ciclo diario)
└─ Resultado: Overfitting

WINDOW IDEAL (24h) ✓
├─ ✅ Captura ciclo completo
├─ ✅ Contexto suficiente
└─ ✅ Muestras balanceadas

WINDOW GRANDE (72h)
├─ ❌ Menos muestras para entrenar
├─ ❌ Información vieja less relevante
└─ Resultado: Underfitting
```

**Fórmula empirica:**
```
W_ideal ≈ Período de ciclo principal
```

Para PM2.5: Ciclo = ~24h → Window = 24h ✓

---

## 🤔 Decisión 4: ¿Modelos Separados vs Uno Compartido?

### Enfoque Elegido: 3 Modelos Independientes

```
OPCIÓN 1: Un modelo predice todo (1h, 3h, 5h)
┌──────────────────────────┐
│ Input: 24 histórico      │
│ Output: [1h, 3h, 5h]     │
└──────────────────────────┘
Desventajas:
├─ Conflicto: Optimizar para 1h vs 5h
├─ Errores de 1h afectan a 3h y 5h
└─ Modelo trata de ser "todo" → mediocre en todo

OPCIÓN 2: Cascada (predice 1h, input a 3h, etc.)
Step1: Predice 1h
Step2: Usa predicción de Step1 → predice 3h
Step3: Usa predicción de Step2 → predice 5h
Desventajas:
├─ Errores se propagan y amplifican
├─ 5h = error de 1h + 3h + 5h
└─ Métricas irreaales

OPCIÓN 3: 3 Modelos Independientes ✓ ELEGIDO
├─ Modelo1: Predice t+1h
├─ Modelo2: Predice t+3h
├─ Modelo3: Predice t+5h
Ventajas:
├─ Cada modelo optimizado para su horizonte
├─ Errores no se propagan
├─ Métricas reales e independientes
├─ Fácil de escalar (n modelos = n horizontes)
└─ Interpretación clara
```

**Decisión justificada:**
```
✓ Claridad: Sé exactamente qué predice cada modelo
✓ Flexibilidad: Puedo entrenar solo 1h si quiero
✓ Realismo: Sin error propagación
✓ Escalabilidad: Agregar 7h es trivial
```

---

## 🤔 Decisión 5: ¿Normalizar o No?

### MinMaxScaler [0, 1]

```
¿POR QUÉ NORMALIZAR?

Problema Sin Normalizar:
├─ PM2.5: Rango 10-100 μg/m³
├─ Temperatura: Rango 15-25 °C
├─ RH: Rango 50-90 %
│
└─ Entrada a LSTM: Magnitudes muy diferentes
   ├─ LSTM asume varianzas similares
   ├─ Gradientes exploran espacio mal
   └─ Convergencia lenta o divergencia

Solución: Normalizar [0, 1]
├─ PM2.5 → [0, 1]
├─ Temp → [0, 1]
├─ RH → [0, 1]
├─ Todas en escala comparable
└─ LSTM entiende mejor

Cuidado: Mantener escaladores
├─ Para entrenar/validar: normalize
├─ Para hacer predicciones finales: inverse_transform
└─ Si pierdes escaladores → métricas sin sentido
```

**Implementado correctamente:**
```python
scaler_pm25 = MinMaxScaler()  # Separado para cada variable
scaler_temp = MinMaxScaler()
scaler_rh = MinMaxScaler()

# Entrenar
y_pred_scaled = model.predict(X)  # [0, 1]

# Revertir normalización para métricas
y_pred_real = scaler_pm25.inverse_transform(y_pred_scaled)
```

---

## 🤔 Decisión 6: ¿Validación Temporal o Random?

### Problema de Data Leakage

```
INCORRECTO: Random Split (¡COMÚN!)

Timeline:
├─ 2025-06-01 ...
├─ 2025-06-15 ← TRAIN
├─ 2025-06-20 ← TEST
├─ 2025-07-01 ← TRAIN (¡Futuro!)
└─ 2025-07-30 ← TEST

Problema:
├─ Modelo VE datos futuros en entrenamiento
├─ "Aprende a engañar" (memoriza patrones)
├─ Métricas son ILUSIÓN
└─ En producción: FALLA miserablemente

CORRECTO: Temporal Split (¡Implementado!)

Timeline:
├─ 2025-06-01 ─────────────────────┐
├─ 2025-06-15 TRAIN                 │
├─ 2025-06-30 (75%)                 │
├─ ────────────────────────────────┤
├─ 2025-07-01 TEST                  │
├─ 2025-07-30 (25%)                 ├→ Orden respetado
├─ ────────────────────────────────┘

Ventaja:
├─ Modelo SOLO ve pasado en entrenamiento
├─ TEST son datos FUTUROS al entrenamiento
├─ Simula uso real: predecir mañana
└─ Métricas son REALES y confiables
```

**Código Implementado:**
```python
split_idx = int(len(X) * 0.75)  # Índice, no random shuffle
X_train = X[:split_idx]          # Primeros 75%
X_test = X[split_idx:]           # Últimos 25%
# ¡SIN shuffle! ← CRÍTICO
```

---

## 🤔 Decisión 7: ¿Qué Métricas Usar?

### Las 4 Escogidas

```
MÉTRICA 1: RMSE (Root Mean Squared Error)
┌──────────────────────────────────────┐
│ RMSE = √[Σ(y - ŷ)² / n]             │
└──────────────────────────────────────┘

Ventajas:
├─ Penaliza errores grandes
├─ Sensible a outliers
├─ En misma unidad que variable (μg/m³)
└─ Fácil de interpretar

Desventajas:
├─ Esconde distribución de errores
└─ Outliers pueden dominar

CUÁNDO USAR: Siempre, es el "estándar"
```

```
MÉTRICA 2: MAE (Mean Absolute Error)
┌──────────────────────────────────────┐
│ MAE = Σ|y - ŷ| / n                  │
└──────────────────────────────────────┘

Ventajas:
├─ Robusto a outliers
├─ Error promedio real
├─ Fácil de explicar (en μg/m³)
└─ No penaliza excesivamente errores grandes

Desventajas:
├─ No diferencia entre -5 y +5
└─ Menos sensible a variabilidad

CUÁNDO USAR: Cuando hay outliers o valores extremos
```

```
MÉTRICA 3: R² (Coeficiente de Determinación)
┌──────────────────────────────────────┐
│ R² = 1 - (SS_res / SS_tot)           │
│ Rango: [0, 1] o negativo             │
└──────────────────────────────────────┘

¿Qué significa?
├─ R² = 0.95 → Modelo explica 95% de variación
├─ R² = 0.50 → Modelo explica 50% de variación
├─ R² = 0.00 → Modelo = predecir siempre la media
└─ R² < 0    → Modelo peor que media simple

Ventajas:
├─ Comparable entre modelos
├─ Interpretación directa: % varianza explicada
├─ Esencial para validación
└─ Adimensional [0, 1]

CUÁNDO USAR: Para comparar modelos
```

```
MÉTRICA 4: MAPE (Mean Absolute Percentage Error)
┌──────────────────────────────────────┐
│ MAPE = Σ|y - ŷ| / |y| × 100%        │
└──────────────────────────────────────┘

Ventajas:
├─ Error en % (fácil de comunicar)
├─ Independiente de escala
├─ Útil para valores con diferentes magnitudes
└─ "El modelo se equivoca en promedio 12%"

Desventajas:
├─ Indefinido si y = 0
├─ Penaliza más errores en valores pequeños
└─ Puede ser engañoso

CUÁNDO USAR: Para comunicar a no-técnicos
```

**Combinación óptima implementada:**
```python
# Complementarias:
├─ RMSE: Magnitud total de error
├─ MAE: Error promedio robusto
├─ R²: Proporción varianza explicada
└─ MAPE: Porcentaje para comunicar

# Análisis completo:
├─ Si RMSE >> MAE → hay outliers
├─ Si R² < 0.7 → modelo débil
├─ Si MAPE alto pero R² alto → escala engaña
└─ Equilibrio entre 4 métricas
```

---

## 🤔 Decisión 8: ¿Arquitectura LSTM?

### Por qué 2 capas LSTM?

```
1 CAPA LSTM
└─ Ventajas: Rápido, simple
   Desventajas: Poca capacidad (puede no aprender patrones)

2 CAPAS LSTM ✓ ELEGIDO
├─ Layer 1: Captura patrones corto plazo (horas)
├─ Layer 2: Captura patrones largo plazo (días)
└─ Combinación: Flexible

3+ CAPAS LSTM
├─ Ventajas: Mayor capacidad
├─ Desventajas: Overfitting, lento
└─ Para nuestros datos: Innecesario
```

### Tamaño de capas: 64 → 32 → 16

```
DISEÑO PIRAMIDAL (Funnel)

Input (24 × 3 = 72)
    ↓
LSTM 64 neuronas
    ↓ (feature extraction)
LSTM 32 neuronas
    ↓ (abstracción)
Dense 16 neuronas
    ↓ (compresión)
Output 1 neurona
    ↓
Predicción

Justificación:
├─ Cada capa reduce dimensionalidad
├─ Permite feature learning jerárquico
├─ 64→32→16 es poder computacional decreciente
├─ Alternativa: 32→32→32 (pero menos flexible)
└─ Alternativa: 128→64→32 (pero overfitting)
```

### Dropout 0.2

```
¿POR QUÉ DROPOUT?

Sin Dropout:
├─ Modelo memoriza datos
├─ Co-adaptación de neuronas
└─ Overfitting garantizado

Con Dropout 0.2:
├─ Durante entrenamiento: desactiva 20% neuronas aleatoriamente
├─ Fuerza red a ser robusta
├─ Generalización mejorada
└─ Regularización efectiva

Dropout 0.2 (20%)
├─ Conservador: Mantiene 80% de computación
├─ Evita underfitting: No poda demasiado
├─ Estándar: Usado en mayoría de redes
└─ Valores típicos: 0.2-0.5
```

---

## 🤔 Decisión 9: ¿Early Stopping?

### Monitoreo de Validación

```
SIN EARLY STOPPING (Entrenamiento crudo)

Loss
  │
  │   ●●●●
  │●●●    ●●●   ← Empieza overfitting aquí
  │           ●●●●
  ├──────────────────→ Épocas
  0         50

Problema:
├─ Continúa entrenando más allá del óptimo
├─ Validation loss sube
├─ Test performance empeora
└─ Desperdicia tiempo

CON EARLY STOPPING (Inteligente)

Loss
  │
  │   ●●●●
  │●●●    ●●  ← STOP aquí
  │
  ├──────────────→ Épocas
  0    ~30

Implementado:
├─ Monitor: val_loss
├─ Patience: 10 (esperamos 10 épocas sin mejoría)
├─ Restore best: Guarda mejor modelo
└─ Resultado: ~30 épocas vs 50, mejor generalización
```

---

## 📊 Síntesis: Decisiones Clave

| Decisión | Opción | Razón |
|----------|--------|-------|
| 1. Algoritmo | LSTM | Captura temporal, flexible |
| 2. Horizontes | 1, 3, 5h | Ciclo PM, límite predictibilidad |
| 3. Window | 24h | Captura ciclo diario completo |
| 4. Modelos | 3 independientes | Sin propagación errores |
| 5. Normalización | MinMax [0,1] | Escala comparable, convergencia |
| 6. Validación | Temporal split | Evita data leakage |
| 7. Métricas | 4 métricas | Análisis completo |
| 8. Capas | 2 LSTM + Dense | Balance capacidad-regularización |
| 9. Early Stop | Sí (patience=10) | Generalización automática |

---

## ✅ Resultado

Un modelo **robusto, interpretable y práctico** que:
- ✅ Predice PM 1, 3, 5 horas adelante
- ✅ Captura patrones no-lineales
- ✅ Se regulariza automáticamente
- ✅ Evita data leakage
- ✅ Genera 4 métricas complementarias
- ✅ Es replicable y mejora

---

**Nota:** Cada decisión fue deliberada y justificada. No hay "magia", solo decisiones informadas basadas en principios de ML y características del problema (series de tiempo de contaminación).
