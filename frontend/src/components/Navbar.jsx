import { useState, useEffect } from 'react';
import { checkHealth } from '../services/api.js';

export function Navbar({ activeTab, setActiveTab }) {
  const [isBackendHealthy, setIsBackendHealthy] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const verifyHealth = async () => {
      const healthy = await checkHealth();
      if (isMounted) setIsBackendHealthy(healthy);
    };

    verifyHealth();
    const interval = setInterval(verifyHealth, 15000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="navbar">
      <div className="navbar-brand">
        <div className="brand-logo">
          <div className="mini-disc red"></div>
          <div className="mini-disc yellow"></div>
        </div>
        <div className="brand-text">
          <span className="brand-title">Connect Four AI</span>
          <span className="brand-badge">Adversarial Engine</span>
        </div>
      </div>

      <nav className="navbar-nav" role="navigation" aria-label="Main Navigation">
        <button
          className={`nav-tab ${activeTab === 'home' ? 'active' : ''}`}
          onClick={() => setActiveTab('home')}
          aria-current={activeTab === 'home' ? 'page' : undefined}
        >
          Home
        </button>
        <button
          className={`nav-tab ${activeTab === 'game' ? 'active' : ''}`}
          onClick={() => setActiveTab('game')}
          aria-current={activeTab === 'game' ? 'page' : undefined}
        >
          Play Game
        </button>
        <button
          className={`nav-tab ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
          aria-current={activeTab === 'analytics' ? 'page' : undefined}
        >
          Analytics
        </button>
      </nav>

      <div className="backend-status">
        <span
          className={`status-dot ${isBackendHealthy ? 'online' : 'offline'}`}
          aria-hidden="true"
        ></span>
        <span className="status-label">
          {isBackendHealthy ? 'API Connected' : 'API Offline'}
        </span>
      </div>
    </header>
  );
}
