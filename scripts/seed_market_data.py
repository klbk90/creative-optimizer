#!/usr/bin/env python3
"""
Seed Market Data - загрузка benchmark видео из локальной папки.

Этот скрипт сканирует ./seed_videos/ и загружает каждое видео в R2,
создает Creative записи с is_benchmark=True, и запускает Claude Vision анализ.

Usage:
    python scripts/seed_market_data.py

Структура папки seed_videos/:
    seed_videos/
    ├── language_learning/
    │   ├── fb_ad_winner_1.mp4
    │   └── tiktok_hit_spanish.mp4
    ├── fitness/
    │   └── workout_transformation.mp4
    └── finance/
        └── wealth_building.mp4

Для каждого видео создается Creative с:
    - is_benchmark = True
    - alpha = 50 (высокий стартовый приоритет)
    - beta = 950 (CVR = 5%)
    - status = 'pending_analysis'
    - source = 'fb_ad_library' или 'tiktok' (по имени файла)
"""

import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.base import SessionLocal
from database.models import Creative
from utils.storage import upload_benchmark, get_download_url
from utils.analysis_orchestrator import force_analyze
from utils.logger import setup_logger
import uuid

logger = setup_logger(__name__)

# Bayesian Prior для benchmarks
BENCHMARK_ALPHA = 50.0
BENCHMARK_BETA = 950.0
BENCHMARK_CVR = BENCHMARK_ALPHA / (BENCHMARK_ALPHA + BENCHMARK_BETA)  # 5%

# Поддерживаемые форматы видео
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}


def detect_source_from_filename(filename: str) -> str:
    """
    Определить источник видео по имени файла.

    Args:
        filename: Имя файла (например: fb_ad_winner_1.mp4)

    Returns:
        'fb_ad_library' или 'tiktok' или 'youtube' или 'unknown'
    """
    filename_lower = filename.lower()

    if 'fb' in filename_lower or 'facebook' in filename_lower:
        return 'fb_ad_library'
    elif 'tiktok' in filename_lower or 'tt_' in filename_lower:
        return 'tiktok'
    elif 'youtube' in filename_lower or 'yt_' in filename_lower:
        return 'youtube'
    else:
        return 'unknown'


