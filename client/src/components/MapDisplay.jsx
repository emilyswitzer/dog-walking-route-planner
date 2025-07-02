// src/components/MapDisplay.jsx

import React from 'react';

const MapDisplay = ({ route, dogSpots }) => {
 
  return (
    <div>
      <h2>Map</h2>
      <div
        style={{
          width: '100%',
          height: '300px',
          backgroundColor: '#eee',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          color: '#999',
        }}
      >
        Map Placeholder
      </div>

      <h3>Route Coordinates:</h3>
      <ul>
        {route?.coordinates?.map((coord, index) => (
          <li key={index}>
            Lat: {coord[1].toFixed(5)}, Lon: {coord[0].toFixed(5)}
          </li>
        )) || <li>No route data available</li>}
      </ul>

      <h3>Dog-friendly Spots:</h3>
      <ul>
        {dogSpots.length > 0 ? (
          dogSpots.map((spot, i) => (
            <li key={i}>
              {spot.name || 'Unnamed Spot'} — Lat: {spot.lat.toFixed(5)}, Lon:{' '}
              {spot.lon.toFixed(5)}
            </li>
          ))
        ) : (
          <li>No dog spots found</li>
        )}
      </ul>
    </div>
  );
};

export default MapDisplay;
