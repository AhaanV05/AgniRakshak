/* Header behavior */
const header = document.getElementById('siteHeader');
const onScroll = () => {
  if (window.scrollY > 6) header.classList.add('scrolled');
  else header.classList.remove('scrolled');
};
window.addEventListener('scroll', onScroll);

/* Leaflet Map */
const startLat = 23.48340, startLng = 77.34375;
const map = L.map('leafletMap', { zoomControl: true, attributionControl: true }).setView([startLat, startLng], 5);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 18,
  attribution: '© OpenStreetMap'
}).addTo(map);

const marker = L.marker([startLat, startLng]).addTo(map);
const coordPill = document.getElementById('coordPill');
coordPill.textContent = `Lat: ${startLat.toFixed(5)}, Lng: ${startLng.toFixed(5)}`;

/* NASA FIRMS WMS overlays */
const FIRMS_KEY = 'af28b7077bbb1bdf9b5e67f7b83d304f';

function getFirmsLayer(sensor, period) {
  return L.tileLayer.wms(
    `https://firms.modaps.eosdis.nasa.gov/mapserver/wms/fires/${FIRMS_KEY}/`,
    {
      layers: `fires_${sensor}_${period}`,
      format: 'image/png',
      transparent: true,
      attribution: 'NASA FIRMS'
    }
  );
}

const modis24 = getFirmsLayer('modis', '24');
const modis48 = getFirmsLayer('modis', '48');
const modis7d  = getFirmsLayer('modis', '7');
const viirs24 = getFirmsLayer('viirs', '24');
const viirs48 = getFirmsLayer('viirs', '48');
const viirs7d  = getFirmsLayer('viirs', '7');

modis24.addTo(map);

const overlayMaps = {
  'MODIS (24h)': modis24,
  'MODIS (48h)': modis48,
  'MODIS (7 days)': modis7d,
  'VIIRS (24h)': viirs24,
  'VIIRS (48h)': viirs48,
  'VIIRS (7 days)': viirs7d
};
L.control.layers(null, overlayMaps, { collapsed: false }).addTo(map);

/* Map activate/deactivate */
const overlay = document.getElementById('mapActivate');
let active = false;

const disableInteractions = (state) => {
  if (state) {
    map.dragging.disable();
    map.scrollWheelZoom.disable();
    map.boxZoom.disable();
    map.keyboard.disable();
    if (map.tap) map.tap.disable();
  } else {
    map.dragging.enable();
    map.scrollWheelZoom.enable();
    map.boxZoom.enable();
    map.keyboard.enable();
    if (map.tap) map.tap.enable();
  }
};
disableInteractions(true);

overlay.addEventListener('click', () => {
  overlay.classList.add('hidden');
  disableInteractions(false);
  active = true;
});

/* Click to set marker + coords */
map.on('click', (e) => {
  if (!active) return;
  marker.setLatLng(e.latlng);
  coordPill.textContent = `Lat: ${e.latlng.lat.toFixed(5)}, Lng: ${e.latlng.lng.toFixed(5)}`;
});

