/**
 * JavaScript para la página de visualización
 */

let currentData = null;
let currentStats = null;

// Elementos del DOM
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingMessage = document.getElementById('loadingMessage');
const btnLoadData = document.getElementById('btnLoadData');
const btnDownloadData = document.getElementById('btnDownloadData');
const btnRunCalibration = document.getElementById('btnRunCalibration');
const dataSource = document.getElementById('dataSource');
const plotType = document.getElementById('plotType');
const pollutant = document.getElementById('pollutant');
const statsSection = document.getElementById('statsSection');
const statsContainer = document.getElementById('statsContainer');
const initialMessage = document.getElementById('initialMessage');
const plotsContent = document.getElementById('plotsContent');
const calibrationResults = document.getElementById('calibrationResults');
const calibrationResultsBody = document.getElementById('calibrationResultsBody');

// Event listeners
btnLoadData.addEventListener('click', loadData);
btnDownloadData.addEventListener('click', downloadData);
btnRunCalibration.addEventListener('click', runCalibration);

/**
 * Carga datos desde el servidor
 */
async function loadData() {
    showLoading('Cargando datos...');

    try {
        const source = dataSource.value;
        let response;

        if (source === 'lowcost') {
            response = await fetch('/api/load-lowcost-data', { method: 'POST' });
        } else if (source === 'rmcab') {
            response = await fetch('/api/load-rmcab-data', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ station_code: 6 })
            });
        } else {
            // Cargar ambas fuentes
            showAlert('Función de comparación en desarrollo', 'info');
            hideLoading();
            return;
        }

        if (!response.ok) {
            throw new Error('Error al cargar los datos');
        }

        const result = await response.json();

        if (result.success) {
            currentData = result.data;
            showAlert(`✓ Datos cargados: ${result.records} registros`, 'success');

            // Cargar estadísticas
            await loadStatistics(source);

            // Generar visualización
            await generateVisualization();

            // Habilitar botón de descarga
            btnDownloadData.disabled = false;
        } else {
            throw new Error(result.error || 'Error desconocido');
        }

    } catch (error) {
        showAlert(`Error: ${error.message}`, 'danger');
        console.error(error);
    } finally {
        hideLoading();
    }
}

/**
 * Carga estadísticas del servidor
 */
async function loadStatistics(source) {
    try {
        const response = await fetch('/api/statistics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data_type: source })
        });

        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                currentStats = result.statistics;
                displayStatistics(currentStats);
            }
        }
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
    }
}

/**
 * Muestra estadísticas en cards
 */
function displayStatistics(stats) {
    if (!stats) return;

    statsContainer.innerHTML = '';

    const createStatCard = (title, value, unit, icon, color) => {
        return `
            <div class="col-md-3 col-sm-6">
                <div class="stats-card">
                    <i class="bi bi-${icon} display-4 text-${color}"></i>
                    <h3>${value}${unit}</h3>
                    <p class="text-muted mb-0">${title}</p>
                </div>
            </div>
        `;
    };

    // Total de registros
    if (stats.general) {
        statsContainer.insertAdjacentHTML('beforeend',
            createStatCard('Total Registros', stats.general.total_records, '', 'database-fill', 'primary')
        );
    }

    // PM2.5 promedio
    if (stats.pm25) {
        statsContainer.insertAdjacentHTML('beforeend',
            createStatCard('PM2.5 Promedio', stats.pm25.mean, ' µg/m³', 'wind', 'success')
        );
    }

    // PM10 promedio
    if (stats.pm10) {
        statsContainer.insertAdjacentHTML('beforeend',
            createStatCard('PM10 Promedio', stats.pm10.mean, ' µg/m³', 'cloud-haze2', 'info')
        );
    }

    // Número de fuentes
    if (stats.general && stats.general.num_devices) {
        statsContainer.insertAdjacentHTML('beforeend',
            createStatCard('Dispositivos', stats.general.num_devices, '', 'hdd-rack', 'warning')
        );
    } else if (stats.general && stats.general.num_stations) {
        statsContainer.insertAdjacentHTML('beforeend',
            createStatCard('Estaciones', stats.general.num_stations, '', 'geo-alt', 'warning')
        );
    }

    statsSection.style.display = 'block';
}

