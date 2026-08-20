import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  BookOpen,
  ChevronDown,
  ChevronUp,
  Mic,
  MicOff,
  RefreshCw,
  Send,
  Sparkles,
  ArrowUpRight,
  ArrowDownRight,
  TrendingUp,
  CreditCard,
  Layers,
  CheckCircle2,
  Trash2
} from 'lucide-react';

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

/* ─── Fast Action Chips ─────────────────────────────────────── */
const ACTION_CHIPS = [
  { label: '🥟 মোমো খেয়েছি ₹৫০', query: 'momo kheyechi 50 takar' },
  { label: '🪑 চেয়ার বিক্রি ₹৬০০', query: 'beter chair bikro korechi 600 takar' },
  { label: '🤝 রিনা দি-কে ধার ₹৩০০', query: 'rina di ke 300 dhar diyechi' },
  { label: '🌾 ধান বিক্রি ₹১২০০', query: 'dhan bikri korechi 1200 takar' },
  { label: '📊 হিসাবের রিপোর্ট', query: 'রিপোর্ট' },
];

/* ─── Main Chat Interface Component ────────────────────────── */
export default function ChatInterface({ userProfile, onSessionExpired }) {
  const storageKey = `ai_sathi_chat_messages_${userProfile?.phone || 'guest'}`;

  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem(`ai_sathi_chat_messages_${userProfile?.phone || 'guest'}`);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed;
        }
      }
    } catch {
      // ignore
    }
    return [
      {
        id: 'welcome',
        sender: 'ai',
        text: `নমস্কার ${userProfile?.name || 'উদ্যোক্তা'}! 🙏\n\nআমি আপনার AI-SATHI সহকারী। আপনার আয়, ব্যয়, ধার, ঋণ বা কিস্তির হিসাব মুখে বলে বা লিখে সহজেই ডিজিটাল খাতায় সংরক্ষণ করতে পারেন।\n\nযেমন বলুন: "মোমো খেয়েছি ৫০ টাকা" বা "চেয়ার বিক্রি করেছি ৬০০ টাকা"।`,
        type: 'text',
        timestamp: new Date(),
      },
    ];
  });
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);

  useEffect(() => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(messages));
    } catch {
      // ignore
    }
  }, [messages, storageKey]);

  const clearChatHistory = () => {
    const defaultMsg = [
      {
        id: 'welcome-' + Date.now(),
        sender: 'ai',
        text: `নমস্কার ${userProfile?.name || 'উদ্যোক্তা'}! 🙏\n\nআমি আপনার AI-SATHI সহকারী। আপনার নতুন হিসাব মুখে বলে বা লিখে শুরু করুন।`,
        type: 'text',
        timestamp: new Date(),
      },
    ];
    setMessages(defaultMsg);
    try {
      localStorage.removeItem(storageKey);
    } catch {
      // ignore
    }
  };

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

      if (res.status === 401) {
        if (onSessionExpired) onSessionExpired();
        addMessage({
          sender: 'ai',
          text: '⚠️ আপনার সেশনের মেয়াদ শেষ হয়েছে। অনুগ্রহ করে আবার লগইন করুন।',
          type: 'text',
        });
        return;
      }

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
          text: 'দুঃখিত, কোনো উত্তর পাওয়া যায়নি।',
          type: 'text',
        });
      }
    } catch (err) {
      console.error('Chat error:', err);
      addMessage({
        sender: 'ai',
        text: 'দুঃখিত, সংযোগে সমস্যা হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।',
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
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        await handleAudioUpload(audioBlob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Microphone error:', err);
      alert('মাইক্রোফোন অ্যাক্সেস করতে পারা যায়নি। অনুগ্রহ করে ব্রাউজারে পারমিশন দিন।');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleAudioUpload = async (audioBlob) => {
    setIsLoading(true);
    const audioUrl = URL.createObjectURL(audioBlob);
    const pendingMsgId = Date.now() + Math.random();

    setMessages((prev) => [
      ...prev,
      {
        id: pendingMsgId,
        sender: 'user',
        text: '🎤 অডিও প্রসেসিং হচ্ছে (AI Saaras STT)...',
        type: 'audio',
        audioUrl,
        timestamp: new Date(),
      },
    ]);

    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');
      formData.append('user_phone', userProfile?.phone || '');

      const token = localStorage.getItem('ai_sathi_token') || '';
      const headers = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch('/api/v1/voice/chat', {
        method: 'POST',
        headers,
        body: formData,
      });

      if (res.status === 401) {
        if (onSessionExpired) onSessionExpired();
        return;
      }

      const voiceData = await res.json();

      if (voiceData.transcript) {
        setMessages((prev) => {
          const updated = [...prev];
          const idx = updated.findIndex((m) => m.id === pendingMsgId);
          if (idx !== -1) {
            updated[idx] = {
              ...updated[idx],
              text: `🎤 "${voiceData.transcript}"`,
            };
          }
          return updated;
        });

        if (voiceData.messages && voiceData.messages.length > 0) {
          addMessage({
            sender: 'ai',
            text: voiceData.messages[0].body,
            type: 'text',
          });

          if (voiceData.messages[0].body.includes('সফলভাবে সংরক্ষণ')) {
            fetchPastLedger();
          }
        }
      } else {
        addMessage({
          sender: 'ai',
          text: voiceData.messages?.[0]?.body || 'ভয়েস রেকর্ডটি ঠিকমত বোঝা যায়নি। অনুগ্রহ করে স্পষ্টভাবে বলুন।',
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
  const totalIncome = ledgerEntries
    .filter((e) => ['income', 'jama', 'recovery'].includes(e.type))
    .reduce((sum, e) => sum + (e.amount || 0), 0);
  const totalExpense = ledgerEntries
    .filter((e) => ['expense', 'khoroch', 'borrow', 'lend', 'kisti', 'wages', 'savings'].includes(e.type))
    .reduce((sum, e) => sum + (e.amount || 0), 0);
  const net = totalIncome - totalExpense;

  const getModeBadge = (type) => {
    switch (type) {
      case 'income':
      case 'jama':
        return { label: 'বিক্রি/জমা', badgeClass: 'badge-emerald' };
      case 'expense':
      case 'khoroch':
        return { label: 'খরচ/ক্রয়', badgeClass: 'badge-rose' };
      case 'lend':
        return { label: 'ধার দেওয়া', badgeClass: 'badge-gold' };
      case 'recovery':
        return { label: 'বাকি আদায়', badgeClass: 'badge-emerald' };
      case 'borrow':
        return { label: 'ঋণ নেওয়া', badgeClass: 'badge-sapphire' };
      case 'kisti':
        return { label: 'কিস্তি শোধ', badgeClass: 'badge-rose' };
      case 'savings':
        return { label: 'সঞ্চয় জমা', badgeClass: 'badge-gold' };
      case 'wages':
        return { label: 'মজুরি', badgeClass: 'badge-rose' };
      default:
        return { label: type || 'লেনদেন', badgeClass: 'badge-neutral' };
    }
  };

  return (
    <div style={{ display: 'flex', flex: 1, overflow: 'hidden', height: '100%', position: 'relative' }}>
      {/* ── Main Chat Column ── */}
      <div style={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        
        {/* Quick Action Chips Bar */}
        <div style={{
          padding: '0.65rem 1.5rem',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          gap: '0.5rem',
          overflowX: 'auto',
          background: 'var(--bg-canvas-subtle)',
          flexShrink: 0
        }}>
          {ACTION_CHIPS.map((chip, idx) => (
            <button
              key={idx}
              className="chip-pill"
              onClick={() => sendTextMessage(chip.query)}
              disabled={isLoading}
            >
              <span>{chip.label}</span>
            </button>
          ))}
          <button
            className="chip-pill"
            style={{ marginLeft: 'auto', opacity: 0.75 }}
            onClick={clearChatHistory}
            title="নতুন চ্যাট শুরু করুন"
          >
            <Trash2 size={12} style={{ marginRight: '4px' }} />
            <span>নতুন আলাপ</span>
          </button>
        </div>

        {/* Messages Stream */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem',
          maxWidth: '860px',
          width: '100%',
          margin: '0 auto'
        }}>
          {messages.map((msg) => (
            <div
              key={msg.id}
              style={{
                alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '82%',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.3rem'
              }}
            >
              <div
                className={msg.sender === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}
                style={{
                  padding: '0.9rem 1.15rem',
                  fontSize: '0.925rem',
                  lineHeight: 1.6,
                  whiteSpace: 'pre-wrap'
                }}
              >
                {msg.text}
              </div>
              <span style={{
                fontSize: '0.68rem',
                color: 'var(--text-muted)',
                alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                padding: '0 0.4rem'
              }}>
                {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) : ''}
              </span>
            </div>
          ))}

          {isLoading && (
            <div style={{ alignSelf: 'flex-start', maxWidth: '82%' }}>
              <div className="chat-bubble-ai" style={{ padding: '0.85rem 1.15rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Sparkles size={16} color="var(--color-gold)" />
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>AI হিসাব বিশ্লেষণ করছে...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Sleek Floating Input Bar */}
        <div style={{
          padding: '1rem 1.5rem',
          borderTop: '1px solid var(--border-subtle)',
          background: 'var(--bg-glass)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
          flexShrink: 0
        }}>
          <div style={{
            maxWidth: '860px',
            margin: '0 auto',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem'
          }}>
            {/* Microphone Button */}
            <button
              type="button"
              className={`btn-luxe ${isRecording ? 'mic-recording' : 'btn-luxe-gold'}`}
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isLoading}
              title={isRecording ? 'রেকর্ডিং বন্ধ করুন' : 'মুখে বলে হিসাব রাখুন'}
              style={{
                width: '44px',
                height: '44px',
                padding: 0,
                borderRadius: 'var(--radius-sleek)',
                flexShrink: 0
              }}
            >
              {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
            </button>

            {/* Input Field */}
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="স্বনির্ভর দল, বেচা-কেনা, ধার বা খরচের হিসাব লিখুন..."
              disabled={isLoading || isRecording}
              className="input-luxe"
              style={{ flex: 1 }}
            />

            {/* Send Button */}
            <button
              type="button"
              className="btn-luxe btn-luxe-primary"
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              style={{
                width: '44px',
                height: '44px',
                padding: 0,
                borderRadius: 'var(--radius-sleek)',
                flexShrink: 0
              }}
              title="পাঠান"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* ── Persistent Past Ledger Sidebar / Mini-Tracker ── */}
      <div
        style={{
          width: showLedgerPanel ? '360px' : '52px',
          borderLeft: '1px solid var(--border-subtle)',
          background: 'var(--bg-canvas-subtle)',
          display: 'flex',
          flexDirection: 'column',
          transition: 'width 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
          zIndex: 10,
          flexShrink: 0,
        }}
      >
        {/* Header Toggle */}
        <div
          onClick={() => setShowLedgerPanel((prev) => !prev)}
          style={{
            padding: '0.85rem 1rem',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            cursor: 'pointer',
            background: 'var(--bg-surface)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <BookOpen size={16} color="var(--color-gold)" />
            {showLedgerPanel && (
              <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                লাইভ খাতা (Live Ledger)
              </span>
            )}
          </div>
          <button style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', display: 'flex' }}>
            {showLedgerPanel ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>

        {showLedgerPanel && (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '0.85rem' }}>
            {/* Quick Metrics */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.85rem' }}>
              <div className="glass-card-sharp" style={{ padding: '0.65rem', textAlign: 'center', borderLeft: '2px solid var(--color-emerald)' }}>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>মোট জমা (Income)</div>
                <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--color-emerald-light)', marginTop: '0.15rem' }}>
                  ₹{totalIncome.toLocaleString('en-IN')}
                </div>
              </div>

              <div className="glass-card-sharp" style={{ padding: '0.65rem', textAlign: 'center', borderLeft: '2px solid var(--color-rose)' }}>
                <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>মোট খরচ (Outflow)</div>
                <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--color-rose-light)', marginTop: '0.15rem' }}>
                  ₹{totalExpense.toLocaleString('en-IN')}
                </div>
              </div>
            </div>

            {/* List Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                হালনাগাদ লেনদেন ({ledgerEntries.length})
              </span>
              <button
                className="btn-luxe btn-luxe-outline"
                onClick={fetchPastLedger}
                style={{ padding: '0.25rem 0.45rem', height: '24px' }}
                title="রিফ্রেশ করুন"
              >
                <RefreshCw size={12} className={ledgerLoading ? 'spin' : ''} />
              </button>
            </div>

            {/* Records List */}
            <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
              {ledgerLoading ? (
                <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                  লোড হচ্ছে...
                </div>
              ) : ledgerEntries.length === 0 ? (
                <div style={{
                  padding: '2rem 1rem',
                  textAlign: 'center',
                  color: 'var(--text-muted)',
                  fontSize: '0.8rem',
                  border: '1px dashed var(--border-subtle)',
                  borderRadius: 'var(--radius-sleek)'
                }}>
                  এখনো কোনো স্থায়ী লেনদেন সংরক্ষণ করা হয়নি।
                </div>
              ) : (
                ledgerEntries.map((entry) => {
                  const badge = getModeBadge(entry.type);
                  const isPositive = ['income', 'jama', 'recovery'].includes(entry.type);
                  return (
                    <div
                      key={entry.id}
                      className="glass-card-sharp"
                      style={{
                        padding: '0.65rem 0.85rem',
                        borderLeft: `3px solid ${isPositive ? 'var(--color-emerald)' : 'var(--color-rose)'}`,
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div style={{ overflow: 'hidden', paddingRight: '0.5rem' }}>
                          <span className={`badge-luxe ${badge.badgeClass}`} style={{ fontSize: '0.65rem' }}>
                            {badge.label}
                          </span>
                          <div style={{ fontSize: '0.825rem', fontWeight: 600, marginTop: '0.2rem', color: 'var(--text-primary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {entry.note || 'বিবরণ নেই'}
                          </div>
                          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                            {entry.category} • {entry.date}
                          </div>
                        </div>

                        <div style={{
                          fontSize: '0.95rem',
                          fontWeight: 800,
                          fontFamily: 'var(--font-display)',
                          color: isPositive ? 'var(--color-emerald-light)' : 'var(--color-rose-light)',
                          whiteSpace: 'nowrap'
                        }}>
                          {isPositive ? '+' : '-'}₹{entry.amount?.toLocaleString('en-IN')}
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

