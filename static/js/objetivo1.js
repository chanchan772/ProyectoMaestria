/**
 * Objetivo 1: Calibración Avanzada de Sensores
 * Script para DOS gráficos de series de tiempo: PM2.5 y PM10
 * Datos 100% REALES - SIN SIMULACIÓN
 */

let currentData = null;

// Verificar que Plotly está cargado
function checkDependencies() {
    if (typeof Plotly === 'undefined') {
        console.error('ERROR: Plotly no está cargado.');
        return false;
    }
    return true;
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('[Objetivo1] DOM cargado, inicializando...');

    if (!checkDependencies()) {
        document.getElementById('errorAlert').textContent = 'Error: Librerías no cargadas. Recargue la página.';
        document.getElementById('errorAlert').style.display = 'block';
        return;
    }

    setupEventListeners();
    console.log('[Objetivo1] Event listeners configurados.');
});

function setupEventListeners() {
    const btnInitData = document.getElementById('btnInitData');
    if (btnInitData) {
        btnInitData.addEventListener('click', handleInitData);
    }

    const btnCalibrate = document.getElementById('btnCalibrate');
    if (btnCalibrate) {
        btnCalibrate.addEventListener('click', handleCalibrate);
    }

    const btnTestRanges = document.getElementById('btnTestRanges');
    if (btnTestRanges) {
        btnTestRanges.addEventListener('click', handleTestRanges);
    }
}

// Maneja la carga inicial de datos
async function handleInitData() {
    const btnInitData = document.getElementById('btnInitData');
    const btnInitText = document.getElementById('btnInitText');
    const btnInitSpinner = document.getElementById('btnInitSpinner');
    const loadingAlert = document.getElementById('loadingAlert');
    const errorAlert = document.getElementById('errorAlert');

    try {
        console.log('[handleInitData] Iniciando carga de datos...');

        btnInitData.disabled = true;
        if (btnInitSpinner) btnInitSpinner.style.display = 'inline-block';
        if (loadingAlert) loadingAlert.style.display = 'block';
        if (errorAlert) errorAlert.style.display = 'none';

        // Llamar a /api/objetivo1/initialize para cargar datos
        console.log('[handleInitData] Llamando a /api/objetivo1/initialize...');
        const initResponse = await fetch('/api/objetivo1/initialize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (!initResponse.ok) {
            throw new Error(`Error: ${initResponse.status} ${initResponse.statusText}`);
        }

        const initData = await initResponse.json();
        console.log('[handleInitData] Datos inicializados:', initData);

        // Cargar DOS gráficos: PM2.5 y PM10
        console.log('[handleInitData] Cargando gráficos...');
        await loadCharts();

        // Actualizar estado
        if (loadingAlert) loadingAlert.style.display = 'none';
        if (btnInitText) btnInitText.textContent = '✅ Datos Cargados';
        console.log('[handleInitData] Completado exitosamente');

    } catch (error) {
        console.error('[handleInitData] Error:', error);
        if (errorAlert) {
            errorAlert.innerHTML = `<strong>Error:</strong> ${error.message}`;
            errorAlert.style.display = 'block';
        }
    } finally {
        btnInitData.disabled = false;
        if (btnInitSpinner) btnInitSpinner.style.display = 'none';
    }
}

// Carga DOS gráficos: PM2.5 y PM10
async function loadCharts() {
    try {
        console.log('[loadCharts] Cargando datos reales...');

        const response = await fetch('/api/objetivo1/charts');

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const apiData = await response.json();
        console.log('[loadCharts] Datos recibidos');

        // Mostrar sección de timeseries (tabbed)
        showSection('timeseriesSection');

        // Gráfico 1: PM2.5
        console.log('[loadCharts] Generando gráfico PM2.5...');
        renderPM25Chart(apiData.pm25);

        // Gráfico 2: PM10
        console.log('[loadCharts] Generando gráfico PM10...');
        renderPM10Chart(apiData.pm10);

        // Mostrar sección de scatter (tabbed)
        showSection('scatterSection');

        // Scatter plots
        console.log('[loadCharts] Generando scatter plots...');
        renderScatterPlots(apiData.pm25, apiData.pm10);

        // Setup tab change handlers para redimensionar gráficos
        setupTabHandlers();

        // Mostrar botón de calibración
        showSection('calibrationButtonSection');

        console.log('[loadCharts] Gráficos generados exitosamente');

    } catch (error) {
        console.error('[loadCharts] Error:', error);
        throw error;
    }
}

