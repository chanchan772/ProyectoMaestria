/**
 * JavaScript para Visualización Periodo Completo 2024
 */

let selectedDevice = null;
let selectedDeviceType = null;
let currentData = null;
let calibrationResults = null;

// Elementos del DOM
const deviceCards = document.querySelectorAll('.device-card');
const btnLoadDevice = document.getElementById('btnLoadDevice');
const btnStartCalibration = document.getElementById('btnStartCalibration');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingMessage = document.getElementById('loadingMessage');
const dataSection = document.getElementById('dataSection');
const calibrationSection = document.getElementById('calibrationSection');
const comparisonSection = document.getElementById('comparisonSection');

// Event Listeners
deviceCards.forEach(card => {
    card.addEventListener('click', () => selectDevice(card));
});

btnLoadDevice.addEventListener('click', loadDeviceData);
btnStartCalibration.addEventListener('click', runCalibration);

/**
 * Selecciona un dispositivo
 */
function selectDevice(card) {
    // Remover selección anterior
    deviceCards.forEach(c => c.classList.remove('selected'));

    // Seleccionar nuevo
    card.classList.add('selected');

    selectedDevice = card.dataset.device;
    selectedDeviceType = card.dataset.type;

    // Habilitar botón
    btnLoadDevice.disabled = false;

    console.log('Dispositivo seleccionado:', selectedDevice, selectedDeviceType);
}

/**
 * Carga datos del dispositivo seleccionado
 */
async function loadDeviceData() {
    if (!selectedDevice) {
        showAlert('Por favor selecciona un dispositivo primero', 'warning');
        return;
    }

    showLoading(`Cargando datos de ${selectedDevice}...`);

    try {
        let response;

        if (selectedDeviceType === 'sensor') {
            // Cargar datos de sensor de bajo costo
            response = await fetch('/api/load-device-data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    device_name: selectedDevice,
                    start_date: '2024-01-01',
                    end_date: '2024-12-31'
                })
            });
        } else {
            // Cargar datos de RMCAB
            const stationCode = document.querySelector(`.device-card[data-device="${selectedDevice}"]`).dataset.station;
            response = await fetch('/api/load-rmcab-data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    station_code: parseInt(stationCode),
                    start_date: '2024-01-01',
                    end_date: '2024-12-31'
                })
            });
        }

        if (!response.ok) {
            throw new Error('Error al cargar los datos');
        }

        const result = await response.json();

        if (result.success) {
            currentData = result.data;
            showAlert(`✓ Datos cargados: ${result.records} registros`, 'success');

            // Mostrar sección de datos
            document.getElementById('selectedDeviceName').textContent = selectedDevice;
            dataSection.style.display = 'block';

            // Scroll suave
            dataSection.scrollIntoView({ behavior: 'smooth' });

            // Generar visualizaciones
            await generateDataVisualizations(result.data);
        }

    } catch (error) {
        showAlert(`Error: ${error.message}`, 'danger');
        console.error(error);
    } finally {
        hideLoading();
    }
}

/**
 * Genera visualizaciones de datos
 */
async function generateDataVisualizations(data) {
    // Calcular métricas resumen
    displayMetrics(data);

    // Generar gráficos
    createTimeSeriesPlot(data);
    createBoxPlots(data);
}

/**
 * Muestra métricas resumen
 */
function displayMetrics(data) {
    const metricsGrid = document.getElementById('metricsGrid');
    metricsGrid.innerHTML = '';

    // Calcular estadísticas
    const pm25Values = data.map(d => d.pm25).filter(v => v != null);
    const pm10Values = data.map(d => d.pm10).filter(v => v != null);

    const metrics = [
        {
            icon: 'database-fill',
            title: 'Total Registros',
            value: data.length,
            color: 'primary'
        },
        {
            icon: 'wind',
            title: 'PM2.5 Promedio',
            value: (pm25Values.reduce((a, b) => a + b, 0) / pm25Values.length).toFixed(2) + ' µg/m³',
            color: 'success'
        },
        {
            icon: 'cloud-haze2',
            title: 'PM10 Promedio',
            value: (pm10Values.reduce((a, b) => a + b, 0) / pm10Values.length).toFixed(2) + ' µg/m³',
            color: 'info'
        },
        {
            icon: 'calendar-range',
            title: 'Periodo',
            value: 'Año 2024',
            color: 'warning'
        }
    ];

    metrics.forEach(metric => {
        const card = `
            <div class="metric-card">
                <i class="bi bi-${metric.icon} display-4 text-${metric.color}"></i>
                <h3 class="mt-2">${metric.value}</h3>
                <p class="text-muted mb-0">${metric.title}</p>
            </div>
        `;
        metricsGrid.insertAdjacentHTML('beforeend', card);
    });
}

