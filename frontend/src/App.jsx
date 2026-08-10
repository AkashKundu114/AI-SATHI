import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import ChatInterface from './components/ChatInterface';
import LedgerDrawer from './components/LedgerDrawer';
import Auth from './components/Auth';

export default function App() {
  const [theme, setTheme] = useState('dark');
  const [ledgerOpen, setLedgerOpen] = useState(false);

  const [userPhone, setUserPhone] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
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
      <Navbar
        currentTheme={theme}
        toggleTheme={toggleTheme}
        userProfile={userProfile}
        onLogout={handleLogout}
        onToggleLedger={() => setLedgerOpen((prev) => !prev)}
      />

      <main style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <ChatInterface userProfile={userProfile} />
      </main>

      <LedgerDrawer isOpen={ledgerOpen} onClose={() => setLedgerOpen(false)} userProfile={userProfile} />
    </div>
  );
}
