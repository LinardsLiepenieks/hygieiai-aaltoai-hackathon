'use client';

import { useState } from 'react';

export default function Home() {
  const [status, setStatus] = useState<string>('');
  const [text, setText] = useState<string>('');

  const sendPost = async () => {
    setStatus('sending...');
    try {
      const res = await fetch('http://localhost:8000/post', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      const txt = await res.text();
      setStatus(txt);
    } catch (err: any) {
      setStatus('error: ' + (err?.message ?? String(err)));
    }
  };

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', padding: 24 }}>
      <h1>Next.js Frontend</h1>
      <p>Enter text and click the button to send it to the backend.</p>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={6}
        style={{ width: '100%', padding: 8, fontSize: 14 }}
        placeholder="Type some text here"
      />

      <button
        onClick={sendPost}
        style={{
          padding: '8px 16px',
          borderRadius: 6,
          border: '1px solid #222',
          background: 'white',
          cursor: 'pointer',
          marginTop: 12,
        }}
      >
        Send POST
      </button>

      <div style={{ marginTop: 12 }}>
        <strong>Result:</strong> {status}
      </div>
    </div>
  );
}
