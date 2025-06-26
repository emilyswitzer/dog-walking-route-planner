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

async function fetchWeather(lat, lon) {
  try {
    const res = await fetch('/weather', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lat, lon })
    });

    if (!res.ok) throw new Error('Weather fetch failed');

    const data = await res.json();

    weatherDiv.innerHTML = `
      <p><strong>${data.temperature}°C</strong> - ${data.description}</p>
      <p>Condition: ${data.condition}</p>
      <p>Walk Recommendation: <strong>${data.recommendation}</strong></p>
      <img src="https://openweathermap.org/img/wn/${data.icon}@2x.png" alt="Weather Icon" />
    `;
  } catch (err) {
    console.error(err);
    weatherDiv.textContent = 'Could not fetch weather data.';
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

    try {
      // Generate Route
      const routeResp = await fetch('/generate-route', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ lat, lon, distance })
      });
      const routeData = await routeResp.json();
      const latlngs = routeData.route.map(coord => [coord[0], coord[1]]);
      routeLayer = L.polyline(latlngs, { color: 'blue' }).addTo(map);
      map.fitBounds(routeLayer.getBounds());

      // Dog Spots
      const spotsResp = await fetch('/dog-spots', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ lat, lon })
      });
      const spotsData = await spotsResp.json();

      spotsLayer = L.layerGroup();
      spotsData.spots.forEach(spot => {
        const marker = L.marker([spot.lat, spot.lon])
          .bindPopup(`${spot.name} (${spot.type})`);
        spotsLayer.addLayer(marker);
      });
      spotsLayer.addTo(map);

      // Weather
      await fetchWeather(lat, lon);
    } catch (err) {
      console.error('Error during generation:', err);
      weatherDiv.textContent = 'An error occurred while generating data.';
    }
  }, () => {
    alert('Could not get your location');
  });
};
