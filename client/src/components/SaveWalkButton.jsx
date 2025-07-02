import React from 'react';

const SaveWalkButton = ({ onClick, disabled }) => {
  return (
    <button onClick={onClick} disabled={disabled}>
      {disabled ? 'Walk Saved' : 'Save Walk'}
    </button>
  );
};

export default SaveWalkButton;
