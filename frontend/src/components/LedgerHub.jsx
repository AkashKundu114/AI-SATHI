import React, { useState, useEffect } from 'react';
import { BookOpen, Send, Plus, ArrowUpRight, ArrowDownRight, CheckCircle, Smartphone } from 'lucide-react';

export default function LedgerHub({ userProfile }) {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showTagadaModal, setShowTagadaModal] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState(null);

  // Form states for manual entry
  const [amount, setAmount] = useState('');
  const [entryType, setEntryType] = useState('income');
  const [category, setCategory] = useState('');
  const [note, setNote] = useState('');
  const [quantity, setQuantity] = useState('');
  const [unit, setUnit] = useState('');

  const fetchLedger = () => {
    if (userProfile && userProfile.phone) {
      setLoading(true);
      fetch(`/api/v1/ledger?phone=${encodeURIComponent(userProfile.phone)}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.status === 'success' && data.entries) {
            setEntries(data.entries);
          }
          setLoading(false);
        })
        .catch((err) => {
          console.error('Error fetching ledger:', err);
          setLoading(false);
        });
    }
  };

  useEffect(() => {
    fetchLedger();
  }, [userProfile]);

  const handleAddEntry = async (e) => {
    e.preventDefault();
    if (!amount || isNaN(amount) || parseFloat(amount) <= 0) {
      alert('অনুগ্রহ করে সঠিক পরিমাণ টাকা লিখুন');
      return;
    }

    try {
      const res = await fetch('/api/v1/ledger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: userProfile.phone,
          entry_type: entryType,
          amount: parseFloat(amount),
          category: category || 'অন্যান্য',
          note: note,
          quantity: quantity ? parseFloat(quantity) : null,
          unit: unit || null,
        }),
      });

      const data = await res.json();
      if (data.status === 'success') {
        setShowAddModal(false);
        // Reset form
        setAmount('');
        setEntryType('income');
        setCategory('');
        setNote('');
        setQuantity('');
        setUnit('');
        // Re-fetch
        fetchLedger();
      } else {
        alert(data.detail || 'লেনদেন যোগ করতে ব্যর্থ হয়েছে');
      }
    } catch (err) {
      console.error('Error adding entry:', err);
    }
  };

  const openTagadaModal = (entry) => {
    setSelectedEntry(entry);
    setShowTagadaModal(true);
  };

  // Calculations
  const totalIncome = entries.filter((e) => e.type === 'income').reduce((sum, e) => sum + e.amount, 0);
  const totalExpense = entries.filter((e) => e.type === 'expense').reduce((sum, e) => sum + e.amount, 0);
  const totalEntries = entries.length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Top Financial Overview Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
        <div className="card-sharp card-sharp-accent">
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>মোট খরচ / বাকি (Total Outflow / Credit)</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-amber)', margin: '0.2rem 0' }}>
            ₹{totalExpense.toLocaleString('en-IN')}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>আপনার খাতা থেকে হিসাবকৃত</div>
        </div>

        <div className="card-sharp">
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>মোট জমা / লাভ (Collected Revenue)</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-emerald)', margin: '0.2rem 0' }}>
            ₹{totalIncome.toLocaleString('en-IN')}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
            <ArrowUpRight size={14} /> সাকসেস জমা হয়েছে
          </div>
        </div>

        <div className="card-sharp">
          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: 600 }}>মোট নিবন্ধিত লেনদেন (Total Entries)</div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-sapphire)', margin: '0.2rem 0' }}>
            {totalEntries}টি
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>সার্ভাম এআই ও ওয়েব খাতা নিবন্ধিত</div>
        </div>
      </div>

      {/* Debt Table Section */}
      <div className="card-sharp" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <BookOpen color="var(--accent-gold)" /> আপনার লেনদেনের খাতা (Active Ledger Book)
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>ভয়েস নোট বা নিচের বোতাম ব্যবহার করে নতুন লেনদেন যোগ করুন</p>
          </div>

          <button className="btn-sharp btn-primary-gold" onClick={() => setShowAddModal(true)}>
            <Plus size={16} /> নতুন লেনদেন যোগ করুন
          </button>
        </div>

        {/* Ledger Table */}
        <div style={{ overflowX: 'auto' }}>
          {loading ? (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>লোড হচ্ছে...</div>
          ) : entries.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)', border: '1px dashed var(--border-dark)', borderRadius: '6px' }}>
              কোনো লেনদেন পাওয়া যায়নি। হোয়াটসঅ্যাপে ভয়েস নোট পাঠিয়ে বা ওপরের বোতাম দিয়ে নতুন লেনদেন যুক্ত করুন।
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-dark)', color: 'var(--text-muted)', fontSize: '0.78rem' }}>
                  <th style={{ padding: '0.75rem 1rem' }}>বিবরণ / নোট</th>
                  <th style={{ padding: '0.75rem 1rem' }}>তারিখ</th>
                  <th style={{ padding: '0.75rem 1rem' }}>প্রকার</th>
                  <th style={{ padding: '0.75rem 1rem' }}>শ্রেণী</th>
                  <th style={{ padding: '0.75rem 1rem' }}>পরিমাণ</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>বাকির তাগাদা অ্যাকশন</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <tr key={entry.id} style={{ borderBottom: '1px solid var(--border-dark)' }}>
                    <td style={{ padding: '0.85rem 1rem', fontWeight: 600 }}>{entry.note || 'কোনো বিবরণ নেই'}</td>
                    <td style={{ padding: '0.85rem 1rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>{entry.date}</td>
                    <td style={{ padding: '0.85rem 1rem' }}>
                      <span className={`badge-sharp ${entry.type === 'expense' ? 'badge-amber' : 'badge-emerald'}`}>
                        {entry.type === 'expense' ? 'খরচ (Outflow)' : 'জমা (Inflow)'}
                      </span>
                    </td>
                    <td style={{ padding: '0.85rem 1rem', color: 'var(--text-muted)' }}>{entry.category}</td>
                    <td style={{ padding: '0.85rem 1rem', fontWeight: 700, color: entry.type === 'expense' ? 'var(--accent-amber)' : 'var(--accent-emerald)' }}>
                      ₹{entry.amount}
                    </td>
                    <td style={{ padding: '0.85rem 1rem', textAlign: 'right' }}>
                      {entry.type === 'expense' ? (
                        <button className="btn-sharp btn-secondary-sapphire" onClick={() => openTagadaModal(entry)} style={{ padding: '0.35rem 0.75rem', fontSize: '0.78rem' }}>
                          <Send size={13} /> তাগাদা পাঠান
                        </button>
                      ) : (
                        <span style={{ fontSize: '0.78rem', color: 'var(--accent-emerald)', display: 'inline-flex', alignItems: 'center', gap: '0.2rem' }}>
                          <CheckCircle size={14} /> সম্পূর্ণ
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Manual Entry Form Modal */}
      {showAddModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.75)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <form onSubmit={handleAddEntry} className="card-sharp" style={{ width: '450px', backgroundColor: 'var(--surface-dark)', border: '1px solid var(--accent-gold)', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-dark)', paddingBottom: '0.75rem' }}>
              <h3 style={{ fontSize: '1.1rem', color: 'var(--accent-gold)' }}>নতুন লেনদেন যুক্ত করুন</h3>
              <button type="button" onClick={() => setShowAddModal(false)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.2rem' }}>✕</button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button type="button" onClick={() => setEntryType('income')} className={`btn-sharp ${entryType === 'income' ? 'btn-primary-gold' : 'btn-outline-sharp'}`} style={{ flex: 1 }}>জমা (Inflow)</button>
                <button type="button" onClick={() => setEntryType('expense')} className={`btn-sharp ${entryType === 'expense' ? 'btn-primary-gold' : 'btn-outline-sharp'}`} style={{ flex: 1 }}>খরচ (Outflow)</button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>লেনদেনের পরিমাণ (টাকা)*</label>
                <input type="number" required placeholder="যেমন: ৫০০" value={amount} onChange={(e) => setAmount(e.target.value)} style={{ padding: '0.6rem', border: '1px solid var(--border-dark)', borderRadius: '4px', backgroundColor: '#0f172a', color: '#fff' }} />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>বিবরণ / নোট</label>
                <input type="text" placeholder="যেমন: চাল ও ডাল বিক্রি" value={note} onChange={(e) => setNote(e.target.value)} style={{ padding: '0.6rem', border: '1px solid var(--border-dark)', borderRadius: '4px', backgroundColor: '#0f172a', color: '#fff' }} />
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>লেনদেনের শ্রেণী (Category)</label>
                <input type="text" placeholder="যেমন: চাল, সবজি, হস্তশিল্প" value={category} onChange={(e) => setCategory(e.target.value)} style={{ padding: '0.6rem', border: '1px solid var(--border-dark)', borderRadius: '4px', backgroundColor: '#0f172a', color: '#fff' }} />
              </div>

              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', flex: 1 }}>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>পরিমাণ (ঐচ্ছিক)</label>
                  <input type="number" placeholder="যেমন: ১০" value={quantity} onChange={(e) => setQuantity(e.target.value)} style={{ padding: '0.6rem', border: '1px solid var(--border-dark)', borderRadius: '4px', backgroundColor: '#0f172a', color: '#fff' }} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', flex: 1 }}>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>একক (ঐচ্ছিক)</label>
                  <input type="text" placeholder="যেমন: কেজি, পিস" value={unit} onChange={(e) => setUnit(e.target.value)} style={{ padding: '0.6rem', border: '1px solid var(--border-dark)', borderRadius: '4px', backgroundColor: '#0f172a', color: '#fff' }} />
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
              <button type="button" className="btn-sharp btn-outline-sharp" onClick={() => setShowAddModal(false)} style={{ flex: 1 }}>বাতিল করুন</button>
              <button type="submit" className="btn-sharp btn-primary-gold" style={{ flex: 1 }}>সংরক্ষণ করুন</button>
            </div>
          </form>
        </div>
      )}

      {/* Baki Tagada Modal */}
      {showTagadaModal && selectedEntry && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.75)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div className="card-sharp" style={{ width: '450px', backgroundColor: 'var(--surface-dark)', border: '1px solid var(--accent-gold)', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-dark)', paddingBottom: '0.75rem' }}>
              <h3 style={{ fontSize: '1.1rem', color: 'var(--accent-gold)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Smartphone size={18} /> বাকির তাগাদা (Baki Tagada Payment Prompt)
              </h3>
              <button onClick={() => setShowTagadaModal(false)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '1.2rem' }}>✕</button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ padding: '1rem', backgroundColor: '#0f172a', borderRadius: '4px', border: '1px solid var(--border-dark)' }}>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>তাগাদা মেসেজের বিবরণ:</div>
                <div style={{ fontSize: '0.9rem', color: '#fff', whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>
                  নমস্কার ব্যবহারকারী,{'\n'}
                  আশা করি ভালো আছেন। আমাদের দোকানে আপনার বাকি টাকার পরিমাণ: *₹{selectedEntry.amount}*। অনুগ্রহ করে সুবিধাজনক সময়ে পরিশোধ করার অনুরোধ জানাচ্ছি।{'\n\n'}
                  আপনার সহযোগিতার জন্য ধন্যবাদ। 🙏
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <button type="button" className="btn-sharp btn-primary-gold" onClick={() => {
                  alert('তাগাদা মেসেজ সফলভাবে হোয়াটসঅ্যাপে পাঠানো হয়েছে!');
                  setShowTagadaModal(false);
                }}>
                  হোয়াটসঅ্যাপে তাগাদা পাঠান
                </button>
                <button type="button" className="btn-sharp btn-outline-sharp" onClick={() => setShowTagadaModal(false)}>
                  বন্ধ করুন
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
