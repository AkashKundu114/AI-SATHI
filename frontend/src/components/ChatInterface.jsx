import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Mic, MicOff, Send, Check, X, BookOpen, ArrowUpRight, ArrowDownRight, RefreshCw, ChevronDown, ChevronUp, Edit3, HandCoins, Building2, PiggyBank, Receipt, HardHat, TrendingDown, TrendingUp } from 'lucide-react';

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

/* ─── 8 Rich Village Transaction Modes ──────────────────────── */
const TRANSACTION_MODES = [
  { id: 'income', label: '📈 জমা / বিক্রি', icon: ArrowUpRight, styleClass: 'btn-sharp--success' },
  { id: 'expense', label: '📉 খরচ / ক্রয়', icon: ArrowDownRight, styleClass: 'btn-sharp--danger' },
  { id: 'lend', label: '🤝 বাকিতে বিক্রি / ধার', icon: HandCoins, styleClass: 'btn-sharp--primary' },
  { id: 'recovery', label: '📥 বাকি আদায় / ফেরত', icon: TrendingUp, styleClass: 'btn-sharp--success' },
  { id: 'borrow', label: '🏦 ঋণ নেওয়া (Loan)', icon: Building2, styleClass: 'btn-sharp--accent' },
  { id: 'kisti', label: '💸 কিস্তি শোধ (Kisti)', icon: Receipt, styleClass: 'btn-sharp--warning' },
  { id: 'savings', label: '🐷 সঞ্চয় জমা (Savings)', icon: PiggyBank, styleClass: 'btn-sharp--primary' },
  { id: 'wages', label: '👷 মজুরি (Wages)', icon: HardHat, styleClass: 'btn-sharp--ghost' },
];

