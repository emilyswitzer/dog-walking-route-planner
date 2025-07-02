import React from 'react';

const WeatherInfo = ({ weather }) => {
  if (!weather) return null;

  return (
    <div>
      <h2>Current Weather</h2>
      <p>
        Temperature: {weather.temp ? weather.temp.toFixed(1) : 'N/A'}°C
      </p>
      <p>Condition: {weather.condition || 'Unknown'}</p>
    </div>
  );
};

export default WeatherInfo;
