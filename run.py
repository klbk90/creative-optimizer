#!/usr/bin/env python3
"""
Railway startup script - properly reads PORT from environment
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))

    print(f"🚀 Starting uvicorn on port {port}")

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        workers=1,
        log_level="info"
    )
