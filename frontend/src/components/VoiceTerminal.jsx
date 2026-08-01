import React, { useState, useRef } from 'react';
import { Mic, MicOff, Send, ShieldCheck } from 'lucide-react';

export default function VoiceTerminal({ userProfile }) {
  const [inputText, setInputText] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [chatHistory, setChatHistory] = useState([
    {
      id: 1,
      sender: 'bot',
      text: 'নমস্কার! আমি AI-সাথী। আপনার ব্যবসার হিসাব রাখা, বাকির তাগাদা তৈরি করা, পণ্যের ক্যাটালগ ও বিজ্ঞাপন তৈরি করা, বা বাজারের দর জানতে নিচে মাইক্রোফোনে কথা বলুন বা লিখে পাঠান।',
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [loading, setLoading] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);

  const startVoiceRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await handleAudioUpload(audioBlob);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setRecordingSeconds(0);
      timerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      alert('মাইক্রোফোন এক্সেস পাওয়া যায়নি। অনুগ্রহ করে ব্রাউজার পারমিশন চেক করুন।');
    }
  };

  const stopVoiceRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      clearInterval(timerRef.current);
      setIsRecording(false);
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach((t) => t.stop());
    }
  };

  const handleAudioUpload = async (audioBlob) => {
    setLoading(true);
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.wav');
    formData.append('user_phone', userProfile?.phone || '+919876543210');

    try {
      const res = await fetch('/api/v1/voice', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();

      if (data.status === 'success') {
        const userMsg = {
          id: Date.now(),
          sender: 'user',
          text: `🎤 [ভয়েস নোট]: ${data.transcript}`,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };

        const botReplyText = data.messages?.map((m) => m.body).join('\n\n') || 'অনুরোধ প্রসেস করা হয়েছে।';
        const botMsg = {
          id: Date.now() + 1,
          sender: 'bot',
          text: botReplyText,
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        };

        setChatHistory((prev) => [...prev, userMsg, botMsg]);
      } else {
        alert(data.message || 'ভয়েস প্রসেস করতে সমস্যা হয়েছে।');
      }
    } catch (err) {
      console.error('Audio upload error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTextSubmit = async (e) => {
    e.preventDefault();
    if (!inputText.trim() || loading) return;

    const userText = inputText;
    setInputText('');
    setLoading(true);

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: userText,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setChatHistory((prev) => [...prev, userMsg]);

    try {
      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: userText,
          user_phone: userProfile?.phone || '+919876543210',
        }),
      });

      const data = await res.json();
      const botReplyText = data.messages?.map((m) => m.body).join('\n\n') || 'আপনার তথ্য প্রসেস করা হয়েছে।';

      const botMsg = {
        id: Date.now() + 1,
        sender: 'bot',
        text: botReplyText,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setChatHistory((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error('Chat error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '1rem' }}>

      {/* Messages Stream */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem', paddingRight: '0.5rem' }}>
        {chatHistory.map((msg) => (
          <div
            key={msg.id}
            style={{
              alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '85%',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.25rem',
            }}
          >
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', padding: '0 0.5rem', alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start' }}>
              {msg.sender === 'user' ? 'আপনি' : 'AI-সাথী'} • {msg.time}
            </div>
            <div
              style={{
                backgroundColor: msg.sender === 'user' ? 'var(--surface-dark)' : 'transparent',
                border: msg.sender === 'user' ? '1px solid var(--border-dark)' : 'none',
                borderRadius: msg.sender === 'user' ? '12px 12px 0 12px' : '12px 12px 12px 0',
                padding: '0.85rem 1.25rem',
              }}
            >
              <p style={{ fontSize: '0.95rem', whiteSpace: 'pre-line', color: 'var(--text-main)', lineHeight: '1.6' }}>{msg.text}</p>
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ alignSelf: 'flex-start', maxWidth: '60%' }}>
            <div className="card-sharp" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.85rem 1.25rem' }}>
              <div className="eq-container">
                <div className="eq-bar" />
                <div className="eq-bar" />
                <div className="eq-bar" />
                <div className="eq-bar" />
                <div className="eq-bar" />
              </div>
              <span style={{ fontSize: '0.85rem', color: 'var(--accent-gold)' }}>লাইভ ব্যাকএন্ড প্রসেসিং (FastAPI + Sarvam AI Pipeline)...</span>
            </div>
          </div>
        )}
      </div>

      {/* Voice Recorder & Text Input Area */}
      <div style={{ padding: '0 1rem 1.5rem', display: 'flex', flexDirection: 'column', gap: '0.75rem', backgroundColor: 'transparent' }}>
        {isRecording && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.6rem 1rem', backgroundColor: 'var(--surface-hover)', border: '1px solid var(--border-dark)', borderRadius: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div className="eq-container">
                <div className="eq-bar" />
                <div className="eq-bar" />
                <div className="eq-bar" />
                <div className="eq-bar" />
                <div className="eq-bar" />
              </div>
              <span style={{ fontSize: '0.85rem', fontWeight: 500, color: 'var(--text-main)' }}>
                রেকর্ডিং চলছে ({recordingSeconds}s)...
              </span>
            </div>

            <button className="btn-sharp" onClick={stopVoiceRecording} style={{ padding: '0.35rem 0.85rem', fontSize: '0.8rem', backgroundColor: 'var(--text-main)', color: 'var(--bg-dark)', borderRadius: '8px', border: 'none' }}>
              <MicOff size={14} /> শেষ করুন
            </button>
          </div>
        )}

        <form onSubmit={handleTextSubmit} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', backgroundColor: 'var(--surface-dark)', border: '1px solid var(--border-dark)', borderRadius: '24px', padding: '0.35rem' }}>
          <button
            type="button"
            onClick={isRecording ? stopVoiceRecording : startVoiceRecording}
            style={{ height: '40px', width: '40px', borderRadius: '50%', border: 'none', backgroundColor: isRecording ? 'var(--text-main)' : 'transparent', color: isRecording ? 'var(--bg-dark)' : 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', transition: 'all 0.2s' }}
            title="ভয়েস রেকর্ড করুন"
          >
            {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
          </button>

          <input
            type="text"
            placeholder="AI-সাথীকে কিছু বলুন..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            disabled={isRecording || loading}
            style={{
              flex: 1,
              height: '40px',
              backgroundColor: 'transparent',
              border: 'none',
              padding: '0 0.5rem',
              color: 'var(--text-main)',
              fontSize: '0.95rem',
              outline: 'none',
            }}
          />

          <button type="submit" disabled={!inputText.trim() || loading} style={{ height: '40px', width: '40px', borderRadius: '50%', border: 'none', backgroundColor: inputText.trim() ? 'var(--text-main)' : 'var(--surface-hover)', color: inputText.trim() ? 'var(--bg-dark)' : 'var(--text-dim)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: inputText.trim() ? 'pointer' : 'default', transition: 'all 0.2s' }}>
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
