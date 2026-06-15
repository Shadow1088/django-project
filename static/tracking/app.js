function initMap(locations) {
  try {
    var el = document.getElementById('map');
    if (!el) { console.error('Map element not found'); return; }

    var map = L.map('map');
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>',
      maxZoom: 19,
    }).addTo(map);

    if (!locations || !locations.length) {
      map.setView([49.5, 15.5], 5);
      return;
    }

    var sorted = locations.slice().sort(function (a, b) {
      return a.recorded_at.localeCompare(b.recorded_at);
    });

    var latlngs = [];
    var bounds = [];
    var markers = [];

    sorted.forEach(function (loc, i) {
      var lat = parseFloat(loc.latitude);
      var lng = parseFloat(loc.longitude);
      if (isNaN(lat) || isNaN(lng)) return;

      var point = [lat, lng];
      latlngs.push(point);
      bounds.push(point);

      var marker;
      if (sorted.length === 1) {
        marker = L.marker(point).addTo(map);
      } else if (i === 0) {
        marker = L.marker(point, {
          icon: L.divIcon({
            className: '',
            html: '<div style="background:#198754;width:20px;height:20px;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.5)"></div>',
            iconSize: [20, 20],
            iconAnchor: [10, 10],
          })
        }).addTo(map);
      } else if (i === sorted.length - 1) {
        marker = L.marker(point, {
          icon: L.divIcon({
            className: '',
            html: '<div style="background:#dc3545;width:20px;height:20px;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.5)"></div>',
            iconSize: [20, 20],
            iconAnchor: [10, 10],
          })
        }).addTo(map);
      } else {
        marker = L.marker(point, {
          icon: L.divIcon({
            className: '',
            html: '<div style="background:#0d6efd;width:16px;height:16px;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,0.5)"></div>',
            iconSize: [16, 16],
            iconAnchor: [8, 8],
          })
        }).addTo(map);
      }

      markers.push(marker);
      marker.bindPopup(
        '<strong>#' + loc.id + '</strong><br>' +
        lat.toFixed(6) + ', ' + lng.toFixed(6) + '<br>' +
        (loc.speed != null ? 'Speed: ' + loc.speed + ' km/h<br>' : '') +
        (loc.note ? 'Note: ' + escapeHtml(loc.note) + '<br>' : '') +
        loc.recorded_at
      );
    });

    if (latlngs.length > 1) {
      L.polyline(latlngs, {
        color: '#0d6efd',
        weight: 3,
        opacity: 0.7
      }).addTo(map);
    }

    map.invalidateSize();

    if (bounds.length === 1) {
      map.setView(bounds[0], 13);
    } else if (bounds.length > 1) {
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 16 });
    }
  } catch (e) {
    console.error('Map init error:', e);
  }
}

function initSpeedChart(locations) {
  var canvas = document.getElementById('speedChart');
  if (!canvas) return;

  var data = locations
    .filter(function (l) { return l.speed != null; })
    .sort(function (a, b) { return a.recorded_at.localeCompare(b.recorded_at); });

  if (data.length < 2) return;

  new Chart(canvas, {
    type: 'line',
    data: {
      labels: data.map(function (l) { return l.recorded_at; }),
      datasets: [{
        label: 'Speed (km/h)',
        data: data.map(function (l) { return l.speed; }),
        borderColor: '#0d6efd',
        backgroundColor: 'rgba(13, 110, 253, 0.1)',
        pointBackgroundColor: '#0d6efd',
        pointRadius: 3,
        pointHoverRadius: 6,
        fill: true,
        tension: 0.3,
        spanGaps: true,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: function (items) { return items[0].label; },
            label: function (item) { return item.parsed.y + ' km/h'; },
          }
        }
      },
      scales: {
        x: {
          ticks: { maxTicksLimit: 10, maxRotation: 0 },
          grid: { display: false },
        },
        y: {
          beginAtZero: true,
          title: { display: true, text: 'km/h' },
          grid: { color: 'rgba(0,0,0,0.05)' },
        }
      },
      interaction: {
        intersect: false,
        mode: 'index',
      }
    }
  });
}

function escapeHtml(text) {
  var div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function showToast(message, type) {
  var container = document.getElementById('toast-container');
  if (!container) return;
  var bg = { success: 'text-bg-success', error: 'text-bg-danger', info: 'text-bg-info' };
  var el = document.createElement('div');
  el.className = 'toast ' + (bg[type] || 'text-bg-info') + ' border-0';
  el.role = 'alert';
  el.innerHTML =
    '<div class="d-flex">' +
      '<div class="toast-body">' + escapeHtml(message) + '</div>' +
      '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>' +
    '</div>';
  container.appendChild(el);
  var toast = bootstrap.Toast.getOrCreateInstance(el);
  toast.show();
  el.addEventListener('hidden.bs.toast', function () { el.remove(); });
}

document.addEventListener('DOMContentLoaded', function () {
  if (window.PING_SUCCESS) showToast('Location reported.', 'success');
});
