"""Railway startup wrapper — bootstrap DB then start uvicorn.

1. Run database bootstrap (apply schema + load Quran data if needed)
2. Start uvicorn with the FastAPI app
"""

import asyncio
import os
import sys

print("=" * 50, flush=True)
print("🚀 Starting Quran Miracles API...", flush=True)
print(f"Python: {sys.version}", flush=True)
print(f"PORT: {os.environ.get('PORT', 'not set')}", flush=True)
print(f"DATABASE_URL: {'set' if os.environ.get('DATABASE_URL') else 'NOT SET'}", flush=True)
print(f"ANTHROPIC_API_KEY: {'set' if os.environ.get('ANTHROPIC_API_KEY') else 'NOT SET'}", flush=True)
print("=" * 50, flush=True)

# ── Step 1: Bootstrap database ──
try:
    from bootstrap_db import bootstrap

    print("\n📋 Running database bootstrap...", flush=True)
    db_ready = asyncio.run(bootstrap())
    if db_ready:
        print("✅ Database ready\n", flush=True)
    else:
        print("⚠️ Database not available — API will use fallback mode\n", flush=True)
except Exception as exc:
    print(f"⚠️ Bootstrap skipped: {exc}\n", flush=True)

# ── Step 2: Start uvicorn ──
try:
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    print(f"✅ Starting uvicorn on port {port}", flush=True)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
except Exception as exc:
    print(f"❌ FATAL: {exc}", flush=True)
    import traceback

    traceback.print_exc()
    sys.exit(1)
