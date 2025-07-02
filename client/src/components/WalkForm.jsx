import React, { useState } from 'react';

const WalkForm = ({ distance, onDistanceChange, onLocationSet, onSubmit, disabled }) => {
  const [gettingLocation, setGettingLocation] = useState(false);

  const handleGetLocation = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser');
      return;
    }

    setGettingLocation(true);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        onLocationSet({
          lat: position.coords.latitude,
          lon: position.coords.longitude,
        });
        setGettingLocation(false);
      },
      () => {
        alert('Unable to retrieve your location');
        setGettingLocation(false);
      }
    );
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
    >
      <label>
        Distance (km):
        <input
          type="number"
          value={distance}
          onChange={(e) => onDistanceChange(e.target.value)}
          disabled={disabled}
          min="0.5"
          max="10"
          step="0.1"
          required
        />
      </label>

      <button type="button" onClick={handleGetLocation} disabled={gettingLocation || disabled}>
        {gettingLocation ? 'Getting Location...' : 'Use My Location'}
      </button>

      <button type="submit" disabled={disabled || !distance}>
        Generate Walk
      </button>
    </form>
  );
};

export default WalkForm;
