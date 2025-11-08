"use client";
import { useState } from "react";

type Msg = { role: "ai" | "user"; text: string };

export default function ScheduleSidebar() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState<"idle" | "ongoing" | "confirmed">("idle");
  const [scenario, setScenario] = useState<"dentist" | "physio" | "checkup">("dentist");

  const startDemo = async () => {
    setMessages([]);
    setStatus("ongoing");
    try {
      const r = await fetch(`http://localhost:8004/schedule/start?service=${encodeURIComponent(scenario)}`, { cache: "no-store" });
      const text = await r.text();
      if (!r.ok) throw new Error(`start ${r.status} ${text}`);
      const data = JSON.parse(text);
      setSessionId(data.session_id);
      setMessages([{ role: "ai", text: data.reply }]);
    } catch (e:any) {
      setMessages([{ role: "ai", text: `Failed to start scheduling demo: ${e?.message || "unknown"}` }]);
      setStatus("idle");
    }
  };

  const send = async () => {
    const t = input.trim();
    if (!t || !sessionId) return;
    setMessages(m => [...m, { role: "user", text: t }]);
    setInput("");
    try {
      const r = await fetch(`http://localhost:8004/schedule/post`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, text: t }),
      });
      const text = await r.text();
      if (!r.ok) throw new Error(`post ${r.status} ${text}`);
      const data = JSON.parse(text);
      setMessages(m => [...m, { role: "ai", text: data.reply }]);
      if (data.status === "confirmed") {
        setStatus("confirmed");
        setTimeout(() => { setSessionId(null); setMessages([]); setStatus("idle"); }, 3000);
      }
    } catch (e:any) {
      setMessages(m => [...m, { role: "ai", text: `Error contacting scheduler: ${e?.message || "unknown"}` }]);
    }
  };

  return (
    <aside className="w-[360px] border-l border-gray-200 p-3 flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Scenario</label>
          <select
            value={scenario}
            onChange={(e) => setScenario(e.target.value as any)}
            className="border rounded-md px-2 py-1 text-sm"
            disabled={status === "ongoing"}
            aria-label="Select scheduling scenario"
          >
            <option value="dentist">Dentist</option>
            <option value="physio">Physio</option>
            <option value="checkup">General checkup</option>
          </select>
        </div>
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
          <div className="text-gray-500">Press “Start demo”. The assistant will message you first and keep asking until a time is agreed.</div>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={`my-1 ${m.role === "user" ? "text-right" : "text-left"}`}>
              <span className={`inline-block px-2.5 py-1.5 rounded-md ${m.role === "user" ? "bg-blue-100" : "bg-gray-200"}`}>
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
          placeholder={status === "ongoing" ? "e.g., Mon 10:00" : "Press Start demo"}
          className="flex-1 border rounded-md px-2 py-1.5"
          disabled={status !== "ongoing"}
          onKeyDown={(e) => { if (e.key === "Enter") send(); }}
        />
        <button onClick={send} disabled={status !== "ongoing"} className="px-3 py-1.5 rounded-md border bg-white disabled:opacity-50" type="button">
          Send
        </button>
      </div>
    </aside>
  );
}
