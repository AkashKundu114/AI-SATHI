import React, { useState, useRef, useEffect, useCallback } from 'react';
import { BookOpen, ChevronDown, ChevronUp, Mic, MicOff, RefreshCw, Send, Trash2 } from 'lucide-react';

/* ─── SHG & Village Life Category Options ───────────────────── */
const VILLAGE_CATEGORIES = [
  { label: '🌾 কৃষি ও ফসল (Agriculture)', value: 'কৃষি ও ফসল' },
  { label: '🐄 পশুপালন ও দুগ্ধ (Livestock & Dairy)', value: 'পশুপালন ও দুগ্ধ' },
  { label: '🐟 মৎস্য চাষ (Pisciculture)', value: 'মৎস্য চাষ' },
  { label: '🧵 হস্তশিল্প ও পোশাক (Handicraft & Tailoring)', value: 'হস্তশিল্প ও পোশাক' },
  { label: '🏬 দোকান ও খুচরা (Grocery & Retail)', value: 'দোকান ও খুচরা' },
  { label: '👷 মজুরি ও পরিবহন (Wages & Transport)', value: 'মজুরি ও পরিবহন' },
  { label: '🏦 স্বনির্ভর দল ও কিস্তি (SHG Loan & Savings)', value: 'স্বনির্ভর দল ও কিস্তি' },
  { label: '🏠 সংসার ও পরিবার (Household Expense)', value: 'সংসার ও পরিবার' },
  { label: '📦 অন্যান্য (Others)', value: 'অন্যান্য' },
];


