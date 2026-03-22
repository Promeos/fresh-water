/**
 * Fresh Water Monitor - Dashboard
 *
 * Loads pre-processed JSON data and renders interactive
 * Plotly charts for the Western US water analysis.
 */

const DATA_BASE = './data';
const PLOTLY_CONFIG = { responsive: true, displayModeBar: false };
const CHART_BG = 'rgba(0,0,0,0)';
const GRID_COLOR = 'rgba(255,255,255,0.06)';
const TEXT_COLOR = '#9ca3af';
const FONT = { family: 'Inter, sans-serif', color: TEXT_COLOR };

// Shared Plotly layout defaults
const BASE_LAYOUT = {
    paper_bgcolor: CHART_BG,
    plot_bgcolor: CHART_BG,
    font: FONT,
    margin: { t: 10, r: 20, b: 40, l: 55 },
    xaxis: { gridcolor: GRID_COLOR, linecolor: GRID_COLOR },
    yaxis: { gridcolor: GRID_COLOR, linecolor: GRID_COLOR },
    legend: { orientation: 'h', y: -0.2, x: 0.5, xanchor: 'center' },
};

async function loadJSON(filename) {
    const resp = await fetch(`${DATA_BASE}/${filename}`);
    if (!resp.ok) throw new Error(`Failed to load ${filename}`);
    return resp.json();
}

function formatNumber(n) {
    if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
    if (n >= 1e3) return (n / 1e3).toFixed(0) + 'K';
    return n.toString();
}

// --- Headline Metrics ---
function renderHeadline(summary) {
    const h = summary.headline;

    document.getElementById('metric-population').textContent =
        formatNumber(h.total_population);
    document.getElementById('metric-population-detail').textContent =
        'United States (50 states)';

    const affectedEl = document.getElementById('metric-affected');
    affectedEl.textContent = formatNumber(h.population_affected);
    affectedEl.className = 'metric-value warning';
    document.getElementById('metric-affected-detail').textContent =
        `${h.pct_affected}% of regional population`;

    const severeEl = document.getElementById('metric-severe');
    severeEl.textContent = formatNumber(h.population_severe);
    severeEl.className = 'metric-value negative';
    document.getElementById('metric-severe-detail').textContent =
        `${h.pct_severe}% in severe decline zones`;

    const trendEl = document.getElementById('metric-trend');
    trendEl.textContent = h.tws_trend_cm_per_year.toFixed(2) + ' cm/yr';
    trendEl.className = 'metric-value ' +
        (h.tws_trend_cm_per_year < -0.5 ? 'negative' : 'warning');
    document.getElementById('metric-trend-detail').textContent =
        'Water storage trend (2002-present)';

    document.getElementById('last-updated').textContent =
        `Last updated: ${summary.metadata.last_updated}`;
    document.getElementById('date-range').textContent =
        summary.metadata.date_range;
}

// --- Water Storage Time Series ---
function renderTWSChart(ts) {
    const monthly = {
        x: ts.dates,
        y: ts.tws_monthly,
        type: 'scatter',
        mode: 'lines',
        name: 'Monthly',
        line: { color: 'rgba(6, 182, 212, 0.3)', width: 1 },
    };

    const annual = {
        x: ts.years.map(y => `${y}-07`),
        y: ts.tws_annual,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Annual Avg',
        line: { color: '#06b6d4', width: 2.5 },
        marker: { size: 4 },
    };

    // Zero reference line
    const zero = {
        x: [ts.dates[0], ts.dates[ts.dates.length - 1]],
        y: [0, 0],
        type: 'scatter',
        mode: 'lines',
        name: 'Baseline',
        line: { color: 'rgba(255,255,255,0.2)', width: 1, dash: 'dot' },
        showlegend: false,
    };

    const layout = {
        ...BASE_LAYOUT,
        yaxis: {
            ...BASE_LAYOUT.yaxis,
            title: { text: 'Water Storage Anomaly (cm)', font: { size: 11 } },
        },
    };

    Plotly.newPlot('chart-tws', [monthly, annual, zero], layout, PLOTLY_CONFIG);
}

