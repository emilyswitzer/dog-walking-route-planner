import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import HomeScreen from './components/HomeScreen';
import WalkHistory from './components/WalkHistory';

function App() {
  return (
    <Router>
      <nav style={{ padding: '1em', borderBottom: '1px solid #ccc' }}>
        <Link to="/" style={{ marginRight: '1em' }}>Home</Link>
        <Link to="/history">Walk History</Link>
      </nav>

      <Routes>
        <Route path="/" element={<HomeScreen />} />
        <Route path="/history" element={<WalkHistory />} />
      </Routes>
    </Router>
  );
}

export default App;
