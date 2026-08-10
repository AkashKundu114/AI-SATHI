import React from 'react';
import { Moon, Sun, Sparkles, BookOpen, LogOut } from 'lucide-react';

export default function Navbar({ currentTheme, toggleTheme, userProfile, onLogout, onToggleLedger }) {
  return (
    <header className="card-sharp" style={{ borderRadius: 0, borderTop: 'none', borderLeft: 'none', borderRight: 'none', padding: '0.85rem 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', zIndex: 50, flexShrink: 0 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <div style={{ width: '36px', height: '36px', backgroundColor: 'var(--accent-gold)', borderRadius: 'var(--radius-sharp)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#0B0F19', fontWeight: 800, fontSize: '1.1rem' }}>
            সা
          </div>
          <div>
            <h1 style={{ fontSize: '1.15rem', lineHeight: 1.1, display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              AI-SATHI <span style={{ fontSize: '0.7rem', color: 'var(--accent-gold)', fontWeight: 600, border: '1px solid var(--accent-gold)', padding: '0.1rem 0.35rem', borderRadius: '4px' }}>v2.0 WEB</span>
            </h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>পশ্চিমবঙ্গের গ্রামীন উদ্যোক্তাদের এআই সহচর</p>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        {/* Status Pill */}
        <div className="badge-sharp badge-emerald">
          <Sparkles size={14} /> Active
        </div>

        {/* Ledger Button */}
        <button className="btn-sharp btn-outline-sharp" onClick={onToggleLedger} style={{ padding: '0.5rem 0.85rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }} title="View Ledger">
          <BookOpen size={16} color="var(--accent-gold)" />
          <span style={{ fontSize: '0.8rem' }}>Ledger</span>
        </button>

        {/* User Info */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', paddingLeft: '0.75rem', borderLeft: '1px solid var(--border-dark)' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600 }}>{userProfile?.name || 'User'}</div>
            <div style={{ fontSize: '0.72rem', color: 'var(--accent-gold)', fontWeight: 500 }}>
              {userProfile?.phone || 'Micro-Entrepreneur'}
            </div>
          </div>
        </div>

        {/* Theme Toggle */}
        <button className="btn-sharp btn-outline-sharp" onClick={toggleTheme} style={{ padding: '0.5rem', width: '36px', height: '36px' }} title="Toggle Theme">
          {currentTheme === 'dark' ? <Sun size={18} color="var(--accent-gold)" /> : <Moon size={18} color="var(--accent-sapphire)" />}
        </button>

        {/* Logout */}
        <button className="btn-sharp btn-outline-sharp" onClick={onLogout} style={{ padding: '0.5rem', width: '36px', height: '36px' }} title="Sign Out">
          <LogOut size={16} color="var(--accent-crimson)" />
        </button>
      </div>
    </header>
  );
}
