import { NextResponse } from "next/server";
export const dynamic = "force-dynamic";

const AGENT = "http://localhost:8004";

export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  try {
    const r = await fetch(`${AGENT}/schedule/post`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    const text = await r.text();
    console.log("[schedule/post] ->", r.status, "AGENT=", AGENT, "body=", text);
    try { return NextResponse.json(JSON.parse(text), { status: r.status }); }
    catch { return new NextResponse(text, { status: r.status }); }
  } catch (e:any) {
    console.error("[schedule/post] fetch error:", e?.message);
    return NextResponse.json({ error: e?.message || "fetch failed", agent: AGENT }, { status: 502 });
  }
}
