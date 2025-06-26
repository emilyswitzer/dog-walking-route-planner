const distSlider = document.getElementById('distance');
const distValue = document.getElementById('dist-value');
const generateBtn = document.getElementById('generateBtn');
const weatherDiv = document.getElementById('weather');

distSlider.oninput = () => {
  distValue.textContent = distSlider.value;
};

let map = L.map('map').setView([37.7749, -122.4194], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19
}).addTo(map);

let routeLayer = null;
let spotsLayer = null;

function clearLayers() {
  if (routeLayer) {
    map.removeLayer(routeLayer);
    routeLayer = null;
  }
  if (spotsLayer) {
    map.removeLayer(spotsLayer);
    spotsLayer = null;
  }
}

generateBtn.onclick = () => {
  if (!navigator.geolocation) {
    alert('Geolocation not supported');
    return;
  }

  navigator.geolocation.getCurrentPosition(async position => {
    const lat = position.coords.latitude;
    const lon = position.coords.longitude;
    const distance = parseFloat(distSlider.value);

    clearLayers();

    // Call /generate-route endpoint
    const routeResp = await fetch('/generate-route', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({lat, lon, distance})
    });
    const routeData = await routeResp.json();

    // Draw route polyline
    const latlngs = routeData.route.map(coord => [coord[0], coord[1]]);
    routeLayer = L.polyline(latlngs, {color: 'blue'}).addTo(map);
    map.fitBounds(routeLayer.getBounds());

    // Call /dog-spots endpoint
    const spotsResp = await fetch('/dog-spots', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({lat, lon})
    });
    const spotsData = await spotsResp.json();

    spotsLayer = L.layerGroup();
    spotsData.spots.forEach(spot => {
      const marker = L.marker([spot.lat, spot.lon])
        .bindPopup(`${spot.name} (${spot.type})`);
      spotsLayer.addLayer(marker);
    });
    spotsLayer.addTo(map);

    // Optionally display simple weather info (later)
    weatherDiv.textContent = 'Weather info coming soon...';
  }, () => {
    alert('Could not get your location');
  });
};
