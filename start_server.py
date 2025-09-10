"""
Startup script for MVP Signaling Server
Simple script to start the server with proper configuration
"""

import uvicorn
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Start the signaling server"""

    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info")
    reload = os.getenv("RELOAD", "true").lower() == "true"

    logger.info(f"Starting MVP Signaling Server...")
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Log Level: {log_level}")
    logger.info(f"Reload: {reload}")
    logger.info(f"WebSocket URL: ws://{host}:{port}/ws/{{client_id}}")

    try:
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            access_log=True,
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
