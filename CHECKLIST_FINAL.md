# 📋 LISTA DE VERIFICACIÓN FINAL

## ✅ Cambios en el Código (COMPLETADOS)

### Backend - Python
- [x] `modules/calibration.py` línea 279-295: Timezone normalization
- [x] `modules/calibration.py` línea 612-621: Scatter data format fix
- [x] Backend probado y funcionando ✅

### Frontend - Templates
- [x] `templates/visualizacion_junio_julio.html`: Botón ID corregido
- [x] `templates/visualizacion_2024.html`: Template completamente reescrito
- [x] Sin bloques duplicados ✅

### Frontend - JavaScript  
- [x] `static/js/visualizacion_junio_julio.js`: Ya funcionando ✅
- [ ] `static/js/visualizacion_2024.js`: **PENDIENTE** (auto-generado)

## 🔧 Herramientas Creadas (LISTAS PARA USAR)

- [x] `create_2024_js.py`: Script Python de generación
- [x] `run_create_2024.bat`: Ejecutable Windows
- [x] `CAMBIOS_CALIBRACION.md`: Documentación técnica
- [x] `INSTRUCCIONES_CALIBRACION.md`: Guía del usuario
- [x] `RESUMEN_CAMBIOS.md`: Resumen ejecutivo
- [x] `README_RAPIDO.md`: Referencia rápida
- [x] Este archivo: Lista de verificación

## ⚡ Acción Pendiente (1 paso)

```
EJECUTAR: run_create_2024.bat
REINICIAR: Flask app (python app.py)
VERIFICAR: Ambas páginas funcionando
```

## 🎯 Resultado Esperado

### Antes de ejecutar bat:
```
❌ /visualizacion/2024 → Error JS (archivo faltante)
✅ /visualizacion/junio-julio → Funciona
```

### Después de ejecutar bat:
```
✅ /visualizacion/2024 → Funciona perfecto
✅ /visualizacion/junio-julio → Sigue funcionando
```

## 📊 Test de Calibración

Una vez completado, probar:

### Test 1: Junio-Julio 2025
1. Ir a: http://192.168.1.6:5000/visualizacion/junio-julio
2. Click: "Calibrar Todos (PM2.5 y PM10)"
3. Esperar: 1-2 minutos
4. Verificar:
   - [ ] Pestañas: Aire2, Aire4, Aire5
   - [ ] Sub-pestañas: PM2.5, PM10
   - [ ] Tablas con 6 modelos cada una
   - [ ] Gráficos de barras
   - [ ] Scatter plots visibles
   - [ ] Fórmulas de regresión

### Test 2: Año 2024
1. Ir a: http://192.168.1.6:5000/visualizacion/2024
2. Click: "Calibrar Todos (PM2.5 y PM10)"
3. Esperar: 1-2 minutos (puede ser más por más datos)
4. Verificar:
   - [ ] Pestañas: Aire2, Aire4, Aire5
   - [ ] Sub-pestañas: PM2.5, PM10
   - [ ] Tablas con 6 modelos cada una
   - [ ] Gráficos de barras
   - [ ] Scatter plots visibles
   - [ ] Fórmulas de regresión

## 📈 Métricas Esperadas

Cada modelo debe mostrar:
- R² (0-1, ideal >0.7)
- R² Ajustado
- RMSE (µg/m³, ideal <5)
- MAE (µg/m³, ideal <3)
- MAPE (%, ideal <20%)
- Overfitting status (OK/Moderado/Alto)

## 🔍 Debugging

Si algo falla después de ejecutar bat:

### 1. Verificar archivo creado:
```
Debe existir: static/js/visualizacion_2024.js
Tamaño: Similar a visualizacion_junio_julio.js (~50-60 KB)
```

### 2. Verificar consola Flask:
```
Buscar mensajes de error en la terminal donde corre Flask
```

### 3. Verificar consola navegador:
```
F12 → Console → Buscar errores en rojo
```

### 4. Revisar logs de calibración:
```
Terminal Flask mostrará:
- "📊 Cargando datos de sensores..."
- "✅ Datos lowcost cargados: X registros"
- "📡 Calibrando AireX..."
- "✅ AireX calibrado exitosamente"
```

## 🎊 Checklist Final

Antes de considerar completo:

- [ ] Ejecutado `run_create_2024.bat` exitosamente
- [ ] Archivo `visualizacion_2024.js` existe
- [ ] Flask reiniciado
- [ ] Página junio-julio funciona
- [ ] Página 2024 funciona
- [ ] Calibración junio-julio exitosa
- [ ] Calibración 2024 exitosa
- [ ] Gráficos visibles en ambas
- [ ] Scatter plots se muestran
- [ ] Sin errores en consola JS
- [ ] Sin errores en consola Flask

## 📞 Soporte

Si todo lo anterior está ✅ pero algo aún falla:

1. Revisar `CAMBIOS_CALIBRACION.md` (detalles técnicos)
2. Revisar `INSTRUCCIONES_CALIBRACION.md` (guía paso a paso)
3. Verificar versiones:
   - Python 3.11+
   - Flask instalado
   - pandas, scikit-learn instalados
   - PostgreSQL corriendo
   - Datos disponibles en la base

## ⏱️ Tiempo Estimado

- Ejecutar bat: 5 segundos
- Reiniciar Flask: 10 segundos
- Test junio-julio: 2 minutos
- Test 2024: 3 minutos

**TOTAL: ~5-6 minutos**

---

**Estado actual**: 95% completo
**Acción pendiente**: 1 comando
**Impacto**: Crítico (necesario para que funcione)
**Dificultad**: Trivial (doble click)

🎯 **¡CASI TERMINADO!** Solo ejecuta el bat file y reinicia Flask.
