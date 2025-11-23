# MODELO PREDICTIVO MEJORADO - GUIA COMPLETA

## 📋 RESUMEN EJECUTIVO

Se implemento un modelo mejorado basado en **XGBoost + Features Temporales** que:
- **Entrena UNA SOLA VEZ** y guarda el modelo
- **Proximas ejecuciones** cargan el modelo sin reentrenar
- **Genera graficos claros** comparando predicciones vs reales
- **Explica el estado** en cada paso del proceso

---

## 🔄 FLUJO DE TRABAJO

### PRIMERA EJECUCION (Entrenamiento)
```
1. Ejecutas: python app.py
2. Accedes: http://127.0.0.1:5000/objetivo-2
3. Haces clic: "Entrenar Modelo"
   ↓
   ESTADO: Cargando datos RMCAB (8760 registros, TODO 2025)
   ↓
   ESTADO: Agregando features temporales (hora, dia semana, mes, estacion)
   ↓
   ESTADO: Entrenando XGBoost para PM2.5 (1-2 min)
   ↓
   ESTADO: Entrenando XGBoost para PM10 (1-2 min)
   ↓
   ESTADO: Generando graficos de evaluacion
   ↓
   RESULTADO: Modelo guardado en /models/
   - xgboost_pm25.pkl
   - xgboost_pm10.pkl
   - training_info.json
```

### PROXIMAS EJECUCIONES (Carga del modelo)
```
1. Ejecutas: python app.py
2. Accedes: http://127.0.0.1:5000/objetivo-2
   ↓
   AUTOMATICO: Sistema detecta modelo entrenado
   ↓
   RESULTADO: Modelo cargado (toma <1 segundo)
   ↓
   LISTO: Para hacer predicciones sin reentrenar
```

---

## 🎯 QUE SE ENTRENA

### MODELO 1: PM2.5 (Particulas Finas)
- **Tipo**: XGBoost Regressor
- **Entrada**: 24 horas de histórico + 6 features temporales
- **Salida**: Predicción de PM2.5 para siguiente hora
- **Archivo**: `/models/xgboost_pm25.pkl`

### MODELO 2: PM10 (Particulas Gruesas)
- **Tipo**: XGBoost Regressor
- **Entrada**: 24 horas de histórico + 6 features temporales
- **Salida**: Predicción de PM10 para siguiente hora
- **Archivo**: `/models/xgboost_pm10.pkl`

---

## 📊 FEATURES AGREGADOS

El modelo mejorando NO solo usa histórico de PM2.5/PM10, sino que agrega:

| Feature | Rango | Proposito |
|---------|-------|-----------|
| Hora (hour) | 0-23 | Captura ciclo diario |
| Dia semana (dayofweek) | 0-6 | Captura patrones semanales |
| Mes (month) | 1-12 | Captura estacionalidad anual |
| Estacion (season) | 0-3 | Captura ciclos de 3 meses |
| Seno Hora (hour_sin) | -1 a 1 | Periodicidad suave 24h |
| Coseno Hora (hour_cos) | -1 a 1 | Periodicidad suave 24h |
| Seno Dia (day_sin) | -1 a 1 | Periodicidad suave 7d |
| Coseno Dia (day_cos) | -1 a 1 | Periodicidad suave 7d |

---

## 📈 GRAFICOS DE EVALUACION

Se generan 4 graficos por contaminante:

### 1. SCATTER PLOT (Real vs Predicho)
```
Eje X: Valores Reales (μg/m³)
Eje Y: Valores Predichos (μg/m³)

Linea roja punteada = Predicción perfecta (y=x)
Nube de puntos = Dispersión de predicciones

Interpretacion:
- Si puntos están en la linea roja → Buena predicción
- Si puntos están dispersos → Malas predicciones
- Cuanto MAS CERCA A LA LINEA, MEJOR
```