/* Buttons */
document.getElementById('checkProb').addEventListener('click', () => {
  // Open prediction box and request prediction for the selected marker coordinates
  const predictBox = document.getElementById('predictBox');
  const predictLoading = document.getElementById('predictLoading');
  predictJson.textContent = '';
  predictLoading.textContent = 'Fetching prediction...';
  predictBox.setAttribute('aria-hidden', 'false');

  const latlng = marker.getLatLng();
  const lat = latlng.lat;
  const lon = latlng.lng;

  // Call backend endpoint /predict?lat=..&lon=..
  const url = `/predict?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`;

  const riskBadge = document.getElementById('riskBadge');
  const predictFields = document.getElementById('predictFields');
  // show spinner
  predictLoading.innerHTML = '<span class="spinner" aria-hidden="true"></span> Fetching prediction...';
  predictFields.innerHTML = '';

  fetch(url, { method: 'GET' })
    .then(async (res) => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      predictLoading.textContent = '';
      renderPrediction(data);
    })
    .catch((err) => {
      predictLoading.textContent = 'Failed to fetch prediction. Please ensure the backend is running.';
      predictFields.innerHTML = '';
      riskBadge.textContent = 'Error';
      riskBadge.className = 'risk-badge';
      console.error('Prediction fetch failed:', err);
    });

  function renderPrediction(data) {
  const predictFields = document.getElementById('predictFields');
  const riskBadge = document.getElementById('riskBadge');
  predictFields.innerHTML = '';

    // Risk badge styling
    const level = (data.wildfire_prediction && data.wildfire_prediction.risk_level) ? data.wildfire_prediction.risk_level.toLowerCase().replace(' ', '-') : '';
    riskBadge.textContent = data.wildfire_prediction ? `${data.wildfire_prediction.fire_risk_percentage}% ${data.wildfire_prediction.risk_level}` : '—';
    riskBadge.className = 'risk-badge ' + (level === 'low' ? 'low' : level === 'moderate' ? 'moderate' : level === 'high' ? 'high' : level === 'very-high' ? 'very-high' : level === 'extreme' ? 'extreme' : '');

    // Populate fields: timestamp, coords, weather, lightning, prediction
    const rows = [];
    rows.push({ label: 'Timestamp', value: data.timestamp || '-' });
    rows.push({ label: 'Latitude', value: data.location ? data.location.latitude : '-' });
    rows.push({ label: 'Longitude', value: data.location ? data.location.longitude : '-' });

    if (data.weather_conditions) {
      rows.push({ label: 'Temperature (°C)', value: data.weather_conditions.temperature_celsius });
      rows.push({ label: 'Rel. Humidity (%)', value: data.weather_conditions.relative_humidity_percent });
      rows.push({ label: 'Wind (m/s)', value: data.weather_conditions.wind_speed_mps });
      rows.push({ label: 'Precip (mm/24h)', value: data.weather_conditions.precipitation_mm_24h });
      rows.push({ label: 'VPD (kPa)', value: data.weather_conditions.vapor_pressure_deficit_kpa });
    }

    if (data.lightning_activity) {
      rows.push({ label: 'Lightning Detected', value: data.lightning_activity.detected ? 'Yes' : 'No' });
      rows.push({ label: 'Strike Count (24h)', value: data.lightning_activity.strike_count_24h });
    }

    if (data.wildfire_prediction) {
      rows.push({ label: 'Fire Risk (%)', value: data.wildfire_prediction.fire_risk_percentage });
      rows.push({ label: 'Risk Level', value: data.wildfire_prediction.risk_level });
      rows.push({ label: 'Fire Expected', value: data.wildfire_prediction.fire_expected ? 'Yes' : 'No' });
    }

    for (const r of rows) {
      const div = document.createElement('div');
      div.className = 'predict-row';
      div.innerHTML = `<div class="label">${r.label}</div><div class="value">${r.value !== undefined ? r.value : '-'}</div>`;
      predictFields.appendChild(div);
    }

    // Show the Analyze Threat button after results are displayed
    const analyzeThreatBtn = document.getElementById('analyzeThreat');
    analyzeThreatBtn.style.display = 'block';
  }
});

