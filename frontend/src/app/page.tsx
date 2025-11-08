'use client';

import { useState } from 'react';
import useRecording from '../hooks/useRecording';
import useTextToSpeech from '../hooks/useTextToSpeech';
import ScheduleSidebar from '@/components/ScheduleSidebar';
import Navbar from '@/components/Navbar';
import ChatHistory, { ChatMessage } from '@/components/ChatHistory';

export default function Home() {
  const [text, setText] = useState<string>('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(false);

  const {
    status,
    isRecording,
    preventDefault,
    toggleRecording,
    hasApiKey,
    setStatus,
  } = useRecording(setText);

  const {
    speak,
    stop: stopTTS,
    status: ttsStatus,
    isPlaying: ttsPlaying,
    hasApiKey: ttsHasKey,
  } = useTextToSpeech();

  const sendPost = async () => {
    if (!text.trim()) return;

    // Add user message to chat history
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      text: text.trim(),
      sender: 'user',
      timestamp: new Date(),
    };
    setChatHistory((prev) => [...prev, userMessage]);

    setStatus('Thinking');
    const userText = text.trim();
    setText(''); // Clear input after sending

    const BACKEND_URL =
      process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

    try {
      const res = await fetch(`${BACKEND_URL}/post`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: userText }),
      });
      const msg = await res.text();
      setStatus('Sent: ' + msg);

      // Add AI response to chat history
      const aiMessage: ChatMessage = {
        id: `ai-${Date.now()}`,
        text: msg,
        sender: 'ai',
        timestamp: new Date(),
      };
      setChatHistory((prev) => [...prev, aiMessage]);

      try {
        if (msg && typeof speak === 'function') speak(msg);
      } catch (ttsErr) {
        setStatus((s) => s + ' • TTS Error');
        console.error('TTS error:', ttsErr);
      }
    } catch (err: any) {
      setStatus('Error: ' + err.message);
    }
  };

  return (
    <div className="relative flex h-screen">
      {/* Left: your existing UI with navbar */}
      <div className="flex-1 min-w-0 flex flex-col">
        {/* Navbar */}
        <Navbar
          onCallClick={() => setIsSidebarOpen(!isSidebarOpen)}
          hasNotification={!isSidebarOpen}
        />

        {/* Main Content */}
        <div className="flex-1 overflow-auto bg-gradient-to-br from-blue-50 via-cyan-50 to-sky-50">
          <div className="max-w-4xl mx-auto px-4 py-6 flex flex-col h-full">
            {/* Header */}
            <div className="mb-4">
              <h1 className="text-2xl font-bold text-gray-800 mb-1">
                You're talking with Jesse
              </h1>
              <p className="text-sm text-gray-500">
                Tap mic to speak • Tap again to stop
              </p>
            </div>

            {/* Status */}
            <div className="mb-4">
              <p className="text-sm italic text-gray-600">{status}</p>
            </div>

            {/* Chat History */}
            <ChatHistory messages={chatHistory} />

            {/* Textarea - 2 lines, above buttons */}
            <div className="mb-3">
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={2}
                className="w-full p-3 text-base text-gray-800 bg-white border border-gray-200 rounded-lg focus:border-blue-500 focus:outline-none resize-none"
                placeholder="Your transcription appears here..."
              />
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={toggleRecording}
                onContextMenu={preventDefault}
                className={`flex-1 py-3 rounded-lg font-semibold text-base transition-all ${
                  isRecording
                    ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                } disabled:bg-gray-400 disabled:cursor-not-allowed`}
                disabled={!hasApiKey}
              >
                {isRecording ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="w-2 h-2 bg-white rounded-full animate-bounce"></span>
                    Recording… Tap to Stop
                  </span>
                ) : (
                  'Tap to Speak'
                )}
              </button>

              <button
                onClick={() => speak(text)}
                disabled={!text.trim() || !ttsHasKey}
                className="flex-none px-4 py-3 rounded-lg font-semibold text-base bg-sky-500 text-white hover:bg-sky-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all"
                title={ttsStatus}
              >
                {ttsPlaying ? 'Reading…' : 'Read Text'}
              </button>

              <button
                onClick={sendPost}
                disabled={!text.trim()}
                className="flex-1 py-3 rounded-lg font-semibold text-base bg-teal-500 text-white hover:bg-teal-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-all"
              >
                Send
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Overlay backdrop for mobile */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black z-40 lg:hidden transition-opacity duration-300 ease-in-out opacity-70"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Right: scheduling sidebar - overlay on mobile, side-by-side on desktop */}
      <ScheduleSidebar
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />
    </div>
  );
}
