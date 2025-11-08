'use client';

import { useState } from 'react';
import useRecording from '../hooks/useRecording';
import useTextToSpeech from '../hooks/useTextToSpeech';

export default function Home() {
  const [text, setText] = useState<string>('');
  const {
    status,
    isRecording,
    preventDefault,
    toggleRecording,
    hasApiKey,
    setStatus,
  } = useRecording(setText);

  const sendPost = async () => {
    if (!text.trim()) return;
    setStatus('Sending to backend…');
    try {
      const res = await fetch('http://localhost:8000/post', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text.trim() }),
      });
      const msg = await res.text();
      setStatus('Sent: ' + msg);
      try {
        // Narrate the backend response if TTS is available
        if (msg && typeof speak === 'function') {
          speak(msg);
        }
      } catch (ttsErr) {
        // Don't let TTS errors break the main flow; just update status
        setStatus((s) => s + ' • TTS Error');
        // eslint-disable-next-line no-console
        console.error('TTS error:', ttsErr);
      }
    } catch (err: any) {
      setStatus('Error: ' + err.message);
    }
  };

  const {
    speak,
    stop: stopTTS,
    status: ttsStatus,
    isPlaying: ttsPlaying,
    hasApiKey: ttsHasKey,
  } = useTextToSpeech();

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-white/90 backdrop-blur-sm rounded-3xl shadow-2xl border border-white/20 overflow-hidden">
        <div className="bg-gradient-to-r from-indigo-600 to-purple-700 text-white p-8 text-center">
          <h1 className="text-4xl font-bold mb-2">ElevenLabs Scribe</h1>
          <p className="text-indigo-100">
            Tap mic to speak • Tap again to stop
          </p>
        </div>

        <div className="bg-gradient-to-r from-indigo-100 to-purple-100 text-indigo-800 px-6 py-4 font-semibold text-center">
          {status}
        </div>

        <div className="p-6">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={8}
            className="w-full p-5 text-lg text-black bg-white/80 border-2 border-indigo-200 rounded-2xl focus:border-indigo-500 focus:outline-none resize-none transition-all shadow-inner"
            placeholder="Your transcription appears here..."
          />
        </div>

        <div className="px-6 pb-8 flex flex-col sm:flex-row gap-4">
          <button
            onClick={toggleRecording}
            onContextMenu={preventDefault}
            className={`flex-1 py-6 rounded-3xl font-bold text-xl transition-all transform active:scale-95 shadow-xl ${
              isRecording
                ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse'
                : 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white hover:from-indigo-700 hover:to-purple-700'
            } disabled:bg-gray-400 disabled:cursor-not-allowed`}
            disabled={!hasApiKey}
          >
            {isRecording ? (
              <span className="flex items-center justify-center gap-3">
                <span className="w-4 h-4 bg-white rounded-full animate-bounce"></span>
                Recording… Tap to Stop
              </span>
            ) : (
              'Tap to Speak'
            )}
          </button>

          <button
            onClick={() => speak(text)}
            disabled={!text.trim() || !ttsHasKey}
            className="flex-none px-5 py-4 rounded-3xl font-semibold text-lg bg-gradient-to-r from-yellow-400 to-amber-500 text-white shadow hover:shadow-md disabled:from-gray-300 disabled:cursor-not-allowed transition-all"
            title={ttsStatus}
          >
            {ttsPlaying ? 'Reading…' : 'Read Text'}
          </button>

          <button
            onClick={sendPost}
            disabled={!text.trim()}
            className="flex-1 py-6 rounded-3xl font-bold text-xl bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-xl hover:shadow-2xl disabled:from-gray-400 disabled:cursor-not-allowed transition-all transform active:scale-95"
          >
            Send to Backend
          </button>
        </div>

        <div className="bg-gray-50/80 px-6 py-5 text-sm text-gray-600 border-t text-center">
          <strong>Tap-to-talk • Works everywhere</strong>
          <br />
          Mobile & Desktop • Chrome • Safari • Firefox
          <br />
          <span className="text-xs text-gray-500 mt-2 block">
            Now with reliable tap-to-record • No hold required
          </span>
        </div>
      </div>
    </div>
  );
}
