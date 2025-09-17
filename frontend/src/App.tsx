import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import './App.css';

interface LootData {
  total_loot: number;
  total_silver: number;
  elapsed_time: number;
}

const socket = io('http://127.0.0.1:5000');

function App() {
  const [data, setData] = useState<LootData>({
    total_loot: 0,
    total_silver: 0,
    elapsed_time: 0,
  });

  useEffect(() => {
    socket.on('update_data', (newData: LootData) => setData(newData));
    return () => { socket.off('update_data'); };
  }, []);

  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
    const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
    return `${h}:${m}`;
  };

  return (
    <div className="overlay-container">
      <div className="title-bar">
        BDO Loot Tracker
      </div>

      <div className="stats-grid">
        <div className="stat-item">
          <span className="label">🕒 TIEMPO</span>
          <span className="value">{formatTime(data.elapsed_time)}</span>
        </div>
        <div className="stat-item">
          <span className="label">💎 BOTÍN</span>
          <span className="value">{data.total_loot.toLocaleString('es-MX')}</span>
        </div>
        <div className="stat-item">
          <span className="label">💰 PLATAS</span>
          <span className="value">{data.total_silver.toLocaleString('es-MX')}</span>
        </div>
      </div>
    </div>
  );
}

export default App;