// --- Precipitation Time Series ---
function renderPrecipChart(ts) {
    const monthly = {
        x: ts.dates,
        y: ts.precip_monthly,
        type: 'bar',
        name: 'Monthly',
        marker: { color: 'rgba(59, 130, 246, 0.4)' },
    };

    const annual = {
        x: ts.years.map(y => `${y}-07`),
        y: ts.precip_annual,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Annual Avg',
        line: { color: '#3b82f6', width: 2.5 },
        marker: { size: 4 },
        yaxis: 'y',
    };

    const layout = {
        ...BASE_LAYOUT,
        yaxis: {
            ...BASE_LAYOUT.yaxis,
            title: { text: 'Precipitation (mm/month)', font: { size: 11 } },
        },
        barmode: 'overlay',
    };

    Plotly.newPlot('chart-precip', [monthly, annual], layout, PLOTLY_CONFIG);
}

// --- Geographic Map ---

// Major US cities for geographic context
const CITIES = [
    { name: 'New York', lat: 40.71, lon: -74.01, pop: '8.3M' },
    { name: 'Los Angeles', lat: 34.05, lon: -118.24, pop: '3.9M' },
    { name: 'Chicago', lat: 41.88, lon: -87.63, pop: '2.7M' },
    { name: 'Houston', lat: 29.76, lon: -95.37, pop: '2.3M' },
    { name: 'Phoenix', lat: 33.45, lon: -112.07, pop: '1.6M' },
    { name: 'Philadelphia', lat: 39.95, lon: -75.17, pop: '1.6M' },
    { name: 'San Antonio', lat: 29.42, lon: -98.49, pop: '1.5M' },
    { name: 'Dallas', lat: 32.78, lon: -96.80, pop: '1.3M' },
    { name: 'Seattle', lat: 47.61, lon: -122.33, pop: '737K' },
    { name: 'Denver', lat: 39.74, lon: -104.99, pop: '713K' },
    { name: 'Atlanta', lat: 33.75, lon: -84.39, pop: '499K' },
    { name: 'Miami', lat: 25.76, lon: -80.19, pop: '450K' },
    { name: 'Minneapolis', lat: 44.98, lon: -93.27, pop: '430K' },
    { name: 'Las Vegas', lat: 36.17, lon: -115.14, pop: '656K' },
    { name: 'Portland', lat: 45.52, lon: -122.68, pop: '653K' },
    { name: 'Kansas City', lat: 39.10, lon: -94.58, pop: '508K' },
    { name: 'Salt Lake City', lat: 40.76, lon: -111.89, pop: '200K' },
];

// Convert a TWS trend value to an rgba color string
function trendToColor(val, zMin, zMax) {
    // Normalize to 0-1 range
    const t = Math.max(0, Math.min(1, (val - zMin) / (zMax - zMin)));

    // Color stops: deep red -> orange -> yellow -> white -> mint -> cyan -> deep blue
    const stops = [
        { t: 0.00, r: 127, g: 29,  b: 29  },
        { t: 0.15, r: 220, g: 38,  b: 38  },
        { t: 0.35, r: 249, g: 115, b: 22  },
        { t: 0.48, r: 253, g: 230, b: 138 },
        { t: 0.50, r: 245, g: 245, b: 244 },
        { t: 0.52, r: 187, g: 247, b: 208 },
        { t: 0.65, r: 34,  g: 211, b: 238 },
        { t: 0.85, r: 2,   g: 132, b: 199 },
        { t: 1.00, r: 30,  g: 58,  b: 95  },
    ];

    // Find which two stops we're between
    let lo = stops[0], hi = stops[stops.length - 1];
    for (let i = 0; i < stops.length - 1; i++) {
        if (t >= stops[i].t && t <= stops[i + 1].t) {
            lo = stops[i];
            hi = stops[i + 1];
            break;
        }
    }

    const f = hi.t === lo.t ? 0 : (t - lo.t) / (hi.t - lo.t);
    const r = Math.round(lo.r + f * (hi.r - lo.r));
    const g = Math.round(lo.g + f * (hi.g - lo.g));
    const b = Math.round(lo.b + f * (hi.b - lo.b));

    return `rgba(${r},${g},${b},0.7)`;
}

