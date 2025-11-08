import { NextResponse } from 'next/server';
export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const AGENT =
  process.env.NEXT_PUBLIC_SCHEDULE_AGENT_URL || 'http://localhost:8004';

export async function GET(req: Request) {
  const url = new URL(req.url);
  const service = url.searchParams.get('service');
  const target = `${AGENT}/schedule/start${
    service ? `?service=${encodeURIComponent(service)}` : ''
  }`;
  try {
    const r = await fetch(target, { cache: 'no-store' });
    const text = await r.text();
    try {
      return NextResponse.json(JSON.parse(text), { status: r.status });
    } catch {
      return new NextResponse(text, { status: r.status });
    }
  } catch (e: any) {
    return NextResponse.json(
      { error: e?.message || 'fetch failed', agent: target },
      { status: 502 }
    );
  }
}
