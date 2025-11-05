/**
 * JavaScript para Visualización 2024
 */

let selectedDevice = null;
let selectedDeviceType = null;
let currentData = null;
let calibrationResults = null;
let activeViewMode = 'single';

const DATE_RANGE = {
    start: '2024-01-01',
    end: '2024-12-31'
};

const POLLUTANTS = ['pm25', 'pm10'];

const DEVICE_CONFIG = {
    Aire2: { type: 'sensor', label: 'Sensor Aire2' },
    Aire4: { type: 'sensor', label: 'Sensor Aire4' },
    Aire5: { type: 'sensor', label: 'Sensor Aire5' },
    RMCAB_MinAmb: { type: 'rmcab', label: 'RMCAB MinAmbiente', station: 17 }
};

const DEVICE_ORDER = ['Aire2', 'Aire4', 'Aire5', 'RMCAB_MinAmb'];
const deviceDataCache = {};
let currentFriendlyName = '';

const SERIES_COLORS = {
    pm25: '#006d77',
    pm10: '#d62828'
};

const BOX_COLORS = {
    pm25: '#83c5be',
    pm10: '#ffb703'
};

// Elementos del DOM - inicializados después de DOMContentLoaded
let btnLoadDevice, btnStartCalibration, btnCalibrateAll, loadingOverlay, loadingMessage;
let dataSection, calibrationSection, quickViewButtons, multiSensorSection, comparisonSection;

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Inicializando visualización 2024...');
    
    // Obtener elementos del DOM
    btnLoadDevice = document.getElementById('btnLoadDevice');
    btnStartCalibration = document.getElementById('btnStartCalibration');
    btnCalibrateAll = document.getElementById('btnCalibrateAll');
    loadingOverlay = document.getElementById('loadingOverlay');
    loadingMessage = document.getElementById('loadingMessage');
    dataSection = document.getElementById('dataSection');
    calibrationSection = document.getElementById('calibrationSection');
    quickViewButtons = document.querySelectorAll('.quick-view-btn');
    multiSensorSection = document.getElementById('multiSensorSection');
    comparisonSection = document.getElementById('comparisonSection');

    // Verificar elementos
    console.log('Elementos del DOM verificados:');
    console.log('  - btnLoadDevice:', !!btnLoadDevice);
    console.log('  - btnStartCalibration:', !!btnStartCalibration);
    console.log('  - calibrationSection:', !!calibrationSection);
    console.log('  - comparisonSection:', !!comparisonSection);
    console.log('  - quickViewButtons:', quickViewButtons.length);
    
    // Verificar Plotly
    if (typeof Plotly === 'undefined') {
        console.error('❌ Plotly NO está cargado');
    } else {
        console.log('✅ Plotly cargado correctamente');
    }

    // Event Listeners
    const multiCalibrationBtn = document.getElementById('multipleCalibrationBtn');
    if (multiCalibrationBtn) {
        multiCalibrationBtn.addEventListener('click', runMultipleCalibration);
        console.log('✅ Botón calibración múltiple conectado');
    }

    const btnPrediction = document.getElementById('btnPrediction');
    if (btnPrediction) {
        btnPrediction.addEventListener('click', showPredictionSection);
        console.log('✅ Botón predicción conectado');
    }

    const btnRunPrediction = document.getElementById('btnRunPrediction');
    if (btnRunPrediction) {
        btnRunPrediction.addEventListener('click', runPrediction);
        console.log('✅ Botón ejecutar predicción conectado');
    }

    const btnRunManualPrediction = document.getElementById('btnRunManualPrediction');
    if (btnRunManualPrediction) {
        btnRunManualPrediction.addEventListener('click', runManualPrediction);
        console.log('✅ Botón predicción manual conectado');
    }

    const btnCancelManual = document.getElementById('btnCancelManual');
    if (btnCancelManual) {
        btnCancelManual.addEventListener('click', hideManualInputSection);
        console.log('✅ Botón cancelar manual conectado');
    }

    if (btnLoadDevice) btnLoadDevice.addEventListener('click', () => loadDeviceData());
    if (btnStartCalibration) btnStartCalibration.addEventListener('click', runCalibration);
    if (btnCalibrateAll) btnCalibrateAll.addEventListener('click', runMultipleCalibration);

    quickViewButtons.forEach(button => {
        button.addEventListener('click', async () => {
            try {
                const isComparison = button.dataset.view === 'comparison';
                if (isComparison) {
                    await showComparisonView();
                    setActiveQuickButton(button);
                    return;
                }

                const deviceName = button.dataset.device;
                if (!deviceName) {
                    return;
                }

                await loadDeviceData(deviceName);
                setActiveQuickButton(button);
            } catch (error) {
                console.error(error);
            }
        });
    });
    
    console.log('✅ Visualización inicializada correctamente');
});

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
    const quickButton = document.querySelector(`.quick-view-btn[data-device="${selectedDevice}"]`);
    setActiveQuickButton(quickButton);
}

function selectDeviceByName(deviceName) {
    if (!deviceName) {
        return;
    }

    const config = DEVICE_CONFIG[deviceName] || {};

    selectedDevice = deviceName;
    if (config.type) {
        selectedDeviceType = config.type;
    }

    btnLoadDevice.disabled = false;
}

function setActiveQuickButton(targetButton) {
    quickViewButtons.forEach(btn => btn.classList.remove('active'));
    if (targetButton) {
        targetButton.classList.add('active');
    }
}

function highlightQuickButtonForDevice(deviceName) {
    if (!deviceName) {
        return;
    }

    const button = document.querySelector(`.quick-view-btn[data-device="${deviceName}"]`);
    setActiveQuickButton(button);
}

/**
 * Carga datos del dispositivo seleccionado
 */


async function loadDeviceData(deviceName = null) {
    const targetDevice = deviceName || selectedDevice;

    if (!targetDevice) {
        showAlert("Por favor selecciona un dispositivo primero", "warning");
        return;
    }

    const deviceConfig = DEVICE_CONFIG[targetDevice];

    if (!deviceConfig) {
        showAlert(`Dispositivo no configurado: ${targetDevice}`, "danger");
        return;
    }

    selectDeviceByName(targetDevice);
    highlightQuickButtonForDevice(targetDevice);

    const friendlyName = deviceConfig.label || targetDevice;
    showLoading(`Cargando datos de ${friendlyName}...`);

    try {
        const result = await getDeviceData(targetDevice);

        currentData = result.data;
        const recordCount = result.records ?? (Array.isArray(result.data) ? result.data.length : 0);

        showAlert(`Datos cargados: ${recordCount} registros`, "success");

        currentFriendlyName = friendlyName;
        document.getElementById("selectedDeviceName").textContent = friendlyName;
        showSingleSensorView();

        await generateDataVisualizations(result.data, friendlyName);

        dataSection.scrollIntoView({ behavior: "smooth" });
    } catch (error) {
        showAlert(`Error: ${error.message}`, "danger");
        console.error(error);
    } finally {
        hideLoading();
        btnStartCalibration.disabled = false;
    }
}

