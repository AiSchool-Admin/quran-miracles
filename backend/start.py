"""Railway startup wrapper — ensures errors are visible in deploy logs."""

import os
import sys

print("=" * 50, flush=True)
print("🚀 Starting Quran Miracles API...", flush=True)
print(f"Python: {sys.version}", flush=True)
print(f"PORT: {os.environ.get('PORT', 'not set')}", flush=True)
print("=" * 50, flush=True)

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
