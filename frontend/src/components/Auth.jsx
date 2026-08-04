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
        onLogin(data.user);
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
      backgroundColor: 'var(--bg-dark)',
      color: 'var(--text-main)',
      fontFamily: 'var(--font-body)'
    }}>
      <div className="card-sharp" style={{
        maxWidth: '420px',
        width: '100%',
        padding: '3rem',
        textAlign: 'center',
        boxShadow: '0 20px 40px rgba(0,0,0,0.5), 0 0 100px rgba(212,175,55,0.05)',
        borderRadius: 'var(--radius-sharp)',
        border: '1px solid var(--border-accent)',
        background: 'linear-gradient(135deg, var(--surface-dark), var(--bg-dark))',
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '4px',
          background: 'linear-gradient(90deg, var(--accent-gold), var(--accent-sapphire))'
        }}></div>

        <h1 style={{ 
          marginBottom: '0.5rem', 
          fontSize: '2rem', 
          fontWeight: '700',
          letterSpacing: '-0.5px',
          background: 'linear-gradient(90deg, var(--text-main), var(--text-dim))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          AI-SATHI
        </h1>
        
        <p style={{ color: 'var(--text-muted)', marginBottom: '2.5rem', fontSize: '0.95rem' }}>
          Secure Portal Access
        </p>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', textAlign: 'left' }}>
            <label style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '1px' }}>
              Username or Phone
            </label>
            <input 
              type="text" 
              placeholder="e.g. admin or 9064349004" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              style={{
                padding: '1rem 1.25rem',
                borderRadius: 'var(--radius-sharp)',
                border: '1px solid var(--border-dark)',
                backgroundColor: 'var(--bg-dark)',
                color: 'var(--text-main)',
                fontSize: '1rem',
                outline: 'none',
                transition: 'border-color 0.25s, box-shadow 0.25s',
              }}
              required
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', textAlign: 'left' }}>
            <label style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '1px' }}>
              Password
            </label>
            <input 
              type="password" 
              placeholder="••••••••" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                padding: '1rem 1.25rem',
                borderRadius: 'var(--radius-sharp)',
                border: '1px solid var(--border-dark)',
                backgroundColor: 'var(--bg-dark)',
                color: 'var(--text-main)',
                fontSize: '1rem',
                outline: 'none',
                transition: 'border-color 0.25s, box-shadow 0.25s',
              }}
              required
            />
          </div>

          {error && (
            <div style={{ 
              color: 'var(--accent-crimson)', 
              fontSize: '0.88rem', 
              textAlign: 'left',
              backgroundColor: 'rgba(231,76,60,0.08)',
              padding: '0.75rem 1rem',
              borderRadius: 'var(--radius-sharp)',
              borderLeft: '3px solid var(--accent-crimson)',
              marginTop: '0.5rem'
            }}>
              {error}
            </div>
          )}
          
          <button 
            type="submit" 
            disabled={loading}
            style={{
              background: 'linear-gradient(90deg, var(--accent-gold), var(--accent-sapphire))',
              color: 'var(--bg-dark)',
              border: 'none',
              padding: '1rem',
              borderRadius: 'var(--radius-sharp)',
              fontSize: '1rem',
              fontWeight: '600',
              cursor: loading ? 'not-allowed' : 'pointer',
              marginTop: '1rem',
              opacity: loading ? 0.7 : 1,
              transition: 'opacity 0.2s, transform 0.2s',
            }}
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}
