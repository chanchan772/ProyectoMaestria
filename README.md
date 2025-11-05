# 🌍 Plataforma Web - Monitoreo de Calidad del Aire

Aplicación web completa para la **validación, modelado predictivo y visualización** de concentraciones de PM2.5 y PM10 mediante sensores de bajo costo.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0+-green)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple)
![License](https://img.shields.io/badge/License-Academic-yellow)

---

## 📋 Tabla de Contenido

- [Descripción del Proyecto](#-descripción-del-proyecto)
- [Características](#-características)
- [Tecnologías Utilizadas](#-tecnologías-utilizadas)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Deployment en Render](#-deployment-en-render)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [API Endpoints](#-api-endpoints)
- [Autores](#-autores)

---

## 📖 Descripción del Proyecto

Este proyecto forma parte de la tesis de Maestría en Analítica de Datos de la **Universidad Central** (2025), y tiene como objetivo desarrollar una estrategia integral para complementar las redes oficiales de monitoreo de calidad del aire en Bogotá, mediante el uso de sensores de bajo costo (PMS5003) calibrados con algoritmos de Machine Learning.

### Problema

- Las redes oficiales de monitoreo (RMCAB) tienen **cobertura limitada** debido a altos costos
- Muchas zonas urbanas carecen de información sobre calidad del aire
- La contaminación atmosférica (PM2.5 y PM10) afecta gravemente la salud pública

### Solución

- Sensores de bajo costo como complemento
- Calibración con Machine Learning (Regresión Lineal, Random Forest, SVR)
- Plataforma web interactiva para visualización y análisis

---

## ✨ Características

### 🏠 Página Principal
- Introducción al proyecto y problema
- Explicación de la solución propuesta
- Tecnologías utilizadas

### 🧠 Modelos de Calibración
- 5 algoritmos de Machine Learning:
  - Linear Regression
  - Random Forest
  - Support Vector Regression (Linear, RBF, Polynomial)
- Comparación de métricas (R², RMSE, MAE, MAPE)
- Selección automática del mejor modelo

### 📊 Visualización Interactiva
- Series de tiempo con límites normativos
- Diagramas de caja para análisis de distribuciones
- Mapas de calor por hora del día
- Estadísticas descriptivas completas
- Exportación de datos en CSV

### 📚 Glosario Técnico
- Definiciones de PM2.5 y PM10
- Índices de calidad del aire (ICA):
  - Colombia (IDEAM)
  - Estados Unidos (EPA)
  - Europa (EEA)
  - Guías OMS 2021
- Explicación de métricas de Machine Learning

### 👥 Acerca del Equipo
- Información de estudiantes y directores
- Objetivos del proyecto
- Contacto e información institucional

---

## 🛠️ Tecnologías Utilizadas

### Backend
- **Python 3.11+**
- **Flask 3.0** - Framework web
- **scikit-learn** - Machine Learning
- **Pandas, NumPy** - Análisis de datos
- **PostgreSQL** - Base de datos
- **Plotly** - Visualizaciones interactivas

### Frontend
- **HTML5 / CSS3**
- **Bootstrap 5.3** - Framework CSS responsive
- **JavaScript (ES6+)**
- **Chart.js / Plotly** - Gráficos interactivos

### DevOps
- **Gunicorn** - WSGI server para producción
- **python-dotenv** - Gestión de variables de entorno
- **Render** - Plataforma de deployment

---

## 🚀 Instalación

### Requisitos Previos

- Python 3.11 o superior
- pip (gestor de paquetes de Python)
- PostgreSQL (acceso a base de datos)
- Git

### 1. Clonar el repositorio

```bash
git clone https://github.com/chanchan772/ProyectoMaestria.git
cd ProyectoMaestria/fase\ 3
```

### 2. Crear entorno virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crea un archivo `.env` basado en `.env.example`:

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus credenciales:

```env
# Database Configuration
DB_NAME=dit_as_events
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_HOST=186.121.143.150
DB_PORT=15432

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=tu-clave-secreta-aqui

# Server Configuration
PORT=5000
```

### 5. Ejecutar la aplicación

```bash
python app.py
```

La aplicación estará disponible en: http://localhost:5000

---

## 💻 Uso

### Navegación

1. **Inicio** - Presentación del proyecto
2. **Modelos** - Información sobre algoritmos de calibración
3. **Visualización** - Exploración interactiva de datos
4. **Definiciones** - Glosario técnico completo
5. **Acerca de** - Equipo e información institucional

### Visualización de Datos

1. Selecciona la fuente de datos:
   - Sensores de bajo costo (Aire2, Aire4, Aire5)
   - RMCAB - Estación Las Ferias
   - Ambas fuentes (comparación)

2. Elige el tipo de visualización:
   - Series de tiempo
   - Diagrama de caja
   - Mapa de calor
   - Diagrama de dispersión

3. Selecciona el contaminante:
   - PM2.5
   - PM10
   - Ambos

4. Haz clic en **"Cargar Datos"**

5. Explora las visualizaciones y descarga datos en CSV

### Calibración de Modelos

1. Ve a la sección de **Visualización**
2. Desplázate hasta **"Comparación de Modelos de Calibración"**
3. Haz clic en **"Ejecutar Calibración"**
4. Espera a que los 5 modelos se entrenen y evalúen
5. Revisa los resultados comparativos

---

## 🌐 Deployment en Render

### Preparación

1. Asegúrate de tener una cuenta en [Render.com](https://render.com)
2. Conecta tu repositorio de GitHub

### Configuración en Render

1. **Crear nuevo Web Service:**
   - Type: `Web Service`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

2. **Variables de Entorno:**

Añade las siguientes variables en la sección "Environment":

```
DB_NAME=dit_as_events
DB_USER=tu_usuario
DB_PASSWORD=tu_password
DB_HOST=186.121.143.150
DB_PORT=15432
SECRET_KEY=tu-clave-secreta-segura
FLASK_ENV=production
```

3. **Deploy:**

Haz clic en "Create Web Service" y espera a que se complete el deployment.

### Verificación

Una vez deployado, tu aplicación estará disponible en:

```
https://tu-app.onrender.com
```

---

## 📁 Estructura del Proyecto

```
fase 3/
├── app.py                          # Aplicación Flask principal
├── requirements.txt                # Dependencias Python
├── Procfile                        # Configuración para Render
├── runtime.txt                     # Versión de Python
├── .env.example                    # Ejemplo de variables de entorno
├── .gitignore                      # Archivos ignorados por Git
│
├── modules/                        # Módulos Python personalizados
│   ├── __init__.py
│   ├── data_loader.py             # Carga de datos (PostgreSQL, API)
│   ├── calibration.py             # Modelos de Machine Learning
│   ├── visualization.py           # Generación de gráficos
│   └── metrics.py                 # Cálculo de estadísticas
│
├── templates/                      # Plantillas HTML (Jinja2)
│   ├── base.html                  # Template base
│   ├── index.html                 # Página principal
│   ├── modelos.html               # Página de modelos
│   ├── visualizacion.html         # Página de visualización
│   ├── definiciones.html          # Glosario técnico
│   └── acerca_de.html             # Acerca del equipo
│
├── static/                         # Archivos estáticos
│   ├── css/
│   │   └── styles.css             # Estilos personalizados
│   ├── js/
│   │   ├── main.js                # JavaScript principal
│   │   └── visualizacion.js       # JS para visualización
│   └── img/                       # Imágenes
│
├── data/                           # Datos (no versionados)
│   └── .gitkeep
│
└── Proyecto de grado.postman_collection.json  # Template API RMCAB
```

---

## 🔌 API Endpoints

### Carga de Datos

#### `POST /api/load-lowcost-data`
Carga datos de sensores de bajo costo desde PostgreSQL

**Response:**
```json
{
  "success": true,
  "records": 15234,
  "data": [...]
}
```

#### `POST /api/load-rmcab-data`
Carga datos de RMCAB desde la API

**Request Body:**
```json
{
  "station_code": 6
}
```

**Response:**
```json
{
  "success": true,
  "records": 1440,
  "data": [...]
}
```

### Calibración

#### `POST /api/calibrate`
Ejecuta calibración con múltiples modelos

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "model_name": "Random Forest",
      "r2": 0.9245,
      "rmse": 3.52,
      "mae": 2.14,
      "mape": 8.5
    },
    ...
  ]
}
```

### Estadísticas

#### `POST /api/statistics`
Calcula estadísticas descriptivas

**Request Body:**
```json
{
  "data_type": "lowcost"
}
```

**Response:**
```json
{
  "success": true,
  "statistics": {
    "pm25": {
      "count": 15234,
      "mean": 18.5,
      "std": 8.2,
      ...
    },
    ...
  }
}
```

### Visualización

#### `POST /api/visualize`
Genera visualizaciones con Plotly

**Request Body:**
```json
{
  "plot_type": "timeseries",
  "data_type": "lowcost"
}
```

**Response:**
```json
{
  "success": true,
  "plot": {
    "data": [...],
    "layout": {...}
  }
}
```

---

## 👥 Autores

### Estudiantes

- **Sebastian Mateus Villegas**
  - Candidato a Magíster en Analítica de Datos
  - Universidad Central

- **Ronal Ricardo Lancheros Casalla**
  - Candidato a Magíster en Analítica de Datos
  - Universidad Central

### Directores de Tesis

- **Oscar Arnulfo Fajardo Montaña** (Director)
- **Javier Casas Salgado** (Codirector)

### Institución

**Universidad Central**
Facultad de Ingeniería y Ciencias Básicas
Maestría en Analítica de Datos
Bogotá, Colombia - 2025

---

## 📄 Licencia

Este proyecto es de uso académico y de investigación.

---

## 🙏 Agradecimientos

- Universidad Central
- Red de Monitoreo de Calidad del Aire de Bogotá (RMCAB)
- Comunidad académica y científica

---

## 📞 Contacto

Para preguntas o colaboraciones:

- Email: smateus@ucentral.edu.co
- Universidad: https://www.ucentral.edu.co
- RMCAB: http://rmcab.ambientebogota.gov.co

---

## 📚 Referencias

- OMS (2021). WHO global air quality guidelines
- Castell et al. (2017). Can commercial low-cost sensor platforms contribute to air quality monitoring?
- Resolución 2254 de 2017 (MinAmbiente, Colombia)
- Universidad Nacional de Colombia (2021). Estado del arte del uso de sensores de bajo costo

---

**Desarrollado con ❤️ para mejorar la calidad del aire en Bogotá**