/**
 * Genera visualización según el tipo seleccionado
 */
async function generateVisualization() {
    try {
        const type = plotType.value;
        const pol = pollutant.value;
        const source = dataSource.value;

        showLoading('Generando visualización...');

        const response = await fetch('/api/visualize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                plot_type: type,
                data_type: source
            })
        });

        if (!response.ok) {
            throw new Error('Error al generar visualización');
        }

        const result = await response.json();

        if (result.success) {
            // Ocultar mensaje inicial y mostrar contenedor
            initialMessage.style.display = 'none';
            plotsContent.style.display = 'block';

            // Renderizar gráfico con Plotly
            const plotDiv = document.getElementById('plot1');
            Plotly.newPlot(plotDiv, result.plot.data, result.plot.layout, {
                responsive: true,
                displayModeBar: true
            });

            // Actualizar título
            document.getElementById('plot1Title').textContent = getTitleForPlotType(type);
        }

    } catch (error) {
        showAlert(`Error generando visualización: ${error.message}`, 'danger');
        console.error(error);
    } finally {
        hideLoading();
    }
}

/**
 * Descarga datos en formato CSV
 */
function downloadData() {
    if (!currentData || currentData.length === 0) {
        showAlert('No hay datos para descargar', 'warning');
        return;
    }

    // Convertir a CSV
    const csv = convertToCSV(currentData);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);

    link.setAttribute('href', url);
    link.setAttribute('download', `datos_calidad_aire_${Date.now()}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showAlert('Descarga iniciada', 'success');
}

/**
 * Ejecuta calibración de modelos
 */
async function runCalibration() {
    showLoading('Ejecutando calibración de modelos...\nEsto puede tardar varios minutos.');

    try {
        const response = await fetch('/api/calibrate', { method: 'POST' });

        if (!response.ok) {
            throw new Error('Error en la calibración');
        }

        const result = await response.json();

        if (result.success && result.results) {
            displayCalibrationResults(result.results);
            showAlert('✓ Calibración completada exitosamente', 'success');
        } else {
            throw new Error(result.error || 'Error desconocido');
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
    calibrationResultsBody.innerHTML = '';

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
            </tr>
        `;
        calibrationResultsBody.insertAdjacentHTML('beforeend', row);
    });

    // Mostrar mejor modelo
    const best = results[0];
    document.getElementById('bestModelAlert').innerHTML = `
        <i class="bi bi-trophy-fill"></i>
        <strong>Mejor modelo: ${best.model_name}</strong><br>
        R² = ${best.r2} | RMSE = ${best.rmse} µg/m³ | MAE = ${best.mae} µg/m³ | MAPE = ${best.mape}%
    `;

    calibrationResults.style.display = 'block';
}

/**
 * Utilidades
 */
function showLoading(message = 'Cargando...') {
    loadingMessage.textContent = message;
    loadingOverlay.classList.add('active');
}

function hideLoading() {
    loadingOverlay.classList.remove('active');
}

function getTitleForPlotType(type) {
    const titles = {
        'timeseries': 'Serie de Tiempo',
        'boxplot': 'Distribución (Diagrama de Caja)',
        'heatmap': 'Mapa de Calor por Hora del Día',
        'scatter': 'Diagrama de Dispersión'
    };
    return titles[type] || 'Visualización';
}

function convertToCSV(data) {
    if (!data || data.length === 0) return '';

    const keys = Object.keys(data[0]);
    const header = keys.join(',');
    const rows = data.map(row => {
        return keys.map(key => {
            const value = row[key];
            return typeof value === 'string' ? `"${value}"` : value;
        }).join(',');
    });

    return [header, ...rows].join('\n');
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '10000';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}
