import React, { useState } from 'react';

export default function Auth({ onLogin }) {
  const [step, setStep] = useState(1);
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handlePhoneSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    // Basic regex for phone validation (allows optional +, followed by 10-14 digits)
    const phoneRegex = /^\+?[0-9]{10,14}$/;
    if (!phoneRegex.test(phone)) {
      setError('Please enter a valid phone number (e.g. +919876543210)');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch('/api/v1/auth/request-otp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ phone })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to request OTP');
      }

      if (data.status === 'success') {
        setStep(2);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    setError('');

    setLoading(true);
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ phone, otp })
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
        maxWidth: '400px',
        width: '100%',
        padding: '2.5rem',
        textAlign: 'center',
        boxShadow: 'var(--shadow-flat)',
        borderRadius: 'var(--radius-sharp)'
      }}>
        <h1 style={{ marginBottom: '0.5rem', fontSize: '1.75rem', fontWeight: '600' }}>Welcome to AI-SATHI</h1>
        
        {step === 1 ? (
          <>
            <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', fontSize: '0.95rem' }}>
              Enter your phone number to continue.
            </p>
            <form onSubmit={handlePhoneSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <input 
                type="tel" 
                placeholder="+919876543210" 
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                style={{
                  padding: '0.875rem 1rem',
                  borderRadius: '8px',
                  border: '1px solid var(--border-accent)',
                  backgroundColor: 'var(--surface-hover)',
                  color: 'var(--text-main)',
                  fontSize: '1rem',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                }}
                required
              />
              {error && <div style={{ color: 'var(--accent-crimson)', fontSize: '0.85rem', textAlign: 'left' }}>{error}</div>}
              
              <button 
                type="submit" 
                disabled={loading}
                style={{
                  backgroundColor: 'var(--text-main)',
                  color: 'var(--bg-dark)',
                  border: 'none',
                  padding: '0.875rem',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  fontWeight: '500',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  marginTop: '0.5rem',
                  opacity: loading ? 0.7 : 1,
                  transition: 'opacity 0.2s'
                }}
              >
                {loading ? 'Sending OTP...' : 'Continue'}
              </button>
            </form>
          </>
        ) : (
          <>
            <p style={{ color: 'var(--text-muted)', marginBottom: '2rem', fontSize: '0.95rem' }}>
              Enter the OTP sent to {phone}.
            </p>
            <form onSubmit={handleOtpSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <input 
                type="text" 
                placeholder="123456" 
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                style={{
                  padding: '0.875rem 1rem',
                  borderRadius: '8px',
                  border: '1px solid var(--border-accent)',
                  backgroundColor: 'var(--surface-hover)',
                  color: 'var(--text-main)',
                  fontSize: '1rem',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                }}
                required
              />
              {error && <div style={{ color: 'var(--accent-crimson)', fontSize: '0.85rem', textAlign: 'left' }}>{error}</div>}
              
              <button 
                type="submit" 
                disabled={loading}
                style={{
                  backgroundColor: 'var(--text-main)',
                  color: 'var(--bg-dark)',
                  border: 'none',
                  padding: '0.875rem',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  fontWeight: '500',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  marginTop: '0.5rem',
                  opacity: loading ? 0.7 : 1,
                  transition: 'opacity 0.2s'
                }}
              >
                {loading ? 'Verifying...' : 'Login'}
              </button>
              <button
                type="button"
                onClick={() => setStep(1)}
                style={{
                  backgroundColor: 'transparent',
                  color: 'var(--text-muted)',
                  border: 'none',
                  fontSize: '0.9rem',
                  cursor: 'pointer',
                  marginTop: '0.5rem',
                  textDecoration: 'underline'
                }}
              >
                Change Phone Number
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
