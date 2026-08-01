import React, { useState, useEffect } from 'react';
import { FileText, Send, Upload, BookOpen, Sparkles, Database, CheckCircle2, Cloud } from 'lucide-react';

export default function PdfRagSubChat({ userProfile }) {
  const [selectedDoc, setSelectedDoc] = useState('');
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [ragHistory, setRagHistory] = useState([]);

  useEffect(() => {
    if (userProfile && userProfile.phone) {
      fetch(`/api/v1/storage/documents?phone=${encodeURIComponent(userProfile.phone)}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.status === 'success' && data.documents) {
            setDocuments(data.documents);
            if (data.documents.length > 0) {
              setSelectedDoc(data.documents[0].name);
            }
          }
        })
        .catch((err) => console.error('Error fetching documents:', err));
    }
  }, [userProfile]);

  const handleFileUpload = async (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const formData = new FormData();
      formData.append('file', file);
      formData.append('container', 'pdf-docs');
      if (userProfile && userProfile.phone) {
        formData.append('user_phone', userProfile.phone);
      }

      try {
        const res = await fetch('/api/v1/storage/azure_upload', {
          method: 'POST',
          body: formData,
        });
        const data = await res.json();

        const newDoc = {
          id: Date.now(),
          name: file.name,
          title: file.name.replace('.pdf', ''),
          size: `${(file.size / 1024 / 1024).toFixed(1)} MB`,
          chunks: 6,
          azureUrl: data.blob_url || `https://aisathistorage.blob.core.windows.net/pdf-docs/${file.name}`,
        };
        setDocuments([...documents, newDoc]);
        setSelectedDoc(file.name);
        alert(`'${file.name}' সফলভাবে আপলোড ও ভেক্টর RAG ইনডেক্স করা হয়েছে!`);
      } catch (err) {
        console.error('File upload error:', err);
      }
    }
  };

  const handleAskQuestion = async (e) => {
    e.preventDefault();
    if (!question.trim() || loading) return;

    const userQ = question;
    setQuestion('');
    setLoading(true);

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      question: userQ,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setRagHistory((prev) => [...prev, userMsg]);

    try {
      const res = await fetch('/api/v1/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          doc_name: selectedDoc,
          question: userQ,
          phone: userProfile ? userProfile.phone : '',
        }),
      });

      const data = await res.json();
      const r = data.result || {};

      const botReply = {
        id: Date.now() + 1,
        sender: 'bot',
        answer: r.answer || 'ডকুমেন্ট সারসংক্ষেপ পাওয়া গেছে।',
        sources: r.sources || [selectedDoc],
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setRagHistory((prev) => [...prev, botReply]);
    } catch (err) {
      console.error('RAG Query Error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '1.25rem', height: '100%' }}>
      {/* Left Column: PDF Document Library */}
      <div className="card-sharp" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div>
          <h3 style={{ fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <FileText color="var(--accent-gold)" /> PDF ডকুমেন্ট লাইব্রেরি
          </h3>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>সরকারি গ্যাজেট, ঋণ সার্কুলার ও আইনি ম্যানুয়েল (Azure Synced)</p>
        </div>

        {/* Upload Button */}
        <label className="btn-sharp btn-primary-gold" style={{ cursor: 'pointer', textAlign: 'center', width: '100%' }}>
          <Upload size={16} /> নতুন PDF আপলোড ও RAG ইনডেক্স
          <input type="file" accept=".pdf" onChange={handleFileUpload} style={{ display: 'none' }} />
        </label>

        {/* Document List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1, overflowY: 'auto' }}>
          {documents.map((doc) => {
            const isSelected = selectedDoc === doc.name;
            return (
              <div
                key={doc.id}
                onClick={() => setSelectedDoc(doc.name)}
                style={{
                  padding: '0.75rem',
                  borderRadius: 'var(--radius-sharp)',
                  backgroundColor: isSelected ? 'var(--surface-hover)' : 'var(--bg-dark)',
                  border: '1px solid',
                  borderColor: isSelected ? 'var(--accent-gold)' : 'var(--border-dark)',
                  cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                  <FileText size={16} color={isSelected ? 'var(--accent-gold)' : 'var(--text-muted)'} />
                  <span style={{ fontSize: '0.85rem', fontWeight: 600, color: isSelected ? 'var(--accent-gold)' : 'var(--text-main)' }}>
                    {doc.title}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                  <span>{doc.size} • {doc.chunks} Vector Chunks</span>
                  <span style={{ color: 'var(--accent-sapphire)', display: 'flex', alignItems: 'center', gap: '0.2rem' }}>
                    <Cloud size={10} /> Azure Blob
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Right Column: Grounded PDF RAG Sub-Chat Terminal */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', height: '100%' }}>
        {/* Top Active PDF Indicator Banner */}
        <div className="card-sharp" style={{ padding: '0.75rem 1.25rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', backgroundColor: 'var(--surface-dark)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <Database size={16} color="var(--accent-gold)" />
            <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>
              সক্রিয় ডকুমেন্ট RAG চ্যাট: <span style={{ color: 'var(--accent-gold)' }}>{selectedDoc}</span>
            </span>
          </div>

          <span className="badge-sharp badge-gold"><Sparkles size={12} /> Live Grounded RAG</span>
        </div>

        {/* Sub-Chat Stream */}
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem', paddingRight: '0.5rem' }}>
          {ragHistory.map((item) => (
            <div key={item.id} style={{ alignSelf: item.sender === 'user' ? 'flex-end' : 'flex-start', maxWidth: '85%' }}>
              <div
                className="card-sharp"
                style={{
                  backgroundColor: item.sender === 'user' ? 'var(--surface-hover)' : 'var(--surface-dark)',
                  borderColor: item.sender === 'user' ? 'var(--accent-sapphire)' : 'var(--border-dark)',
                  borderLeft: item.sender === 'bot' ? '3px solid var(--accent-gold)' : undefined,
                }}
              >
                <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginBottom: '0.35rem', display: 'flex', justifyContent: 'space-between' }}>
                  <span>{item.sender === 'user' ? 'আপনি (ডকুমেন্ট প্রশ্ন)' : 'PDF RAG অ্যানালিস্ট এআই'}</span>
                  <span>{item.time}</span>
                </div>

                <p style={{ fontSize: '0.9rem', whiteSpace: 'pre-line' }}>{item.question || item.answer}</p>

                {item.sources && (
                  <div style={{ marginTop: '0.6rem', paddingTop: '0.4rem', borderTop: '1px solid var(--border-dark)', fontSize: '0.72rem', color: 'var(--accent-gold)' }}>
                    📌 সোর্স সাইটেশন: {item.sources.join(', ')}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div style={{ alignSelf: 'flex-start', color: 'var(--accent-gold)', fontSize: '0.85rem' }}>
              🔍 পিডিএফ ডকুমেন্ট চ্যাঙ্ক সার্চ ও সারসংক্ষেপ করা হচ্ছে...
            </div>
          )}
        </div>

        {/* Input Question Bar */}
        <form onSubmit={handleAskQuestion} className="card-sharp" style={{ display: 'flex', gap: '0.75rem', padding: '0.85rem' }}>
          <input
            type="text"
            placeholder={`'${selectedDoc}' থেকে যে কোনো প্রশ্ন জিজ্ঞাসা করুন...`}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={loading}
            style={{
              flex: 1,
              height: '42px',
              backgroundColor: 'var(--bg-dark)',
              border: '1px solid var(--border-dark)',
              borderRadius: 'var(--radius-sharp)',
              padding: '0 1rem',
              color: 'var(--text-main)',
              fontSize: '0.88rem',
              outline: 'none',
            }}
          />
          <button type="submit" className="btn-sharp btn-primary-gold" disabled={!question.trim() || loading} style={{ height: '42px' }}>
            <Send size={16} /> RAG প্রশ্ন পাঠান
          </button>
        </form>
      </div>
    </div>
  );
}
