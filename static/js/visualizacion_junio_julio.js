/**
 * JavaScript para Visualización Junio-Julio 2024
 */

let selectedDevice = null;
let selectedDeviceType = null;
let currentData = null;
let calibrationResults = null;
let activeViewMode = 'single';

const DATE_RANGE = {
    start: '2025-06-01',
    end: '2025-07-31'
};

const DEVICE_CONFIG = {
    Aire2: { type: 'sensor', label: 'Sensor Aire2' },
    Aire4: { type: 'sensor', label: 'Sensor Aire4' },
    Aire5: { type: 'sensor', label: 'Sensor Aire5' },
    RMCAB_LasFer: { type: 'rmcab', label: 'RMCAB Las Ferias', station: 6 }
};

const DEVICE_ORDER = ['Aire2', 'Aire4', 'Aire5', 'RMCAB_LasFer'];
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

// Elementos del DOM
const btnLoadDevice = document.getElementById('btnLoadDevice');
const btnStartCalibration = document.getElementById('btnStartCalibration');
const loadingOverlay = document.getElementById('loadingOverlay');
const loadingMessage = document.getElementById('loadingMessage');
const dataSection = document.getElementById('dataSection');
const calibrationSection = document.getElementById('calibrationSection');
const quickViewButtons = document.querySelectorAll('.quick-view-btn');
const multiSensorSection = document.getElementById('multiSensorSection');

// Event Listeners
btnLoadDevice.addEventListener('click', () => loadDeviceData());
btnStartCalibration.addEventListener('click', runCalibration);

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
    comparisonSection.style.display = 'none';
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
            value: 'Jun-Jul 2025',
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
        comparisonSection.style.display = 'none';
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
