// src/components/WalkHistory.jsx

import React, { useEffect, useState } from 'react';

const WalkHistory = () => {
  const [walks, setWalks] = useState([]);
  const [selectedWalk, setSelectedWalk] = useState(null);

  useEffect(() => {
    const fetchWalks = async () => {
      try {
        const res = await fetch('/walk-history');
        if (res.ok) {
          const data = await res.json();
          setWalks(data);
        } else {
          console.error('Failed to fetch walks');
        }
      } catch (err) {
        console.error('Error fetching walks:', err);
      }
    };

    fetchWalks();
  }, []);

  return (
    <div>
      <h1>Walk History</h1>
      {walks.length === 0 && <p>No walks saved yet.</p>}

      <ul>
        {walks.map((walk) => (
          <li key={walk.id} style={{ marginBottom: '1em' }}>
            <button
              onClick={() =>
                setSelectedWalk(selectedWalk?.id === walk.id ? null : walk)
              }
            >
              {new Date(walk.timestamp).toLocaleString()} — {walk.distance} km
            </button>

            {selectedWalk?.id === walk.id && (
              <div style={{ marginTop: '0.5em', paddingLeft: '1em' }}>
                <p>Duration: {walk.duration ? `${walk.duration} sec` : 'N/A'}</p>
                <p>Temperature: {walk.temperature ?? 'N/A'} °C</p>
                <p>Condition: {walk.condition || 'N/A'}</p>
                <p>Difficulty: {walk.difficulty || 'N/A'}</p>
                <p>
                  Dog Parks Visited:{' '}
                  {walk.dog_parks_visited
                    ? JSON.parse(walk.dog_parks_visited)
                        .map((park) => park.name || 'Unnamed')
                        .join(', ')
                    : 'None'}
                </p>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default WalkHistory;