// Renderiza gráfico de PM2.5
function renderPM25Chart(chartData) {
    const data = chartData.data;

    // Agrupar por dispositivo
    const sensors = {};
    data.forEach(record => {
        if (!sensors[record.device_name]) {
            sensors[record.device_name] = { datetimes: [], values: [] };
        }
        sensors[record.device_name].datetimes.push(record.datetime);
        sensors[record.device_name].values.push(record.pm25);
    });

    // Crear trazas para sensores (Aire2, Aire4, Aire5)
    const traces = [];
    const sensorOrder = ['Aire2', 'Aire4', 'Aire5'];
    const colors = ['#1f77b4', '#ff7f0e', '#2ca02c'];

    sensorOrder.forEach((sensor, idx) => {
        if (sensors[sensor]) {
            traces.push({
                x: sensors[sensor].datetimes,
                y: sensors[sensor].values,
                mode: 'lines',
                name: sensor,
                line: { color: colors[idx], width: 2 },
                hovertemplate: [
                    '<b>' + sensor + '</b>',
                    'Fecha/Hora: %{x}',
                    'PM2.5: %{y:.2f} μg/m³',
                    '<extra></extra>'
                ].join('<br>')
            });
        }
    });

    // Agregar RMCAB (referencia) - usar pm10_ref si pm25_ref no está disponible
    // Usar datetime_rmcab para horas cerradas
    const rmcabData = { datetimes: [], values: [] };
    data.forEach(record => {
        let refValue = record.pm25_ref;
        if ((refValue === null || refValue === undefined) && record.pm10_ref !== null && record.pm10_ref !== undefined) {
            refValue = record.pm10_ref;
        }
        if (refValue !== null && refValue !== undefined) {
            // Usar datetime_rmcab (horas cerradas) en lugar de datetime del sensor
            rmcabData.datetimes.push(record.datetime_rmcab || record.datetime);
            rmcabData.values.push(refValue);
        }
    });

    // Eliminar duplicados de RMCAB (varios sensores pueden tener la misma hora redondeada)
    const uniqueRmcab = {};
    rmcabData.datetimes.forEach((dt, idx) => {
        if (!uniqueRmcab[dt]) {
            uniqueRmcab[dt] = rmcabData.values[idx];
        }
    });

    if (Object.keys(uniqueRmcab).length > 0) {
        traces.push({
            x: Object.keys(uniqueRmcab),
            y: Object.values(uniqueRmcab),
            mode: 'lines',
            name: 'RMCAB (Referencia)',
            line: { color: 'black', width: 3, dash: 'solid' },
            hovertemplate: [
                '<b>RMCAB - Referencia Oficial</b>',
                'Fecha/Hora: %{x}',
                'Valor: %{y:.2f} μg/m³',
                '<extra></extra>'
            ].join('<br>')
        });
    }

    const layout = {
        title: chartData.title,
        xaxis: { title: 'Fecha' },
        yaxis: { title: 'PM2.5 (μg/m³)', range: [0, 100] },
        hovermode: 'x unified',
        template: 'plotly_white',
        height: 500,
        margin: { l: 60, r: 50, t: 60, b: 60 }
    };

    Plotly.newPlot('timeseriesChart', traces, layout, {
        responsive: true,
        displayModeBar: true
    });
}

