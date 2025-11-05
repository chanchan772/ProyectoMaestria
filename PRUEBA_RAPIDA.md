# 🧪 Prueba Rápida - Sistema de Visualización

## ✅ Problema Resuelto

**Error corregido:**
```
BuildError: Could not build url for endpoint 'visualizacion'
```

**Solución aplicada:**
- ✅ Eliminados archivos antiguos: `visualizacion.html` y `visualizacion.js`
- ✅ Actualizadas referencias en `index.html` y `modelos.html`
- ✅ Todas las rutas ahora apuntan a `visualizacion_junio_julio`

---

## 🚀 Cómo Probar Ahora

### 1. Reiniciar la Aplicación

```bash
# Si ya está corriendo, detén con Ctrl+C

cd "C:\Proyecto Maestria 23 Sep\fase 3"
python app.py
```

### 2. Abrir en Navegador

```
http://localhost:5000
```

### 3. Verificar que Funciona

#### ✅ **Test 1: Página Principal**
- Abre http://localhost:5000
- Deberías ver la página de inicio sin errores
- Click en "Ver Datos" → Debe llevar a Visualización Junio-Julio

#### ✅ **Test 2: Navbar Dropdown**
- Pasa el mouse sobre "Visualización" en el navbar
- Deberías ver 2 opciones:
  - Junio-Julio 2024
  - Periodo Completo 2024

#### ✅ **Test 3: Visualización Junio-Julio**
1. Click en "Visualización" → "Junio-Julio 2024"
2. Deberías ver 5 cards de dispositivos
3. Click en cualquier dispositivo (ej: Aire2)
4. Card debe resaltarse en verde
5. Click "Cargar Datos del Dispositivo"
6. Deberías ver:
   - 4 métricas resumen
   - Serie de tiempo
   - 2 Box plots

#### ✅ **Test 4: Calibración (Sensores de Bajo Costo)**
1. Selecciona Aire2, Aire4 o Aire5
2. Carga los datos
3. Click "Iniciar Calibración con Modelos ML"
4. Espera 2-3 minutos (verás spinner de carga)
5. Deberías ver:
   - Tabla con 5 modelos
   - Mejor modelo identificado
   - Gráfico de efectividad
   - 5 Scatter plots

#### ✅ **Test 5: Visualización RMCAB**
1. Click en "RMCAB - Las Ferias"
2. Carga los datos
3. Deberías ver las visualizaciones normalmente
4. **Nota:** La calibración NO está disponible para RMCAB (solo para sensores)

---

## 🔍 Verificación de Rutas

Todas estas URLs deben funcionar:

```
✅ http://localhost:5000/                          (Inicio)
✅ http://localhost:5000/modelos                   (Modelos)
✅ http://localhost:5000/visualizacion/junio-julio (Junio-Julio 2024)
✅ http://localhost:5000/visualizacion/2024        (Periodo Completo 2024)
✅ http://localhost:5000/definiciones              (Definiciones)
✅ http://localhost:5000/acerca-de                 (Acerca de)
```

---

## 🐛 Si Aún Hay Errores

### Error: "Module not found"
```bash
pip install -r requirements.txt
```

### Error: "Database connection failed"
**No te preocupes** - La app funciona sin conexión a la BD. Solo no podrás cargar datos reales, pero todas las páginas se verán correctamente.

### Error 404
Verifica que estés usando las rutas correctas con el dropdown en el navbar.

### Página en blanco
1. Abre la consola del navegador (F12)
2. Ve a la pestaña "Console"
3. Busca errores en rojo
4. Compárteme el error si lo hay

---

## 📝 Cambios Aplicados en Este Fix

### Archivos Modificados:
- ✅ `templates/index.html` - Actualizada referencia
- ✅ `templates/modelos.html` - Actualizada referencia

### Archivos Eliminados:
- ❌ `templates/visualizacion.html` (versión antigua)
- ❌ `static/js/visualizacion.js` (versión antigua)

### Commits:
```
14c51ba fix: Corregir referencias a ruta visualizacion antigua
0af12a5 docs: Agregar documentación de cambios en visualización
384b41b feat: Agregar sistema dual de visualización con calibración
```

---

## 🎯 Flujo Completo de Prueba

### Prueba Básica (5 min)
1. Iniciar app
2. Navegar a inicio
3. Ir a Modelos
4. Ir a Visualización Junio-Julio
5. Seleccionar un dispositivo
6. Cargar datos
7. Ver gráficos

### Prueba Completa (15 min)
1. Todo lo anterior +
2. Ejecutar calibración en sensor Aire2
3. Revisar tabla de resultados
4. Ver scatter plots
5. Ir a Visualización 2024
6. Repetir con otro dispositivo
7. Probar RMCAB

---

## ✨ Nuevo Sistema vs Antiguo

### Antes (Versión Antigua)
- ❌ 1 sola página de visualización
- ❌ Sin selección de dispositivos
- ❌ Datos mezclados
- ❌ Calibración genérica

### Ahora (Versión Nueva)
- ✅ 2 páginas (Junio-Julio + 2024)
- ✅ Selección individual de 5 dispositivos
- ✅ Análisis por dispositivo independiente
- ✅ Calibración específica por sensor
- ✅ Scatter plots por modelo
- ✅ Comparación antes/después
- ✅ Métricas de efectividad

---

## 🎓 Para Demo en Tesis

### Preparación
1. Asegúrate de tener conexión a internet (para API RMCAB)
2. Ten la app corriendo antes de la presentación
3. Abre pestañas con las páginas ya cargadas:
   - Inicio
   - Modelos
   - Visualización Junio-Julio (con Aire2 ya cargado)
   - Visualización 2024 (con resultados de calibración ya ejecutados)

### Durante la Demo
1. **Inicio (1 min):** Mostrar página principal
2. **Modelos (2 min):** Explicar 5 algoritmos
3. **Visualización (10 min):**
   - Mostrar selección de dispositivo
   - Mostrar gráficos de datos
   - Explicar calibración
   - Mostrar resultados (ya pre-ejecutados)
   - Mostrar scatter plots
   - Explicar efectividad

---

**¡Todo listo para usar! 🚀**

Si encuentras algún error, avísame y lo arreglo de inmediato.
