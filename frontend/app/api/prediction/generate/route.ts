/**
 * POST /api/prediction/generate
 *
 * Proxies prediction requests to the Python backend.
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
    const res = await fetch(`${BACKEND_URL}/api/prediction/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(30_000),
    });

    if (!res.ok) {
      return NextResponse.json(
        { error: `Backend error: ${res.status}` },
        { status: res.status },
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      {
        error: "الخادم الخلفي غير متصل",
        predictions: [],
        research_maps: [],
        total: 0,
        disclaimer:
          "محرك التنبؤ يتطلب تشغيل الخادم الخلفي (Backend) على Railway.",
      },
      { status: 503 },
    );
  }
}
