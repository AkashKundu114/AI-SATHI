import React, { useState, useEffect } from 'react';
import { X, BookOpen, ArrowUpRight, ArrowDownRight, RefreshCw } from 'lucide-react';

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
        // Normalize entry_type to lowercase so it matches our rendering logic
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

  const totalIncome = entries.filter((e) => e.type === 'income').reduce((sum, e) => sum + e.amount, 0);
  const totalExpense = entries.filter((e) => e.type === 'expense').reduce((sum, e) => sum + e.amount, 0);
  const net = totalIncome - totalExpense;

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            zIndex: 998,
            transition: 'opacity 0.3s',
          }}
        />
      )}

      {/* Drawer */}
      <div className={`ledger-drawer ${isOpen ? 'open' : ''}`}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border-dark)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BookOpen size={20} color="var(--accent-gold)" />
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Ledger History</h2>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn-sharp btn-outline-sharp" onClick={fetchLedger} style={{ padding: '0.4rem', width: '36px', height: '36px' }} title="Refresh">
              <RefreshCw size={16} className={loading ? 'spin' : ''} />
            </button>
            <button className="btn-sharp btn-outline-sharp" onClick={onClose} style={{ padding: '0.4rem', width: '36px', height: '36px' }} title="Close">
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Summary Cards */}
        <div style={{ padding: '1rem 1.5rem', display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '0.75rem' }}>
          <div className="card-sharp" style={{ padding: '0.75rem', textAlign: 'center' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase' }}>Income</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>₹{totalIncome.toLocaleString('en-IN')}</div>
          </div>
          <div className="card-sharp" style={{ padding: '0.75rem', textAlign: 'center' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase' }}>Expense</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--accent-amber)' }}>₹{totalExpense.toLocaleString('en-IN')}</div>
          </div>
          <div className="card-sharp" style={{ padding: '0.75rem', textAlign: 'center' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase' }}>Net</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: net >= 0 ? 'var(--accent-emerald)' : 'var(--accent-crimson)' }}>₹{net.toLocaleString('en-IN')}</div>
          </div>
        </div>

        {/* Entries List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '0 1.5rem 1.5rem' }}>
          {loading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading...</div>
          ) : entries.length === 0 ? (
            <div style={{ padding: '3rem 1rem', textAlign: 'center', color: 'var(--text-muted)', border: '1px dashed var(--border-dark)', borderRadius: 'var(--radius-sharp)' }}>
              No entries yet. Start by speaking or typing your transactions in the chat.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {entries.map((entry) => (
                <div key={entry.id} className="card-sharp" style={{ padding: '0.85rem 1rem', borderLeft: `3px solid ${entry.type === 'income' ? 'var(--accent-emerald)' : 'var(--accent-amber)'}` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div>
                      <span className={`badge-sharp ${entry.type === 'income' ? 'badge-emerald' : 'badge-amber'}`} style={{ marginBottom: '0.25rem', display: 'inline-flex' }}>
                        {entry.type === 'income' ? <><ArrowUpRight size={11} /> Income</> : <><ArrowDownRight size={11} /> Expense</>}
                      </span>
                      <div style={{ fontSize: '0.85rem', fontWeight: 600, marginTop: '0.25rem' }}>{entry.note || 'No description'}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>{entry.category} • {entry.date}</div>
                    </div>
                    <div style={{ fontSize: '1.15rem', fontWeight: 800, color: entry.type === 'income' ? 'var(--accent-emerald)' : 'var(--accent-amber)', whiteSpace: 'nowrap' }}>
                      ₹{entry.amount?.toLocaleString('en-IN')}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
