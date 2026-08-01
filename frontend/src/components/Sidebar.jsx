import React from 'react';
import { MessageSquare, FileText, Cloud, BookOpenCheck, ShoppingBag, CreditCard, LayoutDashboard, ChevronRight } from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab, userProfile, onLogout }) {
  const menuItems = [
    { id: 'chat', label: 'Voice & Chat Terminal', sub: 'কথ্য বাংলায় ভয়েস সহকারী', icon: MessageSquare, badge: 'Voice AI' },
    { id: 'pdf_rag', label: 'PDF RAG Sub-Chat', sub: 'সরকারি ঋণ নির্দেশিকা চ্যাট', icon: FileText, badge: 'RAG AI' },
    { id: 'ledger', label: 'Baki Tagada & Ledger', sub: 'ডিজিটাল খাতা ও বাকির তাগাদা', icon: BookOpenCheck, badge: 'UPI' },
  ];

  return (
    <aside style={{ width: '260px', backgroundColor: 'var(--surface-dark)', borderRight: '1px solid var(--border-dark)', display: 'flex', flexDirection: 'column', height: 'calc(100vh - 61px)' }}>
      <div style={{ padding: '1rem 0.5rem', flex: 1, display: 'flex', flexDirection: 'column', gap: '0.2rem', overflowY: 'auto' }}>
        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-dim)', padding: '0.5rem 0.75rem', marginBottom: '0.5rem' }}>
          Menu
        </div>

        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.6rem 0.85rem',
                borderRadius: '8px',
                backgroundColor: isActive ? 'var(--surface-hover)' : 'transparent',
                border: 'none',
                color: isActive ? 'var(--text-main)' : 'var(--text-muted)',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.15s ease',
              }}
            >
              <Icon size={18} />
              <div style={{ fontSize: '0.9rem', fontWeight: isActive ? 500 : 400 }}>{item.label}</div>
            </button>
          );
        })}
      </div>

      <div style={{ padding: '1rem', borderTop: '1px solid var(--border-dark)', backgroundColor: 'var(--bg-dark)', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
          📍 {userProfile?.district || 'হুগলী'} • {userProfile?.block || 'সিঙ্গুর'}
        </div>
        <button
          onClick={onLogout}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            padding: '0.6rem',
            backgroundColor: 'transparent',
            border: '1px solid var(--border-dark)',
            borderRadius: '8px',
            color: 'var(--text-muted)',
            fontSize: '0.85rem',
            cursor: 'pointer',
            transition: 'all 0.2s',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--surface-hover)'; e.currentTarget.style.color = 'var(--text-main)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent'; e.currentTarget.style.color = 'var(--text-muted)'; }}
        >
          Logout
        </button>
      </div>
    </aside>
  );
}
