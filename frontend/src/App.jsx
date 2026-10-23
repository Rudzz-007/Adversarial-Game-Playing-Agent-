import { useState } from 'react';
import { Navbar } from './components/Navbar.jsx';
import { HomePage } from './pages/HomePage.jsx';
import { GamePage } from './pages/GamePage.jsx';
import { AnalyticsPage } from './pages/AnalyticsPage.jsx';
import './App.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('game');

  return (
    <div className="app-root">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="main-content" role="main">
        {activeTab === 'home' && <HomePage onStartPlaying={() => setActiveTab('game')} />}
        {activeTab === 'game' && <GamePage />}
        {activeTab === 'analytics' && <AnalyticsPage />}
      </main>

      <footer className="app-footer">
        <p>
          Connect Four AI — Adversarial Game-Playing Agent &bull; Powered by FastAPI & React &bull; PRD v1.0 Compliant
        </p>
      </footer>
    </div>
  );
}