// Renderiza gráfico de PM10
function renderPM10Chart(chartData) {
    const data = chartData.data;

    console.log('[renderPM10Chart] Datos recibidos:', data.length, 'registros');
    console.log('[renderPM10Chart] Primeros datos:', data.slice(0, 3));

    // Agrupar por dispositivo
    const sensors = {};
    data.forEach(record => {
        if (!sensors[record.device_name]) {
            sensors[record.device_name] = { datetimes: [], values: [] };
        }
        sensors[record.device_name].datetimes.push(record.datetime);
        sensors[record.device_name].values.push(record.pm10);
    });

    console.log('[renderPM10Chart] Sensores agrupados:', Object.keys(sensors));
    for (let sensor in sensors) {
        console.log(`  ${sensor}: ${sensors[sensor].values.length} valores`);
    }

    // Crear trazas para sensores (Aire2, Aire4, Aire5)
    const traces = [];
    const sensorOrder = ['Aire2', 'Aire4', 'Aire5'];
    const colors = ['#1f77b4', '#ff7f0e', '#2ca02c'];

    sensorOrder.forEach((sensor, idx) => {
        if (sensors[sensor]) {
            console.log(`[renderPM10Chart] Agregando traza para ${sensor}`);
            traces.push({
                x: sensors[sensor].datetimes,
                y: sensors[sensor].values,
                mode: 'lines',
                name: sensor,
                line: { color: colors[idx], width: 2 },
                hovertemplate: [
                    '<b>' + sensor + '</b>',
                    'Fecha/Hora: %{x}',
                    'PM10: %{y:.2f} μg/m³',
                    '<extra></extra>'
                ].join('<br>')
            });
        }
    });

    // Agregar RMCAB (referencia) para PM10 - usar datetime_rmcab (horas cerradas)
    const rmcabData = { datetimes: [], values: [] };
    data.forEach(record => {
        if (record.pm10_ref !== null && record.pm10_ref !== undefined) {
            rmcabData.datetimes.push(record.datetime_rmcab || record.datetime);
            rmcabData.values.push(record.pm10_ref);
        }
    });

    console.log('[renderPM10Chart] RMCAB datos recolectados:', rmcabData.datetimes.length);

    // Eliminar duplicados de RMCAB
    const uniqueRmcab = {};
    rmcabData.datetimes.forEach((dt, idx) => {
        if (!uniqueRmcab[dt]) {
            uniqueRmcab[dt] = rmcabData.values[idx];
        }
    });

    console.log('[renderPM10Chart] RMCAB únicos:', Object.keys(uniqueRmcab).length);

    if (Object.keys(uniqueRmcab).length > 0) {
        traces.push({
            x: Object.keys(uniqueRmcab),
            y: Object.values(uniqueRmcab),
            mode: 'lines',
            name: 'RMCAB (Referencia)',
            line: { color: 'black', width: 3, dash: 'solid' },
            hovertemplate: [
                '<b>RMCAB - Referencia Oficial</b>',
                'Fecha/Hora: %{x}',
                'PM10: %{y:.2f} μg/m³',
                '<extra></extra>'
            ].join('<br>')
        });
    }

    // Calcular rango dinámico para Y
    let minY = Infinity;
    let maxY = -Infinity;
    traces.forEach(trace => {
        trace.y.forEach(val => {
            if (typeof val === 'number') {
                minY = Math.min(minY, val);
                maxY = Math.max(maxY, val);
            }
        });
    });

    // Añadir 10% de margen
    const margin = (maxY - minY) * 0.1 || 10;
    const yMin = Math.max(0, minY - margin);
    const yMax = maxY + margin;

    console.log('[renderPM10Chart] Rango Y calculado:', yMin, '-', yMax);

    const layout = {
        title: chartData.title,
        xaxis: { title: 'Fecha' },
        yaxis: { title: 'PM10 (μg/m³)', range: [yMin, yMax] },
        hovermode: 'x unified',
        template: 'plotly_white',
        height: 500,
        margin: { l: 60, r: 50, t: 60, b: 60 }
    };

    console.log('[renderPM10Chart] Renderizando con ', traces.length, ' trazas');
    Plotly.newPlot('pm10Chart', traces, layout, {
        responsive: true,
        displayModeBar: true
    });
}

// Renderiza scatter plots para PM2.5 y PM10
function renderScatterPlots(pm25Data, pm10Data) {
    // Scatter plot PM2.5 vs RMCAB
    renderScatterPM25(pm25Data.data);
    // Scatter plot PM10
    renderScatterPM10(pm10Data.data);
}