### 2. EVOLUCION TEMPORAL
```
Eje X: Tiempo (primeras 200 muestras del test)
Eje Y: Concentración (μg/m³)

Linea azul = Valores reales (observed)
Linea roja = Valores predichos (model output)

Interpretacion:
- Si lineas siguen tendencia similar → Captura patrones
- Si lineas están muy separadas → Underfitting
```

### 3. DISTRIBUCION DE RESIDUOS
```
Eje X: Residuos (Real - Predicho)
Eje Y: Frecuencia

Linea roja = Media de residuos (deberia estar cerca a 0)

Interpretacion:
- Si centrado en 0 → No hay sesgo
- Si desviado → Hay error sistematico
- Si concentrado → Predice bien
- Si disperso → Mucha variabilidad
```

### 4. METRICAS TEXTUALES
```
R²:   Proporción de varianza explicada (0-1, mayor es mejor)
RMSE: Error cuadrático medio (μg/m³, menor es mejor)
MAE:  Error absoluto medio (μg/m³, menor es mejor)
MAPE: Error porcentual (%, menor es mejor)
```

---

## 📁 ARCHIVOS GENERADOS

### Modelos (guardados UNA SOLA VEZ)
```
/models/
├── xgboost_pm25.pkl          ← Modelo entrenado PM2.5
├── xgboost_pm10.pkl          ← Modelo entrenado PM10
├── scaler_pm25.pkl           ← Normalizador PM2.5
├── scaler_pm10.pkl           ← Normalizador PM10
└── training_info.json        ← Info del entrenamiento
```

### Graficos de Evaluacion
```
/static/results/
├── evaluation_pm25.png       ← 4 graficos para PM2.5
└── evaluation_pm10.png       ← 4 graficos para PM10
```

---

## ⏱️ TIEMPOS ESPERADOS

### PRIMERA EJECUCION
- Carga de datos: 5 segundos
- Features temporales: 10 segundos
- Entrenamiento PM2.5: 60-90 segundos
- Entrenamiento PM10: 60-90 segundos
- Graficos: 20 segundos
- **TOTAL**: 3-5 minutos

### PROXIMAS EJECUCIONES
- Carga de modelo: <1 segundo
- **TOTAL**: Instantaneo

---

## ✅ CRITERIOS DE EXITO

### Graficos PM2.5
- [ ] Scatter plot: Puntos cercanos a la linea roja (±3 μg/m³)
- [ ] Temporal: Lineas azul y roja siguen tendencias similares
- [ ] Residuos: Centrado en 0, sin tendencias
- [ ] R² > 0.15 (mejora respecto a 0.02-0.10 anterior)

### Graficos PM10
- [ ] Scatter plot: Puntos cercanos a la linea roja (±5 μg/m³)
- [ ] Temporal: Lineas siguen tendencias similares
- [ ] Residuos: Distribucion normal alrededor de 0
- [ ] R² > 0.20 (mejora respecto a 0.10 anterior)

---

## 🚀 PASOS A SEGUIR

### PASO 1: Instalar XGBoost
```bash
pip install xgboost
```

### PASO 2: Ejecutar servidor
```bash
cd "C:\Users\Sebastian\Documents\Maestria\Proyecto Maestria 23 Sep\fase 4"
python app.py
```

### PASO 3: Abrir navegador
```
http://127.0.0.1:5000/objetivo-2
```

### PASO 4: Entrenar (PRIMERA VEZ)
- Haz clic: "Entrenar Modelo"
- Espera: 3-5 minutos
- Revisa: Los 2 graficos de evaluacion

### PASO 5: Siguientes visitas
- El modelo ya esta entrenado
- Se carga automaticamente
- No necesitas hacer nada mas

---

## 🔍 COMO INTERPRETAR LOS RESULTADOS

### R² Bajo (0.02-0.10) - ANTES
**Significado**: El modelo explica muy poco de la varianza
**Causa**: Solo usa histórico de PM2.5/PM10
**Solucion**: XGBoost + Features temporales