// US States GeoJSON (public, from Plotly datasets)
const STATES_GEOJSON_URL =
    'https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json';
// Simpler: use the US states GeoJSON
const US_STATES_GEOJSON_URL =
    'https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json';

// State label positions (approximate centroids) — all 50 states
// Alaska and Hawaii are outside the contiguous map view but included for data
const STATE_CENTERS = {
    'Alabama':        { lat: 32.8, lon: -86.8 },
    'Alaska':         { lat: 64.2, lon: -152.5 },
    'Arizona':        { lat: 34.3, lon: -111.7 },
    'Arkansas':       { lat: 34.8, lon: -92.2 },
    'California':     { lat: 37.2, lon: -119.5 },
    'Colorado':       { lat: 39.0, lon: -105.5 },
    'Connecticut':    { lat: 41.6, lon: -72.7 },
    'Delaware':       { lat: 39.0, lon: -75.5 },
    'Florida':        { lat: 28.6, lon: -82.5 },
    'Georgia':        { lat: 32.7, lon: -83.5 },
    'Hawaii':         { lat: 20.8, lon: -156.3 },
    'Idaho':          { lat: 44.4, lon: -114.7 },
    'Illinois':       { lat: 40.0, lon: -89.2 },
    'Indiana':        { lat: 39.8, lon: -86.3 },
    'Iowa':           { lat: 42.0, lon: -93.5 },
    'Kansas':         { lat: 38.5, lon: -98.4 },
    'Kentucky':       { lat: 37.8, lon: -85.7 },
    'Louisiana':      { lat: 31.0, lon: -92.0 },
    'Maine':          { lat: 45.3, lon: -69.2 },
    'Maryland':       { lat: 39.0, lon: -76.7 },
    'Massachusetts':  { lat: 42.3, lon: -71.8 },
    'Michigan':       { lat: 44.3, lon: -85.4 },
    'Minnesota':      { lat: 46.3, lon: -94.3 },
    'Mississippi':    { lat: 32.7, lon: -89.7 },
    'Missouri':       { lat: 38.4, lon: -92.5 },
    'Montana':        { lat: 46.8, lon: -110.4 },
    'Nebraska':       { lat: 41.5, lon: -99.8 },
    'Nevada':         { lat: 38.8, lon: -116.6 },
    'New Hampshire':  { lat: 43.7, lon: -71.6 },
    'New Jersey':     { lat: 40.1, lon: -74.7 },
    'New Mexico':     { lat: 34.5, lon: -106.0 },
    'New York':       { lat: 42.9, lon: -75.5 },
    'North Carolina': { lat: 35.6, lon: -79.8 },
    'North Dakota':   { lat: 47.5, lon: -100.5 },
    'Ohio':           { lat: 40.3, lon: -82.8 },
    'Oklahoma':       { lat: 35.5, lon: -97.5 },
    'Oregon':         { lat: 43.8, lon: -120.5 },
    'Pennsylvania':   { lat: 40.9, lon: -77.8 },
    'Rhode Island':   { lat: 41.7, lon: -71.5 },
    'South Carolina': { lat: 33.9, lon: -80.9 },
    'South Dakota':   { lat: 44.4, lon: -100.2 },
    'Tennessee':      { lat: 35.9, lon: -86.4 },
    'Texas':          { lat: 31.5, lon: -99.3 },
    'Utah':           { lat: 39.3, lon: -111.7 },
    'Vermont':        { lat: 44.1, lon: -72.6 },
    'Virginia':       { lat: 37.5, lon: -79.0 },
    'Washington':     { lat: 47.4, lon: -120.5 },
    'West Virginia':  { lat: 38.6, lon: -80.6 },
    'Wisconsin':      { lat: 44.6, lon: -89.8 },
    'Wyoming':        { lat: 43.0, lon: -107.6 },
};

// Stress level to fill color
function stressToFill(stress) {
    if (stress === 'severe')   return 'rgba(220, 38, 38, 0.25)';
    if (stress === 'moderate') return 'rgba(249, 115, 22, 0.2)';
    return 'rgba(16, 185, 129, 0.15)';
}

