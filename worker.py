"""
RQ Worker для фоновых задач.

Запускается отдельным процессом:
python worker.py
"""

import os
from redis import Redis
from rq import Worker, Queue, Connection
from utils.logger import setup_logger

logger = setup_logger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

if __name__ == '__main__':
    logger.info("🚀 Starting RQ Worker...")

    redis_conn = Redis.from_url(REDIS_URL)

    with Connection(redis_conn):
        worker = Worker(['default'], connection=redis_conn)
        logger.info("✅ Worker listening on 'default' queue")
        worker.work()