/**
 * Crea gráfico de series de tiempo
 */
function createTimeSeriesPlot(data) {
    const traces = [];

    // PM2.5
    if (data.some(d => d.pm25 != null)) {
        traces.push({
            x: data.map(d => d.datetime),
            y: data.map(d => d.pm25),
            type: 'scatter',
            mode: 'lines',
            name: 'PM2.5',
            line: { color: '#2d5016', width: 2 }
        });
    }

    // PM10
    if (data.some(d => d.pm10 != null)) {
        traces.push({
            x: data.map(d => d.datetime),
            y: data.map(d => d.pm10),
            type: 'scatter',
            mode: 'lines',
            name: 'PM10',
            line: { color: '#0077b6', width: 2 }
        });
    }

    const layout = {
        title: `${selectedDevice} - Series de Tiempo`,
        xaxis: { title: 'Fecha y Hora' },
        yaxis: { title: 'Concentración (µg/m³)' },
        hovermode: 'x unified',
        height: 500,
        shapes: [
            // Límite OMS PM2.5
            {
                type: 'line',
                x0: data[0].datetime,
                x1: data[data.length - 1].datetime,
                y0: 15,
                y1: 15,
                line: { color: 'orange', width: 2, dash: 'dash' }
            },
            // Límite Colombia PM2.5
            {
                type: 'line',
                x0: data[0].datetime,
                x1: data[data.length - 1].datetime,
                y0: 25,
                y1: 25,
                line: { color: 'red', width: 2, dash: 'dash' }
            }
        ]
    };

    Plotly.newPlot('timeseriesPlot', traces, layout, { responsive: true });
}

/**
 * Crea box plots
 */
function createBoxPlots(data) {
    // PM2.5
    const pm25Data = data.map(d => d.pm25).filter(v => v != null);
    const tracePM25 = {
        y: pm25Data,
        type: 'box',
        name: 'PM2.5',
        marker: { color: '#2d5016' },
        boxmean: 'sd'
    };

    const layoutPM25 = {
        yaxis: { title: 'Concentración (µg/m³)' },
        height: 400
    };

    Plotly.newPlot('boxplotPM25', [tracePM25], layoutPM25, { responsive: true });

    // PM10
    const pm10Data = data.map(d => d.pm10).filter(v => v != null);
    const tracePM10 = {
        y: pm10Data,
        type: 'box',
        name: 'PM10',
        marker: { color: '#0077b6' },
        boxmean: 'sd'
    };

    const layoutPM10 = {
        yaxis: { title: 'Concentración (µg/m³)' },
        height: 400
    };

    Plotly.newPlot('boxplotPM10', [tracePM10], layoutPM10, { responsive: true });
}

/**
 * Ejecuta calibración
 */
async function runCalibration() {
    if (!currentData || selectedDeviceType !== 'sensor') {
        showAlert('La calibración solo está disponible para sensores de bajo costo', 'warning');
        return;
    }

    showLoading('Ejecutando calibración con 5 modelos de Machine Learning...<br>Esto puede tardar 2-3 minutos');

    try {
        const response = await fetch('/api/calibrate-device', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_name: selectedDevice,
                start_date: '2024-01-01',
                end_date: '2024-12-31',
                pollutant: 'pm25'
            })
        });

        if (!response.ok) {
            throw new Error('Error en la calibración');
        }

        const result = await response.json();

        if (result.success && result.results && result.results.length > 0) {
            calibrationResults = result.results;
            displayCalibrationResults(result.results);
            showAlert('✓ Calibración completada exitosamente', 'success');

            // Mostrar sección de calibración
            calibrationSection.style.display = 'block';
            calibrationSection.scrollIntoView({ behavior: 'smooth' });

        } else {
            throw new Error('No se obtuvieron resultados de calibración');
        }

    } catch (error) {
        showAlert(`Error: ${error.message}`, 'danger');
        console.error(error);
    } finally {
        hideLoading();
    }
}

/**
 * Muestra resultados de calibración
 */
