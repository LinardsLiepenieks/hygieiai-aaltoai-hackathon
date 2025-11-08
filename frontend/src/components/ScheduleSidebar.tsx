'use client';
import { useState } from 'react';
import useTextToSpeech from '../hooks/useTextToSpeech';

type Msg = { role: 'ai' | 'user'; text: string };

interface ScheduleSidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export default function ScheduleSidebar({
  isOpen = false,
  onClose,
}: ScheduleSidebarProps) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [status, setStatus] = useState<'idle' | 'ongoing' | 'confirmed'>(
    'idle'
  );
  const [scenario, setScenario] = useState<'dentist' | 'physio' | 'checkup'>(
    'dentist'
  );

  const { speak } = useTextToSpeech();

  // Use relative URLs to go through Caddy reverse proxy in production
  const SCHEDULE_AGENT_URL =
    typeof window !== 'undefined' && window.location.hostname !== 'localhost'
      ? '/api' // Production: use Caddy reverse proxy
      : process.env.NEXT_PUBLIC_SCHEDULE_AGENT_URL || 'http://localhost:8004'; // Dev: direct connection

  const startDemo = async () => {
    setMessages([]);
    setStatus('ongoing');
    try {
      const r = await fetch(
        `${SCHEDULE_AGENT_URL}/schedule/start?service=${encodeURIComponent(
          scenario
        )}`,
        { cache: 'no-store' }
      );
      const text = await r.text();
      if (!r.ok) throw new Error(`start ${r.status} ${text}`);
      const data = JSON.parse(text);
      setSessionId(data.session_id);
      setMessages([{ role: 'ai', text: data.reply }]);

      // Narrate the AI's first message
      if (data.reply && typeof speak === 'function') {
        speak(data.reply);
      }
    } catch (e: any) {
      setMessages([
        {
          role: 'ai',
          text: `Failed to start scheduling demo: ${e?.message || 'unknown'}`,
        },
      ]);
      setStatus('idle');
    }
  };

  const send = async () => {
    const t = input.trim();
    if (!t || !sessionId) return;
    setMessages((m) => [...m, { role: 'user', text: t }]);
    setInput('');
    try {
      const r = await fetch(`${SCHEDULE_AGENT_URL}/schedule/post`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, text: t }),
      });
      const text = await r.text();
      if (!r.ok) throw new Error(`post ${r.status} ${text}`);
      const data = JSON.parse(text);
      setMessages((m) => [...m, { role: 'ai', text: data.reply }]);

      // Narrate the AI's response
      if (data.reply && typeof speak === 'function') {
        speak(data.reply);
      }

      if (data.status === 'confirmed') {
        setStatus('confirmed');
        setTimeout(() => {
          setSessionId(null);
          setMessages([]);
          setStatus('idle');
        }, 3000);
      }
    } catch (e: any) {
      setMessages((m) => [
        ...m,
        {
          role: 'ai',
          text: `Error contacting scheduler: ${e?.message || 'unknown'}`,
        },
      ]);
    }
  };

  return (
    <aside
      className={`
        border-gray-200 bg-gradient-to-br from-blue-50 via-cyan-50 to-sky-50 
        flex flex-col gap-3 transition-all duration-300 ease-in-out overflow-hidden
        
        /* Mobile: Fixed overlay that slides in from right */
        fixed lg:relative
        top-0 right-0 h-full
        z-50 lg:z-auto
        shadow-2xl lg:shadow-none
        
        ${
          isOpen
            ? 'w-[90vw] sm:w-[360px] lg:w-[360px] p-4 border-l opacity-100 translate-x-0'
            : 'w-0 p-0 border-0 opacity-0 translate-x-full lg:translate-x-0 pointer-events-none'
        }
      `}
    >
      {/* Header row with X button, Scenario selector, and Demo Call button */}
      <div className="flex items-center justify-between gap-2">
        {/* Close button for mobile - inline with other elements */}
        {isOpen && onClose && (
          <button
            onClick={onClose}
            className="lg:hidden w-8 h-8 flex-shrink-0 flex items-center justify-center rounded-full bg-gray-200 hover:bg-gray-300 text-gray-700 transition-colors"
            aria-label="Close sidebar"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        )}

        {/* Scenario selector */}
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <label className="text-sm font-medium text-gray-700 hidden sm:block">
            Scenario
          </label>
          <select
            value={scenario}
            onChange={(e) => setScenario(e.target.value as any)}
            className="border border-gray-200 rounded-lg px-2 sm:px-3 py-1.5 text-sm text-slate-900 bg-white focus:border-blue-500 focus:outline-none flex-1 min-w-0"
            disabled={status === 'ongoing'}
            aria-label="Select scheduling scenario"
          >
            <option value="dentist">Dentist</option>
            <option value="physio">Physio</option>
            <option value="checkup">Checkup</option>
          </select>
        </div>

        {/* Demo Call button */}
        <button
          onClick={startDemo}
          disabled={status === 'ongoing'}
          className="px-3 sm:px-4 py-1.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-all font-semibold text-xs whitespace-nowrap flex-shrink-0"
          type="button"
        >
          Demo
        </button>
      </div>

      <div className="flex-1 overflow-y-auto border border-gray-200 rounded-lg p-3 bg-transparent">
        {messages.length === 0 ? (
          <div className="text-sm text-gray-500 italic">
            Press "Start demo". The assistant will message you first and keep
            asking until a time is agreed.
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`flex ${
                  m.role === 'user' ? 'justify-end' : 'justify-start'
                } animate-[fadeInScale_0.3s_ease-out]`}
              >
                <span
                  className={`inline-block px-3 py-2 rounded-lg text-sm max-w-[85%] ${
                    m.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-800'
                  }`}
                >
                  {m.text}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            status === 'ongoing' ? 'e.g., Mon 10:00' : 'Press Start demo'
          }
          className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none disabled:bg-gray-100 disabled:cursor-not-allowed"
          disabled={status !== 'ongoing'}
          onKeyDown={(e) => {
            if (e.key === 'Enter') send();
          }}
        />
        <button
          onClick={send}
          disabled={status !== 'ongoing'}
          className="px-4 py-2 rounded-lg bg-teal-500 text-white hover:bg-teal-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all font-semibold text-sm"
          type="button"
        >
          Send
        </button>
      </div>
    </aside>
  );
}
