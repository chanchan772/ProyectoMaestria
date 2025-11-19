/**
 * JavaScript para Visualización Junio-Julio 2024
 */

let selectedDevice = null;
let selectedDeviceType = null;
let currentData = null;
let calibrationResults = null;
let activeViewMode = 'single';

const DATE_RANGE = {
    start: '2023-01-01',
    end: '2023-12-31'
};

const POLLUTANTS = ['pm25', 'pm10'];  // Agregado PM10
const POLLUTANT_LABELS = {
    pm25: 'PM2.5',
    pm10: 'PM10'
};

const DEVICE_CONFIG = {
    Aire2: { type: 'sensor', label: 'Sensor Aire2' },
    Aire4: { type: 'sensor', label: 'Sensor Aire4' },
    Aire5: { type: 'sensor', label: 'Sensor Aire5' },
    RMCAB_LasFer: { type: 'rmcab', label: 'RMCAB Las Ferias', station: 6 }
};

const DEVICE_ORDER = ['Aire2', 'Aire4', 'Aire5', 'RMCAB_LasFer'];
const STAGE2_DEVICES = [];
const STAGE2_WINDOW_DAYS = 5;
const deviceDataCache = {};
let currentFriendlyName = '';
let stage2Section = null;
let stage2SummaryRow = null;
let stage2DeviceTableBody = null;
let stage2CalibrationContainer = null;
let stage2AlertContainer = null;
let stage2StartInput = null;
let stage2EndInput = null;
let stage2ApplyManualBtn = null;

const STAGE2_DEFAULT_START = '2023-06-22';
const STAGE2_DEFAULT_END = '2023-06-25';

let stage2State = {
    window: null,
    lowcost: [],
    rmcab: [],
    autoWindow: null,
    autoLowcost: [],
    autoRmcab: [],
    fullLowcost: [],
    fullRmcab: []
};

const SERIES_COLORS = {
    pm25: '#006d77',
    pm10: '#d62828'
};

const BOX_COLORS = {
    pm25: '#83c5be',
    pm10: '#ffb703'
};

// Helpers para normalizar datos de sensores y RMCAB
function coalesceValue(source, keys) {
    if (!source) {
        return null;
    }
    for (const key of keys) {
        if (Object.prototype.hasOwnProperty.call(source, key)) {
            const value = source[key];
            if (value !== null && value !== undefined) {
                return value;
            }
        }
    }
    return null;
}

function toNumeric(value) {
    if (value === null || value === undefined || value === '') {
        return null;
    }
    const numberValue = Number(value);
    return Number.isFinite(numberValue) ? numberValue : null;
}

function slugifyId(value) {
    return String(value || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-zA-Z0-9]/g, '_')
        .replace(/_+/g, '_')
        .replace(/^_+|_+$/g, '');
}

function normalizeDataset(rawData, deviceName = null) {
    if (!Array.isArray(rawData)) {
        return [];
    }

    return rawData
        .map(entry => {
            const datetimeValue = coalesceValue(entry, ['datetime', 'timestamp', 'fecha', 'date', 'time']);
            return {
                ...entry,
                datetime: datetimeValue ? String(datetimeValue) : null,
                pm25: toNumeric(coalesceValue(entry, ['pm25', 'pm25_sensor', 'pm25_ref', 'pm2_5', 'pm25_raw'])),
                pm10: toNumeric(coalesceValue(entry, ['pm10', 'pm10_sensor', 'pm10_ref', 'pm10_raw'])),
                temperature: toNumeric(coalesceValue(entry, ['temperature', 'temp', 'temperature_c', 'temperature_celsius'])),
                rh: toNumeric(coalesceValue(entry, ['rh', 'relative_humidity', 'humidity', 'humidity_relative']))
            };
        })
        .filter(entry => entry.datetime);
}

