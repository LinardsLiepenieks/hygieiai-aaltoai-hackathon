"use client";

import { useState } from "react";

type Msg = { role: "ai" | "user"; text: string };

export default function ScheduleSidebar() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<"idle" | "ongoing" | "confirmed">("idle");

  const startDemo = async () => {
    setMessages([]);
    setStatus("ongoing");
    try {
      const r = await fetch(`http://localhost:8004/schedule/start`, { cache: "no-store" });
      if (!r.ok) throw new Error(String(r.status));
      const data = await r.json();
      setSessionId(data.session_id);
      setMessages([{ role: "ai", text: data.reply }]);
    } catch {
      setMessages([{ role: "ai", text: "Failed to start scheduling demo." }]);
      setStatus("idle");
    }
  };

  const send = async () => {
    const t = input.trim();
    if (!t || !sessionId) return;
    setMessages((m) => [...m, { role: "user", text: t }]);
    setInput("");
    try {
      const r = await fetch(`http://localhost:8004/schedule/post`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, text: t }),
      });
      if (!r.ok) throw new Error(String(r.status));
      const data = await r.json();
      setMessages((m) => [...m, { role: "ai", text: data.reply }]);
      if (data.status === "confirmed") {
        setStatus("confirmed");
        setTimeout(() => {
          setSessionId(null);
          setMessages([]);
          setStatus("idle");
        }, 3000);
      }
    } catch {
      setMessages((m) => [...m, { role: "ai", text: "Error contacting scheduler." }]);
    }
  };

  return (
    <aside className="w-[360px] border-l border-gray-200 p-3 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <h3 className="m-0 text-base font-semibold">Scheduling demo</h3>
        <button
          onClick={startDemo}
          disabled={status === "ongoing"}
          className="px-3 py-1.5 rounded-md border bg-blue-600 text-white disabled:opacity-50"
          type="button"
        >
          Start demo
        </button>
      </div>

      <div className="flex-1 overflow-y-auto border border-gray-100 rounded-md p-2 bg-gray-50 text-sm">
        {messages.length === 0 ? (
          <div className="text-gray-500">
            Press “Start demo”. The assistant will message you first and keep asking until a time is agreed.
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={`my-1 ${m.role === "user" ? "text-right" : "text-left"}`}>
              <span
                className={`inline-block px-2.5 py-1.5 rounded-md ${
                  m.role === "user" ? "bg-blue-100" : "bg-gray-200"
                }`}
              >
                {m.text}
              </span>
            </div>
          ))
        )}
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={status === "ongoing" ? "e.g., Mon 10:00 dentist" : "Press Start demo"}
          className="flex-1 border rounded-md px-2 py-1.5"
          disabled={status !== "ongoing"}
          onKeyDown={(e) => {
            if (e.key === "Enter") send();
          }}
        />
        <button
          onClick={send}
          disabled={status !== "ongoing"}
          className="px-3 py-1.5 rounded-md border bg-white disabled:opacity-50"
          type="button"
        >
          Send
        </button>
      </div>
    </aside>
  );
}