// Scatter plot PM2.5 vs RMCAB
function renderScatterPM25(data) {
    const traces = [];
    const sensorOrder = ['Aire2', 'Aire4', 'Aire5'];
    const colors = ['#1f77b4', '#ff7f0e', '#2ca02c'];

    // Crear trazas para cada sensor
    sensorOrder.forEach((sensor, idx) => {
        const sensorData = data.filter(d => d.device_name === sensor);
        const refValues = [];
        const sensorValues = [];

        sensorData.forEach(record => {
            let refVal = record.pm25_ref;
            if ((refVal === null || refVal === undefined) && record.pm10_ref !== null) {
                refVal = record.pm10_ref;
            }
            if (refVal !== null && refVal !== undefined) {
                refValues.push(refVal);
                sensorValues.push(record.pm25);
            }
        });

        if (refValues.length > 0) {
            traces.push({
                x: refValues,
                y: sensorValues,
                mode: 'markers',
                name: sensor,
                marker: { color: colors[idx], size: 6, opacity: 0.6 },
                type: 'scatter',
                hovertemplate: [
                    '<b>' + sensor + '</b>',
                    'RMCAB: %{x:.2f} μg/m³',
                    'Sensor: %{y:.2f} μg/m³',
                    'Diferencia: %{customdata:.2f} μg/m³',
                    '<extra></extra>'
                ].join('<br>'),
                customdata: sensorValues.map((v, i) => v - refValues[i])
            });
        }
    });

    // Agregar línea diagonal y=x (referencia)
    const maxVal = Math.max(...data.map(d => Math.max(d.pm25 || 0, d.pm25_ref || d.pm10_ref || 0)));
    traces.push({
        x: [0, maxVal],
        y: [0, maxVal],
        mode: 'lines',
        name: 'y=x (Referencia)',
        line: { color: 'red', width: 2, dash: 'dash' },
        showlegend: true
    });

    const layout = {
        title: 'PM2.5: Sensores vs RMCAB',
        xaxis: { title: 'RMCAB PM2.5 (μg/m³)', range: [0, 100] },
        yaxis: { title: 'Sensor PM2.5 (μg/m³)', range: [0, 100] },
        hovermode: 'closest',
        template: 'plotly_white',
        height: 480,
        margin: { l: 70, r: 50, t: 60, b: 70 }
    };

    const pm25Div = document.getElementById('scatterPM25');
    if (pm25Div) {
        Plotly.newPlot('scatterPM25', traces, layout, {
            responsive: true,
            displayModeBar: true
        });
    }
}

// Scatter plot PM10 vs RMCAB
function renderScatterPM10(data) {
    const traces = [];
    const sensorOrder = ['Aire2', 'Aire4', 'Aire5'];
    const colors = ['#1f77b4', '#ff7f0e', '#2ca02c'];

    // Crear trazas para cada sensor
    sensorOrder.forEach((sensor, idx) => {
        const sensorData = data.filter(d => d.device_name === sensor);
        const refValues = [];
        const sensorValues = [];

        sensorData.forEach(record => {
            let refVal = record.pm10_ref;
            if (refVal !== null && refVal !== undefined) {
                refValues.push(refVal);
                sensorValues.push(record.pm10);
            }
        });

        if (refValues.length > 0) {
            traces.push({
                x: refValues,
                y: sensorValues,
                mode: 'markers',
                name: sensor,
                marker: { color: colors[idx], size: 6, opacity: 0.6 },
                type: 'scatter',
                hovertemplate: [
                    '<b>' + sensor + '</b>',
                    'RMCAB: %{x:.2f} μg/m³',
                    'Sensor: %{y:.2f} μg/m³',
                    'Diferencia: %{customdata:.2f} μg/m³',
                    '<extra></extra>'
                ].join('<br>'),
                customdata: sensorValues.map((v, i) => v - refValues[i])
            });
        }
    });

    // Agregar línea diagonal y=x (referencia)
    const maxVal = Math.max(...data.map(d => Math.max(d.pm10 || 0, d.pm10_ref || 0)));
    traces.push({
        x: [0, maxVal],
        y: [0, maxVal],
        mode: 'lines',
        name: 'y=x (Referencia)',
        line: { color: 'red', width: 2, dash: 'dash' },
        showlegend: true
    });

    const layout = {
        title: 'PM10: Sensores vs RMCAB',
        xaxis: { title: 'RMCAB PM10 (μg/m³)', range: [0, Math.max(60, maxVal * 1.1)] },
        yaxis: { title: 'Sensor PM10 (μg/m³)', range: [0, Math.max(60, maxVal * 1.1)] },
        hovermode: 'closest',
        template: 'plotly_white',
        height: 480,
        margin: { l: 70, r: 50, t: 60, b: 70 }
    };

    const pm10Div = document.getElementById('scatterPM10');
    if (pm10Div) {
        Plotly.newPlot('scatterPM10', traces, layout, {
            responsive: true,
            displayModeBar: true
        });
    }
}

