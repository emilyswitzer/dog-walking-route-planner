const distSlider = document.getElementById('distance');
const distValue = document.getElementById('dist-value');
const generateBtn = document.getElementById('generateBtn');
const weatherDiv = document.getElementById('weather');

const startWalkBtn = document.getElementById('startWalkBtn');
const stopWalkBtn = document.getElementById('stopWalkBtn');
const timerDisplay = document.getElementById('timerDisplay');

distSlider.oninput = () => {
  distValue.textContent = distSlider.value;
};

let map = L.map('map').setView([37.7749, -122.4194], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19
}).addTo(map);

let routeLayers = [];  // ⬅ Store multiple routes
let spotsLayer = null;
let selectedRouteIndex = null;

function clearLayers() {
  // Remove all route polylines
  if (routeLayers.length) {
    routeLayers.forEach(layer => map.removeLayer(layer));
    routeLayers = [];
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
    showError('An error occurred while generating data.');
    weatherDiv.textContent = 'Could not fetch weather data.';
  }
}

let timer = null;
let secondsElapsed = 0;
let currentWalkData = null; // holds generated route and other info

function formatDuration(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function updateTimer() {
  secondsElapsed++;
  timerDisplay.textContent = `Duration: ${formatDuration(secondsElapsed)}`;
}

document.getElementById('saveWalkBtn').onclick = async () => {
  if (selectedRouteIndex === null || !routeLayers[selectedRouteIndex]) {
    showError('Please select a route first.');
    return;
  }

  const selectedCoords = routeLayers[selectedRouteIndex]
    .getLatLngs()
    .map(latlng => [latlng.lat, latlng.lng]);

  const distance = parseFloat(distSlider.value);
  const duration = parseFloat(durationInput.value || 0); // if you have this field

  try {
    const res = await fetch('/save-walk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        route: selectedCoords,
        distance,
        duration
      })
    });

    const data = await res.json();
    if (!res.ok) {
      showError(data.error || 'Failed to save walk.');
      return;
    }

    alert('Walk saved successfully!');
  } catch (err) {
    console.error(err);
    showError('Failed to save walk.');
  }
};


async function saveWalk(data) {
  // Duration already in seconds here
  const payload = {
    lat: data.lat,
    lon: data.lon,
    distance: data.distance,
    duration: data.duration,
    temperature: data.temperature,
    condition: data.condition,
    dog_parks_visited: data.dog_parks_visited || [],
    difficulty: data.difficulty || 'medium'
  };

  try {
    const response = await fetch('/save-walk', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errData = await response.json();
      console.error('Save walk failed:', errData);
      alert('Failed to save walk: ' + (errData.error || 'Unknown error'));
      return;
    }

    alert('Walk saved successfully!');
  } catch (error) {
    console.error('Error saving walk:', error);

    showError('An error occurred while saving data.');
    alert('Error saving walk. Check console for details.');
  }
}

generateBtn.onclick = () => {
  clearError();
  if (!navigator.geolocation) {
    alert('Geolocation not supported');
    return;
  }

  const distance = parseFloat(distSlider.value);
  if (isNaN(distance) || distance < 0.5 || distance > 10) {
    showError('Please select a distance between 0.5 and 10 km.');
    return;
  }

  generateBtn.disabled = true;

  navigator.geolocation.getCurrentPosition(async position => {
    const lat = position.coords.latitude;
    const lon = position.coords.longitude;

    clearRoutes();
    clearMapData(); // remove spots, weather, etc if needed

    try {
      const res = await fetch('/generate-route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ lat, lon, distance })
      });

      const data = await res.json();
      if (!res.ok) {
        showError(data.error || 'Failed to generate routes');
        return;
      }

      const colors = ['blue', 'green', 'orange'];
      data.routes.forEach((routeCoords, i) => {
        const latlngs = routeCoords.map(([lat, lon]) => [lat, lon]);
        const color = colors[i % colors.length];

        const polyline = L.polyline(latlngs, {
          color,
          weight: 5,
          opacity: 0.7
        }).addTo(map);

        polyline.options.originalColor = color;
        polyline.on('click', () => selectRoute(i));
        routeLayers.push(polyline);
      });

      if (data.routes.length > 0) {
        map.fitBounds(routeLayers[0].getBounds());
        selectRoute(0); // select first route by default
      }

      // Store metadata if needed (e.g. currentWeather = data.weather)
    } catch (err) {
      console.error(err);
      showError('An error occurred while generating routes.');
    } finally {
      generateBtn.disabled = false;
    }
  }, () => {
    alert('Could not get your location');
    generateBtn.disabled = false;
  });
};

function clearRoutes() {
  routeLayers.forEach(layer => map.removeLayer(layer));
  routeLayers = [];
}

function clearWeatherInfo() {
  const weatherDiv = document.getElementById('weather-info');
  if (weatherDiv) {
    weatherDiv.innerHTML = '';
  }
}

function clearMapData() {
  // Remove all route layers
  routeLayers.forEach(layer => map.removeLayer(layer));
  routeLayers = [];

  // Remove dog park markers if you keep them in a separate array (example: dogParkMarkers)
  if (typeof dogParkMarkers !== 'undefined') {
    dogParkMarkers.forEach(marker => map.removeLayer(marker));
    dogParkMarkers = [];
  }

  clearWeatherInfo();
  clearError();
}

function selectRoute(index) {
  selectedRouteIndex = index;
  routeLayers.forEach((layer, idx) => {
    layer.setStyle({
      weight: idx === index ? 8 : 4,
      opacity: idx === index ? 1 : 0.3,
      color: idx === index ? 'red' : layer.options.originalColor
    });
  });
}

startWalkBtn.onclick = () => {
  if (!currentWalkData) {
    alert('Please generate a route first!');
    return;
  }
  if (timer) return; // prevent multiple timers running
  startWalkBtn.disabled = true;
  stopWalkBtn.disabled = false;
  timer = setInterval(updateTimer, 1000);
};

stopWalkBtn.onclick = async () => {
  if (!timer) return;
  clearInterval(timer);
  timer = null;

  startWalkBtn.disabled = true;
  stopWalkBtn.disabled = true;

  try {
    await saveWalk({
      ...currentWalkData,
      duration: secondsElapsed
    });
    currentWalkData = null;
    secondsElapsed = 0;            // reset elapsed time here
    timerDisplay.textContent = 'Duration: 0:00'; // reset display
  } catch (e) {
    showError('An error occurred while saving data.');
    alert('Error saving walk: ' + e.message);
  }
};

async function generateRoute() {
  try {
    const response = await fetch('/generate-route', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        lat: currentLat,
        lon: currentLon,
        distance: selectedDistance,
        duration: walkDuration
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      showError(errorData.error || "Failed to generate route");
      return;
    }

    const data = await response.json();
    clearError();
  } catch (error) {
    showError('An error occurred while connecting to the server');
    showError("Network error or server unavailable");
  }
}

function showError(message) {
  const errorDiv = document.getElementById('error-message');
  if (errorDiv) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
  } else {
    alert(message); // fallback
  }
}

function clearError() {
  const errorDiv = document.getElementById('error-message');
  if (errorDiv) errorDiv.style.display = 'none';
}
