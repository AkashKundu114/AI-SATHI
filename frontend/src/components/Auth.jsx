import React, { useState } from 'react';

export default function Auth({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!username.trim() || !password.trim()) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
      }

      if (data.status === 'success' && data.user) {
        onLogin(data.user, data.token);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      backgroundColor: 'var(--bg-canvas)',
      color: 'var(--text-primary)',
      fontFamily: 'var(--font-body)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Ambient background glow orbs */}
      <div style={{
        position: 'absolute',
        top: '20%',
        left: '30%',
        width: '400px',
        height: '400px',
        background: 'radial-gradient(circle, rgba(212, 175, 55, 0.08) 0%, rgba(0,0,0,0) 70%)',
        pointerEvents: 'none',
        filter: 'blur(40px)'
      }}></div>
      <div style={{
        position: 'absolute',
        bottom: '20%',
        right: '30%',
        width: '350px',
        height: '350px',
        background: 'radial-gradient(circle, rgba(14, 165, 233, 0.07) 0%, rgba(0,0,0,0) 70%)',
        pointerEvents: 'none',
        filter: 'blur(40px)'
      }}></div>

      <div style={{
        maxWidth: '440px',
        width: '90%',
        padding: '3rem 2.5rem',
        textAlign: 'center',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6), 0 0 40px rgba(212, 175, 55, 0.08)',
        borderRadius: 'var(--radius-smooth)',
        border: '1px solid var(--border-medium)',
        background: 'var(--bg-glass)',
        backdropFilter: 'blur(24px)',
        WebkitBackdropFilter: 'blur(24px)',
        position: 'relative',
        zIndex: 10
      }}>
        {/* Top Accent Line */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '3px',
          background: 'linear-gradient(90deg, #F3E5AB 0%, #D4AF37 50%, #0EA5E9 100%)',
          borderRadius: 'var(--radius-smooth) var(--radius-smooth) 0 0'
        }}></div>

        {/* Monogram */}
        <div style={{
          width: '48px',
          height: '48px',
          margin: '0 auto 1.25rem',
          background: 'linear-gradient(135deg, #F3E5AB 0%, #D4AF37 50%, #B8860B 100%)',
          borderRadius: 'var(--radius-sharp)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#090B10',
          fontWeight: 800,
          fontSize: '1.4rem',
          boxShadow: '0 4px 16px rgba(212, 175, 55, 0.35)'
        }}>
          সা
        </div>

        <h1 style={{ 
          marginBottom: '0.4rem', 
          fontSize: '1.75rem', 
          fontWeight: '800',
          letterSpacing: '-0.03em',
          background: 'linear-gradient(135deg, #FFFFFF 0%, #E2E8F0 50%, #CBD5E1 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          AI-SATHI
        </h1>
        
        <p style={{ color: 'var(--text-secondary)', marginBottom: '2.25rem', fontSize: '0.875rem' }}>
          স্বনির্ভর দল ও গ্রামীন ব্যবসায়িক প্ল্যাটফর্ম
        </p>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', textAlign: 'left' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Username or Phone
            </label>
            <input 
              type="text" 
              placeholder="e.g. admin or 9064349004" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input-luxe"
              required
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', textAlign: 'left' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Password
            </label>
            <input 
              type="password" 
              placeholder="••••••••" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-luxe"
              required
            />
          </div>

          {error && (
            <div style={{ 
              color: 'var(--color-rose-light)', 
              fontSize: '0.825rem', 
              textAlign: 'left',
              backgroundColor: 'var(--color-rose-muted)',
              padding: '0.65rem 0.85rem',
              borderRadius: 'var(--radius-sleek)',
              border: '1px solid rgba(244, 63, 94, 0.3)',
              marginTop: '0.25rem'
            }}>
              {error}
            </div>
          )}
          
          <button 
            type="submit" 
            disabled={loading}
            className="btn-luxe btn-luxe-primary"
            style={{
              padding: '0.85rem',
              fontSize: '0.925rem',
              marginTop: '0.75rem',
              width: '100%'
            }}
          >
            {loading ? 'Authenticating...' : 'Sign In / লগইন করুন'}
          </button>
        </form>

        <div style={{ marginTop: '2rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'center', gap: '1rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          <span>🔒 256-bit Encrypted</span>
          <span>•</span>
          <span>⚡ Sarvam AI Powered</span>
        </div>
      </div>
    </div>
  );
}