// Setup tab handlers para redimensionar gráficos cuando cambian tabs
function setupTabHandlers() {
    // Tabs de timeseries
    const pm25TimeseriesTab = document.getElementById('pm25-timeseries-tab');
    const pm10TimeseriesTab = document.getElementById('pm10-timeseries-tab');

    if (pm25TimeseriesTab) {
        pm25TimeseriesTab.addEventListener('shown.bs.tab', function() {
            console.log('[setupTabHandlers] PM2.5 timeseries tab activado');
            setTimeout(() => {
                Plotly.Plots.resize('timeseriesChart');
            }, 100);
        });
    }

    if (pm10TimeseriesTab) {
        pm10TimeseriesTab.addEventListener('shown.bs.tab', function() {
            console.log('[setupTabHandlers] PM10 timeseries tab activado');
            setTimeout(() => {
                Plotly.Plots.resize('pm10Chart');
            }, 100);
        });
    }

    // Tabs de scatter plots
    const pm25ScatterTab = document.getElementById('pm25-scatter-tab');
    const pm10ScatterTab = document.getElementById('pm10-scatter-tab');

    if (pm25ScatterTab) {
        pm25ScatterTab.addEventListener('shown.bs.tab', function() {
            console.log('[setupTabHandlers] PM2.5 scatter tab activado');
            setTimeout(() => {
                Plotly.Plots.resize('scatterPM25');
            }, 100);
        });
    }

    if (pm10ScatterTab) {
        pm10ScatterTab.addEventListener('shown.bs.tab', function() {
            console.log('[setupTabHandlers] PM10 scatter tab activado');
            setTimeout(() => {
                Plotly.Plots.resize('scatterPM10');
            }, 100);
        });
    }
}

function showSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.style.display = 'block';
    }
}

// ============== CALIBRACIÓN MULTI-RANGO ==============

function handleCalibrate() {
    console.log('[handleCalibrate] Iniciando calibración completa...');

    const btn = document.getElementById('btnCalibrate');
    const btnText = document.getElementById('btnCalibrateText');
    const btnSpinner = document.getElementById('btnCalibrateSpinner');

    btn.disabled = true;
    btnSpinner.style.display = 'inline-block';
    btnText.textContent = '⏳ Calibrando...';

    // Mostrar sección de progreso
    const progressSection = document.getElementById('calibrationProgressSection');
    if (progressSection) {
        progressSection.style.display = 'block';
    }

    fetch('/api/objetivo1/calibration', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return response.json();
    })
    .then(data => {
        console.log('[handleCalibrate] Datos recibidos:', data);

        if (data.status === 'success') {
            // Procesar y mostrar resultados
            processCalibrationResults(data.data);

            // Mostrar sección de resultados
            const resultsSection = document.getElementById('calibrationResultsSection');
            if (resultsSection) {
                resultsSection.style.display = 'block';
            }

            btnText.textContent = '✅ Calibración Completada';
        } else {
            throw new Error(data.message || 'Error en calibración');
        }
    })
    .catch(error => {
        console.error('[handleCalibrate] Error:', error);
        btnText.textContent = '❌ Error en Calibración';
        alert(`Error: ${error.message}`);
    })
    .finally(() => {
        btn.disabled = false;
        btnSpinner.style.display = 'none';

        // Ocultar progreso
        const progressSection = document.getElementById('calibrationProgressSection');
        if (progressSection) {
            progressSection.style.display = 'none';
        }
    });
}

