#!/usr/bin/env python3
"""
Railway startup script - properly reads PORT from environment
"""
import os
import subprocess
import uvicorn

if __name__ == "__main__":
    # Run database migrations before starting server
    print("🔄 Running database migrations...")
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("✅ Migrations completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e}")
        print("⚠️  Continuing anyway (migrations may already be applied)")

    port = int(os.getenv("PORT", "8000"))

    print(f"🚀 Starting uvicorn on port {port}")

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        workers=1,
        log_level="info"
    )
