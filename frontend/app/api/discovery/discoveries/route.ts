/**
 * GET /api/discovery/discoveries?tier=...
 *
 * Proxies discovery listing to the Python backend.
 */

import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams.toString();
  const url = `${BACKEND_URL}/api/discovery/discoveries${params ? `?${params}` : ""}`;

  try {
    const res = await fetch(url, {
      signal: AbortSignal.timeout(5000),
    });

    if (!res.ok) {
      return NextResponse.json(
        { discoveries: [], error: `Backend error: ${res.status}` },
        { status: res.status },
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({
      discoveries: [],
      note: "الخادم الخلفي غير متصل — لا توجد اكتشافات محفوظة حالياً.",
    });
  }
}