### R² Mejorado (0.15-0.30) - AHORA (esperado)
**Significado**: El modelo explica ~15-30% de la varianza
**Causa**: XGBoost es mejor + features temporales ayudan
**Interpretacion**: Mejora clara respecto al anterior

### Si R² sigue bajo (<0.10) - Proximo paso
**Causa**: Posiblemente se necesita meteorología (HR, Temp, Presión, Viento)
**Solucion**: Agregar variables externas cuando disponibles

---

## 📝 ESTADO DEL ENTRENAMIENTO - MENSAJES ESPERADOS

```
[ENTRENAMIENTO MEJORADO] XGBoost + Features Temporales
[PASO 1/3] Cargando datos REALES de RMCAB (TODO EL AÑO 2025)...
   Registros: 8760
   Periodo: 2025-01-01 00:00:00 a 2025-12-31 23:00:00

[PASO 2/3] Entrenando modelo XGBoost con 24h historico + features temporales...
   [ENTRENAMIENTO PM2.5] 24 horas de historico + features temporales
      Registros: 8760
      Train: 6570 muestras
      Test:  2190 muestras
      RMSE Test: 1.2340
      MAE Test:  0.8945
      R² Test:   0.1234
      MAPE Test: 15.67%
      Modelo guardado: models/xgboost_pm25.pkl

   [ENTRENAMIENTO PM10] 24 horas de historico + features temporales
      Registros: 8760
      Train: 6570 muestras
      Test:  2190 muestras
      RMSE Test: 2.1234
      MAE Test:  1.5432
      R² Test:   0.2345
      MAPE Test: 18.90%
      Modelo guardado: models/xgboost_pm10.pkl

[PASO 3/3] Generando graficos de evaluacion...

[EXITO] Modelo entrenado, guardado y evaluado
Archivos generados:
  - models/xgboost_pm25.pkl
  - models/xgboost_pm10.pkl
  - static/results/evaluation_pm25.png
  - static/results/evaluation_pm10.png

Proximas ejecuciones: Cargan el modelo guardado (sin reentrenar)
```

---

## ❓ PREGUNTAS FRECUENTES

### P: Por que XGBoost y no LSTM?
R: TensorFlow/LSTM no funciona en Python 3.14 (tu version). XGBoost es mas practico, rapido y funciona bien.

### P: Por que features temporales?
R: PM2.5/PM10 tienen ciclos diarios y semanales. Agregar estas features ayuda al modelo a capturarlos.

### P: Puedo reentrenar en cualquier momento?
R: Si, pero no es necesario. El modelo guarda los parametros, reutilizalos es mas rapido.

### P: Que pasa si borro los archivos en /models/?
R: El sistema lo detecta y te pide entrenar de nuevo.

### P: Como mejoro los resultados?
R: Agrega variables meteorologicas (HR, Temp, Presión, Viento) cuando disponibles.

---

## 📞 SOPORTE

Si tienes problemas:

1. **Verifica XGBoost instalado**: `pip list | grep xgboost`
2. **Lee los logs**: Mira el output en la terminal de `python app.py`
3. **Revisa los graficos**: Abre `/static/results/evaluation_*.png`
4. **Compara R²**: Si R² > 0.15, la mejora funciono

---

## 🎓 RESUMEN TECNICO

| Aspecto | Valor |
|---------|-------|
| Algoritmo | XGBoost Regressor |
| Datos | 8,760 registros (TODO 2025) |
| Features | 14 (8 historico + 6 temporales) |
| Split | 75% train / 25% test (temporal) |
| Parametros XGB | max_depth=6, learning_rate=0.1, n_estimators=200 |
| Evaluacion | RMSE, MAE, R², MAPE |
| Persistencia | Modelo + Scaler guardados |
| Interfaz | Web con graficos interactivos |

---

**Ultima actualizacion**: 2025-11-20
**Versión**: 2.0 (XGBoost Mejorado)
