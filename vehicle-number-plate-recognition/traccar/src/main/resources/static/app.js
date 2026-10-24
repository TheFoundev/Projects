'use strict';

const state = { devices: [], selected: null, markers: new Map(), trail: null, fences: [] };

const map = L.map('map', { zoomControl: true }).setView([51.5074, -0.1278], 12);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; OpenStreetMap contributors',
}).addTo(map);

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}

function toast(message) {
  const node = document.createElement('div');
  node.className = 'toast';
  node.textContent = message;
  document.body.append(node);
  setTimeout(() => node.remove(), 3200);
}

const deviceIcon = (online) => L.divIcon({
  className: 'device-dot',
  html: `<span style="background:${online ? '#15803d' : '#a1a1aa'}"></span>`,
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

async function refresh() {
  try {
    const [devices, latest, summary, alertRows, fences] = await Promise.all([
      api('/api/devices'), api('/api/positions/latest'), api('/api/summary'),
      api('/api/alerts'), api('/api/geofences'),
    ]);
    state.devices = devices;
    renderStats(summary);
    renderDevices(devices);
    renderPositions(latest);
    renderAlerts(alertRows);
    renderFences(fences);
    if (!state.selected && devices.length) selectDevice(devices[0].id);
    else if (state.selected) renderTrips(await api(`/api/trips?deviceId=${state.selected.id}`));
  } catch (error) {
    toast(error.message);
  }
}

function renderStats(summary) {
  document.getElementById('stats').innerHTML = `
    <span class="stat"><b>${summary.online}</b> online</span>
    <span class="stat"><b>${summary.devices}</b> devices</span>
    <span class="stat"><b>${summary.positionsToday}</b> positions today</span>
    <span class="stat"><b>${summary.alertsToday}</b> alerts</span>`;
}

function renderDevices(devices) {
  const container = document.getElementById('devices');
  if (!devices.length) {
    container.innerHTML = '<p class="muted">No devices registered yet.</p>';
    return;
  }
  container.innerHTML = devices.map((device) => `
    <button class="device ${state.selected && state.selected.id === device.id ? 'active' : ''}" data-id="${device.id}">
      <span class="dot ${device.status === 'online' ? 'on' : ''}"></span>
      <span class="grow"><strong>${esc(device.name)}</strong><small>${esc(device.uniqueId)} · ${esc(device.model || 'unknown model')}</small></span>
      <small>${device.lastUpdate ? new Date(device.lastUpdate).toLocaleTimeString() : 'never'}</small>
    </button>`).join('');
  container.querySelectorAll('.device').forEach((button) => {
    button.addEventListener('click', () => {
      const device = state.devices.find((d) => d.id === Number(button.dataset.id));
      if (device) selectDevice(device.id);
    });
  });
}

function renderPositions(latest) {
  for (const position of latest) {
    const device = state.devices.find((d) => d.id === position.deviceId);
    if (!device) continue;
    const marker = state.markers.get(device.id) || L.marker([position.latitude, position.longitude], {
      icon: deviceIcon(device.status === 'online'),
    }).addTo(map);
    marker.setLatLng([position.latitude, position.longitude]);
    marker.bindPopup(`<strong>${esc(device.name)}</strong><br>${position.speedKph ?? 0} km/h<br><small>${new Date(position.recordedAt).toLocaleString()}</small>`);
    state.markers.set(device.id, marker);
  }
}

function renderFences(fences) {
  state.fences.forEach((layer) => map.removeLayer(layer));
  state.fences = fences.map((fence) => L.circle([fence.latitude, fence.longitude], {
    radius: fence.radiusMeters,
    color: '#ea580c',
    fillOpacity: 0.06,
    weight: 1.5,
  }).addTo(map).bindPopup(`<strong>${esc(fence.name)}</strong><br>${fence.radiusMeters} m radius`));
}

function renderAlerts(rows) {
  document.getElementById('alerts').innerHTML = rows.length
    ? rows.slice(0, 8).map((alert) => `<div class="alert"><span>${esc(alert.message)}</span><small>${new Date(alert.createdAt).toLocaleString()}</small></div>`).join('')
    : '<p class="muted">No alerts yet. Add a geofence and send a position inside it.</p>';
}

function renderTrips(trips) {
  document.getElementById('trips').innerHTML = trips.length
    ? trips.slice(-6).reverse().map((trip) => `
        <div class="trip"><div><strong>${trip.distanceKm} km</strong><small>${trip.durationMinutes} min · ${trip.avgSpeedKph} km/h avg</small></div>
        <small>${new Date(trip.start).toLocaleTimeString()} → ${new Date(trip.end).toLocaleTimeString()}</small></div>`).join('')
    : '<p class="muted">No trips recorded for this device.</p>';
}

async function selectDevice(id) {
  state.selected = state.devices.find((device) => device.id === id) || null;
  if (!state.selected) return;
  document.getElementById('selected-label').textContent = state.selected.name;
  renderDevices(state.devices);
  if (state.trail) { map.removeLayer(state.trail); state.trail = null; }
  try {
    const points = (await api(`/api/positions?deviceId=${id}&limit=300`)).slice().reverse();
    if (points.length > 1) {
      state.trail = L.polyline(points.map((p) => [p.latitude, p.longitude]), { color: '#ea580c', weight: 3 }).addTo(map);
      map.fitBounds(state.trail.getBounds(), { padding: [40, 40] });
    } else if (points.length === 1) {
      map.setView([points[0].latitude, points[0].longitude], 14);
    }
    renderTrips(await api(`/api/trips?deviceId=${id}`));
  } catch (error) {
    toast(error.message);
  }
}

document.getElementById('refresh').addEventListener('click', refresh);

document.getElementById('device-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  try {
    await api('/api/devices', { method: 'POST', body: Object.fromEntries(form) });
    event.target.reset();
    toast('Device registered');
    refresh();
  } catch (error) { toast(error.message); }
});

document.getElementById('position-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!state.selected) { toast('Select a device first'); return; }
  const form = new FormData(event.target);
  try {
    await api('/api/positions', { method: 'POST', body: {
      deviceId: state.selected.id,
      latitude: Number(form.get('latitude')),
      longitude: Number(form.get('longitude')),
      speedKph: Number(form.get('speedKph') || 0),
    } });
    toast('Position accepted');
    refresh();
  } catch (error) { toast(error.message); }
});

refresh();
setInterval(refresh, 30000);
