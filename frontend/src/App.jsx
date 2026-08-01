import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import VoiceTerminal from './components/VoiceTerminal';
import PdfRagSubChat from './components/PdfRagSubChat';
import LedgerHub from './components/LedgerHub';
import Auth from './components/Auth';

export default function App() {
  const [theme, setTheme] = useState('light');
  const [activeTab, setActiveTab] = useState('chat');
  
  const [userPhone, setUserPhone] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    // Load auth from localStorage on mount
    const savedPhone = localStorage.getItem('userPhone');
    const savedProfile = localStorage.getItem('userProfile');
    
    if (savedPhone && savedProfile) {
      setUserPhone(savedPhone);
      try {
        setUserProfile(JSON.parse(savedProfile));
      } catch (e) {
        // bad profile JSON
      }
    }
    setIsInitializing(false);
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const handleLogin = (user) => {
    setUserPhone(user.phone);
    setUserProfile(user);
    localStorage.setItem('userPhone', user.phone);
    localStorage.setItem('userProfile', JSON.stringify(user));
  };

  const handleLogout = () => {
    setUserPhone(null);
    setUserProfile(null);
    localStorage.removeItem('userPhone');
    localStorage.removeItem('userProfile');
  };

  if (isInitializing) return null;

  if (!userPhone || !userProfile) {
    return <Auth onLogin={handleLogin} />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden', backgroundColor: 'var(--bg-dark)', color: 'var(--text-main)' }}>
      {/* Top Navbar */}
      <Navbar currentTheme={theme} toggleTheme={toggleTheme} userProfile={userProfile} activeTab={activeTab} onLogout={handleLogout} />

      {/* Main Workspace */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Navigation Sidebar */}
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} userProfile={userProfile} onLogout={handleLogout} />

        {/* Content View Container */}
        <main style={{ flex: 1, padding: '2rem', overflowY: 'auto', backgroundColor: 'var(--bg-dark)' }}>
          <div style={{ maxWidth: '1000px', margin: '0 auto', height: '100%' }}>
            {activeTab === 'chat' && <VoiceTerminal userProfile={userProfile} />}
            {activeTab === 'pdf_rag' && <PdfRagSubChat userProfile={userProfile} />}
            {activeTab === 'ledger' && <LedgerHub userProfile={userProfile} />}
          </div>
        </main>
      </div>
    </div>
  );
}
