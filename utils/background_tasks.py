"""
Background task queue для тяжелых операций.

Используется для:
- Claude Vision анализа видео (expensive!)
- Обработки больших файлов
"""

from rq import Queue
from redis import Redis
import os
from utils.logger import setup_logger

logger = setup_logger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    redis_conn = Redis.from_url(REDIS_URL)
    task_queue = Queue("default", connection=redis_conn)
    logger.info(f"✅ Task queue connected: {REDIS_URL}")
except Exception as e:
    logger.warning(f"⚠️ Task queue unavailable: {e}")
    redis_conn = None
    task_queue = None


def enqueue_deep_analysis(creative_id):
    """
    Enqueue deep analysis task for creative.

    Args:
        creative_id: UUID of creative to analyze
    """
    if not task_queue:
        logger.warning("Task queue unavailable. Running synchronously...")
        # Fallback: run synchronously
        deep_analyze_creative_task(str(creative_id))
        return

    # Enqueue async task
    job = task_queue.enqueue(
        deep_analyze_creative_task,
        str(creative_id),
        job_timeout='10m',  # 10 minutes max
        result_ttl=3600  # Keep result for 1 hour
    )

    logger.info(f"🔄 Deep analysis task enqueued: {job.id}")
    return job.id


def deep_analyze_creative_task(creative_id_str: str):
    """
    Background task: Analyze creative with Claude Vision.

    This runs asynchronously in a worker process.

    Args:
        creative_id_str: String UUID of creative
    """
    import uuid
    from database.base import SessionLocal
    from database.models import Creative
    from utils.video_analyzer import analyze_video_with_retry
    from utils.conversion_observer import mark_as_deeply_analyzed

    logger.info(f"🎬 Starting deep analysis for creative: {creative_id_str}")

    db = SessionLocal()
    creative_id = uuid.UUID(creative_id_str)

    try:
        creative = db.query(Creative).filter(Creative.id == creative_id).first()

        if not creative:
            logger.error(f"Creative {creative_id} not found")
            return {"error": "Creative not found"}

        if not creative.video_url:
            logger.error(f"No video URL for creative {creative.name}")
            return {"error": "No video URL"}

        # Run Claude Vision analysis
        logger.info(f"📹 Analyzing video: {creative.video_url}")
        analysis_result = analyze_video_with_retry(creative.video_url)

        if not analysis_result:
            logger.error(f"Analysis failed for {creative.name}")
            creative.analysis_status = "failed"
            db.commit()
            return {"error": "Analysis failed"}

        # Save results
        from utils.analysis_orchestrator import mark_analysis_complete
        mark_analysis_complete(creative_id, analysis_result, db)

        logger.info(
            f"✅ WINNER DECONSTRUCTED: {creative.name} → "
            f"{analysis_result['hook_type']} + {analysis_result['emotion']}"
        )

        return {
            "success": True,
            "creative_id": creative_id_str,
            "analysis": analysis_result
        }

    except Exception as e:
        logger.error(f"Deep analysis task failed: {e}")
        return {"error": str(e)}

    finally:
        db.close()


def analyze_facebook_ad_library_video(video_url: str, metadata: dict):
    """
    Анализ видео из Facebook Ad Library (для seed данных).

    Эти видео анализируем СРАЗУ, т.к. уже знаем что они winners.

    Args:
        video_url: URL видео
        metadata: {product_category, estimated_cvr, ...}

    Returns:
        Analysis result
    """
    from utils.video_analyzer import analyze_video_with_retry

    logger.info(f"🎯 Analyzing Facebook Ad Library winner: {video_url}")

    # Анализируем без задержки
    analysis = analyze_video_with_retry(video_url)

    if analysis:
        logger.info(
            f"✅ FB Ad Library analyzed: {analysis['hook_type']} + {analysis['emotion']}"
        )
    else:
        logger.warning(f"⚠️ FB Ad Library analysis failed for {video_url}")

    return analysis