// Analyze Threat button functionality
document.getElementById('analyzeThreat').addEventListener('click', () => {
  const threatBox = document.getElementById('threatBox');
  const threatLoading = document.getElementById('threatLoading');
  const threatFields = document.getElementById('threatFields');
  const threatBadge = document.getElementById('threatBadge');
  
  // Show threat analysis box
  threatBox.setAttribute('aria-hidden', 'false');
  threatLoading.innerHTML = '<span class="spinner" aria-hidden="true"></span> Running comprehensive threat analysis...';
  threatFields.innerHTML = '';
  threatBadge.textContent = '—';
  threatBadge.className = 'threat-badge';

  const latlng = marker.getLatLng();
  const lat = latlng.lat;
  const lon = latlng.lng;

  // Call comprehensive threat analysis endpoint
  const url = `/analyze-threat?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`;

  fetch(url, { method: 'GET' })
    .then(async (res) => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      threatLoading.textContent = '';
      renderThreatAnalysis(data);
    })
    .catch((err) => {
      threatLoading.textContent = 'Failed to fetch threat analysis. Please ensure the backend is running.';
      threatFields.innerHTML = '';
      threatBadge.textContent = 'Error';
      threatBadge.className = 'threat-badge';
      console.error('Threat analysis fetch failed:', err);
    });

  function renderThreatAnalysis(data) {
    const threatFields = document.getElementById('threatFields');
    const threatBadge = document.getElementById('threatBadge');
    threatFields.innerHTML = '';

    // Threat level badge
    if (data.threat_assessment) {
      const level = data.threat_assessment.threat_level.toLowerCase();
      threatBadge.textContent = `${data.threat_assessment.threat_level} THREAT`;
      threatBadge.className = 'threat-badge ' + (level === 'low' ? 'low' : level === 'moderate' ? 'moderate' : level === 'high' ? 'high' : level === 'extreme' ? 'extreme' : '');
    }

    // Create sections for different data types
    const sections = [
      {
        title: 'Fire Behavior',
        data: data.fire_behavior,
        fields: [
          { key: 'ros_base_m_per_min', label: 'Rate of Spread (m/min)', format: ':.3f' },
          { key: 'ros_effective_m_per_min', label: 'Effective ROS (m/min)', format: ':.3f' },
          { key: 'flame_length_m', label: 'Flame Length (m)', format: ':.2f' },
          { key: 'intensity_kW_per_m', label: 'Fire Intensity (kW/m)', format: ':.0f' },
          { key: 'severity_class', label: 'Severity Class' },
          { key: 'spotting_distance_km', label: 'Spotting Distance (km)', format: ':.2f' }
        ]
      },
      {
        title: 'Crown Fire Assessment',
        data: data.fire_behavior,
        fields: [
          { key: 'crown_fire_score', label: 'Crown Fire Score', format: '/100' },
          { key: 'crown_fire_class', label: 'Crown Fire Class' }
        ]
      },
      {
        title: 'Time & Impact Estimates',
        data: data.fire_behavior,
        fields: [
          { key: 'time_to_burn_5km2_hours', label: 'Time to burn 5km² (hours)', format: ':.1f' },
          { key: 'damage_estimate_rs', label: 'Damage Estimate (₹)', format: ':,.0f' },
          { key: 'containment_difficulty', label: 'Containment Difficulty' }
        ]
      },
      {
        title: 'Environmental Conditions',
        data: data.live_features,
        fields: [
          { key: 'temp_c', label: 'Temperature (°C)', format: ':.1f' },
          { key: 'rel_humidity_pct', label: 'Humidity (%)', format: ':.1f' },
          { key: 'wind_speed_ms', label: 'Wind Speed (m/s)', format: ':.1f' },
          { key: 'fwi', label: 'Fire Weather Index', format: ':.2f' },
          { key: 'ndvi', label: 'NDVI', format: ':.3f' },
          { key: 'elevation_m', label: 'Elevation (m)', format: ':.0f' }
        ]
      }
    ];

    sections.forEach(section => {
      if (section.data) {
        const sectionDiv = document.createElement('div');
        sectionDiv.className = 'threat-section';
        
        const titleDiv = document.createElement('div');
        titleDiv.className = 'threat-section-title';
        titleDiv.textContent = section.title;
        sectionDiv.appendChild(titleDiv);

        section.fields.forEach(field => {
          if (section.data[field.key] !== undefined) {
            const row = document.createElement('div');
            row.className = 'threat-row';
            
            let value = section.data[field.key];
            if (field.format) {
              if (field.format.includes(':')) {
                const precision = field.format.split(':')[1];
                if (precision.includes('f')) {
                  const decimals = parseInt(precision.replace('f', '').replace('.', ''));
                  value = parseFloat(value).toFixed(decimals);
                } else if (precision.includes(',')) {
                  value = parseInt(value).toLocaleString();
                }
              } else if (field.format === '/100') {
                value = `${value}/100`;
              }
            }
            
            row.innerHTML = `<div class="label">${field.label}</div><div class="value">${value}</div>`;
            sectionDiv.appendChild(row);
          }
        });
        
        threatFields.appendChild(sectionDiv);
      }
    });

    // Add key concerns if available
    if (data.threat_assessment && data.threat_assessment.key_concerns && data.threat_assessment.key_concerns.length > 0) {
      const concernsDiv = document.createElement('div');
      concernsDiv.className = 'threat-section';
      
      const titleDiv = document.createElement('div');
      titleDiv.className = 'threat-section-title';
      titleDiv.textContent = 'Key Concerns';
      concernsDiv.appendChild(titleDiv);

      data.threat_assessment.key_concerns.forEach(concern => {
        const concernDiv = document.createElement('div');
        concernDiv.className = 'threat-concern';
        concernDiv.innerHTML = `⚠️ ${concern}`;
        concernsDiv.appendChild(concernDiv);
      });
      
      threatFields.appendChild(concernsDiv);
    }
  }
});

