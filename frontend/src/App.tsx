import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import { Button } from 'primereact/button';
import './App.css';

interface ItemData {
  count: number;
  silver_value: number;
}

interface FullSessionData {
  items: { [key: string]: ItemData };
  elapsed_time: number;
}

const socket = io('http://127.0.0.1:5000');

// Lista de ítems para mostrar en el sidebar con sus imágenes
const ALL_ITEMS_INFO: { [key: string]: { silver_value: number, img: string } } = {
  "Máscara de Bandido Desgastado": { silver_value: 21000, img: "00065249.webp" },
  "Piedra de Caphras": { silver_value: 1900000, img: "00721003.webp" },
  "Piedra Negra": { silver_value: 258000, img: "00000008.webp" },
  "Polvo del Espíritu Ancestral": { silver_value: 325000, img: "00721002.webp" },
  "El Origen de la Depredación Oscura": { silver_value: 540000000, img: "00767102.webp" },
  "Cristal de la Madrugada WON - Evasión": { silver_value: 80000000, img: "00015275_1.webp" },
  "Cristal de la Madrugada WON - Furia del Espíritu Negro": { silver_value: 80000000, img: "00015266_1.webp" },
  "Cristal de la Madrugada WON - Puntería": { silver_value: 80000000, img: "00015269_1.webp" },
  "Cristal de la Madrugada WON - Reducción de Daño": { silver_value: 80000000, img: "00015272_1.webp" },
  "Cristal de la Madrugada BON - Furia del Espíritu Negro": { silver_value: 80000000, img: "00015265_1.webp" },
  "Cristal de la Madrugada BON - Todo Ataque": { silver_value: 80000000, img: "00015262_1.webp" },
  "Cristal de la Madrugada BON - Reducción de Daño": { silver_value: 80000000, img: "00015271_1.webp" },
  "Cristal de la Madrugada BON - Evasión": { silver_value: 80000000, img: "00015274_1.webp" },
  "Cristal de la Madrugada BON - Puntería": { silver_value: 80000000, img: "00015268_1.webp" },
};

function App() {
  const [sessionData, setSessionData] = useState<FullSessionData>({ items: {}, elapsed_time: 0 });
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [sidebarVisible, setSidebarVisible] = useState(false);

  useEffect(() => {
    socket.on('update_full_data', (newData: FullSessionData) => {
      setSessionData(newData);
    });

    return () => { socket.off('update_full_data'); };
  }, []);

  const handleControl = (action: 'start' | 'pause' | 'stop') => {
    socket.emit('control_session', { action });
    if (action === 'start') { setIsRunning(true); setIsPaused(false); }
    else if (action === 'pause') { setIsPaused(!isPaused); }
    else if (action === 'stop') { setIsRunning(false); setIsPaused(false); }
  };

  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
    const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
    const s = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${h}:${m}:${s}`;
  };

  const formatSilver = (silver: number) => {
    if (silver >= 1_000_000_000) return `${(silver / 1_000_000_000).toFixed(2)}B`;
    if (silver >= 1_000_000) return `${(silver / 1_000_000).toFixed(2)}M`;
    if (silver >= 1_000) return `${(silver / 1_000).toFixed(0)}K`;
    return silver.toString();
  };

  const totalLoot = Object.values(sessionData.items).reduce((sum, item) => sum + item.count, 0);
  const totalSilver = Object.values(sessionData.items).reduce((sum, item) => sum + (item.count * item.silver_value), 0);

  return (
    <>
      <div className={`sidebar ${sidebarVisible ? "open" : ""}`}>
        <div className="sidebar-content">
          <div className="sidebar-header">
            <h3>Botín de la Zona</h3>
            <Button
              icon="pi pi-times"
              className="p-button-rounded p-button-text sidebar-toggle"
              onClick={() => {
                setSidebarVisible(false);
                window.electronAPI.resizeWindow(350, 400);
              }}
            />
          </div>
          <div className="item-list-sidebar">
            {Object.entries(ALL_ITEMS_INFO).map(([name, data]) => (
              <div className="item-row-sidebar" key={name}>
                <img
                  src={`/img/${data.img}`}
                  alt={name}
                  className="item-icon-sidebar"
                  onError={(e) => e.currentTarget.src = 'https://placehold.co/32x32/2a2a2a/e0e0e0?text=?'}
                />
                <span className="item-name-sidebar">{name}</span>
                <span className="item-value-sidebar">{formatSilver(data.silver_value)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="app-container">
        <div className="header-bar">
          {!sidebarVisible && (
            <Button
              icon="pi pi-bars"
              className="p-button-rounded p-button-text sidebar-toggle"
              onClick={() => {
                setSidebarVisible(true);
                window.electronAPI.resizeWindow(800, 400);
              }}
            />
          )}
          <span className="app-title">BDO Loot Tracker</span>
          <span className="current-time">
            {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>

        <div className="main-content">
          <div className="card summary-card">
            <div className="card-header">
              <span className="card-title">Resumen de Sesión</span>
            </div>
            <div className="summary-grid">
              <div className="summary-item">
                <span className="summary-label">Botín Total</span>
                <span className="summary-value">{totalLoot.toLocaleString('es-MX')}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Plata Estimada</span>
                <span className="summary-value">{formatSilver(totalSilver)}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Tiempo</span>
                <span className="summary-value">{formatTime(sessionData.elapsed_time)}</span>
              </div>
            </div>
          </div>

          <div className="controls">
            {!isRunning ? (
              <button className="control-button start" onClick={() => handleControl('start')}>Iniciar Sesión</button>
            ) : (
              <>
                <button
                  className={`control-button ${isPaused ? 'resume' : 'pause'}`}
                  onClick={() => handleControl('pause')}
                >
                  {isPaused ? 'Reanudar' : 'Pausar'}
                </button>
                <button className="control-button stop" onClick={() => handleControl('stop')}>Detener</button>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

export default App;