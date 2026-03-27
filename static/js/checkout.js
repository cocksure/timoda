// ============================================================
// Checkout page — delivery, pickup, maps
// ============================================================

// ── Delivery method toggle ────────────────────────────────────
const deliveryRadios = document.querySelectorAll('.delivery-radio');
const addressSection = document.getElementById('addressSection');
const pickupSection  = document.getElementById('pickupSection');
let pickupMap = null;

function onDeliveryChange() {
  const val = document.querySelector('.delivery-radio:checked')?.value;
  const isCourier = val !== 'pickup';

  if (addressSection) addressSection.style.display = isCourier ? '' : 'none';
  if (pickupSection)  pickupSection.style.display  = isCourier ? 'none' : '';

  if (addressSection) {
    addressSection.querySelectorAll('input, textarea, select').forEach(el => {
      if (isCourier) {
        if (el.dataset.required) el.required = true;
      } else {
        if (el.required) el.dataset.required = 'true';
        el.required = false;
      }
    });
  }

  document.querySelectorAll('.delivery-option').forEach(opt => {
    opt.classList.toggle('active', opt.querySelector('input').checked);
  });
}

deliveryRadios.forEach(r => r.addEventListener('change', onDeliveryChange));

// ── Pickup tabs ───────────────────────────────────────────────
document.querySelectorAll('.pickup-tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.pickup-tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.pickup-tab-pane').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    const paneId = 'pickupPane' + btn.dataset.tab.charAt(0).toUpperCase() + btn.dataset.tab.slice(1);
    document.getElementById(paneId)?.classList.add('active');
    if (btn.dataset.tab === 'map') {
      if (!pickupMap) initPickupMap();
      else setTimeout(() => pickupMap.invalidateSize(), 50);
    }
  });
});

// ── Select a pickup point ─────────────────────────────────────
let selectedPickupId = null;

function selectPickupPoint(itemEl) {
  selectedPickupId = itemEl.dataset.id;
  document.getElementById('pickupPointId').value = selectedPickupId;
  document.querySelectorAll('.pickup-point-item').forEach(i => i.classList.remove('selected'));
  itemEl.classList.add('selected');
  document.querySelectorAll('[id^=pickup-icon-]').forEach(ic => ic.className = 'bi bi-circle');
  const icon = document.getElementById('pickup-icon-' + selectedPickupId);
  if (icon) icon.className = 'bi bi-record-circle-fill text-dark';
  if (pickupMap && itemEl.dataset.lat && itemEl.dataset.lng) {
    pickupMap.setView([parseFloat(itemEl.dataset.lat), parseFloat(itemEl.dataset.lng)], 16);
  }
}

document.querySelectorAll('.pickup-point-item').forEach(item => {
  item.addEventListener('click', () => selectPickupPoint(item));
});

function initPickupMap() {
  pickupMap = L.map('pickupMapFull').setView([41.2995, 69.2401], 12);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> © <a href="https://carto.com/attributions">CARTO</a>'
  }).addTo(pickupMap);

  // Logo URL passed via data attribute on the map container
  const logoUrl = document.getElementById('pickupMapFull')?.dataset.logo || '';
  const timodaIcon = L.divIcon({
    html: `<div class="timoda-map-marker"><img src="${logoUrl}" alt="Timoda"></div>`,
    className: '',
    iconSize: [40, 40],
    iconAnchor: [20, 40],
    popupAnchor: [0, -42]
  });

  document.querySelectorAll('.pickup-point-item').forEach(item => {
    if (!item.dataset.lat || !item.dataset.lng) return;
    const lat = parseFloat(item.dataset.lat), lng = parseFloat(item.dataset.lng);
    const name = item.querySelector('.fw-semibold')?.textContent.trim() || '';
    const addr = item.querySelector('.text-muted')?.textContent.trim() || '';
    L.marker([lat, lng], {icon: timodaIcon}).addTo(pickupMap)
      .bindPopup(`<strong>${name}</strong><br><span style="font-size:12px">${addr}</span>`)
      .on('click', () => {
        selectPickupPoint(item);
        document.querySelector('[data-tab="list"]')?.click();
      });
  });

  setTimeout(() => pickupMap.invalidateSize(), 100);
}

// ── Courier delivery map ──────────────────────────────────────
const DEFAULT_LAT = 41.2995, DEFAULT_LNG = 69.2401;
let map, marker;

function initMap() {
  map = L.map('deliveryMap').setView([DEFAULT_LAT, DEFAULT_LNG], 12);
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> © <a href="https://carto.com/attributions">CARTO</a>'
  }).addTo(map);
  map.on('click', e => {
    placeMarker(e.latlng.lat, e.latlng.lng);
    reverseGeocode(e.latlng.lat, e.latlng.lng);
  });
}

function placeMarker(lat, lng) {
  if (marker) {
    marker.setLatLng([lat, lng]);
  } else {
    marker = L.marker([lat, lng], { draggable: true }).addTo(map);
    marker.on('dragend', e => {
      const pos = e.target.getLatLng();
      reverseGeocode(pos.lat, pos.lng);
      document.getElementById('hiddenLat').value = pos.lat;
      document.getElementById('hiddenLng').value = pos.lng;
    });
  }
  document.getElementById('hiddenLat').value = lat;
  document.getElementById('hiddenLng').value = lng;
  document.getElementById('mapFilledBadge')?.classList.add('show');
}

async function reverseGeocode(lat, lng) {
  try {
    const url = `https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&accept-language=ru`;
    const resp = await fetch(url, { headers: { 'Accept-Language': 'ru' } });
    const data = await resp.json();
    if (!data.address) return;
    const a = data.address;
    const road = a.road || a.pedestrian || a.footway || '';
    const street = [road, a.house_number].filter(Boolean).join(', ');
    const city = a.city || a.town || a.village || a.county || a.state || '';
    if (street) setField('shipping_address', street);
    if (city)   setField('city', city);
    if (a.postcode) setField('postal_code', a.postcode);
    if (a.country)  setField('country', a.country);
  } catch (_) {}
}

function setField(name, value) {
  const el = document.querySelector(`[name="${name}"]`);
  if (el && value) el.value = value;
}

document.getElementById('toggleMapBtn')?.addEventListener('click', () => {
  const container = document.getElementById('mapContainer');
  const btn = document.getElementById('toggleMapBtn');
  const visible = container.style.display !== 'none';
  container.style.display = visible ? 'none' : 'block';
  btn.classList.toggle('active', !visible);
  if (!visible) {
    if (!map) initMap();
    else map.invalidateSize();
  }
});

async function searchAddress() {
  const q = document.getElementById('mapSearch')?.value.trim();
  if (!q) return;
  try {
    const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}&limit=1&accept-language=ru`;
    const resp = await fetch(url);
    const results = await resp.json();
    if (!results.length) return;
    const lat = parseFloat(results[0].lat), lng = parseFloat(results[0].lon);
    map.setView([lat, lng], 17);
    placeMarker(lat, lng);
    reverseGeocode(lat, lng);
  } catch (_) {}
}

document.getElementById('mapSearchBtn')?.addEventListener('click', searchAddress);
document.getElementById('mapSearch')?.addEventListener('keydown', e => {
  if (e.key === 'Enter') { e.preventDefault(); searchAddress(); }
});