import React from 'react';
import { Moon, Sun, Sparkles, BookOpen, LogOut, ShieldCheck } from 'lucide-react';

export default function Navbar({ currentTheme, toggleTheme, userProfile, onLogout, onToggleLedger }) {
  return (
    <header style={{
      background: 'var(--bg-glass)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      borderBottom: '1px solid var(--border-subtle)',
      padding: '0.75rem 1.75rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      zIndex: 50,
      flexShrink: 0
    }}>
      {/* Brand & Identity */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{
          width: '38px',
          height: '38px',
          background: 'linear-gradient(135deg, #F3E5AB 0%, #D4AF37 50%, #996515 100%)',
          borderRadius: 'var(--radius-sharp)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#080A0F',
          fontWeight: 800,
          fontSize: '1.15rem',
          boxShadow: '0 2px 10px rgba(212, 175, 55, 0.3)'
        }}>
          সা
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{
              fontFamily: 'var(--font-display)',
              fontWeight: 800,
              fontSize: '1.15rem',
              letterSpacing: '-0.03em',
              background: 'linear-gradient(135deg, #FFFFFF 0%, #E2E8F0 60%, #CBD5E1 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              AI-SATHI
            </span>
            <span className="badge-luxe badge-gold" style={{ fontSize: '0.65rem', padding: '0.15rem 0.45rem' }}>
              LUXE v2.0
            </span>
          </div>
          <p style={{ fontSize: '0.725rem', color: 'var(--text-secondary)', fontWeight: 400 }}>
            Rural Micro-Enterprise Intelligence
          </p>
        </div>
      </div>

      {/* Right Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
        {/* Active Pill */}
        <div className="badge-luxe badge-emerald" style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#10B981', display: 'inline-block', boxShadow: '0 0 8px #10B981' }}></span>
          <span>Online</span>
        </div>

        {/* Ledger Trigger */}
        <button
          className="btn-luxe btn-luxe-gold"
          onClick={onToggleLedger}
          title="Open Ledger Drawer"
          style={{ padding: '0.45rem 0.9rem', fontSize: '0.8rem' }}
        >
          <BookOpen size={15} />
          <span>খাতা / Ledger</span>
        </button>

        {/* User Card */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          paddingLeft: '0.85rem',
          borderLeft: '1px solid var(--border-subtle)'
        }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.825rem', fontWeight: 600, color: 'var(--text-primary)' }}>
              {userProfile?.name || 'Micro-Entrepreneur'}
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--color-gold-light)', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.25rem' }}>
              <ShieldCheck size={12} color="var(--color-gold)" />
              <span>{userProfile?.phone || '9064349004'}</span>
            </div>
          </div>
        </div>

        {/* Theme Toggle */}
        <button
          className="btn-luxe btn-luxe-outline"
          onClick={toggleTheme}
          title="Toggle Theme"
          style={{ width: '36px', height: '36px', padding: 0 }}
        >
          {currentTheme === 'dark' ? <Sun size={16} color="var(--color-gold)" /> : <Moon size={16} color="var(--color-sapphire)" />}
        </button>

        {/* Logout */}
        <button
          className="btn-luxe btn-luxe-danger"
          onClick={onLogout}
          title="Sign Out"
          style={{ width: '36px', height: '36px', padding: 0 }}
        >
          <LogOut size={15} />
        </button>
      </div>
    </header>
  );
}