document.getElementById('deactivateMap').addEventListener('click', () => {
  overlay.classList.remove('hidden');
  disableInteractions(true);
  active = false;
});

/* ===== Performance tabs ===== */
const btnFire = document.getElementById('btnFire');
const btnOcc  = document.getElementById('btnOcc');
const paneFire = document.getElementById('paneFire');
const paneOcc  = document.getElementById('paneOcc');

if (btnFire && btnOcc && paneFire && paneOcc) {
  const setBtnStyles = (activeBtn, inactiveBtn) => {
    // Active button becomes orange
    activeBtn.classList.add('active');
    activeBtn.classList.remove('btn-ghost');
    activeBtn.classList.add('btn-primary');

    // Inactive button becomes gray
    inactiveBtn.classList.remove('active');
    inactiveBtn.classList.remove('btn-primary');
    inactiveBtn.classList.add('btn-ghost');
  };

  const selectPane = (which) => {
    if (which === 'fire') {
      paneFire.classList.add('show');
      paneOcc.classList.remove('show');
      setBtnStyles(btnFire, btnOcc);
    } else {
      paneOcc.classList.add('show');
      paneFire.classList.remove('show');
      setBtnStyles(btnOcc, btnFire);
    }
  };

  // Wire up
  btnFire.addEventListener('click', () => selectPane('fire'));
  btnOcc.addEventListener('click',  () => selectPane('occ'));
}

/* ===== Image modal ===== */
const modal = document.getElementById('imgModal');
const modalImg = document.getElementById('imgModalSrc');
const modalClose = document.getElementById('imgModalClose');

if (modal && modalImg && modalClose) {
  document.addEventListener('click', (e) => {
    const t = e.target;
    if (t && t.classList && t.classList.contains('zoomable')) {
      modalImg.src = t.src;
      modal.classList.add('show');
      document.body.style.overflow = 'hidden';
    }
  });

  const closeModal = () => {
    modal.classList.remove('show');
    modalImg.src = '';
    document.body.style.overflow = '';
  };

  modalClose.addEventListener('click', closeModal);
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('show')) closeModal();
  });
}

/* Predict box close handler */
const predictClose = document.getElementById('predictClose');
if (predictClose) {
  predictClose.addEventListener('click', () => {
    const predictBox = document.getElementById('predictBox');
    predictBox.setAttribute('aria-hidden', 'true');
  });
}

/* Threat analysis box close handler */
const threatClose = document.getElementById('threatClose');
if (threatClose) {
  threatClose.addEventListener('click', () => {
    const threatBox = document.getElementById('threatBox');
    threatBox.setAttribute('aria-hidden', 'true');
  });
}