def process_video_file(
    video_path: Path,
    product_category: str,
    db: Session
) -> dict:
    """
    Обработать одно видео: загрузить в R2, создать Creative, запустить анализ.

    Args:
        video_path: Path к видео файлу
        product_category: Категория продукта (из имени папки)
        db: Database session

    Returns:
        {
            "creative_id": "...",
            "r2_key": "...",
            "analysis": {...},
            "success": True/False
        }
    """
    filename = video_path.name
    logger.info(f"📹 Обрабатываем: {filename}")

    try:
        # 1. Читаем видео файл
        with open(video_path, 'rb') as f:
            video_content = f.read()

        file_size_mb = len(video_content) / (1024 * 1024)
        logger.info(f"   Размер: {file_size_mb:.2f} MB")

        # 2. Определяем источник по имени файла
        source = detect_source_from_filename(filename)
        logger.info(f"   Источник: {source}")

        # 3. Загружаем в R2 (bucket: market-benchmarks - PUBLIC)
        logger.info(f"   ☁️  Загружаем в R2 (market-benchmarks)...")

        r2_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
        r2_key = upload_benchmark(
            file_content=video_content,
            filename=r2_filename,
            content_type="video/mp4"
        )
        logger.info(f"   ✅ Загружено: {r2_key}")

        # 4. Создаем Creative запись
        logger.info(f"   💾 Создаем запись в БД...")

        # Генерируем понятное имя из filename
        name = filename.replace('.mp4', '').replace('_', ' ').title()

        creative = Creative(
            id=uuid.uuid4(),
            name=name,
            video_url=r2_key,
            product_category=product_category,
            is_benchmark=True,
            source=source,
            user_id=None,  # Benchmark видео не привязаны к user
            is_public=True,
            # Bayesian Prior (α=50, β=950 → CVR=5%)
            bayesian_alpha=BENCHMARK_ALPHA,
            bayesian_beta=BENCHMARK_BETA,
            # Analysis status
            analysis_status='pending_analysis',
        )
        db.add(creative)
        db.commit()
        db.refresh(creative)

        logger.info(f"   ✅ Creative ID: {creative.id}")
        logger.info(f"   📊 Bayesian Prior: α={BENCHMARK_ALPHA}, β={BENCHMARK_BETA} (CVR={BENCHMARK_CVR*100:.1f}%)")

        # 5. Запускаем Claude Vision анализ (принудительно)
        logger.info(f"   🤖 Запускаем Claude Vision анализ...")
        logger.info(f"   (это займет 10-30 секунд)")

        analysis_result = force_analyze(creative.id, db)

        if analysis_result:
            logger.info(f"   ✅ АНАЛИЗ ЗАВЕРШЕН!")
            logger.info(f"      Hook: {analysis_result.get('hook_type', 'N/A')}")
            logger.info(f"      Emotion: {analysis_result.get('emotion', 'N/A')}")
            logger.info(f"      Pacing: {analysis_result.get('pacing', 'N/A')}")
            logger.info(f"      Psychotype: {analysis_result.get('psychotype', 'N/A')}")
            logger.info(f"      Winning Elements: {analysis_result.get('winning_elements', 'N/A')[:100]}...")

            # Обновляем статус
            creative.analysis_status = 'completed'
            db.commit()
        else:
            logger.warning(f"   ⚠️  Анализ не удался (проверьте ANTHROPIC_API_KEY)")
            creative.analysis_status = 'failed'
            db.commit()

        return {
            "creative_id": str(creative.id),
            "r2_key": r2_key,
            "analysis": analysis_result,
            "success": True
        }

    except Exception as e:
        logger.error(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return {
            "creative_id": None,
            "r2_key": None,
            "analysis": None,
            "success": False,
            "error": str(e)
        }


def scan_and_process_videos(seed_videos_dir: str = "./seed_videos") -> dict:
    """
    Сканировать папку seed_videos/ и обработать все видео.

    Структура:
        seed_videos/
        ├── language_learning/
        │   ├── fb_ad_winner_1.mp4
        │   └── tiktok_hit_spanish.mp4
        └── fitness/
            └── workout.mp4

    Args:
        seed_videos_dir: Путь к папке с видео

    Returns:
        {
            "total": 5,
            "processed": 4,
            "failed": 1,
            "results": [...]
        }
    """
    seed_dir = Path(seed_videos_dir)

    if not seed_dir.exists():
        logger.error(f"❌ Папка не найдена: {seed_dir}")
        logger.error(f"   Создайте папку и добавьте видео:")
        logger.error(f"   mkdir -p {seed_dir}/language_learning")
        logger.error(f"   mkdir -p {seed_dir}/fitness")
        logger.error(f"   mkdir -p {seed_dir}/finance")
        return {
            "total": 0,
            "processed": 0,
            "failed": 0,
            "results": []
        }

    logger.info("="*60)
    logger.info("🚀 SEED MARKET DATA - BENCHMARK VIDEO LOADER")
    logger.info("="*60)
    logger.info(f"📁 Сканируем: {seed_dir.absolute()}")
    logger.info("")

    db = SessionLocal()
    results = []
    total_videos = 0
    processed = 0
    failed = 0

    try:
        # Проход по категориям (папкам)
        for category_dir in seed_dir.iterdir():
            if not category_dir.is_dir():
                continue

            product_category = category_dir.name
            logger.info(f"📂 Категория: {product_category}")

            # Проход по видео в категории
            for video_file in category_dir.iterdir():
                if video_file.suffix.lower() not in VIDEO_EXTENSIONS:
                    logger.info(f"   ⏭️  Пропускаем: {video_file.name} (не видео)")
                    continue

                total_videos += 1
                logger.info("")

                # Обрабатываем видео
                result = process_video_file(video_file, product_category, db)
                results.append({
                    "filename": video_file.name,
                    "category": product_category,
                    **result
                })

                if result["success"]:
                    processed += 1
                else:
                    failed += 1

                # Небольшая задержка между видео (чтобы не перегрузить Claude API)
                if total_videos < len(list(seed_dir.rglob('*.mp4'))):
                    logger.info("")
                    logger.info("   ⏳ Пауза 5 секунд перед следующим видео...")
                    time.sleep(5)

            logger.info("")

    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

    return {
        "total": total_videos,
        "processed": processed,
        "failed": failed,
        "results": results
    }


def main():
    """Main entry point."""

    # Проверка env variables
    required_vars = [
        "R2_ENDPOINT_URL",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_MARKET_BENCHMARKS_BUCKET",
        "ANTHROPIC_API_KEY",
        "DATABASE_URL"
    ]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        logger.error(f"❌ Отсутствуют переменные окружения: {', '.join(missing)}")
        logger.error("\nДобавьте в .env:")
        for var in missing:
            logger.error(f"   {var}=...")
        sys.exit(1)

    # Сканируем и обрабатываем
    summary = scan_and_process_videos()

    # Итоговый отчет
    logger.info("")
    logger.info("="*60)
    logger.info("📊 ИТОГОВЫЙ ОТЧЕТ")
    logger.info("="*60)
    logger.info(f"Всего видео найдено: {summary['total']}")
    logger.info(f"Успешно обработано: {summary['processed']} ✅")
    logger.info(f"Ошибок: {summary['failed']} ❌")
    logger.info("")

    if summary['processed'] > 0:
        logger.info("✨ Benchmark видео загружены и проанализированы!")
        logger.info("   Теперь они будут использоваться для Thompson Sampling")
        logger.info("")
        logger.info("Следующие шаги:")
        logger.info("   1. Проверьте анализ: http://localhost:8000/api/v1/creatives/benchmarks")
        logger.info("   2. Запустите Thompson Sampling: http://localhost:8000/api/v1/rudderstack/thompson-sampling")
    else:
        logger.warning("⚠️  Не удалось обработать ни одного видео")
        logger.warning("   Проверьте:")
        logger.warning("   - Есть ли видео в ./seed_videos/")
        logger.warning("   - Настроены ли R2 credentials")
        logger.warning("   - Настроен ли ANTHROPIC_API_KEY")

    logger.info("="*60)


if __name__ == "__main__":
    main()