function stressToBorder(stress) {
    if (stress === 'severe')   return 'rgba(220, 38, 38, 0.7)';
    if (stress === 'moderate') return 'rgba(249, 115, 22, 0.5)';
    return 'rgba(16, 185, 129, 0.4)';
}

// Real US county boundaries from Plotly datasets (FIPS-keyed)
const COUNTIES_GEOJSON_URL =
    'https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json';

async function renderSpatialMap(spatial, stateData) {
    // Load real county shapes + our county data + state boundaries
    let realCountyShapes = null;
    let countyData = null;
    let statesGeoJSON = null;
    try {
        const [shapesResp, dataResp, stateResp] = await Promise.all([
            fetch(COUNTIES_GEOJSON_URL),
            fetch(`${DATA_BASE}/counties.json`),
            fetch(US_STATES_GEOJSON_URL),
        ]);
        realCountyShapes = await shapesResp.json();
        countyData = await dataResp.json();
        statesGeoJSON = await stateResp.json();
    } catch (e) {
        console.warn('Could not load boundary data:', e);
    }

    const traces = [];
    const allStates = Object.keys(STATE_CENTERS);

    // Build a lookup from our pipeline data: FIPS -> properties
    const countyLookup = {};
    if (countyData && countyData.features) {
        for (const f of countyData.features) {
            countyLookup[f.properties.fips] = f.properties;
        }
    }

    // Layer 1: County-level choropleth using REAL boundaries
    if (realCountyShapes && Object.keys(countyLookup).length > 0) {
        // Build arrays for all counties we have data for
        const fips = [], zVals = [], hovers = [];
        for (const fipsCode of Object.keys(countyLookup)) {
            const p = countyLookup[fipsCode];
            fips.push(fipsCode);
            zVals.push(p.tws_trend);

            const sign = p.tws_trend > 0 ? '+' : '';
            const popStr = p.population >= 1e6
                ? `${(p.population / 1e6).toFixed(1)}M`
                : p.population >= 1e3
                    ? `${(p.population / 1e3).toFixed(0)}K`
                    : `${p.population}`;
            hovers.push(
                `<b>${p.name} County</b>, ${p.state}<br>` +
                `Trend: ${sign}${p.tws_trend} cm/yr<br>` +
                `Pop: ${popStr}<br>` +
                `Status: <b>${p.water_stress.toUpperCase()}</b>`
            );
        }

        traces.push({
            type: 'choroplethmapbox',
            geojson: realCountyShapes,
            locations: fips,
            featureidkey: 'id',
            z: zVals,
            colorscale: [
                [0, '#7f1d1d'],
                [0.15, '#dc2626'],
                [0.3, '#f97316'],
                [0.45, '#fbbf24'],
                [0.5, '#fef3c7'],
                [0.55, '#bbf7d0'],
                [0.7, '#22d3ee'],
                [0.85, '#0284c7'],
                [1, '#0c4a6e'],
            ],
            zmin: -3,
            zmax: 3,
            marker: {
                opacity: 0.8,
                line: { width: 0.5, color: 'rgba(255,255,255,0.15)' },
            },
            colorbar: {
                title: { text: 'cm/yr', font: { size: 11, color: TEXT_COLOR } },
                thickness: 14,
                len: 0.6,
                y: 0.5,
                tickfont: { size: 10, color: TEXT_COLOR },
                tickvals: [-3, -2, -1, 0, 1, 2, 3],
                ticktext: ['-3', '-2', '-1', '0', '+1', '+2', '+3'],
                outlinewidth: 0,
                bgcolor: 'rgba(0,0,0,0)',
            },
            hoverinfo: 'text',
            hovertext: hovers,
        });
    }

    // Layer 2: State boundary outlines (no fill, just borders for context)
    if (statesGeoJSON) {
        for (const feature of statesGeoJSON.features) {
            const stateName = feature.properties.name;
            if (!allStates.includes(stateName)) continue;

            traces.push({
                type: 'choroplethmapbox',
                geojson: { type: 'FeatureCollection', features: [feature] },
                locations: [feature.id || feature.properties.name],
                featureidkey: feature.id ? 'id' : 'properties.name',
                z: [0],
                colorscale: [[0, 'rgba(0,0,0,0)'], [1, 'rgba(0,0,0,0)']],
                marker: {
                    opacity: 0,
                    line: { width: 2, color: 'rgba(255,255,255,0.5)' },
                },
                showscale: false,
                hoverinfo: 'skip',
            });
        }
    }

    // Layer 3: State abbreviation labels (compact for 50-state view)
    const STATE_ABBREV = {
        'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA',
        'Colorado':'CO','Connecticut':'CT','Delaware':'DE','Florida':'FL','Georgia':'GA',
        'Hawaii':'HI','Idaho':'ID','Illinois':'IL','Indiana':'IN','Iowa':'IA',
        'Kansas':'KS','Kentucky':'KY','Louisiana':'LA','Maine':'ME','Maryland':'MD',
        'Massachusetts':'MA','Michigan':'MI','Minnesota':'MN','Mississippi':'MS','Missouri':'MO',
        'Montana':'MT','Nebraska':'NE','Nevada':'NV','New Hampshire':'NH','New Jersey':'NJ',
        'New Mexico':'NM','New York':'NY','North Carolina':'NC','North Dakota':'ND','Ohio':'OH',
        'Oklahoma':'OK','Oregon':'OR','Pennsylvania':'PA','Rhode Island':'RI','South Carolina':'SC',
        'South Dakota':'SD','Tennessee':'TN','Texas':'TX','Utah':'UT','Vermont':'VT',
        'Virginia':'VA','Washington':'WA','West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY',
    };

    if (stateData) {
        const labelLats = [], labelLons = [], labelTexts = [], labelHovers = [];
        for (const [state, center] of Object.entries(STATE_CENTERS)) {
            const info = stateData.states[state];
            if (!info) continue;
            // Skip Alaska/Hawaii (outside contiguous map view)
            if (state === 'Alaska' || state === 'Hawaii') continue;

            labelLats.push(center.lat);
            labelLons.push(center.lon);

            const abbrev = STATE_ABBREV[state] || state;
            labelTexts.push(abbrev);
            const sign = info.tws_trend > 0 ? '+' : '';
            labelHovers.push(
                `<b>${state}</b><br>` +
                `Water trend: ${sign}${info.tws_trend} cm/yr<br>` +
                `Population: ${(info.population / 1e6).toFixed(1)}M<br>` +
                `Status: <b>${info.water_stress.toUpperCase()}</b>`
            );
        }

        traces.push({
            type: 'scattermapbox',
            lat: labelLats,
            lon: labelLons,
            mode: 'text',
            text: labelTexts,
            textfont: {
                size: 9,
                color: 'rgba(255,255,255,0.7)',
                family: 'Inter, sans-serif',
            },
            hoverinfo: 'text',
            hovertext: labelHovers,
            showlegend: false,
        });
    }

    // Layer 4: City markers
    traces.push({
        type: 'scattermapbox',
        lat: CITIES.map(c => c.lat),
        lon: CITIES.map(c => c.lon),
        mode: 'markers+text',
        marker: { size: 5, color: '#ffffff', opacity: 0.8 },
        text: CITIES.map(c => c.name),
        textposition: 'top right',
        textfont: { size: 9, color: '#d1d5db', family: 'Inter, sans-serif' },
        hoverinfo: 'text',
        hovertext: CITIES.map(c => `<b>${c.name}</b><br>Pop: ${c.pop}`),
        showlegend: false,
    });

    const layout = {
        paper_bgcolor: CHART_BG,
        font: FONT,
        margin: { t: 0, r: 10, b: 0, l: 0 },
        mapbox: {
            style: 'carto-darkmatter',
            center: { lat: 39.0, lon: -96.0 },
            zoom: 3.5,
        },
        annotations: [
            {
                x: 0.01, y: 0.99, xref: 'paper', yref: 'paper',
                text: '<b>Water Stress by County</b><br>' +
                      '<span style="color:#ef4444">■</span> Severe (< -1.5 cm/yr)  ' +
                      '<span style="color:#f97316">■</span> Moderate (< -0.5)  ' +
                      '<span style="color:#10b981">■</span> Stable (≥ -0.5)',
                showarrow: false,
                font: { size: 11, color: '#e5e7eb' },
                xanchor: 'left', yanchor: 'top',
                bgcolor: 'rgba(0,0,0,0.6)',
                borderpad: 6,
            },
        ],
        dragmode: 'pan',
    };

    Plotly.newPlot('chart-spatial', traces, layout, {
        ...PLOTLY_CONFIG,
        scrollZoom: true,
    });
}

