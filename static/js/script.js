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

  // Validate distance slider value
  const distance = parseFloat(distSlider.value);
  if (isNaN(distance) || distance < 0.5 || distance > 10) {
    showError('Please select a distance between 0.5 and 10 km.');
    return;
  }

  generateBtn.disabled = true;

  navigator.geolocation.getCurrentPosition(async position => {
    const lat = position.coords.latitude;
    const lon = position.coords.longitude;
    const duration = 0; 

    clearLayers();

    try {
      // Generate Route, now including duration in minutes
      const routeResp = await fetch('/generate-route', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ lat, lon, distance, duration })
      });

      if (!routeResp.ok) {
        const errorData = await routeResp.json();
        showError(errorData.error || 'Failed to generate route.');
        generateBtn.disabled = false;
        return;
      }

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

      // Save current walk data to use on start/stop buttons
      currentWalkData = {
        lat, lon, distance,
        temperature: routeData.weather.temperature,
        condition: routeData.weather.condition,
        dog_parks_visited: spotsData.spots.filter(s => s.type === 'dog_park').map(s => s.name),
        difficulty: routeData.difficulty
      };

      startWalkBtn.disabled = false;
      stopWalkBtn.disabled = true;
      secondsElapsed = 0;
      timerDisplay.textContent = 'Duration: 0:00';
      generateBtn.disabled = false;

    } catch (err) {
      console.error('Error during generation:', err);
      showError('An error occurred while generating data.');
      weatherDiv.textContent = 'An error occurred while generating data.';
      generateBtn.disabled = false;
    }
  }, () => {
    alert('Could not get your location');
    generateBtn.disabled = false;
  });
};

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
    // Proceed with rendering route, weather, etc.
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
