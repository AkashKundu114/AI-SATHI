import React, { useState } from 'react';
import { User, Lock, UserPlus, LogIn, Sparkles, Phone, MapPin, Calendar, Users } from 'lucide-react';

export default function Auth({ onLogin }) {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [gender, setGender] = useState('male');
  const [dob, setDob] = useState('');
  const [phone, setPhone] = useState('');
  const [pincode, setPincode] = useState('');
  const [shgRegNo, setShgRegNo] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const cleanUsername = username.trim().toLowerCase();
    const cleanPassword = password.trim();

    if (!cleanUsername || !cleanPassword) {
      setError('ব্যবহারকারীর নাম এবং পাসওয়ার্ড দিন');
      return;
    }

    setLoading(true);
    try {
      const endpoint = isRegister ? '/api/v1/auth/register' : '/api/v1/auth/login';
      const payload = isRegister
        ? {
            username: cleanUsername,
            password: cleanPassword,
            name: name.trim() || undefined,
            gender: gender,
            dob: dob.trim() || undefined,
            phone: phone.trim() || undefined,
            pincode: pincode.trim() || undefined,
            shg_reg_no: shgRegNo.trim() || undefined,
          }
        : { username: cleanUsername, password: cleanPassword };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || (isRegister ? 'Registration failed' : 'Login failed'));
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
      overflow: 'hidden',
      padding: '2rem 1rem'
    }}>
      {/* Background ambient lighting */}
      <div style={{
        position: 'absolute',
        top: '15%',
        left: '25%',
        width: '450px',
        height: '450px',
        background: 'radial-gradient(circle, rgba(212, 175, 55, 0.08) 0%, rgba(0,0,0,0) 70%)',
        pointerEvents: 'none',
        filter: 'blur(50px)'
      }}></div>
      <div style={{
        position: 'absolute',
        bottom: '15%',
        right: '25%',
        width: '400px',
        height: '400px',
        background: 'radial-gradient(circle, rgba(14, 165, 233, 0.07) 0%, rgba(0,0,0,0) 70%)',
        pointerEvents: 'none',
        filter: 'blur(50px)'
      }}></div>

      <div style={{
        maxWidth: isRegister ? '520px' : '430px',
        width: '100%',
        padding: '2.25rem 2rem',
        textAlign: 'center',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6), 0 0 40px rgba(212, 175, 55, 0.08)',
        borderRadius: 'var(--radius-smooth)',
        border: '1px solid var(--border-medium)',
        background: 'var(--bg-glass)',
        backdropFilter: 'blur(24px)',
        WebkitBackdropFilter: 'blur(24px)',
        position: 'relative',
        zIndex: 10,
        transition: 'max-width 0.3s ease'
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
          margin: '0 auto 0.75rem',
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
          marginBottom: '0.25rem', 
          fontSize: '1.75rem', 
          fontWeight: '800',
          letterSpacing: '-0.03em',
          background: 'linear-gradient(135deg, #FFFFFF 0%, #E2E8F0 50%, #CBD5E1 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          AI-SATHI
        </h1>
        
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.85rem' }}>
          স্বনির্ভর দল ও গ্রামীণ ব্যবসায়িক প্ল্যাটফর্ম
        </p>

        {/* Sign In vs Register Tabs */}
        <div style={{
          display: 'flex',
          backgroundColor: 'rgba(255, 255, 255, 0.04)',
          borderRadius: 'var(--radius-sleek)',
          padding: '0.25rem',
          marginBottom: '1.5rem',
          border: '1px solid var(--border-subtle)'
        }}>
          <button
            type="button"
            onClick={() => { setIsRegister(false); setError(''); }}
            style={{
              flex: 1,
              padding: '0.5rem',
              fontSize: '0.825rem',
              fontWeight: 600,
              borderRadius: 'var(--radius-sharp)',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.35rem',
              transition: 'all 0.2s',
              backgroundColor: !isRegister ? 'var(--color-gold)' : 'transparent',
              color: !isRegister ? '#090B10' : 'var(--text-secondary)'
            }}
          >
            <LogIn size={14} />
            <span>লগইন / Sign In</span>
          </button>

          <button
            type="button"
            onClick={() => { setIsRegister(true); setError(''); }}
            style={{
              flex: 1,
              padding: '0.5rem',
              fontSize: '0.825rem',
              fontWeight: 600,
              borderRadius: 'var(--radius-sharp)',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.35rem',
              transition: 'all 0.2s',
              backgroundColor: isRegister ? 'var(--color-gold)' : 'transparent',
              color: isRegister ? '#090B10' : 'var(--text-secondary)'
            }}
          >
            <UserPlus size={14} />
            <span>নতুন অ্যাকাউন্ট / Register</span>
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {isRegister && (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', textAlign: 'left' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                  <label style={{ fontSize: '0.725rem', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    পুরো নাম / Full Name
                  </label>
                  <input 
                    type="text" 
                    placeholder="e.g. Akash Kundu" 
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="input-luxe"
                    required
                  />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                  <label style={{ fontSize: '0.725rem', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    লিঙ্গ / Gender
                  </label>
                  <select 
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    className="input-luxe"
                    style={{ padding: '0.7rem' }}
                  >
                    <option value="male" style={{ background: '#090B10', color: '#FFF' }}>পুরুষ (Male)</option>
                    <option value="female" style={{ background: '#090B10', color: '#FFF' }}>মহিলা (Female)</option>
                    <option value="other" style={{ background: '#090B10', color: '#FFF' }}>অন্যান্য (Other)</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', textAlign: 'left' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                  <label style={{ fontSize: '0.725rem', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    মোবাইল নম্বর / Phone
                  </label>
                  <input 
                    type="tel" 
                    placeholder="10-digit number" 
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="input-luxe"
                  />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                  <label style={{ fontSize: '0.725rem', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    পিনকোড / Pincode
                  </label>
                  <input 
                    type="text" 
                    placeholder="6-digit Pincode" 
                    maxLength={6}
                    value={pincode}
                    onChange={(e) => setPincode(e.target.value)}
                    className="input-luxe"
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', textAlign: 'left' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                  <label style={{ fontSize: '0.725rem', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    জন্মতারিখ / DOB or Age
                  </label>
                  <input 
                    type="text" 
                    placeholder="e.g. 1998 or 26" 
                    value={dob}
                    onChange={(e) => setDob(e.target.value)}
                    className="input-luxe"
                  />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                  <label style={{ fontSize: '0.725rem', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    SHG Reg. No. (ঐচ্ছিক)
                  </label>
                  <input 
                    type="text" 
                    placeholder="If SHG member" 
                    value={shgRegNo}
                    onChange={(e) => setShgRegNo(e.target.value)}
                    className="input-luxe"
                  />
                </div>
              </div>
            </>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem', textAlign: 'left' }}>
            <label style={{ fontSize: '0.725rem', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              ব্যবহারকারীর নাম / Username
            </label>
            <input 
              type="text" 
              placeholder="e.g. admin or akash_kundu" 
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="input-luxe"
              required
              autoFocus
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem', textAlign: 'left' }}>
            <label style={{ fontSize: '0.725rem', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              পাসওয়ার্ড / Password
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
              marginTop: '0.5rem',
              width: '100%'
            }}
          >
            {loading ? 'প্রক্রিয়াকরণ হচ্ছে...' : isRegister ? 'অ্যাকাউন্ট তৈরি করুন / Register' : 'লগইন করুন / Sign In'}
          </button>
        </form>

        <div style={{ marginTop: '1.75rem', paddingTop: '1rem', borderTop: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'center', gap: '1rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          <span>🔒 PBKDF2 Password Hashing</span>
          <span>•</span>
          <span>⚡ Sarvam AI Powered</span>
        </div>
      </div>
    </div>
  );
}