// Genera dinámicamente las pestañas para cada sensor (Aire2, Aire4, Aire5)
function generateCalibrationTabs(calibrationData) {
    console.log('[generateCalibrationTabs] Generando pestañas dinámicamente...');

    const sensors = ['Aire2', 'Aire4', 'Aire5'];
    const pollutants = ['PM2.5', 'PM10'];
    const timeRanges = [
        { key: 'completo', label: 'Completo (60 días)' },
        { key: '30dias', label: '30 días' },
        { key: '15dias', label: '15 días' },
        { key: '5dias', label: '5 días' },
        { key: '3dias', label: '3 días' }
    ];

    const tabsContainer = document.getElementById('calibrationMainTabs');
    const contentContainer = document.getElementById('calibrationMainTabContent');

    if (!tabsContainer || !contentContainer) {
        console.error('[generateCalibrationTabs] Contenedores no encontrados');
        return;
    }

    tabsContainer.innerHTML = '';
    contentContainer.innerHTML = '';

    // Crear tab buttons para cada sensor
    sensors.forEach((sensor, sensorIndex) => {
        const tabId = `sensor-${sensor.toLowerCase()}-tab`;
        const panelId = `sensor-${sensor.toLowerCase()}-pane`;
        const isActive = sensorIndex === 0 ? 'active' : '';

        const tabBtn = document.createElement('button');
        tabBtn.className = `nav-link ${isActive}`;
        tabBtn.id = tabId;
        tabBtn.setAttribute('data-bs-toggle', 'tab');
        tabBtn.setAttribute('data-bs-target', `#${panelId}`);
        tabBtn.setAttribute('type', 'button');
        tabBtn.setAttribute('role', 'tab');
        tabBtn.setAttribute('aria-controls', panelId);
        tabBtn.setAttribute('aria-selected', isActive ? 'true' : 'false');
        tabBtn.textContent = sensor;

        const li = document.createElement('li');
        li.className = 'nav-item';
        li.setAttribute('role', 'presentation');
        li.appendChild(tabBtn);
        tabsContainer.appendChild(li);

        // Crear panel para cada sensor
        const sensorPanel = document.createElement('div');
        sensorPanel.className = `tab-pane fade ${isActive ? 'show active' : ''}`;
        sensorPanel.id = panelId;
        sensorPanel.setAttribute('role', 'tabpanel');
        sensorPanel.setAttribute('aria-labelledby', tabId);

        // Crear sub-tabs para PM2.5 y PM10 dentro de cada sensor
        const particleTabsHtml = `
            <ul class="nav nav-tabs nav-tabs-secondary mt-2 mb-3" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="${sensor}-pm25-tab" data-bs-toggle="tab"
                            data-bs-target="#${sensor}-pm25-pane" type="button" role="tab"
                            aria-controls="${sensor}-pm25-pane" aria-selected="true">
                        PM2.5
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="${sensor}-pm10-tab" data-bs-toggle="tab"
                            data-bs-target="#${sensor}-pm10-pane" type="button" role="tab"
                            aria-controls="${sensor}-pm10-pane" aria-selected="false">
                        PM10
                    </button>
                </li>
            </ul>
            <div class="tab-content">
                <div class="tab-pane fade show active" id="${sensor}-pm25-pane" role="tabpanel" aria-labelledby="${sensor}-pm25-tab">
                    ${generateTimeRangeTabs(sensor, 'pm25', timeRanges, calibrationData)}
                </div>
                <div class="tab-pane fade" id="${sensor}-pm10-pane" role="tabpanel" aria-labelledby="${sensor}-pm10-tab">
                    ${generateTimeRangeTabs(sensor, 'pm10', timeRanges, calibrationData)}
                </div>
            </div>
        `;

        sensorPanel.innerHTML = particleTabsHtml;
        contentContainer.appendChild(sensorPanel);
    });

    console.log('[generateCalibrationTabs] Pestañas generadas exitosamente');
}

