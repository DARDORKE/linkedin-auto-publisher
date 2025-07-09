#!/usr/bin/env python3

import sys
from dotenv import load_dotenv
from loguru import logger
from src.scheduler import PostScheduler

load_dotenv()

logger.add("logs/app.log", rotation="1 week", retention="1 month")

def main():
    logger.info("Starting LinkedIn Auto Publisher")
    
    scheduler = PostScheduler()
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        scheduler.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()