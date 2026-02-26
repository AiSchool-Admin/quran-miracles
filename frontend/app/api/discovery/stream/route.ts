/**
 * POST /api/discovery/stream
 *
 * Proxies the SSE discovery stream to the Python backend.
 * Returns a clear error message when the backend is unavailable.
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  let body: Record<string, unknown>;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  try {
    const res = await fetch(`${BACKEND_URL}/api/discovery/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(60_000),
    });

    if (!res.ok) {
      return NextResponse.json(
        { error: `Backend error: ${res.status}` },
        { status: res.status },
      );
    }

    // Forward the SSE stream as-is
    return new Response(res.body, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch {
    // Return a single SSE event with error info
    const errorEvent = [
      `data: ${JSON.stringify({
        stage: "error",
        message:
          "الخادم الخلفي غير متصل. تأكد من تشغيل Backend على Railway " +
          "وتعيين متغير BACKEND_URL في إعدادات Vercel.",
      })}`,
      "",
      "",
    ].join("\n");

    return new Response(errorEvent, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
      },
    });
  }
}