// Genera las sub-pestañas de rangos temporales para cada sensor-partícula
function generateTimeRangeTabs(sensor, pollutant, timeRanges, calibrationData) {
    const timeRangeKey = pollutant.toLowerCase();
    const pollutantData = calibrationData[timeRangeKey] || {};

    let html = `<ul class="nav nav-pills mb-3" role="tablist">`;

    timeRanges.forEach((range, index) => {
        const isActive = index === 0 ? 'active' : '';
        const pollutantUpper = pollutant.toUpperCase();
        const tabId = `${sensor}-${pollutantUpper}-${range.key}-tab`;
        const panelId = `${sensor}-${pollutantUpper}-${range.key}-pane`;
        html += `
            <li class="nav-item" role="presentation">
                <button class="nav-link ${isActive}" id="${tabId}" data-bs-toggle="tab"
                        data-bs-target="#${panelId}" type="button" role="tab"
                        aria-controls="${panelId}" aria-selected="${isActive ? 'true' : 'false'}">
                    ${range.label}
                </button>
            </li>
        `;
    });

    html += `</ul><div class="tab-content">`;

    timeRanges.forEach((range, index) => {
        const isActive = index === 0 ? 'show active' : '';
        const pollutantUpper = pollutant.toUpperCase();
        const panelId = `${sensor}-${pollutantUpper}-${range.key}-pane`;
        const tableId = `${sensor}-${pollutantUpper}-${range.key}-table`;

        html += `
            <div class="tab-pane fade ${isActive}" id="${panelId}" role="tabpanel">
                <h6 class="mb-3">${range.label} - ${sensor} - ${pollutantUpper}</h6>
                <div class="table-responsive">
                    <table class="table table-sm table-hover table-bordered" id="${tableId}">
                        <thead class="table-light">
                            <tr>
                                <th>Modelo</th>
                                <th>R² Score</th>
                                <th>RMSE</th>
                                <th>MAE</th>
                                <th>MAPE (%)</th>
                                <th>Muestras</th>
                            </tr>
                        </thead>
                        <tbody id="${tableId}_tbody">
                            <tr><td colspan="6" class="text-center text-muted">Cargando datos...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    });

    html += `</div>`;
    return html;
}

function processCalibrationResults(calibrationData) {
    // Procesa y visualiza resultados de calibración para PM2.5 y PM10
    console.log('[processCalibrationResults] Procesando resultados...');
    console.log('[processCalibrationResults] Estructura de datos completa:', calibrationData);

    // Generar pestañas dinámicamente
    generateCalibrationTabs(calibrationData);

    const sensors = ['Aire2', 'Aire4', 'Aire5'];
    const pollutants = ['pm25', 'pm10'];
    const timeRanges = ['completo', '30dias', '15dias', '5dias', '3dias'];

    // Llenar tablas dinámicamente
    for (const sensor of sensors) {
        for (const pollutant of pollutants) {
            const pollutantData = calibrationData[pollutant];
            if (!pollutantData) {
                console.warn(`[processCalibrationResults] No hay datos para ${pollutant}`);
                continue;
            }

            // Obtener datos específicos de este sensor
            const sensorData = pollutantData.all_results[sensor] || pollutantData.by_sensor[sensor];
            if (!sensorData) {
                console.warn(`[processCalibrationResults] Sin datos para ${sensor} - ${pollutant}`, sensorData);
                console.log(`[DEBUG] Estructura pollutantData:`, pollutantData);
                continue;
            }

            console.log(`[DEBUG] Datos para ${sensor}-${pollutant}:`, sensorData);

            // Procesar cada rango de tiempo
            for (const timeRange of timeRanges) {
                const tableId = `${sensor}-${pollutant.toUpperCase()}-${timeRange}-table_tbody`;
                const tableBody = document.getElementById(tableId);

                if (!tableBody) {
                    console.warn(`[processCalibrationResults] Tabla no encontrada: ${tableId}`);
                    continue;
                }

                console.log(`[DEBUG] Procesando ${sensor}-${pollutant}-${timeRange}`);
                console.log(`[DEBUG] sensorData[${timeRange}]:`, sensorData[timeRange]);

                // Limpiar tabla anterior
                tableBody.innerHTML = '';

                // Obtener resultados para este rango Y sensor
                const rangeResults = sensorData[timeRange];
                console.log(`[DEBUG] rangeResults para ${timeRange}:`, rangeResults);
                console.log(`[DEBUG] Tipo de rangeResults:`, typeof rangeResults);
                console.log(`[DEBUG] Keys en rangeResults:`, Object.keys(rangeResults || {}));

                // Si no hay resultados, mostrar mensaje
                if (!rangeResults || Object.keys(rangeResults).length === 0) {
                    console.log(`[DEBUG] SIN DATOS para ${sensor}-${pollutant}-${timeRange}`);
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td colspan="6" class="text-center text-muted">
                            <em>No hay datos válidos para este rango</em>
                        </td>
                    `;
                    tableBody.appendChild(row);
                } else {
                    console.log(`[DEBUG] Llenando tabla con ${Object.keys(rangeResults).length} modelos`);
                    // Llenar tabla con resultados de todos los modelos
                    for (const [modelName, metrics] of Object.entries(rangeResults)) {
                        console.log(`[DEBUG] Modelo: ${modelName}`, metrics);
                        console.log(`[DEBUG] Campos de metrics:`, {
                            status: metrics.status,
                            r2: metrics.r2,
                            rmse: metrics.rmse,
                            mae: metrics.mae,
                            mape: metrics.mape,
                            n_samples: metrics.n_samples
                        });

                        if (metrics.status === 'error') {
                            console.log(`[DEBUG] Saltando modelo ${modelName} por error`);
                            continue;
                        }

                        try {
                            const row = document.createElement('tr');
                            row.innerHTML = `
                                <td><strong>${modelName}</strong></td>
                                <td><span class="badge" style="background-color: ${getR2Color(metrics.r2)}">${metrics.r2.toFixed(4)}</span></td>
                                <td>${metrics.rmse.toFixed(4)}</td>
                                <td>${metrics.mae.toFixed(4)}</td>
                                <td>${metrics.mape.toFixed(2)}%</td>
                                <td>${metrics.n_samples}</td>
                            `;
                            tableBody.appendChild(row);
                            console.log(`[DEBUG] Fila agregada para ${modelName}`);
                        } catch (err) {
                            console.error(`[ERROR] Error al agregar fila para ${modelName}:`, err);
                        }
                    }
                }
            }
        }
    }

    console.log('[processCalibrationResults] Resultados procesados exitosamente');
}