/* ─── Editable Confirmation Card Component ─────────────────── */
function EditableConfirmationCard({ initialEntries, onConfirm, onReject }) {
  const [entries, setEntries] = useState(initialEntries || []);

  const updateEntry = (index, field, value) => {
    setEntries((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const totalAmount = entries.reduce((sum, e) => sum + (parseFloat(e.amount) || 0), 0);

  return (
    <div className="confirmation-card" style={{ maxWidth: '540px', width: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', paddingBottom: '0.5rem', borderBottom: '1px solid var(--border-subtle)' }}>
        <Edit3 size={18} color="var(--color-gold)" />
        <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
          যাচাই ও সম্পাদন করুন (Review & Edit Entry)
        </span>
      </div>

      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
        নিচের লেনদেনের সঠিক ধরন বা মোড বেছে নিয়ে **সংরক্ষণ করুন**:
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', marginBottom: '1rem' }}>
        {entries.map((entry, idx) => (
          <div key={idx} className="card-sharp" style={{ padding: '0.9rem 1rem', background: 'var(--bg-surface-raised)', border: '1px solid var(--border-strong)' }}>
            
            {/* Entry Type Selector Grid (8 Transaction Modes) */}
            <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.35rem', fontWeight: 600 }}>
              লেনদেনের সঠিক ধরন (Transaction Mode)*
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.35rem', marginBottom: '0.75rem' }}>
              {TRANSACTION_MODES.map((mode) => {
                const IconComponent = mode.icon;
                const isSelected = entry.entry_type === mode.id;
                return (
                  <button
                    key={mode.id}
                    type="button"
                    className={`btn-sharp btn-sharp--sm ${isSelected ? mode.styleClass : 'btn-sharp--ghost'}`}
                    onClick={() => updateEntry(idx, 'entry_type', mode.id)}
                    style={{ fontSize: '0.75rem', padding: '0.4rem 0.5rem', justifyContent: 'flex-start' }}
                  >
                    <IconComponent size={13} /> {mode.label}
                  </button>
                );
              })}
            </div>

            {/* Amount & Category Inputs */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.58rem' }}>
              <div>
                <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.2rem' }}>
                  পরিমাণ (টাকা)*
                </label>
                <input
                  type="number"
                  value={entry.amount || ''}
                  onChange={(e) => updateEntry(idx, 'amount', parseFloat(e.target.value) || 0)}
                  style={{
                    width: '100%',
                    padding: '0.45rem 0.65rem',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-default)',
                    background: 'var(--bg-primary)',
                    color: 'var(--text-primary)',
                    fontSize: '0.9rem',
                    fontWeight: 700,
                  }}
                />
              </div>

              <div>
                <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.2rem' }}>
                  বিভাগ (Category)
                </label>
                <select
                  value={entry.category || 'অন্যান্য'}
                  onChange={(e) => updateEntry(idx, 'category', e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.45rem 0.65rem',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-default)',
                    background: 'var(--bg-primary)',
                    color: 'var(--text-primary)',
                    fontSize: '0.8rem',
                  }}
                >
                  {VILLAGE_CATEGORIES.map((cat) => (
                    <option key={cat.value} value={cat.value}>{cat.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Note & Description Input */}
            <div>
              <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.2rem' }}>
                বিবরণ / কথা (Notes/Details)
              </label>
              <input
                type="text"
                value={entry.note || ''}
                placeholder="যেমন: রীনা দি কে ৫০ টাকা ধার দেওয়া হলো"
                onChange={(e) => updateEntry(idx, 'note', e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.45rem 0.65rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-default)',
                  background: 'var(--bg-primary)',
                  color: 'var(--text-primary)',
                  fontSize: '0.85rem',
                }}
              />
            </div>
          </div>
        ))}
      </div>

      {entries.length > 1 && (
        <div style={{ textAlign: 'right', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem', fontWeight: 700 }}>
          সর্বমোট পরিমাণ: ₹{totalAmount.toLocaleString('en-IN')}
        </div>
      )}

      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: '0.65rem' }}>
        <button
          type="button"
          className="btn-sharp btn-sharp--primary"
          onClick={() => onConfirm(entries)}
          style={{ flex: 1, padding: '0.65rem 1rem' }}
        >
          <Check size={16} /> নিশ্চিত করে সংরক্ষণ করুন
        </button>
        <button
          type="button"
          className="btn-sharp btn-sharp--ghost"
          onClick={onReject}
          style={{ flex: 1, padding: '0.65rem 1rem' }}
        >
          <X size={16} /> বাতিল করুন
        </button>
      </div>
    </div>
  );
}

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
      const res = await fetch(`/api/v1/ledger?phone=${encodeURIComponent(userProfile.phone)}`);
      const data = await res.json();
      if (data.status === 'success' && data.entries) {
        setLedgerEntries(data.entries);
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

  const parseText = async (text) => {
    setIsLoading(true);
    addMessage({ sender: 'user', text, type: 'text' });

    try {
      const res = await fetch('/api/v1/chat/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_phone: userProfile.phone, text }),
      });
      const data = await res.json();

      if (data.parsed_entries && data.parsed_entries.length > 0) {
        const confirmMsgId = Date.now() + Math.random();
        setMessages((prev) => [
          ...prev,
          {
            id: confirmMsgId,
            sender: 'ai',
            text: data.ai_message || 'আপনার বার্তা থেকে এই লেনদেনগুলো চিহ্নিত করা হয়েছে:',
            type: 'confirmation',
            entries: data.parsed_entries,
            timestamp: new Date(),
          },
        ]);
      } else {
        addMessage({
          sender: 'ai',
          text: data.ai_message || 'আপনার বার্তাটি প্রক্রিয়া করা হয়েছে। কোনো নতুন লেনদেন চিহ্নিত করা যায়নি।',
          type: 'text',
        });
      }
    } catch (err) {
      console.error('Parse error:', err);
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
    parseText(trimmed);
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

        const parseRes = await fetch('/api/v1/chat/parse', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_phone: userProfile.phone, text: transcript }),
        });
        const parseData = await parseRes.json();

        if (parseData.parsed_entries && parseData.parsed_entries.length > 0) {
          const confirmMsgId = Date.now() + Math.random();
          setMessages((prev) => [
            ...prev,
            {
              id: confirmMsgId,
              sender: 'ai',
              text: parseData.ai_message || 'ভয়েস নোট থেকে এই লেনদেন চিহ্নিত করা হয়েছে:',
              type: 'confirmation',
              entries: parseData.parsed_entries,
              timestamp: new Date(),
            },
          ]);
        } else {
          addMessage({
            sender: 'ai',
            text: parseData.ai_message || voiceData.messages?.[0]?.body || 'ভয়েস প্রক্রিয়া করা হয়েছে। কোনো লেনদেন পাওয়া যায়নি।',
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

  const handleConfirm = async (msgId, updatedEntries) => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/v1/ledger/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: userProfile.phone, entries: updatedEntries }),
      });
      const data = await res.json();

      setMessages((prev) =>
        prev.map((m) =>
          m.id === msgId
            ? {
                ...m,
                type: 'text',
                text: `✅ ${data.saved_count || updatedEntries.length}টি লেনদেন সফলভাবে আপনার খাতায় স্থায়ীভাবে সংরক্ষণ করা হয়েছে!`,
                entries: undefined,
              }
            : m
        )
      );

      fetchPastLedger();
    } catch (err) {
      console.error('Confirm error:', err);
      addMessage({ sender: 'ai', text: 'তথ্য সংরক্ষণ করতে সমস্যা হয়েছে। আবার চেষ্টা করুন।', type: 'text' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleReject = (msgId) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === msgId
          ? { ...m, type: 'text', text: '❌ লেনদেন বাতিল করা হয়েছে। আবার স্পষ্টভাবে বলুন বা লিখুন।', entries: undefined }
          : m
      )
    );
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
              {msg.type === 'confirmation' && msg.entries ? (
                <>
                  <div style={{ marginBottom: '0.75rem', fontSize: '0.9rem', fontWeight: 600 }}>{msg.text}</div>
                  <EditableConfirmationCard
                    initialEntries={msg.entries}
                    onConfirm={(modified) => handleConfirm(msg.id, modified)}
                    onReject={() => handleReject(msg.id)}
                  />
                </>
              ) : (
                <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{msg.text}</div>
              )}
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