// --- State Impact Table ---
function renderStateTable(stateData) {
    const tbody = document.getElementById('state-tbody');
    tbody.innerHTML = '';

    // Sort by water stress severity
    const stressOrder = { severe: 0, moderate: 1, stable: 2 };
    const sorted = Object.entries(stateData.states).sort(
        (a, b) => stressOrder[a[1].water_stress] - stressOrder[b[1].water_stress]
    );

    for (const [state, data] of sorted) {
        const tr = document.createElement('tr');

        const badgeClass = data.water_stress;
        const precipSign = data.precip_change_pct >= 0 ? '+' : '';

        tr.innerHTML = `
            <td style="font-weight:500">${state}</td>
            <td>${(data.population / 1e6).toFixed(1)}M</td>
            <td style="color:${data.tws_trend < -0.5 ? '#ef4444' : data.tws_trend < 0 ? '#f59e0b' : '#10b981'}">
                ${data.tws_trend > 0 ? '+' : ''}${data.tws_trend} cm/yr
            </td>
            <td style="color:${data.precip_change_pct < -5 ? '#ef4444' : data.precip_change_pct < 0 ? '#f59e0b' : '#10b981'}">
                ${precipSign}${data.precip_change_pct}%
            </td>
            <td><span class="stress-badge ${badgeClass}">${data.water_stress}</span></td>
            <td><div id="spark-${state.replace(/\s/g, '-')}" style="width:120px;height:35px"></div></td>
        `;
        tbody.appendChild(tr);

        // Render sparkline after element is in DOM
        setTimeout(() => renderSparkline(
            `spark-${state.replace(/\s/g, '-')}`,
            data.tws_timeseries
        ), 0);
    }
}

