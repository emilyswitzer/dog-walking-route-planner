import React, { useState } from 'react';
import WalkForm from './WalkForm';
import MapDisplay from './MapDisplay';
import WeatherInfo from './WeatherInfo';
import SaveWalkButton from './SaveWalkButton';

const HomeScreen = () => {
  const [location, setLocation] = useState(null); // { lat, lon }
  const [distance, setDistance] = useState('');
  const [route, setRoute] = useState(null);
  const [dogSpots, setDogSpots] = useState([]);
  const [weather, setWeather] = useState(null);
  const [loading, setLoading] = useState(false);
  const [walkSaved, setWalkSaved] = useState(false);

  const handleGenerateWalk = async () => {
    if (!location || !distance) return alert('Please set your location and distance');

    setLoading(true);
    setWalkSaved(false);

    try {
      // 1. Fetch route (POST with JSON body)
      const routeRes = await fetch('http://localhost:5000/generate-route', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat: location.lat,
          lon: location.lon,
          distance: parseFloat(distance),
        }),
      });

      if (!routeRes.ok) {
        const err = await routeRes.text();
        throw new Error(`Route Error: ${err}`);
      }

      const routeData = await routeRes.json();
      setRoute(routeData);

      // 2. Fetch dog spots (POST with JSON body)
      const spotsRes = await fetch('/dog-spots', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat: location.lat,
          lon: location.lon,
        }),
      });

      if (!spotsRes.ok) {
        const err = await spotsRes.text();
        throw new Error(`Dog Spots Error: ${err}`);
      }

      const spotsData = await spotsRes.json();
      setDogSpots(spotsData.spots || []);

      // 3. Fetch weather (POST with JSON body)
      const weatherRes = await fetch('/weather', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat: location.lat,
          lon: location.lon,
        }),
      });

      if (!weatherRes.ok) {
        const err = await weatherRes.text();
        throw new Error(`Weather Error: ${err}`);
      }

      const weatherData = await weatherRes.json();
      setWeather(weatherData);
    } catch (error) {
      alert('Error fetching walk data: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveWalk = async () => {
    if (!route) return alert('Generate a walk first');

    const walkPayload = {
      lat: location.lat,
      lon: location.lon,
      distance: parseFloat(distance),
      duration: 0,
      temperature: weather?.temp || null,
      condition: weather?.condition || '',
      dog_parks_visited: JSON.stringify(dogSpots),
      difficulty: 'medium',
      route: JSON.stringify(route),
    };

    try {
      const res = await fetch('/save-walk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(walkPayload),
      });

      if (res.ok) {
        setWalkSaved(true);
        alert('Walk saved successfully!');
      } else {
        const err = await res.json();
        alert('Failed to save walk: ' + err.message);
      }
    } catch (error) {
      alert('Error saving walk: ' + error.message);
    }
  };

  return (
    <div>
      <h1>Dog Walking App</h1>

      <WalkForm
        distance={distance}
        onDistanceChange={setDistance}
        onLocationSet={setLocation}
        onSubmit={handleGenerateWalk}
        disabled={loading}
      />

      {loading && <p>Loading walk data...</p>}

      {route && (
        <>
          <MapDisplay route={route} dogSpots={dogSpots} />
          <WeatherInfo weather={weather} />
          <SaveWalkButton onClick={handleSaveWalk} disabled={walkSaved} />
        </>
      )}
    </div>
  );
};

export default HomeScreen;
