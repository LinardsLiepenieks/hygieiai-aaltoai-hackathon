import { NextResponse } from "next/server";
export const dynamic = "force-dynamic";

const AGENT = process.env.SCHEDULE_AGENT_URL || "http://schedule_agent:8004";

export async function GET() {
  try {
    const r = await fetch(`${AGENT}/schedule/start`, { cache: "no-store" });
    const text = await r.text();
    // log everything server-side
    console.log("[schedule/start] ->", r.status, "AGENT=", AGENT, "body=", text);
    try { return NextResponse.json(JSON.parse(text), { status: r.status }); }
    catch { return new NextResponse(text, { status: r.status }); }
  } catch (e:any) {
    console.error("[schedule/start] fetch error:", e?.message);
    return NextResponse.json({ error: e?.message || "fetch failed", agent: AGENT }, { status: 502 });
  }
}
