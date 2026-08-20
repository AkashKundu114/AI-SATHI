import React, { useState, useEffect } from 'react';
import { X, BookOpen, ArrowUpRight, ArrowDownRight, RefreshCw, Layers } from 'lucide-react';

export default function LedgerDrawer({ isOpen, onClose, userProfile }) {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchLedger = async () => {
    if (!userProfile?.phone) return;
    setLoading(true);
    try {
      const token = localStorage.getItem('ai_sathi_token') || '';
      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`/api/v1/ledger?phone=${encodeURIComponent(userProfile.phone)}`, { headers });
      const data = await res.json();
      if (data.status === 'success' && data.entries) {
        const normalized = data.entries.map(e => ({...e, type: e.type.toLowerCase()}));
        setEntries(normalized);
      }
    } catch (err) {
      console.error('Error fetching ledger:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) fetchLedger();
  }, [isOpen]);

  const totalIncome = entries
    .filter((e) => ['income', 'jama', 'recovery'].includes(e.type))
    .reduce((sum, e) => sum + (e.amount || 0), 0);
  const totalExpense = entries
    .filter((e) => ['expense', 'khoroch', 'borrow', 'lend', 'kisti', 'wages', 'savings'].includes(e.type))
    .reduce((sum, e) => sum + (e.amount || 0), 0);
  const net = totalIncome - totalExpense;

  const getEntryBadge = (type) => {
    switch (type) {
      case 'income':
      case 'jama':
        return { label: 'Income', isIncome: true, badgeClass: 'badge-emerald' };
      case 'recovery':
        return { label: 'Recovery (আদায়)', isIncome: true, badgeClass: 'badge-emerald' };
      case 'expense':
      case 'khoroch':
        return { label: 'Expense', isIncome: false, badgeClass: 'badge-rose' };
      case 'lend':
        return { label: 'Lend (ধার)', isIncome: false, badgeClass: 'badge-gold' };
      case 'borrow':
        return { label: 'Borrow (ঋণ)', isIncome: false, badgeClass: 'badge-sapphire' };
      case 'kisti':
        return { label: 'Kisti (কিস্তি)', isIncome: false, badgeClass: 'badge-rose' };
      case 'savings':
        return { label: 'Savings (সঞ্চয়)', isIncome: false, badgeClass: 'badge-gold' };
      case 'wages':
        return { label: 'Wages (মজুরি)', isIncome: false, badgeClass: 'badge-rose' };
      default:
        return { label: type || 'Entry', isIncome: false, badgeClass: 'badge-neutral' };
    }
  };

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.65)',
            backdropFilter: 'blur(8px)',
            WebkitBackdropFilter: 'blur(8px)',
            zIndex: 998,
            transition: 'opacity 0.25s ease',
          }}
        />
      )}

      {/* Drawer */}
      <div style={{
        position: 'fixed',
        top: 0,
        right: 0,
        bottom: 0,
        width: '420px',
        maxWidth: '90vw',
        background: 'var(--bg-canvas-subtle)',
        borderLeft: '1px solid var(--border-medium)',
        boxShadow: '-10px 0 35px rgba(0,0,0,0.5)',
        zIndex: 999,
        display: 'flex',
        flexDirection: 'column',
        transform: isOpen ? 'translateX(0)' : 'translateX(100%)',
        transition: 'transform 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid var(--border-subtle)',
          background: 'var(--bg-glass)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: 'var(--radius-sharp)',
              background: 'var(--color-gold-muted)',
              border: '1px solid var(--border-gold)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--color-gold-light)'
            }}>
              <BookOpen size={16} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.05rem', fontWeight: 700 }}>ডিজিটাল খতিয়ান</h2>
              <p style={{ fontSize: '0.725rem', color: 'var(--text-secondary)' }}>Ledger Statement</p>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.4rem' }}>
            <button
              className="btn-luxe btn-luxe-outline"
              onClick={fetchLedger}
              style={{ padding: '0.4rem', width: '32px', height: '32px' }}
              title="Refresh"
            >
              <RefreshCw size={14} />
            </button>
            <button
              className="btn-luxe btn-luxe-outline"
              onClick={onClose}
              style={{ padding: '0.4rem', width: '32px', height: '32px' }}
              title="Close"
            >
              <X size={14} />
            </button>
          </div>
        </div>

        {/* Financial Overview Metrics */}
        <div style={{ padding: '1.25rem 1.5rem', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.65rem' }}>
          <div className="glass-card-sharp" style={{ padding: '0.85rem 0.6rem', textAlign: 'center', borderLeft: '2px solid var(--color-emerald)' }}>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Income (জমা)</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--color-emerald-light)', marginTop: '0.2rem' }}>₹{totalIncome.toLocaleString('en-IN')}</div>
          </div>
          <div className="glass-card-sharp" style={{ padding: '0.85rem 0.6rem', textAlign: 'center', borderLeft: '2px solid var(--color-rose)' }}>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Expense (খরচ)</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--color-rose-light)', marginTop: '0.2rem' }}>₹{totalExpense.toLocaleString('en-IN')}</div>
          </div>
          <div className="glass-card-sharp" style={{ padding: '0.85rem 0.6rem', textAlign: 'center', borderLeft: '2px solid var(--color-gold)' }}>
            <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Net (লাভ)</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: net >= 0 ? 'var(--color-emerald-light)' : 'var(--color-rose-light)', marginTop: '0.2rem' }}>
              ₹{net.toLocaleString('en-IN')}
            </div>
          </div>
        </div>

        {/* Entries List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '0 1.5rem 1.5rem', display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              লেনদেনের তালিকা ({entries.length})
            </span>
          </div>

          {loading ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>Loading entries...</div>
          ) : entries.length === 0 ? (
            <div style={{
              padding: '3rem 1.5rem',
              textAlign: 'center',
              color: 'var(--text-muted)',
              border: '1px dashed var(--border-subtle)',
              borderRadius: 'var(--radius-smooth)',
              background: 'rgba(255,255,255,0.01)'
            }}>
              <Layers size={28} color="var(--text-dim)" style={{ margin: '0 auto 0.75rem' }} />
              <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-secondary)' }}>কোনো হিসাব এখনও জমা নেই</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>চ্যাটে আপনার আয় বা খরচের কথা লিখে বা বলে হিসাব রাখুন।</div>
            </div>
          ) : (
            entries.map((entry) => {
              const badge = getEntryBadge(entry.type);
              return (
                <div
                  key={entry.id}
                  className="glass-card-sharp"
                  style={{
                    padding: '0.9rem 1rem',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    borderLeft: `3px solid ${badge.isIncome ? 'var(--color-emerald)' : 'var(--color-rose)'}`
                  }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                      <span className={`badge-luxe ${badge.badgeClass}`}>
                        {badge.isIncome ? <ArrowUpRight size={11} /> : <ArrowDownRight size={11} />}
                        {badge.label}
                      </span>
                      <span style={{ fontSize: '0.725rem', color: 'var(--text-dim)' }}>
                        {entry.category}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {entry.note || 'No description'}
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      {entry.date}
                    </div>
                  </div>

                  <div style={{
                    fontSize: '1.15rem',
                    fontWeight: 800,
                    fontFamily: 'var(--font-display)',
                    color: badge.isIncome ? 'var(--color-emerald-light)' : 'var(--color-rose-light)',
                    whiteSpace: 'nowrap',
                    paddingLeft: '0.75rem'
                  }}>
                    {badge.isIncome ? '+' : '-'}₹{entry.amount?.toLocaleString('en-IN')}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </>
  );
}