async function getDeviceData(deviceName, forceRefresh = false) {
    if (!deviceName) {
        throw new Error("Dispositivo no especificado");
    }

    if (!forceRefresh && deviceDataCache[deviceName]) {
        return deviceDataCache[deviceName];
    }

    const config = DEVICE_CONFIG[deviceName];

    if (!config) {
        throw new Error(`Dispositivo no configurado: ${deviceName}`);
    }

    const payload = {
        start_date: DATE_RANGE.start,
        end_date: DATE_RANGE.end
    };

    let url = '';

    if (config.type === 'sensor') {
        url = '/api/load-device-data';
        payload.device_name = deviceName;
    } else {
        url = '/api/load-rmcab-data';
        payload.station_code = config.station ?? 6;
    }

    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        let message = 'Error al cargar los datos';
        try {
            const errorResponse = await response.json();
            if (errorResponse && errorResponse.error) {
                message = errorResponse.error;
            }
        } catch (parseError) {
            console.warn('No se pudo interpretar el error recibido del servidor', parseError);
        }
        throw new Error(message);
    }

    const result = await response.json();

    if (!result.success) {
        throw new Error(result.error || 'No se pudo obtener la informacion solicitada');
    }

    deviceDataCache[deviceName] = result;
    return result;
}

function showSingleSensorView() {
    activeViewMode = 'single';
    dataSection.style.display = 'block';
    multiSensorSection.style.display = 'none';
    calibrationSection.style.display = 'none';
    if (comparisonSection) {
        comparisonSection.style.display = 'none';
    }
}



/**
 * Genera visualizaciones de datos
 */