/* ─── Main Chat Interface Component ────────────────────────── */
export default function ChatInterface({ userProfile }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'ai',
      text: `নমস্কার ${userProfile?.name || 'ব্যবহারকারী'}! 🙏\n\nআমি আপনার AI-SATHI সহকারী। নিচে দেওয়া ৮টি লেনদেন মোডে আপনার হিসাব সহজে জমা রাখতে পারেন:\n\n১. 📈 বিক্রি/জমা  ২. 📉 খরচ/ক্রয়  ৩. 🤝 বাকিতে বিক্রি  ৪. 📥 বাকি আদায়\n৫. 🏦 ঋণ গ্রহণ  ৬. 💸 কিস্তি শোধ  ৭. 🐷 সঞ্চয় জমা  ৮. 👷 মজুরি`,
      type: 'text',
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);

  // Past ledger records tracking state
  const [ledgerEntries, setLedgerEntries] = useState([]);
  const [ledgerLoading, setLedgerLoading] = useState(false);
  const [showLedgerPanel, setShowLedgerPanel] = useState(true);

  const messagesEndRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  // Fetch past ledger entries
  const fetchPastLedger = useCallback(async () => {
    if (!userProfile?.phone) return;
    setLedgerLoading(true);
    try {
      const token = localStorage.getItem('ai_sathi_token') || '';
      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`/api/v1/ledger?phone=${encodeURIComponent(userProfile.phone)}`, { headers });
      const data = await res.json();
      if (data.status === 'success' && data.entries) {
        // Normalize entry_type to lowercase so it matches our rendering logic
        const normalized = data.entries.map(e => ({...e, type: e.type.toLowerCase()}));
        setLedgerEntries(normalized);
      }
    } catch (err) {
      console.error('Error fetching past ledger:', err);
    } finally {
      setLedgerLoading(false);
    }
  }, [userProfile]);

  useEffect(() => {
    fetchPastLedger();
  }, [fetchPastLedger]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const addMessage = useCallback((msg) => {
    setMessages((prev) => [...prev, { ...msg, id: Date.now() + Math.random(), timestamp: new Date() }]);
  }, []);

  const sendTextMessage = async (text) => {
    setIsLoading(true);
    addMessage({ sender: 'user', text, type: 'text' });

    try {
      const token = localStorage.getItem('ai_sathi_token') || '';
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        headers,
        body: JSON.stringify({ user_phone: userProfile?.phone, text }),
      });
      const data = await res.json();

      if (data.messages && data.messages.length > 0) {
        addMessage({
          sender: 'ai',
          text: data.messages[0].body,
          type: 'text',
        });
        
        // Auto-refresh ledger if it was saved
        if (data.messages[0].body.includes('সফলভাবে সংরক্ষণ')) {
          fetchPastLedger();
        }
      } else {
        addMessage({
          sender: 'ai',
          text: 'দুঃখিত, আমি উত্তর দিতে পারলাম না।',
          type: 'text',
        });
      }
    } catch (err) {
      console.error('Chat error:', err);
      addMessage({
        sender: 'ai',
        text: 'দুঃখিত, কোনো একটি সমস্যা হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।',
        type: 'text',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;
    setInput('');
    sendTextMessage(trimmed);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach((t) => t.stop());
        await processVoice(blob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Microphone access error:', err);
      addMessage({
        sender: 'ai',
        text: 'মাইক্রোফোন অ্যাক্সেস করা যায়নি। অনুগ্রহ করে ব্রাউজার পারমিশন পরীক্ষা করে আবার চেষ্টা করুন।',
        type: 'text',
      });
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processVoice = async (blob) => {
    setIsLoading(true);
    addMessage({ sender: 'user', text: '🎙️ ভয়েস বার্তা পাঠানো হচ্ছে...', type: 'text' });

    try {
      const formData = new FormData();
      formData.append('file', blob, 'recording.webm');
      formData.append('user_phone', userProfile.phone);

      const voiceRes = await fetch('/api/v1/voice', {
        method: 'POST',
        body: formData,
      });
      const voiceData = await voiceRes.json();
      const transcript = voiceData.transcript || '';

      if (transcript) {
        setMessages((prev) => {
          const updated = [...prev];
          const lastUserIdx = updated.findLastIndex((m) => m.sender === 'user');
          if (lastUserIdx >= 0) {
            updated[lastUserIdx] = { ...updated[lastUserIdx], text: `🎙️ "${transcript}"` };
          }
          return updated;
        });

        if (voiceData.messages && voiceData.messages.length > 0) {
          addMessage({
            sender: 'ai',
            text: voiceData.messages[0].body,
            type: 'text',
          });

          // Auto-refresh ledger if it was saved
          if (voiceData.messages[0].body.includes('সফলভাবে সংরক্ষণ')) {
            fetchPastLedger();
          }
        } else {
          addMessage({
            sender: 'ai',
            text: 'ভয়েস প্রক্রিয়া করা হয়েছে। কোনো লেনদেন পাওয়া যায়নি।',
            type: 'text',
          });
        }
      } else {
        addMessage({
          sender: 'ai',
          text: voiceData.messages?.[0]?.body || 'ভয়েস রেকর্ডটি ঠিকমত বোঝা যায়নি। অনুগ্রহ করে স্পষ্টভাবে আবার বলুন।',
          type: 'text',
        });
      }
    } catch (err) {
      console.error('Voice processing error:', err);
      addMessage({
        sender: 'ai',
        text: 'ভয়েস প্রক্রিয়া করতে সমস্যা হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।',
        type: 'text',
      });
    } finally {
      setIsLoading(false);
    }
  };


  // Past ledger financial totals
  const totalIncome = ledgerEntries.filter((e) => ['income', 'jama', 'recovery'].includes(e.type)).reduce((sum, e) => sum + (e.amount || 0), 0);
  const totalExpense = ledgerEntries.filter((e) => ['expense', 'khoroch', 'borrow', 'lend', 'kisti', 'wages', 'savings'].includes(e.type)).reduce((sum, e) => sum + (e.amount || 0), 0);

  const getModeBadge = (type) => {
    switch (type) {
      case 'income': return { label: 'বিক্রি/জমা', class: 'badge-sharp--emerald' };
      case 'expense': return { label: 'খরচ/ক্রয়', class: 'badge-sharp--amber' };
      case 'lend': return { label: 'ধার দেওয়া', class: 'badge-sharp--sapphire' };
      case 'recovery': return { label: 'বাকি আদায়', class: 'badge-sharp--emerald' };
      case 'borrow': return { label: 'ঋণ নেওয়া', class: 'badge-sharp--gold' };
      case 'kisti': return { label: 'কিস্তি শোধ', class: 'badge-sharp--amber' };
      case 'savings': return { label: 'সঞ্চয় জমা', class: 'badge-sharp--sapphire' };
      case 'wages': return { label: 'মজুরি', class: 'badge-sharp--gold' };
      default: return { label: type || 'লেনদেন', class: 'badge-sharp--emerald' };
    }
  };

  return (
    <div style={{ display: 'flex', flex: 1, overflow: 'hidden', height: '100%', position: 'relative' }}>
      {/* ── Main Chat Area ── */}
      <div className="chat-container" style={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* Messages List */}
        <div className="chat-messages" style={{ flex: 1, overflowY: 'auto', padding: '1.25rem' }}>
          {messages.map((msg) => (
            <div key={msg.id} className={`slide-up ${msg.sender === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}`}>
              <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{msg.text}</div>
              <div className="bubble-time">
                {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : ''}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="chat-bubble-ai slide-up">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Floating Input Bar */}
        <div className="chat-input-bar">
          <button
            type="button"
            className={`voice-btn ${isRecording ? 'recording' : ''}`}
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isLoading}
            title={isRecording ? 'রেকর্ডিং বন্ধ করুন' : 'মুখে বলতে চাপুন (Voice Record)'}
            style={{
              width: '46px',
              height: '46px',
              borderRadius: '50%',
              border: 'none',
              background: isRecording ? 'var(--color-crimson)' : 'var(--color-gold)',
              color: '#0A0F1A',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              flexShrink: 0,
              boxShadow: isRecording ? '0 0 15px var(--color-crimson)' : 'var(--shadow-glow-gold)',
            }}
          >
            {isRecording ? <MicOff size={22} color="#FFF" /> : <Mic size={22} color="#0A0F1A" />}
          </button>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="স্বনির্ভর দল, বেচা-কেনা, ধার বা কিস্তির হিসাব লিখুন..."
            disabled={isLoading || isRecording}
          />

          <button
            type="button"
            className="btn-sharp btn-sharp--primary"
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            style={{ height: '46px', width: '46px', padding: 0, borderRadius: '50%', flexShrink: 0 }}
            title="পাঠান"
          >
            <Send size={18} />
          </button>
        </div>
      </div>

      {/* ── Persistent Past Ledger Records Sidebar / Drawer Panel ── */}
      <div
        style={{
          width: showLedgerPanel ? '350px' : '48px',
          borderLeft: '1px solid var(--border-default)',
          background: 'var(--bg-secondary)',
          display: 'flex',
          flexDirection: 'column',
          transition: 'width 0.3s ease',
          zIndex: 10,
          flexShrink: 0,
        }}
      >
        {/* Header Toggle */}
        <div
          onClick={() => setShowLedgerPanel((prev) => !prev)}
          style={{
            padding: '0.85rem 1rem',
            borderBottom: '1px solid var(--border-default)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            cursor: 'pointer',
            background: 'var(--bg-surface)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BookOpen size={18} color="var(--color-gold)" />
            {showLedgerPanel && <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>হিসাবের খাতা (SHG & Past Ledger)</span>}
          </div>
          <button style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}>
            {showLedgerPanel ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </button>
        </div>

        {showLedgerPanel && (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '0.85rem' }}>
            {/* Metrics Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.85rem' }}>
              <div className="card-sharp" style={{ padding: '0.65rem', textAlign: 'center', background: 'var(--bg-surface)' }}>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 600 }}>মোট জমা (Income)</div>
                <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--color-emerald-light)' }}>
                  ₹{totalIncome.toLocaleString('en-IN')}
                </div>
              </div>

              <div className="card-sharp" style={{ padding: '0.65rem', textAlign: 'center', background: 'var(--bg-surface)' }}>
                <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 600 }}>মোট খরচ (Outflow)</div>
                <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--color-amber-light)' }}>
                  ₹{totalExpense.toLocaleString('en-IN')}
                </div>
              </div>
            </div>

            {/* Refresh Button */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: 600 }}>
                সংরক্ষিত লেনদেনসমূহ ({ledgerEntries.length})
              </span>
              <button
                className="btn-sharp btn-sharp--sm btn-sharp--ghost"
                onClick={fetchPastLedger}
                style={{ padding: '0.25rem 0.5rem' }}
                title="রিফ্রেশ করুন"
              >
                <RefreshCw size={13} className={ledgerLoading ? 'spin' : ''} />
              </button>
            </div>

            {/* Records List */}
            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
              {ledgerLoading ? (
                <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                  লোড হচ্ছে...
                </div>
              ) : ledgerEntries.length === 0 ? (
                <div style={{ padding: '1.5rem 0.75rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem', border: '1px dashed var(--border-default)', borderRadius: 'var(--radius-md)' }}>
                  এখনো কোনো স্থায়ী লেনদেন সংরক্ষণ করা হয়নি। কথা বলে বা লিখে স্থায়ীভাবে জমা করুন।
                </div>
              ) : (
                ledgerEntries.map((entry) => {
                  const badge = getModeBadge(entry.type);
                  return (
                    <div
                      key={entry.id}
                      className="card-sharp"
                      style={{
                        padding: '0.65rem 0.85rem',
                        borderLeft: `3px solid ${
                          entry.type === 'income' || entry.type === 'recovery' ? 'var(--color-emerald)' :
                          entry.type === 'lend' || entry.type === 'savings' ? 'var(--color-sapphire)' :
                          entry.type === 'borrow' || entry.type === 'wages' ? 'var(--color-gold)' : 'var(--color-amber)'
                        }`,
                        background: 'var(--bg-surface)',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div style={{ overflow: 'hidden', paddingRight: '0.5rem' }}>
                          <span className={`badge-sharp ${badge.class}`} style={{ fontSize: '0.65rem' }}>
                            {badge.label}
                          </span>
                          <div style={{ fontSize: '0.82rem', fontWeight: 600, marginTop: '0.2rem', color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {entry.note || 'বিবরণ নেই'}
                          </div>
                          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                            {entry.category} • {entry.date}
                          </div>
                        </div>

                        <div style={{ fontSize: '1rem', fontWeight: 800, color: ['income', 'recovery'].includes(entry.type) ? 'var(--color-emerald-light)' : 'var(--color-amber-light)', whiteSpace: 'nowrap' }}>
                          ₹{entry.amount?.toLocaleString('en-IN')}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