function updateRangeConclusion(pollutant, timeRange, bestModelInfo, conclusionData) {
    // Actualiza la conclusión (CUMPLE/NO CUMPLE) para un rango específico, incluyendo recomendación
    const bestModelEl = document.getElementById(`${pollutant}_${timeRange}_best_model`);
    const cumpleEl = document.getElementById(`${pollutant}_${timeRange}_cumple`);
    const razonEl = document.getElementById(`${pollutant}_${timeRange}_razon`);
    const recommendEl = document.getElementById(`${pollutant}_${timeRange}_recommendation`);
    const statusDiv = document.getElementById(`${pollutant}_${timeRange}_status`);

    if (!bestModelEl || !cumpleEl || !razonEl) return;

    if (!bestModelInfo || !bestModelInfo.model) {
        cumpleEl.innerHTML = '❌ NO DATOS';
        razonEl.textContent = 'No hay datos suficientes para este rango';
        if (recommendEl) {
            recommendEl.style.display = 'none';
        }
        return;
    }

    const r2 = bestModelInfo.r2;
    const threshold = 0.8;
    const cumple = r2 >= threshold;

    bestModelEl.textContent = bestModelInfo.model;
    cumpleEl.innerHTML = cumple
        ? `✅ CUMPLE (R² = ${r2.toFixed(4)})`
        : `❌ NO CUMPLE (R² = ${r2.toFixed(4)})`;
    razonEl.textContent = cumple
        ? `R² de ${r2.toFixed(4)} >= ${threshold} (umbral)`
        : `R² de ${r2.toFixed(4)} < ${threshold} (umbral)`;

    // Mostrar recomendación si existe
    if (recommendEl && conclusionData && conclusionData.recommendation) {
        const recommendTextEl = document.getElementById(`${pollutant}_${timeRange}_recommendation_text`);
        if (recommendTextEl) {
            recommendTextEl.textContent = conclusionData.recommendation;
        }
        recommendEl.style.display = 'block';
    }

    // Mostrar el div de status
    if (statusDiv) {
        statusDiv.style.display = 'block';
    }
}

function getR2Color(r2Value) {
    // Retorna color según valor de R²
    if (r2Value >= 0.9) return '#28a745'; // Verde fuerte
    if (r2Value >= 0.8) return '#5cb85c'; // Verde
    if (r2Value >= 0.7) return '#ffc107'; // Amarillo
    if (r2Value >= 0.6) return '#ff9800'; // Naranja
    return '#dc3545'; // Rojo
}

function handleTestRanges() {
    console.log('[handleTestRanges] Probando rangos de tiempo...');

    // Esta función se puede usar para ejecutar calibración rápida por rango
    // Por ahora, simplemente llamamos a la calibración completa
    handleCalibrate();
}
