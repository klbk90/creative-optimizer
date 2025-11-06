"""
Task queue wrapper (RQ) for background jobs.
"""

import os
from typing import Optional, Any, Callable
from utils.logger import setup_logger

logger = setup_logger(__name__)

try:
    import redis
    from rq import Queue
    RQ_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ RQ not available. Install with: pip install rq")
    RQ_AVAILABLE = False


class TaskQueue:
    """Task queue wrapper with graceful fallback."""

    def __init__(self):
        self.client: Optional[Any] = None
        self.queue: Optional[Any] = None
        if RQ_AVAILABLE:
            self._connect()

    def _connect(self):
        """Connect to Redis queue with error handling."""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        try:
            self.client = redis.from_url(redis_url)
            self.queue = Queue(connection=self.client)
            logger.info(f"✅ Connected to task queue: {redis_url}")
        except Exception as e:
            logger.warning(f"⚠️ Task queue connection failed: {e}")
            self.client = None
            self.queue = None

    def enqueue(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """
        Enqueue a background job.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Job instance or None
        """
        if not self.queue:
            # Fallback: execute synchronously
            logger.warning(f"Queue not available. Executing {func.__name__} synchronously.")
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Sync execution error: {e}")
                return None

        try:
            job = self.queue.enqueue(func, *args, **kwargs)
            logger.info(f"Job enqueued: {func.__name__} (ID: {job.id})")
            return job
        except Exception as e:
            logger.error(f"Enqueue error: {e}")
            return None

    def get_job(self, job_id: str) -> Optional[Any]:
        """
        Get job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job instance or None
        """
        if not self.queue:
            return None

        try:
            from rq.job import Job
            return Job.fetch(job_id, connection=self.client)
        except Exception as e:
            logger.error(f"Get job error: {e}")
            return None


# Global queue instance
_queue_instance = None


def get_queue() -> TaskQueue:
    """
    Get global task queue instance (singleton).

    Returns:
        TaskQueue instance
    """
    global _queue_instance
    if _queue_instance is None:
        _queue_instance = TaskQueue()
    return _queue_instance