// Elementos del DOM - inicializados después de DOMContentLoaded
let btnLoadDevice, btnStartCalibration, btnCalibrateAll, loadingOverlay, loadingMessage;
let dataSection, calibrationSection, quickViewButtons, multiSensorSection, comparisonSection;

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Inicializando visualización junio-julio...');
    
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
    stage2Section = document.getElementById('stage2Section');
    stage2SummaryRow = document.getElementById('stage2SummaryRow');
    stage2DeviceTableBody = document.getElementById('stage2DeviceTableBody');
    stage2CalibrationContainer = document.getElementById('stage2CalibrationResults');
    stage2AlertContainer = document.getElementById('stage2AlertContainer');
    stage2StartInput = document.getElementById('stage2StartDate');
    stage2EndInput = document.getElementById('stage2EndDate');
    stage2ApplyManualBtn = document.getElementById('stage2ApplyManualBtn');
    if (stage2StartInput && !stage2StartInput.value) {
        stage2StartInput.value = STAGE2_DEFAULT_START;
    }
    if (stage2EndInput && !stage2EndInput.value) {
        stage2EndInput.value = STAGE2_DEFAULT_END;
    }

    // Verificar elementos
    console.log('Elementos del DOM verificados:');
    console.log('  - btnLoadDevice:', !!btnLoadDevice);
    console.log('  - btnStartCalibration:', !!btnStartCalibration);
    console.log('  - calibrationSection:', !!calibrationSection);
    console.log('  - comparisonSection:', !!comparisonSection);
    console.log('  - quickViewButtons:', quickViewButtons.length);
    console.log('  - stage2Section:', !!stage2Section);
    
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

    // Event listeners para fechas sugeridas
    const suggestedDateButtons = document.querySelectorAll('.suggested-date');
    suggestedDateButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const dateValue = this.getAttribute('data-date');
            const predictionDateInput = document.getElementById('predictionDate');
            if (predictionDateInput) {
                predictionDateInput.value = dateValue;
                showAlert(`📅 Fecha seleccionada: ${dateValue}`, 'info');
            }
        });
    });
    console.log(`✅ ${suggestedDateButtons.length} botones de fechas sugeridas conectados`);

    if (btnLoadDevice) btnLoadDevice.addEventListener('click', () => loadDeviceData());
    if (btnStartCalibration) btnStartCalibration.addEventListener('click', runCalibration);
    if (btnCalibrateAll) btnCalibrateAll.addEventListener('click', runMultipleCalibration);
    if (stage2ApplyManualBtn) stage2ApplyManualBtn.addEventListener('click', applyManualStage2Window);
    const stage2CalibrateBtn = document.getElementById('stage2CalibrateBtn');
    if (stage2CalibrateBtn) {
        stage2CalibrateBtn.addEventListener('click', runStage2Calibration);
        console.log('✅ Botón calibración etapa 2 conectado');
    }
    const stage2DownloadBtn = document.getElementById('stage2DownloadBtn');
    if (stage2DownloadBtn) {
        stage2DownloadBtn.addEventListener('click', downloadStage2Excel);
        console.log('? Bot�n descarga etapa 2 conectado');
    }
    const stage2ReloadBtn = document.getElementById('stage2ReloadBtn');
    if (stage2ReloadBtn) {
        stage2ReloadBtn.addEventListener('click', () => showStage2View(true));
        console.log('✅ Botón recalcular ventana etapa 2 conectado');
    }

    quickViewButtons.forEach(button => {
        button.addEventListener('click', async () => {
            try {
                const isComparison = button.dataset.view === 'comparison';
                if (isComparison) {
                    await showComparisonView();
                    setActiveQuickButton(button);
                    return;
                }

                const isStage2 = button.dataset.view === 'stage2';
                if (isStage2) {
                    await showStage2View();
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

    if (stage2Section) {
        stage2Section.style.display = 'none';
    }
    stage2Alert('');

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
        const normalizedData = result.normalizedData || normalizeDataset(result.data, targetDevice);

        currentData = normalizedData;
        const recordCount = result.records ?? (Array.isArray(normalizedData) ? normalizedData.length : 0);

        showAlert(`Datos cargados: ${recordCount} registros`, "success");

        currentFriendlyName = friendlyName;
        document.getElementById("selectedDeviceName").textContent = friendlyName;
        showSingleSensorView();

        generateDataVisualizations(targetDevice, normalizedData, friendlyName);

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

    const normalizedData = normalizeDataset(result.data, deviceName);
    result.normalizedData = normalizedData;

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
function generateDataVisualizations(deviceName, data, deviceLabel = null) {
    const normalized = Array.isArray(data) ? data : [];

    // Calcular métricas resumen
    displayMetrics(normalized);

    // Generar gráficos
    createTimeSeriesPlot(normalized, deviceLabel);
    createBoxPlots(normalized, deviceLabel);
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

    if (stage2Section) {
        stage2Section.style.display = 'none';
    }
    stage2Alert('');

    try {
        const datasets = {};

        for (const deviceName of DEVICE_ORDER) {
            try {
                const result = await getDeviceData(deviceName);
                const normalized = result.normalizedData || normalizeDataset(result.data, deviceName);
                datasets[deviceName] = normalized;
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

function stage2Alert(message = '', type = 'info') {
    if (!stage2AlertContainer) {
        return;
    }
    if (!message) {
        stage2AlertContainer.innerHTML = '';
        return;
    }
    stage2AlertContainer.innerHTML = `
        <div class="alert alert-${type}" role="alert">
            ${message}
        </div>
    `;
}

function buildQueryHtml(query) {
    if (!query) {
        return '';
    }
    const sanitized = String(query)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    return `<pre class="mt-2 small bg-light rounded p-2">${sanitized}</pre>`;
}

function formatStage2ErrorMessage(result, fallbackMessage = 'Ocurrió un error.') {
    if (!result) {
        return fallbackMessage;
    }
    const message = result.error || fallbackMessage;
    const queryHtml = buildQueryHtml(result.query);
    return `${message}${queryHtml}`;
}

function logQueryIfAvailable(context, payload) {
    if (payload && payload.query) {
        console.warn(`[${context}] Consulta ejecutada:\n${payload.query}`);
    }
}

function formatStage2Date(value) {
    if (!value) {
        return 'N/D';
    }
    const dateObj = new Date(value);
    if (Number.isNaN(dateObj.getTime())) {
        return value;
    }
    return dateObj.toLocaleString('es-CO', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatStage2Number(value, fractionDigits = 0) {
    const formatter = new Intl.NumberFormat('es-CO', {
        minimumFractionDigits: fractionDigits,
        maximumFractionDigits: fractionDigits
    });
    if (value === null || value === undefined || Number.isNaN(value)) {
        return 'N/D';
    }
    return formatter.format(value);
}

function toStage2Date(value) {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date;
}

function alignLowcostToReference(lowRecords, referenceRecords, toleranceMinutes = 60) {
    if (!Array.isArray(lowRecords) || !Array.isArray(referenceRecords)) {
        return [];
    }

    const toleranceMs = toleranceMinutes * 60 * 1000;
    const grouped = new Map();

    lowRecords.forEach(record => {
        const device = record.device_name;
        if (!device) {
            return;
        }
        const sensorTime = toStage2Date(record.sensor_datetime || record.datetime);
        if (!sensorTime) {
            return;
        }
        const clone = { ...record, __sensor_ts: sensorTime };
        grouped.set(device, (grouped.get(device) || []).concat(clone));
    });

    grouped.forEach(list => list.sort((a, b) => a.__sensor_ts - b.__sensor_ts));

    const aligned = [];
    referenceRecords.forEach(ref => {
        const refTs = toStage2Date(ref.datetime);
        if (!refTs) {
            return;
        }
        grouped.forEach((records, device) => {
            let closest = null;
            let closestDiff = Infinity;
            for (const entry of records) {
                const diff = Math.abs(entry.__sensor_ts - refTs);
                if (diff < closestDiff) {
                    closestDiff = diff;
                    closest = entry;
                    if (diff === 0) {
                        break;
                    }
                } else if (entry.__sensor_ts > refTs && diff > closestDiff) {
                    break;
                }
            }
            if (closest && closestDiff <= toleranceMs) {
                const { __sensor_ts, ...rest } = closest;
                aligned.push({
                    ...rest,
                    datetime: ref.datetime,
                    reference_datetime: ref.datetime,
                    sensor_datetime: closest.sensor_datetime || closest.datetime || __sensor_ts.toISOString(),
                    time_diff_ms: closestDiff,
                    device_name: device
                });
            }
        });
    });

    return aligned;
}

function buildStage2DeviceSummary(alignedRecords) {
    const summaryMap = new Map();
    const ensureEntry = (device) => {
        if (!summaryMap.has(device)) {
            summaryMap.set(device, {
                device,
                label: DEVICE_CONFIG[device]?.label || device,
                records: 0,
                pm25: 0,
                pm10: 0
            });
        }
        return summaryMap.get(device);
    };

    alignedRecords.forEach(record => {
        const device = record.device_name;
        if (!device) {
            return;
        }
        const entry = ensureEntry(device);
        entry.records += 1;
        if (record.pm25_sensor !== null && record.pm25_sensor !== undefined && record.pm25_sensor !== '') {
            entry.pm25 += 1;
        }
        if (record.pm10_sensor !== null && record.pm10_sensor !== undefined && record.pm10_sensor !== '') {
            entry.pm10 += 1;
        }
    });

    return Array.from(summaryMap.values()).sort((a, b) => {
        if (b.records !== a.records) {
            return b.records - a.records;
        }
        return a.label.localeCompare(b.label);
    });
}

function renderStage2Summary(windowInfo) {
    if (!stage2SummaryRow) {
        return;
    }
    if (!windowInfo) {
        stage2SummaryRow.innerHTML = '';
        return;
    }

    const cards = [
        {
            icon: 'bi-calendar-event',
            title: 'Inicio ventana',
            value: formatStage2Date(windowInfo.start_date || windowInfo.start)
        },
        {
            icon: 'bi-calendar4-event',
            title: 'Fin ventana',
            value: formatStage2Date(windowInfo.end_date || windowInfo.end)
        },
        {
            icon: 'bi-collection',
            title: 'Registros totales',
            value: formatStage2Number(windowInfo.total_records || 0)
        },
        {
            icon: 'bi-clock-history',
            title: 'Horas con datos',
            value: formatStage2Number(windowInfo.hours_covered || 0)
        }
    ];

    stage2SummaryRow.innerHTML = cards.map(card => `
        <div class="col-md-3 col-sm-6">
            <div class="metric-card h-100">
                <i class="bi ${card.icon} display-6 text-primary"></i>
                <h4>${card.value}</h4>
                <p class="text-muted mb-0">${card.title}</p>
            </div>
        </div>
    `).join('');
}

function renderStage2DeviceTable(perDevice = []) {
    if (!stage2DeviceTableBody) {
        return;
    }

    if (!Array.isArray(perDevice) || perDevice.length === 0) {
        stage2DeviceTableBody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center text-muted">Sin información disponible.</td>
            </tr>
        `;
        return;
    }

    stage2DeviceTableBody.innerHTML = perDevice.map(device => `
        <tr>
            <td><strong>${device.label || device.device}</strong></td>
            <td>${formatStage2Number(device.records)}</td>
            <td>${formatStage2Number(device.pm25)}</td>
            <td>${formatStage2Number(device.pm10)}</td>
        </tr>
    `).join('');
}

function buildStage2HoverMetadata(row) {
    if (!row) {
        return ['N/D', 'N/D', 'Ajuste no disponible'];
    }

    const referenceDate = toStage2Date(row.datetime);
    const sensorDate = toStage2Date(row.sensor_datetime || row.datetime);
    const referenceLabel = referenceDate ? formatStage2Date(referenceDate) : 'N/D';
    const sensorLabel = sensorDate ? formatStage2Date(sensorDate) : 'N/D';

    let adjustmentLabel = 'Ajuste no disponible';

    if (referenceDate && sensorDate) {
        const diffMinutes = (sensorDate.getTime() - referenceDate.getTime()) / 60000;
        if (Number.isFinite(diffMinutes)) {
            if (Math.abs(diffMinutes) < 0.01) {
                adjustmentLabel = '0 min (sin ajuste)';
            } else {
                const direction = diffMinutes > 0 ? 'sensor adelantado' : 'sensor atrasado';
                const signedValue = diffMinutes > 0 ? `+${diffMinutes.toFixed(1)}` : diffMinutes.toFixed(1);
                adjustmentLabel = `${signedValue} min (${direction})`;
            }
        }
    } else if (sensorDate && !referenceDate) {
        adjustmentLabel = 'Sin referencia';
    } else if (referenceDate && !sensorDate) {
        adjustmentLabel = 'Sin dato del sensor';
    }

    return [referenceLabel, sensorLabel, adjustmentLabel];
}

function createStage2PollutantTrace(records, fieldName, label, color) {
    if (!Array.isArray(records)) {
        return null;
    }

    const points = records
        .filter(row => row && row[fieldName] !== null && row[fieldName] !== undefined)
        .map(row => {
            const numericValue = toNumeric(row[fieldName]);
            if (numericValue === null) {
                return null;
            }
            return {
                x: row.datetime,
                y: numericValue,
                metadata: buildStage2HoverMetadata(row)
            };
        })
        .filter(point => point !== null);

    if (!points.length) {
        return null;
    }

    return {
        x: points.map(point => point.x),
        y: points.map(point => point.y),
        customdata: points.map(point => point.metadata),
        type: 'scatter',
        mode: 'lines+markers',
        name: label,
        line: { color, width: 2 },
        marker: { size: 5 },
        hovertemplate: [
            'Fecha referencia: %{customdata[0]}',
            'Fecha real del sensor: %{customdata[1]}',
            'Ajuste aplicado: %{customdata[2]}',
            `${label}: %{y:.2f} ug/m3`,
            '<extra></extra>'
        ].join('<br>')
    };
}

function computeStage2WindowData(startISO, endISO) {
    if (!startISO || !endISO) {
        return null;
    }

    const startBoundary = new Date(startISO);
    startBoundary.setHours(0, 0, 0, 0);
    const endBoundary = new Date(endISO);
    endBoundary.setHours(23, 0, 0, 0);

    if (Number.isNaN(startBoundary.getTime()) || Number.isNaN(endBoundary.getTime()) || startBoundary > endBoundary) {
        return null;
    }

    const parseTimestamp = (value) => {
        const ts = new Date(value);
        return Number.isNaN(ts.getTime()) ? null : ts;
    };

    const lowcostFiltered = (stage2State.fullLowcost || []).filter(row => {
        const ts = parseTimestamp(row.sensor_datetime || row.datetime);
        return ts && ts >= startBoundary && ts <= endBoundary;
    });

    const rmcabFiltered = (stage2State.fullRmcab || []).filter(row => {
        const ts = parseTimestamp(row.datetime);
        return ts && ts >= startBoundary && ts <= endBoundary;
    });

    if (!lowcostFiltered.length || !rmcabFiltered.length) {
        return null;
    }

    const alignedRecords = alignLowcostToReference(lowcostFiltered, rmcabFiltered, 60);
    if (!alignedRecords.length) {
        return null;
    }

    const perDevice = buildStage2DeviceSummary(alignedRecords);
    const hourSet = new Set(
        alignedRecords
            .map(row => parseTimestamp(row.datetime))
            .filter(Boolean)
            .map(date => date.toISOString().slice(0, 13))
    );

    const stationInfo = stage2State.autoWindow?.station || stage2State.window?.station || null;

    return {
        window: {
            start: startBoundary.toISOString(),
            end: endBoundary.toISOString(),
            start_date: startISO,
            end_date: endISO,
            total_records: alignedRecords.length,
            hours_covered: hourSet.size,
            per_device: perDevice,
            station: stationInfo
        },
        lowcost: alignedRecords,
        rmcab: rmcabFiltered
    };
}

function applyStage2Window(startISO, endISO, showMessage = true) {
    const computed = computeStage2WindowData(startISO, endISO);
    if (!computed) {
        if (showMessage) {
            stage2Alert('No hay datos disponibles para la ventana seleccionada.', 'warning');
        }
        return false;
    }

    stage2State.window = computed.window;
    stage2State.lowcost = computed.lowcost;
    stage2State.rmcab = computed.rmcab;

    renderStage2Summary(stage2State.window);
    renderStage2DeviceTable(stage2State.window.per_device || []);
    renderStage2Charts(stage2State.lowcost, stage2State.rmcab);

    if (showMessage) {
        stage2Alert(`Ventana aplicada (${startISO} a ${endISO}).`, 'success');
    } else {
        stage2Alert('');
    }

    return true;
}

function applyManualStage2Window() {
    if (!stage2StartInput || !stage2EndInput) {
        return;
    }

    const startValue = stage2StartInput.value;
    const endValue = stage2EndInput.value;

    if (!startValue || !endValue) {
        stage2Alert('Selecciona una fecha inicial y final antes de aplicar la ventana.', 'warning');
        return;
    }

    if (new Date(startValue) > new Date(endValue)) {
        stage2Alert('La fecha final debe ser posterior a la fecha inicial.', 'warning');
        return;
    }

    if (!stage2State.fullLowcost.length) {
        stage2Alert('Recalcula la ventana antes de aplicar un rango manual.', 'warning');
        return;
    }

    const applied = applyStage2Window(startValue, endValue, true);
    if (!applied) {
        if (stage2State.autoWindow && stage2State.autoLowcost.length) {
            stage2State.window = stage2State.autoWindow;
            stage2State.lowcost = stage2State.autoLowcost.slice();
            stage2State.rmcab = stage2State.autoRmcab.slice();
            renderStage2Summary(stage2State.window);
            renderStage2DeviceTable(stage2State.window.per_device || []);
            renderStage2Charts(stage2State.lowcost, stage2State.rmcab);
        }
        return;
    }

    if (stage2Section) {
        stage2Section.scrollIntoView({ behavior: 'smooth' });
    }
}


function getStage2DevicesWithData(minRecords = 1) {
    if (!stage2State.window || !Array.isArray(stage2State.window.per_device)) {
        return [];
    }

    return stage2State.window.per_device
        .filter(item => (item.records || 0) >= minRecords)
        .map(item => item.device);
}

function renderStage2Charts(lowcostRecords = [], rmcabRecords = []) {
    const plotConfigs = [
        { device: 'Aire2', title: 'Aire2 - PM2.5 y PM10', container: 'stage2ChartAire2' },
        { device: 'Aire4', title: 'Aire4 - PM2.5 y PM10', container: 'stage2ChartAire4' },
        { device: 'Aire5', title: 'Aire5 - PM2.5 y PM10', container: 'stage2ChartAire5' }
    ];

    plotConfigs.forEach(cfg => {
        const container = document.getElementById(cfg.container);
        if (!container) {
            return;
        }

        const deviceData = (lowcostRecords || []).filter(row => row.device_name === cfg.device);
        if (!deviceData.length) {
            container.innerHTML = '<p class="text-muted text-center mb-0">Sin datos disponibles.</p>';
            if (window.Plotly) {
                Plotly.purge(container);
            }
            return;
        }

        deviceData.sort((a, b) => new Date(a.datetime) - new Date(b.datetime));
        const timestamps = deviceData.map(row => row.datetime);

        const traces = [];

        const pm25Trace = createStage2PollutantTrace(deviceData, 'pm25_sensor', 'PM2.5', SERIES_COLORS.pm25);
        if (pm25Trace) {
            traces.push(pm25Trace);
        }

        const pm10Trace = createStage2PollutantTrace(deviceData, 'pm10_sensor', 'PM10', SERIES_COLORS.pm10);
        if (pm10Trace) {
            traces.push(pm10Trace);
        }

        const minX = timestamps[0];
        const maxX = timestamps[timestamps.length - 1];

        traces.push({
            x: [minX, maxX],
            y: [15, 15],
            type: 'scatter',
            mode: 'lines',
            name: 'OMS PM2.5 (15)',
            line: { color: '#f4a261', dash: 'dash' },
            hoverinfo: 'skip'
        });

        traces.push({
            x: [minX, maxX],
            y: [25, 25],
            type: 'scatter',
            mode: 'lines',
            name: 'Colombia PM2.5 (25)',
            line: { color: '#e76f51', dash: 'dashdot' },
            hoverinfo: 'skip'
        });

        traces.push({
            x: [minX, maxX],
            y: [45, 45],
            type: 'scatter',
            mode: 'lines',
            name: 'OMS PM10 (45)',
            line: { color: '#0ea5e9', dash: 'dot' },
            hoverinfo: 'skip'
        });

        traces.push({
            x: [minX, maxX],
            y: [50, 50],
            type: 'scatter',
            mode: 'lines',
            name: 'Colombia PM10 (50)',
            line: { color: '#2563eb', dash: 'dot' },
            hoverinfo: 'skip'
        });

        const layout = {
            title: cfg.title,
            margin: { t: 45, r: 20, l: 60, b: 80 },
            hovermode: 'x unified',
            showlegend: true,
            legend: { orientation: 'h', y: -0.35 },
            xaxis: { title: 'Fecha y hora' },
            yaxis: { title: 'µg/m³' }
        };

        if (window.Plotly) {
            Plotly.react(container, traces, layout, { responsive: true, displaylogo: false });
        }
    });

    const rmcabContainer = document.getElementById('stage2ChartRMCAB');
    if (rmcabContainer) {
        const records = (rmcabRecords || []).slice().sort((a, b) => new Date(a.datetime) - new Date(b.datetime));
        if (!records.length) {
            rmcabContainer.innerHTML = '<p class="text-muted text-center mb-0">Sin datos disponibles.</p>';
            if (window.Plotly) {
                Plotly.purge(rmcabContainer);
            }
        } else if (window.Plotly) {
            const timestamps = records.map(row => row.datetime);
            const pm25Values = records.map(row => toNumeric(row.pm25));
            const pm10Values = records.map(row => toNumeric(row.pm10));

            const traces = [];
            const minX = timestamps[0];
            const maxX = timestamps[timestamps.length - 1];
            if (pm25Values.some(val => val !== null)) {
                traces.push({
                    x: timestamps,
                    y: pm25Values,
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: 'PM2.5',
                    line: { color: SERIES_COLORS.pm25, width: 2 },
                    marker: { size: 5 }
                });
            }
            if (pm10Values.some(val => val !== null)) {
                traces.push({
                    x: timestamps,
                    y: pm10Values,
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: 'PM10',
                    line: { color: SERIES_COLORS.pm10, width: 2 },
                    marker: { size: 5 }
                });
            }

            traces.push({
                x: [minX, maxX],
                y: [15, 15],
                type: 'scatter',
                mode: 'lines',
                name: 'OMS PM2.5 (15)',
                line: { color: '#f4a261', dash: 'dash' },
                hoverinfo: 'skip'
            });

            traces.push({
                x: [minX, maxX],
                y: [25, 25],
                type: 'scatter',
                mode: 'lines',
                name: 'Colombia PM2.5 (25)',
                line: { color: '#e76f51', dash: 'dashdot' },
                hoverinfo: 'skip'
            });

            traces.push({
                x: [minX, maxX],
                y: [45, 45],
                type: 'scatter',
                mode: 'lines',
                name: 'OMS PM10 (45)',
                line: { color: '#0ea5e9', dash: 'dot' },
                hoverinfo: 'skip'
            });

            traces.push({
                x: [minX, maxX],
                y: [50, 50],
                type: 'scatter',
                mode: 'lines',
                name: 'Colombia PM10 (50)',
                line: { color: '#2563eb', dash: 'dot' },
                hoverinfo: 'skip'
            });

            const layout = {
                title: 'RMCAB Las Ferias - PM2.5 y PM10',
                margin: { t: 45, r: 20, l: 60, b: 80 },
                hovermode: 'x unified',
                showlegend: true,
                legend: { orientation: 'h', y: -0.35 },
                xaxis: { title: 'Fecha y hora' },
                yaxis: { title: 'µg/m³' }
            };

            Plotly.react(rmcabContainer, traces, layout, { responsive: true, displaylogo: false });
        }
    }
}

async function showStage2View(forceReload = false) {
    activeViewMode = 'stage2';

    if (dataSection) dataSection.style.display = 'none';
    if (calibrationSection) calibrationSection.style.display = 'none';
    if (multiSensorSection) multiSensorSection.style.display = 'none';
    if (comparisonSection) comparisonSection.style.display = 'none';
    const predictionSection = document.getElementById('predictionSection');
    if (predictionSection) predictionSection.style.display = 'none';

    if (stage2Section) stage2Section.style.display = 'block';

    if (!forceReload && stage2State.window && stage2State.lowcost.length) {
        if (stage2StartInput && stage2State.window.start_date) {
            stage2StartInput.value = stage2State.window.start_date;
        }
        if (stage2EndInput && stage2State.window.end_date) {
            stage2EndInput.value = stage2State.window.end_date;
        }
        renderStage2Summary(stage2State.window);
        renderStage2DeviceTable(stage2State.window.per_device || []);
        renderStage2Charts(stage2State.lowcost, stage2State.rmcab);
        stage2Alert('');
        stage2Section.scrollIntoView({ behavior: 'smooth' });
        return;
    }

    if (forceReload) {
        stage2State = {
            window: null,
            lowcost: [],
            rmcab: [],
            autoWindow: null,
            autoLowcost: [],
            autoRmcab: [],
            fullLowcost: [],
            fullRmcab: []
        };
    }

    showLoading(`Buscando ventana óptima de ${STAGE2_WINDOW_DAYS} días...`);
    stage2Alert('');

    try {
        const stage2Payload = {
            start_date: DATE_RANGE.start,
            end_date: DATE_RANGE.end,
            station_code: DEVICE_CONFIG.RMCAB_LasFer.station,
            window_days: STAGE2_WINDOW_DAYS
        };
        if (Array.isArray(STAGE2_DEVICES) && STAGE2_DEVICES.length > 0) {
            stage2Payload.devices = STAGE2_DEVICES;
        }

        const response = await fetch('/api/stage2/load', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(stage2Payload)
        });

        const result = await response.json();
        if (!result.success) {
            logQueryIfAvailable('Stage2 Load', result);
            stage2Alert(
                formatStage2ErrorMessage(result, 'No fue posible calcular la ventana óptima.'),
                'danger'
            );
            renderStage2Summary(null);
            renderStage2DeviceTable([]);
            renderStage2Charts([], []);
            return;
        }

        // Mostrar consulta SQL ejecutada (si está disponible)
        try {
            const queryBox = document.getElementById('stage2QueryBox');
            if (queryBox) {
                const build = (window.buildQueryHtml || (q => `<pre class=\"mt-2 small bg-light rounded p-2\">${String(q || '(consulta no disponible)')}</pre>`));
                queryBox.innerHTML = build(result.query || '(consulta no disponible)');
            }
        } catch (e) {
            console.warn('No fue posible mostrar la consulta ejecutada', e);
        }

        stage2State.autoWindow = result.window || null;
        stage2State.autoLowcost = (result.lowcost || []).slice();
        stage2State.autoRmcab = (result.rmcab || []).slice();
        stage2State.fullLowcost = (result.full_lowcost || result.lowcost || []).slice();
        stage2State.fullRmcab = (result.full_rmcab || result.rmcab || []).slice();
        stage2State.window = stage2State.autoWindow;
        stage2State.lowcost = stage2State.autoLowcost.slice();
        stage2State.rmcab = stage2State.autoRmcab.slice();

        if (stage2StartInput) {
            stage2StartInput.value = STAGE2_DEFAULT_START;
        }
        if (stage2EndInput) {
            stage2EndInput.value = STAGE2_DEFAULT_END;
        }

        let manualApplied = false;
        let autoApplied = false;

        if (stage2StartInput && stage2EndInput) {
            manualApplied = applyStage2Window(stage2StartInput.value, stage2EndInput.value, false);
        }

        if (!manualApplied && stage2State.autoWindow) {
            const autoStart = stage2State.autoWindow.start ? stage2State.autoWindow.start.slice(0, 10) : '';
            const autoEnd = stage2State.autoWindow.end ? stage2State.autoWindow.end.slice(0, 10) : '';
            if (autoStart) {
                if (stage2StartInput) stage2StartInput.value = autoStart;
                if (stage2EndInput) stage2EndInput.value = autoEnd;
                autoApplied = applyStage2Window(autoStart, autoEnd, false);
            }
        }

        if (manualApplied) {
            stage2Alert(`Ventana manual aplicada (${stage2StartInput.value} a ${stage2EndInput.value}).`, 'success');
        } else if (autoApplied) {
            stage2Alert('Ventana automática identificada correctamente.', 'success');
        } else {
            stage2Alert('No se encontraron datos en la ventana seleccionada. Ajusta las fechas manualmente.', 'warning');
            renderStage2Summary(null);
            renderStage2DeviceTable([]);
            renderStage2Charts([], []);
        }

        if ((manualApplied || autoApplied) && stage2Section) {
            stage2Section.scrollIntoView({ behavior: 'smooth' });
        }
    } catch (error) {
        console.error('Error cargando etapa 2:', error);
        stage2Alert('Ocurrió un error calculando la ventana óptima.', 'danger');
        renderStage2Summary(null);
        renderStage2DeviceTable([]);
        renderStage2Charts([], []);
    } finally {
        hideLoading();
    }
}

async function runStage2Calibration() {
    if (!stage2State.window) {
        stage2Alert('Primero recalcula la ventana óptima antes de calibrar.', 'warning');
        return;
    }
    if (!stage2State.lowcost || !stage2State.lowcost.length) {
        stage2Alert('No hay datos disponibles en la ventana seleccionada. Ajusta el rango y vuelve a intentarlo.', 'warning');
        return;
    }

    showLoading('Ejecutando calibración avanzada...');
    stage2Alert('');

    try {
        const devicesForCalibration = getStage2DevicesWithData();

        if (!devicesForCalibration.length) {
            stage2Alert('No hay dispositivos con datos suficientes en la ventana seleccionada.', 'warning');
            return;
        }

        const response = await fetch('/api/stage2/calibrate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start_date: DATE_RANGE.start,
                end_date: DATE_RANGE.end,
                window_start: stage2State.window.start,
                window_end: stage2State.window.end,
                devices: devicesForCalibration,
                pollutants: POLLUTANTS,
                station_code: DEVICE_CONFIG.RMCAB_LasFer.station
            })
        });

        const result = await response.json();
        if (!result.success) {
            logQueryIfAvailable('Stage2 Calibrate', result);
            stage2Alert(
                formatStage2ErrorMessage(result, 'No fue posible ejecutar la calibración.'),
                'danger'
            );
            return;
        }

        renderStage2CalibrationResults(result.devices || []);
        stage2Alert('Calibración completada correctamente.', 'success');
    } catch (error) {
        console.error('Error en calibración etapa 2:', error);
        stage2Alert('Ocurrió un error ejecutando la calibración.', 'danger');
    } finally {
        hideLoading();
    }
}

async function downloadStage2Excel() {
    if (!stage2State.window) {
        stage2Alert('Primero recalcula la ventana óptima para definir el rango a descargar.', 'warning');
        return;
    }

    const devicesForDownload = getStage2DevicesWithData();
    if (!devicesForDownload.length) {
        stage2Alert('No hay dispositivos con datos suficientes en la ventana seleccionada.', 'warning');
        return;
    }

    showLoading('Generando archivo Excel...');
    stage2Alert('');

    try {
        const response = await fetch('/api/stage2/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start_date: DATE_RANGE.start,
                end_date: DATE_RANGE.end,
                window_start: stage2State.window.start,
                window_end: stage2State.window.end,
                devices: devicesForDownload,
                station_code: DEVICE_CONFIG.RMCAB_LasFer.station
            })
        });

        if (!response.ok) {
            let errorMessage = 'No fue posible generar el archivo.';
            const contentType = response.headers.get('Content-Type') || '';
            let errorPayload = null;
            if (contentType.includes('application/json')) {
                try {
                    errorPayload = await response.json();
                    errorMessage = errorPayload.error || errorMessage;
                } catch (jsonError) {
                    console.warn('No se pudo leer la respuesta de error:', jsonError);
                }
            }
            logQueryIfAvailable('Stage2 Download', errorPayload);
            stage2Alert(
                formatStage2ErrorMessage(errorPayload, errorMessage),
                'danger'
            );
            return;
        }

        const blob = await response.blob();
        if (!blob || blob.size === 0) {
            stage2Alert('El archivo descargado está vacío.', 'warning');
            return;
        }

        const disposition = response.headers.get('Content-Disposition') || '';
        let filename = 'datos_stage2.xlsx';
        const match = disposition.match(/filename="?([^";]+)"?/i);
        if (match && match[1]) {
            filename = match[1];
        }

        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(url);

        stage2Alert('Archivo Excel descargado correctamente.', 'success');
    } catch (error) {
        console.error('Error descargando Excel Stage 2:', error);
        stage2Alert('Ocurrió un error generando el archivo.', 'danger');
    } finally {
        hideLoading();
    }
}
function renderStage2CalibrationResults(deviceResults = []) {
    if (!stage2CalibrationContainer) {
        return;
    }

    if (!deviceResults.length) {
        stage2CalibrationContainer.innerHTML = `
            <p class="text-muted text-center">Ejecuta la calibración para visualizar resultados.</p>
        `;
        return;
    }

    const accordionId = 'stage2CalibrationAccordion';
    const scatterTasks = [];
    let html = `<div class="accordion" id="${accordionId}">`;

    deviceResults.forEach((deviceResult, deviceIndex) => {
        const deviceLabel = DEVICE_CONFIG[deviceResult.device]?.label || deviceResult.device;
        const headingId = `stage2Heading${deviceIndex}`;
        const collapseId = `stage2Collapse${deviceIndex}`;
        const isFirst = deviceIndex === 0;

        let bodyHtml = '';
        const deviceWarnings = (deviceResult.warnings || []).filter(Boolean);
        const deviceWarningsHtml = deviceWarnings.length
            ? `
                <div class="alert alert-warning">
                    <strong>Advertencias generales (${deviceLabel}):</strong>
                    <ul class="mb-0">${deviceWarnings.map(msg => `<li>${msg}</li>`).join('')}</ul>
                </div>
            `
            : '';

        if (deviceResult.error) {
            bodyHtml = `<div class="alert alert-warning mb-0">${deviceResult.error}</div>`;
        } else {
            const pollutants = Object.keys(deviceResult.pollutants || {});
            if (!pollutants.length) {
                bodyHtml = '<p class="text-muted mb-0">Sin resultados disponibles.</p>';
            } else {
                pollutants.forEach(pollutantKey => {
                    const sectionHtml = buildStage2PollutantSection(
                        deviceResult.device,
                        pollutantKey,
                        deviceResult.pollutants[pollutantKey],
                        scatterTasks
                    );
                    bodyHtml += sectionHtml;
                });
            }
        }

        bodyHtml = deviceWarningsHtml + bodyHtml;

        html += `
            <div class="accordion-item">
                <h2 class="accordion-header" id="${headingId}">
                    <button class="accordion-button ${isFirst ? '' : 'collapsed'}" type="button"
                            data-bs-toggle="collapse" data-bs-target="#${collapseId}"
                            aria-expanded="${isFirst}" aria-controls="${collapseId}">
                        ${deviceLabel}
                    </button>
                </h2>
                <div id="${collapseId}" class="accordion-collapse collapse ${isFirst ? 'show' : ''}"
                     data-bs-parent="#${accordionId}">
                    <div class="accordion-body">
                        ${bodyHtml}
                    </div>
                </div>
            </div>
        `;
    });

    html += '</div>';
    stage2CalibrationContainer.innerHTML = html;

    scatterTasks.forEach(task => plotStage2Scatter(task));
}

function buildStage2PollutantSection(deviceName, pollutantKey, data, scatterTasks) {
    const label = POLLUTANT_LABELS[pollutantKey] || pollutantKey.toUpperCase();

    if (!data || data.error) {
        return `<div class="alert alert-warning">${data?.error || 'Sin datos de calibración disponibles.'}</div>`;
    }

    const warningsList = (data.warnings || []).filter(Boolean);
    const warningsHtml = warningsList.length
        ? `
            <div class="alert alert-warning mb-3">
                <strong>Advertencias:</strong>
                <ul class="mb-0">${warningsList.map(item => `<li>${item}</li>`).join('')}</ul>
            </div>
        `
        : '';

    const metricsRows = (data.metrics || []).map(model => {
        const rowClass = model.is_best ? 'table-success' : '';
        return `
            <tr class="${rowClass}">
                <td><strong>${model.model_name}</strong>${model.is_best ? ' <span class="badge bg-success ms-2">Mejor</span>' : ''}</td>
                <td>${model.r2?.toFixed(4) ?? 'N/D'}</td>
                <td>${model.r2_adjusted?.toFixed(4) ?? 'N/D'}</td>
                <td>${model.rmse?.toFixed(3) ?? 'N/D'}</td>
                <td>${model.mae?.toFixed(3) ?? 'N/D'}</td>
                <td>${model.mape?.toFixed(2) ?? 'N/D'}</td>
            </tr>
        `;
    }).join('') || `
        <tr>
            <td colspan="6" class="text-center text-muted">No se generaron métricas para este contaminante.</td>
        </tr>
    `;

    const bestMetrics = data.best_metrics || {};
    const linearModelInfo = data.linear_model?.formula ? `
        <div class="alert alert-secondary mb-3">
            <strong>Fórmula Regresión Lineal:</strong><br>
            <code>${data.linear_model.formula}</code>
        </div>
    ` : '';

    const scatterHtmlParts = [];
    (data.scatter || []).forEach((modelData, index) => {
        const chartId = `stage2-scatter-${slugifyId(deviceName)}-${slugifyId(pollutantKey)}-${index}`;
        scatterHtmlParts.push(`
            <div class="col-lg-6">
                <div class="plot-container">
                    <h6>${modelData.model_name}</h6>
                    <div id="${chartId}" style="min-height: 320px;"></div>
                </div>
            </div>
        `);
        scatterTasks.push({
            containerId: chartId,
            modelName: modelData.model_name,
            pollutantLabel: label,
            points: modelData.points || []
        });
    });

    const scatterHtml = scatterHtmlParts.length
        ? `<div class="row g-3">${scatterHtmlParts.join('')}</div>`
        : '<p class="text-muted">No se encontraron datos de dispersión.</p>';

    return `
        <div class="stage2-pollutant mb-4">
            <h5 class="fw-bold mb-3">${label}</h5>

            <div class="row g-3 mb-3">
                <div class="col-md-3">
                    <div class="metric-card">
                        <i class="bi bi-collection-play display-6 text-primary"></i>
                        <h4>${formatStage2Number(data.records)}</h4>
                        <p class="text-muted mb-0">Registros totales</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card">
                        <i class="bi bi-check-circle display-6 text-success"></i>
                        <h4>${formatStage2Number(data.records_after_cleaning)}</h4>
                        <p class="text-muted mb-0">Después de limpieza</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card">
                        <i class="bi bi-slash-circle display-6 text-warning"></i>
                        <h4>${formatStage2Number(data.outliers_removed)}</h4>
                        <p class="text-muted mb-0">Outliers eliminados</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="metric-card">
                        <i class="bi bi-award display-6 text-info"></i>
                        <h4>${bestMetrics.model_name || 'N/D'}</h4>
                        <p class="text-muted mb-0">Mejor modelo (R²: ${bestMetrics.r2?.toFixed(3) ?? 'N/D'})</p>
                    </div>
                </div>
            </div>

            <div class="plot-container mb-3">
                <h6>Comparación de modelos</h6>
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead>
                            <tr>
                                <th>Modelo</th>
                                <th>R²</th>
                                <th>R² Ajustado</th>
                                <th>RMSE</th>
                                <th>MAE</th>
                                <th>MAPE (%)</th>
                            </tr>
                        </thead>
                        <tbody>${metricsRows}</tbody>
                    </table>
                </div>
            </div>

            ${linearModelInfo}
            ${warningsHtml}
            ${scatterHtml}
        </div>
    `;
}

function plotStage2Scatter({ containerId, modelName, pollutantLabel, points }) {
    const container = document.getElementById(containerId);
    if (!container) {
        return;
    }

    if (!Array.isArray(points) || !points.length) {
        container.innerHTML = '<p class="text-muted text-center mb-0">Sin datos disponibles.</p>';
        if (window.Plotly) {
            Plotly.purge(container);
        }
        return;
    }

    const actualValues = points.map(point => point.actual);
    const predictedValues = points.map(point => point.predicted);

    if (window.Plotly) {
        const lineMin = Math.min(...actualValues, ...predictedValues);
        const lineMax = Math.max(...actualValues, ...predictedValues);

        const scatterTrace = {
            x: actualValues,
            y: predictedValues,
            mode: 'markers',
            type: 'scatter',
            name: 'Predicciones',
            marker: { color: '#1d4ed8', size: 8, opacity: 0.7 }
        };

        const perfectLine = {
            x: [lineMin, lineMax],
            y: [lineMin, lineMax],
            mode: 'lines',
            type: 'scatter',
            name: 'Línea ideal',
            line: { color: '#ef4444', dash: 'dash', width: 2 },
            hoverinfo: 'skip'
        };

        const layout = {
            margin: { t: 50, r: 30, l: 60, b: 60 },
            title: `${modelName} - ${pollutantLabel}`,
            xaxis: { title: `${pollutantLabel} real (µg/m³)` },
            yaxis: { title: `${pollutantLabel} predicho (µg/m³)` },
            showlegend: true,
            legend: { x: 0.02, y: 0.98 }
        };

        Plotly.react(container, [scatterTrace, perfectLine], layout, { responsive: true, displaylogo: false });
    }
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
async function runPrediction(useManualValues = false) {
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
            period: '2025',
            station_code: 6
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
            period: '2025',
            station_code: 6,
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
    const predictionAnalysis = document.getElementById('predictionAnalysis');
    const descriptiveStatsTable = document.getElementById('descriptiveStatsTable');
    const improvementSummary = document.getElementById('improvementSummary');
    const predictionInterpretation = document.getElementById('predictionInterpretation');
    const predictionPlot = document.getElementById('predictionPlot');
    const scatterPlotContainer = document.getElementById('scatterPlotContainer');
    const predictionScatterPlot = document.getElementById('predictionScatterPlot');

    const device_name = result.device_name;
    const pollutant = result.pollutant;
    const mode = result.mode || 'real_data';

    // Mostrar métricas de error
    if (result.error_stats) {
        predictionMetrics.innerHTML = `
            <div class="metric-card">
                <h6>RMSE Calibrado</h6>
                <p class="h4">${result.error_stats.rmse}</p>
                <small class="text-muted">Sin calibrar: ${result.error_stats.rmse_raw}</small>
            </div>
            <div class="metric-card">
                <h6>MAE Calibrado</h6>
                <p class="h4">${result.error_stats.mae}</p>
                <small class="text-muted">Sin calibrar: ${result.error_stats.mae_raw}</small>
            </div>
            <div class="metric-card">
                <h6>R² Calibrado</h6>
                <p class="h4">${result.error_stats.r2}</p>
                <small class="text-muted">Sin calibrar: ${result.error_stats.r2_raw}</small>
            </div>
            <div class="metric-card">
                <h6>Mejora RMSE</h6>
                <p class="h4 text-success">${result.error_stats.rmse_improvement_pct}%</p>
                <small class="text-muted">Reducción de error</small>
            </div>
            <div class="metric-card">
                <h6>Mejora MAE</h6>
                <p class="h4 text-success">${result.error_stats.mae_improvement_pct}%</p>
                <small class="text-muted">Reducción de error</small>
            </div>
        `;

        // Análisis descriptivo
        const stats = result.descriptive_stats;
        descriptiveStatsTable.innerHTML = `
            <tr><th colspan="3" class="table-light"><strong>Sensor Raw</strong></th></tr>
            <tr><td>Media:</td><td>${stats.sensor_raw.mean} µg/m³</td><td>Desv. Est: ${stats.sensor_raw.std}</td></tr>
            <tr><td>Mediana:</td><td>${stats.sensor_raw.median} µg/m³</td><td>Rango: ${stats.sensor_raw.min} - ${stats.sensor_raw.max}</td></tr>

            <tr><th colspan="3" class="table-light mt-2"><strong>Calibrado</strong></th></tr>
            <tr><td>Media:</td><td>${stats.predicted.mean} µg/m³</td><td>Desv. Est: ${stats.predicted.std}</td></tr>
            <tr><td>Mediana:</td><td>${stats.predicted.median} µg/m³</td><td>Rango: ${stats.predicted.min} - ${stats.predicted.max}</td></tr>

            ${stats.rmcab ? `
            <tr><th colspan="3" class="table-light mt-2"><strong>RMCAB Referencia</strong></th></tr>
            <tr><td>Media:</td><td>${stats.rmcab.mean} µg/m³</td><td>Desv. Est: ${stats.rmcab.std}</td></tr>
            <tr><td>Mediana:</td><td>${stats.rmcab.median} µg/m³</td><td>Rango: ${stats.rmcab.min} - ${stats.rmcab.max}</td></tr>
            ` : ''}
        `;

        improvementSummary.innerHTML = `
            <div class="alert alert-success mb-0">
                <h6><i class="bi bi-check-circle-fill"></i> Resumen de Mejora</h6>
                <ul class="mb-0">
                    <li><strong>RMSE:</strong> ${result.error_stats.rmse_raw} → ${result.error_stats.rmse} (${result.error_stats.rmse_improvement_pct}% mejor)</li>
                    <li><strong>MAE:</strong> ${result.error_stats.mae_raw} → ${result.error_stats.mae} (${result.error_stats.mae_improvement_pct}% mejor)</li>
                    <li><strong>R²:</strong> ${result.error_stats.r2_raw} → ${result.error_stats.r2}</li>
                    <li><strong>Comparaciones válidas:</strong> ${result.error_stats.comparisons_count} de ${result.records_count} registros</li>
                </ul>
            </div>
        `;

        predictionAnalysis.style.display = 'block';

        // Interpretación de resultados
        let interpretation = `<h6><i class="bi bi-lightbulb-fill"></i> Interpretación de Resultados</h6>`;
        const r2 = result.error_stats.r2;
        const improvement = result.error_stats.rmse_improvement_pct;

        if (r2 >= 0.9 && improvement >= 30) {
            interpretation += `<p><strong class="text-success">✓ Excelente calibración:</strong> El modelo calibrado tiene un R² de ${r2}, lo que indica un ajuste muy bueno a los datos de referencia RMCAB. La mejora de ${improvement}% en RMSE demuestra que la calibración redujo significativamente el error del sensor.</p>`;
        } else if (r2 >= 0.7 && improvement >= 20) {
            interpretation += `<p><strong class="text-info">→ Buena calibración:</strong> El R² de ${r2} indica un buen ajuste, y la mejora de ${improvement}% en RMSE muestra que la calibración es efectiva para reducir errores.</p>`;
        } else if (r2 >= 0.5 && improvement >= 10) {
            interpretation += `<p><strong class="text-warning">⚠ Calibración moderada:</strong> El R² de ${r2} sugiere un ajuste aceptable, con mejora de ${improvement}% en RMSE. Considera revisar las features utilizadas o el método de calibración.</p>`;
        } else {
            interpretation += `<p><strong class="text-danger">✗ Calibración limitada:</strong> El R² de ${r2} y la mejora de ${improvement}% indican que la calibración tuvo impacto limitado. Revisa la calidad de los datos y el modelo utilizado.</p>`;
        }

        interpretation += `<p><strong>Modelo utilizado:</strong> ${result.model_info.model_name}</p>`;
        interpretation += `<p><strong>Error promedio:</strong> ${result.error_stats.mean_error} µg/m³ (rango: ${result.error_stats.min_error} - ${result.error_stats.max_error})</p>`;

        predictionInterpretation.innerHTML = interpretation;
        predictionInterpretation.style.display = 'block';

        // Crear gráfico de dispersión
        const validPredictions = result.predictions.filter(p => p.rmcab_reference !== null);
        if (validPredictions.length > 0) {
            const rmcabVals = validPredictions.map(p => p.rmcab_reference);
            const predictedVals = validPredictions.map(p => p.predicted);
            const sensorRawVals = validPredictions.map(p => p.sensor_raw);

            const scatterTraces = [
                {
                    x: rmcabVals,
                    y: sensorRawVals,
                    mode: 'markers',
                    name: 'Sensor Raw',
                    marker: { color: '#83c5be', size: 8, opacity: 0.6 }
                },
                {
                    x: rmcabVals,
                    y: predictedVals,
                    mode: 'markers',
                    name: 'Calibrado',
                    marker: { color: '#006d77', size: 8, opacity: 0.8 }
                },
                {
                    x: rmcabVals,
                    y: rmcabVals,
                    mode: 'lines',
                    name: 'Línea 1:1',
                    line: { color: '#d62828', dash: 'dash', width: 2 }
                }
            ];

            const scatterLayout = {
                xaxis: { title: `RMCAB Referencia (µg/m³)` },
                yaxis: { title: `Predicción (µg/m³)` },
                hovermode: 'closest',
                showlegend: true
            };

            Plotly.newPlot(predictionScatterPlot, scatterTraces, scatterLayout, { responsive: true });
            scatterPlotContainer.style.display = 'block';
        }

    } else {
        predictionMetrics.innerHTML = `
            <div class="alert alert-warning">
                <strong><i class="bi bi-exclamation-triangle"></i> No hay datos de RMCAB disponibles para comparación en esta fecha.</strong>
                <p class="mb-0 mt-2">Prueba con una de las fechas sugeridas arriba para ver la comparación completa.</p>
            </div>
        `;
        predictionAnalysis.style.display = 'none';
        predictionInterpretation.style.display = 'none';
        scatterPlotContainer.style.display = 'none';
    }

    // Crear gráfico de serie de tiempo
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