async function generateDataVisualizations(data, deviceLabel = null) {
    // Calcular métricas resumen
    displayMetrics(data);

    // Generar gráficos
    createTimeSeriesPlot(data, deviceLabel);
    createBoxPlots(data, deviceLabel);
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

    const pm25Average = pm25Values.length
        ? (pm25Values.reduce((sum, value) => sum + value, 0) / pm25Values.length).toFixed(2) + ' ug/m3'
        : 'Sin datos';

    const pm10Average = pm10Values.length
        ? (pm10Values.reduce((sum, value) => sum + value, 0) / pm10Values.length).toFixed(2) + ' ug/m3'
        : 'Sin datos';

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
            value: pm25Average,
            color: 'success'
        },
        {
            icon: 'cloud-haze2',
            title: 'PM10 Promedio',
            value: pm10Average,
            color: 'info'
        },
        {
            icon: 'calendar-range',
            title: 'Periodo',
            value: '2024',
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
async function showComparisonView() {
    activeViewMode = 'comparison';

    const comparisonButton = document.querySelector('.quick-view-btn[data-view="comparison"]');
    setActiveQuickButton(comparisonButton);
    showLoading('Preparando comparativa de sensores...');

    try {
        const datasets = {};

        for (const deviceName of DEVICE_ORDER) {
            try {
                const result = await getDeviceData(deviceName);
                datasets[deviceName] = result.data || [];
            } catch (loadError) {
                console.error(`Error cargando ${deviceName}:`, loadError);
                datasets[deviceName] = [];
            }
        }

        renderComparisonPlots(datasets);

        dataSection.style.display = 'none';
        calibrationSection.style.display = 'none';
        if (comparisonSection) {
            comparisonSection.style.display = 'none';
        }
        multiSensorSection.style.display = 'block';
        multiSensorSection.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        showAlert(`Error preparando comparativa: ${error.message}`, 'danger');
        console.error(error);
    } finally {
        hideLoading();
    }
}

function renderComparisonPlots(datasets) {
    DEVICE_ORDER.forEach(deviceName => {
        const containerId = `comparisonPlot${deviceName}`;
        const container = document.getElementById(containerId);
        if (!container) {
            return;
        }

        const deviceData = Array.isArray(datasets[deviceName]) ? datasets[deviceName] : [];
        const pm25Values = deviceData.filter(d => d.pm25 != null);
        const pm10Values = deviceData.filter(d => d.pm10 != null);
        const pm25Count = pm25Values.length;
        const pm10Count = pm10Values.length;

        if (!pm25Count && !pm10Count) {
            container.innerHTML = '<p class="text-muted mb-0">Sin datos disponibles.</p>';
            Plotly.purge(container);
            return;
        }

        container.innerHTML = '';

        const label = DEVICE_CONFIG[deviceName]?.label || deviceName;
        const traces = [];

        if (pm25Count) {
            traces.push({
                x: pm25Values.map(d => d.datetime),
                y: pm25Values.map(d => d.pm25),
                type: 'scatter',
                mode: 'lines',
                name: `PM2.5 (n=${pm25Count})`,
                line: { color: SERIES_COLORS.pm25, width: 2 }
            });
        }

        if (pm10Count) {
            traces.push({
                x: pm10Values.map(d => d.datetime),
                y: pm10Values.map(d => d.pm10),
                type: 'scatter',
                mode: 'lines',
                name: `PM10 (n=${pm10Count})`,
                line: { color: SERIES_COLORS.pm10, width: 2 }
            });
        }

        const layout = {
            title: `${label} (PM2.5: ${pm25Count} | PM10: ${pm10Count})`,
            margin: { t: 40, r: 20, l: 50, b: 50 },
            hovermode: 'x unified',
            height: 320,
            legend: { orientation: 'h', x: 0, y: -0.2 },
            xaxis: { title: 'Fecha y Hora' },
            yaxis: { title: 'Concentracion (ug/m3)' }
        };

        Plotly.newPlot(container, traces, layout, { responsive: true });
    });
}

/**
 * Crea gráfico de series de tiempo
 */
function createTimeSeriesPlot(data, deviceLabel) {
    const container = document.getElementById('timeSeriesPlot');
    if (!container) {
        console.error('Container timeSeriesPlot not found');
        return;
    }

    const pm25Data = data.filter(d => d.pm25 != null);
    const pm10Data = data.filter(d => d.pm10 != null);

    if (pm25Data.length === 0 && pm10Data.length === 0) {
        container.innerHTML = '<p class="text-center text-muted">No hay datos disponibles para graficar</p>';
        return;
    }

    const traces = [];

    // Trace PM2.5
    if (pm25Data.length > 0) {
        traces.push({
            x: pm25Data.map(d => d.datetime),
            y: pm25Data.map(d => d.pm25),
            type: 'scatter',
            mode: 'lines',
            name: 'PM2.5',
            line: { color: SERIES_COLORS.pm25, width: 2 }
        });
    }

    // Trace PM10
    if (pm10Data.length > 0) {
        traces.push({
            x: pm10Data.map(d => d.datetime),
            y: pm10Data.map(d => d.pm10),
            type: 'scatter',
            mode: 'lines',
            name: 'PM10',
            line: { color: SERIES_COLORS.pm10, width: 2 }
        });
    }

    // Líneas de límites normativos
    // OMS PM2.5: 15 µg/m³ (24h)
    traces.push({
        x: [pm25Data[0]?.datetime, pm25Data[pm25Data.length - 1]?.datetime],
        y: [15, 15],
        type: 'scatter',
        mode: 'lines',
        name: 'Límite OMS PM2.5',
        line: { color: '#ffc107', width: 2, dash: 'dash' },
        hovertemplate: 'OMS PM2.5: 15 µg/m³<extra></extra>'
    });

    // OMS PM10: 45 µg/m³ (24h)
    traces.push({
        x: [pm10Data[0]?.datetime, pm10Data[pm10Data.length - 1]?.datetime],
        y: [45, 45],
        type: 'scatter',
        mode: 'lines',
        name: 'Límite OMS PM10',
        line: { color: '#dc3545', width: 2, dash: 'dash' },
        hovertemplate: 'OMS PM10: 45 µg/m³<extra></extra>'
    });

    const layout = {
        title: `Series de Tiempo - ${deviceLabel || 'Dispositivo'}`,
        xaxis: {
            title: 'Fecha y Hora',
            type: 'date'
        },
        yaxis: {
            title: 'Concentración (µg/m³)',
            rangemode: 'tozero'
        },
        hovermode: 'x unified',
        showlegend: true,
        legend: {
            orientation: 'h',
            y: -0.2
        },
        margin: { t: 50, r: 50, l: 70, b: 100 }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false
    };

    Plotly.newPlot(container, traces, layout, config);
}

/**
 * Crea gráficos de caja (boxplots)
 */
function createBoxPlots(data, deviceLabel) {
    const pm25Container = document.getElementById('boxPlotPM25');
    const pm10Container = document.getElementById('boxPlotPM10');

    if (!pm25Container || !pm10Container) {
        console.error('Boxplot containers not found');
        return;
    }

    // BoxPlot PM2.5
    const pm25Values = data.filter(d => d.pm25 != null).map(d => d.pm25);
    
    if (pm25Values.length > 0) {
        const trace25 = {
            y: pm25Values,
            type: 'box',
            name: 'PM2.5',
            marker: { color: BOX_COLORS.pm25 },
            boxmean: 'sd'
        };

        const layout25 = {
            title: `Distribución PM2.5 - ${deviceLabel || 'Dispositivo'}`,
            yaxis: {
                title: 'Concentración (µg/m³)',
                rangemode: 'tozero'
            },
            showlegend: false,
            margin: { t: 50, r: 30, l: 70, b: 50 }
        };

        Plotly.newPlot(pm25Container, [trace25], layout25, { responsive: true, displaylogo: false });
    } else {
        pm25Container.innerHTML = '<p class="text-center text-muted">No hay datos PM2.5</p>';
    }

    // BoxPlot PM10
    const pm10Values = data.filter(d => d.pm10 != null).map(d => d.pm10);
    
    if (pm10Values.length > 0) {
        const trace10 = {
            y: pm10Values,
            type: 'box',
            name: 'PM10',
            marker: { color: BOX_COLORS.pm10 },
            boxmean: 'sd'
        };

        const layout10 = {
            title: `Distribución PM10 - ${deviceLabel || 'Dispositivo'}`,
            yaxis: {
                title: 'Concentración (µg/m³)',
                rangemode: 'tozero'
            },
            showlegend: false,
            margin: { t: 50, r: 30, l: 70, b: 50 }
        };

        Plotly.newPlot(pm10Container, [trace10], layout10, { responsive: true, displaylogo: false });
    } else {
        pm10Container.innerHTML = '<p class="text-center text-muted">No hay datos PM10</p>';
    }
}

/**
 * Ejecuta calibración para múltiples dispositivos
 */
async function runMultipleCalibration() {
    const devices = ['Aire2', 'Aire4', 'Aire5'];
    
    showLoading(`Calibrando ${devices.length} sensores...`);

    try {
        const payload = {
            devices: devices,
            start_date: DATE_RANGE.start,
            end_date: DATE_RANGE.end,
            pollutants: POLLUTANTS  // Enviar PM2.5 y PM10
        };

        console.log('Enviando petición de calibración múltiple:', payload);

        const response = await fetch('/api/calibrate-multiple-devices', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        console.log('Respuesta recibida:', response.status, response.statusText);

        const result = await response.json();
        console.log('Resultado completo de calibración múltiple:', result);

        if (!response.ok) {
            const errorMessage = result.error || `Error ${response.status}: ${response.statusText}`;
            console.error('Error del servidor:', errorMessage);
            throw new Error(errorMessage);
        }

        if (!result.success) {
            const errorDetail = result.error || 'Calibración fallida sin detalles';
            console.error('Calibración no exitosa:', errorDetail);
            console.error('Resultados por dispositivo:', result.results_by_device);
            
            // Mostrar detalles de cada dispositivo
            Object.keys(result.results_by_device).forEach(device => {
                const deviceResult = result.results_by_device[device];
                console.error(`${device}:`, deviceResult);
                if (!deviceResult.success) {
                    console.error(`  ❌ Error: ${deviceResult.error}`);
                }
            });
            
            // Aún si hay errores, intentar mostrar los que sí funcionaron
            const successfulDevices = Object.keys(result.results_by_device).filter(
                device => result.results_by_device[device].success
            );
            
            if (successfulDevices.length > 0) {
                console.log(`Mostrando ${successfulDevices.length} dispositivos exitosos`);
                displayMultipleCalibrationResults(result.results_by_device);
                calibrationSection.style.display = 'block';
                calibrationSection.scrollIntoView({ behavior: 'smooth' });
                showAlert(`⚠️ Calibración parcial: ${successfulDevices.length}/${result.total_devices} sensores`, 'warning');
                return; // No lanzar error si hay al menos uno exitoso
            }
            
            throw new Error(errorDetail);
        }

        // Mostrar resultados con pestañas
        displayMultipleCalibrationResults(result.results_by_device);

        calibrationSection.style.display = 'block';
        calibrationSection.scrollIntoView({ behavior: 'smooth' });

        // Habilitar botón de predicción después de calibración exitosa
        const btnPrediction = document.getElementById('btnPrediction');
        if (btnPrediction) {
            btnPrediction.disabled = false;
        }

        showAlert(`✅ Calibración completada para ${result.devices_calibrated}/${result.total_devices} sensores`, 'success');
    } catch (error) {
        showAlert(`❌ Error en calibración múltiple: ${error.message}`, 'danger');
        console.error('Error completo:', error);
        console.error('Stack trace:', error.stack);
    } finally {
        hideLoading();
    }
}

/**
 * Muestra resultados de calibración múltiple con pestañas
 */
function displayMultipleCalibrationResults(resultsByDevice) {
    const tabsContainer = document.getElementById('calibrationDeviceTabs');
    const contentContainer = document.getElementById('calibrationDeviceTabContent');

    if (!tabsContainer || !contentContainer) {
        console.error('Contenedores de pestañas no encontrados');
        return;
    }

    console.log('🎨 Renderizando resultados de calibración:', resultsByDevice);

    tabsContainer.innerHTML = '';
    contentContainer.innerHTML = '';

    const devices = Object.keys(resultsByDevice);
    
    if (devices.length === 0) {
        contentContainer.innerHTML = '<p class="text-center text-muted">No hay resultados disponibles</p>';
        return;
    }

    devices.forEach((deviceName, index) => {
        const isActive = index === 0;
        const result = resultsByDevice[deviceName];
        const tabId = `tab-${deviceName}`;
        const paneId = `pane-${deviceName}`;

        console.log(`📋 Procesando ${deviceName}:`, result);

        // Crear pestaña
        const tabItem = document.createElement('li');
        tabItem.className = 'nav-item';
        tabItem.role = 'presentation';

        const statusIcon = result.success 
            ? '<i class="bi bi-check-circle-fill text-success"></i>' 
            : '<i class="bi bi-x-circle-fill text-danger"></i>';

        tabItem.innerHTML = `
            <button class="nav-link ${isActive ? 'active' : ''}" 
                    id="${tabId}" 
                    data-bs-toggle="tab" 
                    data-bs-target="#${paneId}" 
                    type="button" 
                    role="tab" 
                    aria-controls="${paneId}" 
                    aria-selected="${isActive}">
                ${statusIcon} ${deviceName}
            </button>
        `;

        tabsContainer.appendChild(tabItem);

        // Crear contenido de la pestaña
        const paneDiv = document.createElement('div');
        paneDiv.className = `tab-pane fade ${isActive ? 'show active' : ''}`;
        paneDiv.id = paneId;
        paneDiv.role = 'tabpanel';
        paneDiv.setAttribute('aria-labelledby', tabId);

        if (result.success && result.pollutant_results) {
            paneDiv.innerHTML = createMultiPollutantContent(deviceName, result);
        } else if (result.success) {
            // Backward compatibility: si no hay pollutant_results, usar la estructura antigua
            paneDiv.innerHTML = createDeviceCalibrationContent(deviceName, result);
        } else {
            paneDiv.innerHTML = `
                <div class="alert alert-danger">
                    <h5><i class="bi bi-exclamation-triangle"></i> Error en ${deviceName}</h5>
                    <p class="mb-0">${result.error || 'Error desconocido'}</p>
                </div>
            `;
        }

        contentContainer.appendChild(paneDiv);
    });

    // Inicializar gráficos para la primera pestaña
    setTimeout(() => {
        const firstDevice = devices[0];
        const firstResult = resultsByDevice[firstDevice];
        if (firstResult.success) {
            renderDeviceMultiPollutantGraphs(firstDevice, firstResult);
        }
    }, 100);

    // Agregar listener para cargar gráficos al cambiar de pestaña
    tabsContainer.addEventListener('shown.bs.tab', (event) => {
        const targetPaneId = event.target.getAttribute('data-bs-target');
        const deviceName = targetPaneId.replace('#pane-', '');
        const result = resultsByDevice[deviceName];
        
        if (result && result.success) {
            setTimeout(() => renderDeviceMultiPollutantGraphs(deviceName, result), 100);
        }
    });
}

/**
 * Crea el HTML del contenido de calibración para un dispositivo
 */
function createDeviceCalibrationContent(deviceName, result) {
    return `
        <div class="mb-3">
            <div class="row">
                <div class="col-md-4">
                    <div class="metric-card">
                        <i class="bi bi-database-fill display-6 text-primary"></i>
                        <h4>${result.records || 0}</h4>
                        <p class="text-muted mb-0">Registros Totales</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="metric-card">
                        <i class="bi bi-check-circle-fill display-6 text-success"></i>
                        <h4>${result.records_after_cleaning || 0}</h4>
                        <p class="text-muted mb-0">Después de Limpieza</p>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="metric-card">
                        <i class="bi bi-trash-fill display-6 text-warning"></i>
                        <h4>${result.outliers_removed || 0}</h4>
                        <p class="text-muted mb-0">Outliers Eliminados</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tabla de Modelos -->
        <div class="plot-container mb-4">
            <h5>Comparación de Modelos - ${deviceName}</h5>
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead>
                        <tr>
                            <th>Modelo</th>
                            <th>R²</th>
                            <th>R² Ajustado</th>
                            <th>RMSE</th>
                            <th>MAE</th>
                            <th>MAPE</th>
                            <th>Overfitting</th>
                        </tr>
                    </thead>
                    <tbody id="modelsTableBody-${deviceName}"></tbody>
                </table>
            </div>
        </div>

        <!-- Gráfico de Comparación -->
        <div class="plot-container mb-4">
            <h5>Gráfico de Comparación de Métricas - ${deviceName}</h5>
            <div id="modelsComparisonPlot-${deviceName}" style="min-height: 400px;"></div>
        </div>

        <!-- Fórmula Lineal -->
        <div id="linearFormulaContainer-${deviceName}"></div>

        <!-- Scatter Plot -->
        <div class="plot-container">
            <h5>Gráfico de Calibración (Real vs Predicho) - ${deviceName}</h5>
            <div id="scatterPlotsContainer-${deviceName}" style="min-height: 500px;"></div>
        </div>
    `;
}

/**
 * Renderiza los gráficos para un dispositivo específico
 */
function renderDeviceGraphs(deviceName, result) {
    console.log(`Renderizando gráficos para ${deviceName}`);

    // Renderizar tabla
    const tableBody = document.getElementById(`modelsTableBody-${deviceName}`);
    if (tableBody && result.results) {
        tableBody.innerHTML = '';
        result.results.forEach((model, index) => {
            const isBest = index === 0 || model.is_best;
            const rowClass = isBest ? 'table-success' : '';
            const badge = isBest ? '<span class="badge bg-success ms-2">Mejor</span>' : '';

            const overfittingBadge = model.overfitting ? 
                (model.overfitting.status === 'ok' ? 
                    '<span class="badge bg-success">OK</span>' : 
                    `<span class="badge bg-warning">${model.overfitting.severity}</span>`) 
                : '<span class="badge bg-secondary">N/A</span>';

            const row = `
                <tr class="${rowClass}">
                    <td><strong>${model.model_name || 'Desconocido'}</strong>${badge}</td>
                    <td>${model.r2 !== undefined ? model.r2.toFixed(4) : 'N/A'}</td>
                    <td>${model.r2_adjusted !== undefined ? model.r2_adjusted.toFixed(4) : 'N/A'}</td>
                    <td>${model.rmse !== undefined ? model.rmse.toFixed(2) : 'N/A'}</td>
                    <td>${model.mae !== undefined ? model.mae.toFixed(2) : 'N/A'}</td>
                    <td>${model.mape !== undefined ? model.mape.toFixed(2) + '%' : 'N/A'}</td>
                    <td>${overfittingBadge}</td>
                </tr>
            `;
            tableBody.insertAdjacentHTML('beforeend', row);
        });
    }

    // Renderizar gráfico de comparación
    const comparisonContainer = document.getElementById(`modelsComparisonPlot-${deviceName}`);
    if (comparisonContainer && result.results && result.results.length > 0) {
        try {
            const modelNames = result.results.map(m => m.model_name || 'Desconocido');
            const r2Values = result.results.map(m => m.r2 || 0);
            const rmseValues = result.results.map(m => m.rmse || 0);

            const trace1 = {
                x: modelNames,
                y: r2Values,
                type: 'bar',
                name: 'R²',
                marker: { color: '#28a745' },
                text: r2Values.map(v => v.toFixed(4)),
                textposition: 'auto'
            };

            const trace2 = {
                x: modelNames,
                y: rmseValues,
                type: 'bar',
                name: 'RMSE',
                yaxis: 'y2',
                marker: { color: '#dc3545' },
                text: rmseValues.map(v => v.toFixed(2)),
                textposition: 'auto'
            };

            const layout = {
                title: `Comparación de Modelos - ${deviceName}`,
                xaxis: {
                    tickangle: -45,
                    automargin: true
                },
                yaxis: {
                    title: 'R²',
                    rangemode: 'tozero'
                },
                yaxis2: {
                    title: 'RMSE (µg/m³)',
                    overlaying: 'y',
                    side: 'right',
                    rangemode: 'tozero'
                },
                legend: {
                    x: 0.5,
                    y: 1.15,
                    xanchor: 'center',
                    orientation: 'h'
                },
                margin: { t: 80, r: 80, l: 70, b: 140 },
                height: 400
            };

            Plotly.newPlot(comparisonContainer, [trace1, trace2], layout, { responsive: true, displaylogo: false });
        } catch (error) {
            console.error(`Error creando gráfico de comparación para ${deviceName}:`, error);
        }
    }

    // Renderizar scatter plot
    const scatterContainer = document.getElementById(`scatterPlotsContainer-${deviceName}`);
    if (scatterContainer && result.scatter && result.scatter.points && result.scatter.points.length > 0) {
        try {
            const points = result.scatter.points;
            const actualValues = points.map(p => p.actual);
            const predictedValues = points.map(p => p.predicted);

            const trace1 = {
                x: actualValues,
                y: predictedValues,
                mode: 'markers',
                type: 'scatter',
                name: 'Predicciones',
                marker: {
                    color: '#006d77',
                    size: 8,
                    opacity: 0.6
                },
                text: actualValues.map((val, i) => 
                    `Real: ${val.toFixed(2)}<br>Predicho: ${predictedValues[i].toFixed(2)}`
                ),
                hovertemplate: '%{text}<extra></extra>'
            };

            const minVal = Math.min(...actualValues, ...predictedValues);
            const maxVal = Math.max(...actualValues, ...predictedValues);

            const trace2 = {
                x: [minVal, maxVal],
                y: [minVal, maxVal],
                mode: 'lines',
                type: 'scatter',
                name: 'Línea perfecta (y=x)',
                line: {
                    color: '#dc3545',
                    dash: 'dash',
                    width: 2
                }
            };

            const r2Value = result.results && result.results[0] ? result.results[0].r2 : null;
            const titleText = r2Value 
                ? `${deviceName} - R² = ${r2Value.toFixed(4)}`
                : deviceName;

            const layout = {
                title: titleText,
                xaxis: {
                    title: 'PM2.5 Real (µg/m³)',
                    rangemode: 'tozero'
                },
                yaxis: {
                    title: 'PM2.5 Predicho (µg/m³)',
                    rangemode: 'tozero',
                    scaleanchor: 'x',
                    scaleratio: 1
                },
                showlegend: true,
                legend: {
                    orientation: 'h',
                    y: -0.15,
                    x: 0.5,
                    xanchor: 'center'
                },
                margin: { t: 60, r: 50, l: 70, b: 100 },
                height: 500
            };

            Plotly.newPlot(scatterContainer, [trace1, trace2], layout, { responsive: true, displaylogo: false });
        } catch (error) {
            console.error(`Error creando scatter plot para ${deviceName}:`, error);
        }
    }

    // Renderizar fórmula lineal
    const formulaContainer = document.getElementById(`linearFormulaContainer-${deviceName}`);
    if (formulaContainer && result.linear_regression && result.linear_regression.formula) {
        formulaContainer.innerHTML = `
            <div class="alert alert-info">
                <h5><i class="bi bi-calculator"></i> Fórmula de Regresión Lineal - ${deviceName}</h5>
                <p class="mb-0"><code>${result.linear_regression.formula}</code></p>
            </div>
        `;
    }
}

/**
 * Muestra resultados de calibración individual (mantener para compatibilidad)
 */
function displayCalibrationResults(result) {
    console.log('Mostrando resultados:', result);
    
    // Usar el sistema de pestañas con un solo dispositivo
    const deviceName = result.device || selectedDevice || 'Sensor';
    const resultsByDevice = {};
    resultsByDevice[deviceName] = result;
    
    displayMultipleCalibrationResults(resultsByDevice);
}

/**
 * Ejecuta la calibración
 */
async function runCalibration() {
    if (!selectedDevice || !currentData) {
        showAlert('Primero carga los datos de un dispositivo', 'warning');
        return;
    }

    const config = DEVICE_CONFIG[selectedDevice];
    if (!config || config.type !== 'sensor') {
        showAlert('Solo se puede calibrar sensores de bajo costo', 'warning');
        return;
    }

    showLoading('Ejecutando calibración con 6 modelos de ML...');

    try {
        const payload = {
            device_name: selectedDevice,
            start_date: DATE_RANGE.start,
            end_date: DATE_RANGE.end,
            pollutant: 'pm25'
        };

        console.log('Enviando petición de calibración:', payload);

        const response = await fetch('/api/calibrate-device', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        console.log('Respuesta recibida:', response.status);

        if (!response.ok) {
            let errorMessage = 'Error en la calibración';
            try {
                const errorData = await response.json();
                errorMessage = errorData.error || errorMessage;
            } catch (e) {
                console.error('Error parseando respuesta de error:', e);
            }
            throw new Error(errorMessage);
        }

        const result = await response.json();
        console.log('Resultado de calibración:', result);

        if (!result.success) {
            throw new Error(result.error || 'Calibración fallida');
        }

        calibrationResults = result;
        displayCalibrationResults(result);

        calibrationSection.style.display = 'block';
        calibrationSection.scrollIntoView({ behavior: 'smooth' });

        // Encontrar el mejor modelo
        const bestModel = result.results && result.results.length > 0 
            ? result.results[0].model_name 
            : 'Desconocido';
        
        showAlert(`✅ Calibración completada exitosamente. Mejor modelo: ${bestModel}`, 'success');
    } catch (error) {
        showAlert(`❌ Error en calibración: ${error.message}`, 'danger');
        console.error('Error completo:', error);
    } finally {
        hideLoading();
    }
}

/**
 * Muestra resultados de calibración
 */
function displayCalibrationResults(result) {
    console.log('Mostrando resultados:', result);
    
    if (!result || !result.results || result.results.length === 0) {
        showAlert('No hay resultados de calibración para mostrar', 'warning');
        console.error('Resultado inválido:', result);
        return;
    }

    try {
        // Mostrar tabla de resultados
        displayModelsTable(result.results);

        // Mostrar gráfico de comparación de modelos
        createModelsComparisonChart(result.results);

        // Mostrar scatter plots
        if (result.scatter && result.scatter.points) {
            createCalibrationScatterPlots(result);
        } else {
            console.warn('No hay datos de scatter plot disponibles');
        }

        // Mostrar fórmula de regresión lineal si existe
        if (result.linear_regression && result.linear_regression.formula) {
            displayLinearFormula(result.linear_regression);
        } else {
            console.warn('No hay fórmula de regresión lineal disponible');
        }
    } catch (error) {
        console.error('Error mostrando resultados:', error);
        showAlert('Error al mostrar los resultados de calibración', 'danger');
    }
}

/**
 * Muestra tabla de modelos (Ya no se usa directamente, se usa en renderDeviceGraphs)
 */
function displayModelsTable(models) {
    // Esta función se mantiene para compatibilidad pero ya no se usa directamente
    console.warn('displayModelsTable is deprecated, use renderDeviceGraphs instead');
}

/**
 * Crea gráfico de comparación de modelos (Ya no se usa directamente)
 */
function createModelsComparisonChart(models) {
    // Esta función se mantiene para compatibilidad pero ya no se usa directamente
    console.warn('createModelsComparisonChart is deprecated, use renderDeviceGraphs instead');
}

/**
 * Crea scatter plots de calibración (Ya no se usa directamente)
 */
function createCalibrationScatterPlots(result) {
    // Esta función se mantiene para compatibilidad pero ya no se usa directamente
    console.warn('createCalibrationScatterPlots is deprecated, use renderDeviceGraphs instead');
}

/**
 * Muestra la fórmula de regresión lineal
 */
function displayLinearFormula(linearReg) {
    const container = document.getElementById('linearFormulaContainer');
    if (!container) return;

    const formula = linearReg.formula || 'No disponible';

    container.innerHTML = `
        <div class="alert alert-info">
            <h5><i class="bi bi-calculator"></i> Fórmula de Regresión Lineal</h5>
            <p class="mb-0"><code>${formula}</code></p>
        </div>
    `;
}

/**
 * Crea contenido para múltiples contaminantes (PM2.5 y PM10)
 */
function createMultiPollutantContent(deviceName, result) {
    const pollutantResults = result.pollutant_results || [];
    
    if (pollutantResults.length === 0) {
        return '<p class="text-center text-muted">No hay resultados de calibración</p>';
    }

    // Crear pestañas internas para cada contaminante
    const pollutantTabsHtml = pollutantResults.map((pr, idx) => {
        const isActive = idx === 0;
        const pollutantLabel = pr.pollutant_label || pr.pollutant;
        return `
            <li class="nav-item" role="presentation">
                <button class="nav-link ${isActive ? 'active' : ''}" 
                        id="tab-${deviceName}-${pr.pollutant}" 
                        data-bs-toggle="tab" 
                        data-bs-target="#pane-${deviceName}-${pr.pollutant}" 
                        type="button" 
                        role="tab">
                    ${pollutantLabel}
                </button>
            </li>
        `;
    }).join('');

    const pollutantPanesHtml = pollutantResults.map((pr, idx) => {
        const isActive = idx === 0;
        const models = pr.models || [];
        const records = pr.records || 0;
        const recordsAfterCleaning = pr.records_after_cleaning || 0;
        const outliersRemoved = pr.outliers_removed || 0;

        return `
            <div class="tab-pane fade ${isActive ? 'show active' : ''}" 
                 id="pane-${deviceName}-${pr.pollutant}" 
                 role="tabpanel">
                
                <!-- Métricas -->
                <div class="mb-3">
                    <div class="row">
                        <div class="col-md-4">
                            <div class="metric-card">
                                <i class="bi bi-database-fill display-6 text-primary"></i>
                                <h4>${records}</h4>
                                <p class="text-muted mb-0">Registros Totales</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="metric-card">
                                <i class="bi bi-check-circle-fill display-6 text-success"></i>
                                <h4>${recordsAfterCleaning}</h4>
                                <p class="text-muted mb-0">Después de Limpieza</p>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="metric-card">
                                <i class="bi bi-trash-fill display-6 text-warning"></i>
                                <h4>${outliersRemoved}</h4>
                                <p class="text-muted mb-0">Outliers Eliminados</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Tabla de Modelos -->
                <div class="plot-container mb-4">
                    <h5>Comparación de Modelos - ${pr.pollutant_label}</h5>
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Modelo</th>
                                    <th>R²</th>
                                    <th>R² Ajustado</th>
                                    <th>RMSE</th>
                                    <th>MAE</th>
                                    <th>MAPE (%)</th>
                                    <th>Overfitting</th>
                                </tr>
                            </thead>
                            <tbody id="modelsTableBody-${deviceName}-${pr.pollutant}"></tbody>
                        </table>
                    </div>
                </div>

                <!-- Gráfico de Comparación -->
                <div class="plot-container mb-4">
                    <h5>Gráfico de Comparación de Métricas</h5>
                    <div id="modelsComparisonPlot-${deviceName}-${pr.pollutant}" style="min-height: 400px;"></div>
                </div>

                <!-- Fórmula Lineal -->
                <div id="linearFormulaContainer-${deviceName}-${pr.pollutant}"></div>

                <!-- Scatter Plot -->
                <div class="plot-container">
                    <h5>Gráfico de Calibración (Real vs Predicho)</h5>
                    <div id="scatterPlotsContainer-${deviceName}-${pr.pollutant}" style="min-height: 500px;"></div>
                </div>
            </div>
        `;
    }).join('');

    return `
        <ul class="nav nav-pills mb-3" role="tablist">
            ${pollutantTabsHtml}
        </ul>
        <div class="tab-content">
            ${pollutantPanesHtml}
        </div>
    `;
}

/**
 * Renderiza gráficos para un dispositivo con múltiples contaminantes
 */
function renderDeviceMultiPollutantGraphs(deviceName, result) {
    console.log(`🎨 Renderizando gráficos para ${deviceName}`);

    if (!result.pollutant_results || result.pollutant_results.length === 0) {
        console.warn('No hay pollutant_results, usando estructura antigua');
        renderDeviceGraphs(deviceName, result);
        return;
    }

    // Renderizar cada contaminante
    result.pollutant_results.forEach(pr => {
        const pollutant = pr.pollutant;
        const models = pr.models || [];
        
        console.log(`  📊 Renderizando ${pr.pollutant_label}: ${models.length} modelos`);

        // Renderizar tabla
        const tableBody = document.getElementById(`modelsTableBody-${deviceName}-${pollutant}`);
        if (tableBody && models.length > 0) {
            tableBody.innerHTML = '';
            models.forEach((model, index) => {
                const isBest = index === 0 || model.is_best;
                const rowClass = isBest ? 'table-success' : '';
                const badge = isBest ? '<span class="badge bg-success ms-2">Mejor</span>' : '';

                const overfittingBadge = model.overfitting ? 
                    (model.overfitting.status === 'ok' ? 
                        '<span class="badge bg-success">OK</span>' : 
                        '<span class="badge bg-warning">Alto</span>') 
                    : '<span class="badge bg-secondary">N/A</span>';

                const row = `
                    <tr class="${rowClass}">
                        <td><strong>${model.model_name}</strong>${badge}</td>
                        <td>${model.r2?.toFixed(4) || 'N/A'}</td>
                        <td>${model.r2_adjusted?.toFixed(4) || 'N/A'}</td>
                        <td>${model.rmse?.toFixed(4) || 'N/A'}</td>
                        <td>${model.mae?.toFixed(4) || 'N/A'}</td>
                        <td>${model.mape?.toFixed(2) || 'N/A'}</td>
                        <td>${overfittingBadge}</td>
                    </tr>
                `;
                tableBody.innerHTML += row;
            });
        }

        // Renderizar gráfico de comparación de métricas
        const comparisonPlot = document.getElementById(`modelsComparisonPlot-${deviceName}-${pollutant}`);
        if (comparisonPlot && models.length > 0) {
            try {
                const modelNames = models.map(m => m.model_name);
                const r2Values = models.map(m => m.r2 || 0);
                const rmseValues = models.map(m => m.rmse || 0);

                const trace1 = {
                    x: modelNames,
                    y: r2Values,
                    name: 'R²',
                    type: 'bar',
                    marker: { color: '#007bff' }
                };

                const trace2 = {
                    x: modelNames,
                    y: rmseValues,
                    name: 'RMSE',
                    type: 'bar',
                    marker: { color: '#dc3545' },
                    yaxis: 'y2'
                };

                const layout = {
                    title: `Comparación de Modelos - ${pr.pollutant_label}`,
                    xaxis: { title: 'Modelos', tickangle: -45 },
                    yaxis: { title: 'R²', side: 'left' },
                    yaxis2: { title: 'RMSE', side: 'right', overlaying: 'y' },
                    showlegend: true,
                    legend: { x: 0.5, y: 1.1, xanchor: 'center', orientation: 'h' },
                    margin: { t: 50, r: 80, l: 70, b: 100 },
                    height: 400
                };

                Plotly.newPlot(comparisonPlot, [trace1, trace2], layout, { responsive: true, displaylogo: false });
            } catch (error) {
                console.error(`Error creando gráfico de comparación para ${pollutant}:`, error);
            }
        }

        // Renderizar scatter plot
        const scatterContainer = document.getElementById(`scatterPlotsContainer-${deviceName}-${pollutant}`);
        if (scatterContainer && pr.scatter) {
            try {
                const scatter = pr.scatter;
                const trace1 = {
                    x: scatter.y_test,
                    y: scatter.y_pred,
                    mode: 'markers',
                    type: 'scatter',
                    name: 'Predicciones',
                    marker: { color: '#007bff', size: 8, opacity: 0.6 }
                };

                const trace2 = {
                    x: scatter.y_test,
                    y: scatter.y_test,
                    mode: 'lines',
                    type: 'scatter',
                    name: 'Línea Ideal',
                    line: { color: '#dc3545', dash: 'dash', width: 2 }
                };

                const layout = {
                    title: `Calibración ${pr.pollutant_label} - ${deviceName}<br>Mejor Modelo: ${scatter.best_model}`,
                    xaxis: { title: `${pr.pollutant_label} Real (µg/m³)` },
                    yaxis: { title: `${pr.pollutant_label} Predicho (µg/m³)` },
                    showlegend: true,
                    legend: { x: 0.05, y: 0.95 },
                    margin: { t: 80, r: 50, l: 70, b: 70 },
                    height: 500
                };

                Plotly.newPlot(scatterContainer, [trace1, trace2], layout, { responsive: true, displaylogo: false });
            } catch (error) {
                console.error(`Error creando scatter plot para ${pollutant}:`, error);
            }
        }

        // Renderizar fórmula lineal
        const formulaContainer = document.getElementById(`linearFormulaContainer-${deviceName}-${pollutant}`);
        if (formulaContainer && pr.linear_regression && pr.linear_regression.formula) {
            formulaContainer.innerHTML = `
                <div class="alert alert-info">
                    <h5><i class="bi bi-calculator"></i> Fórmula de Regresión Lineal - ${pr.pollutant_label}</h5>
                    <p class="mb-0"><code>${pr.linear_regression.formula}</code></p>
                </div>
            `;
        }
    });
}

/**
 * Muestra la sección de predicción
 */
function showPredictionSection() {
    const predictionSection = document.getElementById('predictionSection');
    if (predictionSection) {
        predictionSection.style.display = 'block';
        predictionSection.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Muestra la sección de entrada manual
 */
function showManualInputSection() {
    const manualInputSection = document.getElementById('manualInputSection');
    const pollutantSelect = document.getElementById('predictionPollutant');
    const pollutantLabel = document.getElementById('manualPollutantLabel');

    if (manualInputSection) {
        // Actualizar label según contaminante seleccionado
        if (pollutantLabel && pollutantSelect) {
            const pollutant = pollutantSelect.value.toUpperCase();
            pollutantLabel.textContent = `${pollutant} del Sensor (µg/m³)`;
        }

        manualInputSection.style.display = 'block';
        manualInputSection.scrollIntoView({ behavior: 'smooth' });
    }
}

/**
 * Oculta la sección de entrada manual
 */
function hideManualInputSection() {
    const manualInputSection = document.getElementById('manualInputSection');
    if (manualInputSection) {
        manualInputSection.style.display = 'none';
    }
}

/**
 * Ejecuta predicción con modelo calibrado (intenta con datos reales primero)
 */
async function runPrediction() {
    const deviceSelect = document.getElementById('predictionDevice');
    const dateInput = document.getElementById('predictionDate');
    const pollutantSelect = document.getElementById('predictionPollutant');

    const device_name = deviceSelect.value;
    const target_date = dateInput.value;
    const pollutant = pollutantSelect.value;

    if (!device_name) {
        showAlert('Por favor selecciona un sensor', 'warning');
        return;
    }

    if (!target_date) {
        showAlert('Por favor selecciona una fecha', 'warning');
        return;
    }

    showLoading('Generando predicción...');

    try {
        const payload = {
            device_name: device_name,
            pollutant: pollutant,
            target_date: target_date,
            period: '2024',
            station_code: 17  // MinAmbiente
        };

        const response = await fetch('/api/predict-with-calibration', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (!response.ok) {
            // Si el error sugiere usar modo manual, mostrar campos
            if (result.suggestion === 'use_manual_mode') {
                hideLoading();
                showManualInputSection();
                showAlert(result.message, 'warning');
                return;
            }
            throw new Error(result.error || 'Error en la predicción');
        }

        console.log('Resultado de predicción:', result);

        // Ocultar campos manuales si estaban visibles
        hideManualInputSection();

        displayPredictionResults(result);

    } catch (error) {
        showAlert(`❌ Error en predicción: ${error.message}`, 'danger');
        console.error(error);
    } finally {
        hideLoading();
    }
}

/**
 * Ejecuta predicción con valores manuales
 */
async function runManualPrediction() {
    const deviceSelect = document.getElementById('predictionDevice');
    const dateInput = document.getElementById('predictionDate');
    const pollutantSelect = document.getElementById('predictionPollutant');

    const manualPMValue = document.getElementById('manualPMValue');
    const manualTemperature = document.getElementById('manualTemperature');
    const manualRH = document.getElementById('manualRH');

    const device_name = deviceSelect.value;
    const target_date = dateInput.value;
    const pollutant = pollutantSelect.value;

    if (!device_name || !target_date) {
        showAlert('Por favor completa todos los campos', 'warning');
        return;
    }

    // Validar valores manuales
    const pm_value = parseFloat(manualPMValue.value);
    const temp_value = parseFloat(manualTemperature.value);
    const rh_value = parseFloat(manualRH.value);

    if (isNaN(pm_value) || isNaN(temp_value) || isNaN(rh_value)) {
        showAlert('Por favor ingresa valores numéricos válidos', 'warning');
        return;
    }

    showLoading('Generando predicción con valores manuales...');

    try {
        const payload = {
            device_name: device_name,
            pollutant: pollutant,
            target_date: target_date,
            period: '2024',
            station_code: 17,  // MinAmbiente
            manual_values: {
                [`${pollutant}_sensor`]: pm_value,
                temperature: temp_value,
                rh: rh_value
            }
        };

        console.log('Enviando predicción manual:', payload);

        const response = await fetch('/api/predict-with-calibration', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || 'Error en la predicción');
        }

        console.log('Resultado de predicción manual:', result);

        hideManualInputSection();
        displayPredictionResults(result);

    } catch (error) {
        showAlert(`❌ Error en predicción manual: ${error.message}`, 'danger');
        console.error(error);
    } finally {
        hideLoading();
    }
}

/**
 * Muestra los resultados de predicción en la UI
 */
function displayPredictionResults(result) {
    const predictionResults = document.getElementById('predictionResults');
    const predictionMetrics = document.getElementById('predictionMetrics');
    const predictionPlot = document.getElementById('predictionPlot');

    const device_name = result.device_name;
    const pollutant = result.pollutant;
    const mode = result.mode || 'real_data';

    // Mostrar métricas
    if (result.error_stats) {
        predictionMetrics.innerHTML = `
            <div class="metric-card">
                <h6>RMSE</h6>
                <p class="h4">${result.error_stats.rmse}</p>
            </div>
            <div class="metric-card">
                <h6>MAE</h6>
                <p class="h4">${result.error_stats.mae}</p>
            </div>
            <div class="metric-card">
                <h6>R²</h6>
                <p class="h4">${result.error_stats.r2}</p>
            </div>
            <div class="metric-card">
                <h6>Error Promedio</h6>
                <p class="h4">${result.error_stats.mean_error}</p>
            </div>
            <div class="metric-card">
                <h6>Comparaciones</h6>
                <p class="h4">${result.error_stats.comparisons_count}</p>
            </div>
        `;
    } else {
        predictionMetrics.innerHTML = `
            <div class="alert alert-warning">
                No hay datos de RMCAB disponibles para comparación en esta fecha.
            </div>
        `;
    }

    // Crear gráfico de predicción
    const datetimes = result.predictions.map(p => p.datetime);
    const sensorRaw = result.predictions.map(p => p.sensor_raw);
    const predicted = result.predictions.map(p => p.predicted);
    const rmcabReference = result.predictions.map(p => p.rmcab_reference || null);

    const traces = [
        {
            x: datetimes,
            y: sensorRaw,
            type: 'scatter',
            mode: 'lines+markers',
            name: `${device_name} Raw ${mode === 'manual' ? '(Manual)' : ''}`,
            line: { color: '#83c5be', width: 2 },
            marker: { size: 4 }
        },
        {
            x: datetimes,
            y: predicted,
            type: 'scatter',
            mode: 'lines+markers',
            name: `${device_name} Calibrado (Predicción)`,
            line: { color: '#006d77', width: 2, dash: 'dot' },
            marker: { size: 6 }
        }
    ];

    if (result.rmcab_available) {
        traces.push({
            x: datetimes,
            y: rmcabReference,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'RMCAB Referencia',
            line: { color: '#d62828', width: 2 },
            marker: { size: 5 }
        });
    }

    const modeLabel = mode === 'manual' ? ' [Valores Manuales]' : '';
    const layout = {
        title: `Predicción ${pollutant.toUpperCase()} - ${device_name} (${result.target_date})${modeLabel}`,
        xaxis: { title: 'Hora' },
        yaxis: { title: `${pollutant.toUpperCase()} (µg/m³)` },
        hovermode: 'x unified',
        showlegend: true,
        legend: { x: 0, y: 1 }
    };

    Plotly.newPlot(predictionPlot, traces, layout, { responsive: true });

    predictionResults.style.display = 'block';
    predictionResults.scrollIntoView({ behavior: 'smooth' });

    const modeMsg = mode === 'manual' ? ' (con valores manuales)' : '';
    showAlert(`✅ Predicción completada${modeMsg}: ${result.records_count} registros`, 'success');
}

/**
 * Utility: Mostrar loading
 */
function showLoading(message = 'Cargando...') {
    if (loadingOverlay && loadingMessage) {
        loadingMessage.textContent = message;
        loadingOverlay.classList.add('active');
    }
}

/**
 * Utility: Ocultar loading
 */
function hideLoading() {
    if (loadingOverlay) {
        loadingOverlay.classList.remove('active');
    }
}

/**
 * Utility: Mostrar alerta
 */
function showAlert(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    // Aquí podrías implementar un sistema de notificaciones más elaborado
}