function renderSparkline(containerId, data) {
    const el = document.getElementById(containerId);
    if (!el) return;

    const trace = {
        y: data,
        type: 'scatter',
        mode: 'lines',
        line: {
            color: data[data.length - 1] < data[0] ? '#ef4444' : '#10b981',
            width: 1.5,
        },
        hoverinfo: 'skip',
    };

    const layout = {
        paper_bgcolor: CHART_BG,
        plot_bgcolor: CHART_BG,
        margin: { t: 2, r: 2, b: 2, l: 2 },
        xaxis: { visible: false },
        yaxis: { visible: false },
    };

    Plotly.newPlot(el, [trace], layout, {
        ...PLOTLY_CONFIG,
        staticPlot: true,
    });
}

// --- Initialize ---
async function init() {
    try {
        // Load all data files in parallel
        const [summary, timeseries, spatial, states] = await Promise.all([
            loadJSON('summary.json'),
            loadJSON('timeseries.json'),
            loadJSON('spatial.json'),
            loadJSON('states.json'),
        ]);

        // Render all components
        renderHeadline(summary);
        renderTWSChart(timeseries);
        renderPrecipChart(timeseries);
        renderSpatialMap(spatial, states);
        renderStateTable(states);

        // Remove loading states
        document.querySelectorAll('.loading').forEach(el => {
            el.classList.remove('loading');
        });
    } catch (err) {
        console.error('Failed to load dashboard data:', err);
        document.querySelectorAll('.loading').forEach(el => {
            el.innerHTML = `<p style="color: var(--accent-red)">
                Failed to load data. Run the pipeline first:<br>
                <code>python -m pipeline.export</code>
            </p>`;
        });
    }
}

document.addEventListener('DOMContentLoaded', init);