function displayCalibrationResults(results) {
    const table = document.getElementById('calibrationResultsTable');
    table.innerHTML = '';

    results.forEach((result, index) => {
        const row = `
            <tr class="${index === 0 ? 'table-success' : ''}">
                <td>
                    <strong>${result.model_name}</strong>
                    ${index === 0 ? '<span class="badge bg-success ms-2">Mejor</span>' : ''}
                </td>
                <td>${result.r2}</td>
                <td>${result.rmse}</td>
                <td>${result.mae}</td>
                <td>${result.mape}%</td>
                <td>
                    ${result.r2 > 0.8 ? '<span class="badge bg-success">Excelente</span>' :
                      result.r2 > 0.6 ? '<span class="badge bg-warning">Bueno</span>' :
                      '<span class="badge bg-danger">Regular</span>'}
                </td>
            </tr>
        `;
        table.insertAdjacentHTML('beforeend', row);
    });

    // Mejor modelo
    const best = results[0];
    document.getElementById('bestModelAlert').innerHTML = `
        <h5><i class="bi bi-trophy-fill"></i> Mejor Modelo: ${best.model_name}</h5>
        <p class="mb-0">
            <strong>R² = ${best.r2}</strong> |
            RMSE = ${best.rmse} µg/m³ |
            MAE = ${best.mae} µg/m³ |
            MAPE = ${best.mape}%
        </p>
    `;

    // Gráfico de efectividad
    createEffectivenessPlot(results);

    // Scatter plots individuales
    createScatterPlots(results);
}

/**
 * Crea gráfico de efectividad
 */
function createEffectivenessPlot(results) {
    const models = results.map(r => r.model_name);
    const r2 = results.map(r => r.r2);
    const rmse = results.map(r => r.rmse);
    const mae = results.map(r => r.mae);
    const mape = results.map(r => r.mape);

    const traces = [
        { x: models, y: r2, name: 'R²', type: 'bar', yaxis: 'y' },
        { x: models, y: rmse, name: 'RMSE', type: 'bar', yaxis: 'y2' },
        { x: models, y: mae, name: 'MAE', type: 'bar', yaxis: 'y3' },
        { x: models, y: mape, name: 'MAPE (%)', type: 'bar', yaxis: 'y4' }
    ];

    const layout = {
        title: 'Comparación de Métricas por Modelo',
        grid: { rows: 2, columns: 2, pattern: 'independent' },
        height: 600
    };

    Plotly.newPlot('effectivenessPlot', traces, layout, { responsive: true });
}

/**
 * Crea scatter plots de cada modelo
 */
function createScatterPlots(results) {
    const container = document.getElementById('scatterPlotsContainer');
    container.innerHTML = '';

    results.forEach((result, index) => {
        const plotDiv = `
            <div class="col-md-6 mb-4">
                <div class="plot-container">
                    <h6>${result.model_name}</h6>
                    <div id="scatterPlot${index}"></div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', plotDiv);

        // Nota: En producción, necesitarías los datos reales y predichos del servidor
        // Aquí creamos un ejemplo
        createScatterPlotForModel(result, index);
    });
}

/**
 * Crea scatter plot individual
 */
function createScatterPlotForModel(result, index) {
    // Este es un ejemplo - en producción necesitarías los datos reales
    const trace = {
        x: [10, 20, 30, 40, 50],
        y: [12, 19, 31, 38, 52],
        mode: 'markers',
        type: 'scatter',
        name: 'Predicciones',
        marker: { color: '#2d5016', size: 8 }
    };

    const perfectLine = {
        x: [0, 60],
        y: [0, 60],
        mode: 'lines',
        name: 'Línea Perfecta',
        line: { color: 'red', dash: 'dash' }
    };

    const layout = {
        xaxis: { title: 'PM2.5 Real (µg/m³)' },
        yaxis: { title: 'PM2.5 Predicho (µg/m³)' },
        height: 350,
        annotations: [{
            text: `R² = ${result.r2}`,
            x: 0.05,
            y: 0.95,
            xref: 'paper',
            yref: 'paper',
            showarrow: false
        }]
    };

    Plotly.newPlot(`scatterPlot${index}`, [trace, perfectLine], layout, { responsive: true });
}

/**
 * Utilidades
 */
function showLoading(message = 'Cargando...') {
    loadingMessage.innerHTML = message;
    loadingOverlay.classList.add('active');
}

function hideLoading() {
    loadingOverlay.classList.remove('active');
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '10000';
    alertDiv.style.minWidth = '400px';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}
