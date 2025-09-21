#!/usr/bin/env python3
"""
Startup script for the Signaling Server API
"""
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "true").lower() == "true"

    print(f"Starting Signaling Server API on {host}:{port}")
    print(f"Reload mode: {reload}")
    print(f"API Documentation: http://{host}:{port}/docs")

    uvicorn.run("app.main:app", host=host, port=port, reload=reload, log_level="info")
