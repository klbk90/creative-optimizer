"""
Influencer CSV Import - Simple endpoint to upload influencer database
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import csv
import io
import uuid

from database.base import get_db
from database.models import TrafficSource
from api.dependencies import get_current_user
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/v1/influencers", tags=["Influencer Import"])


@router.post("/import-csv")
async def import_influencers_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Import influencers from CSV file.

    Expected CSV format:
    handle,email,followers,engagement_rate,platform,niche

    Example:
    @fitness_coach,coach@email.com,25000,4.5,tiktok,fitness
    @language_guru,guru@email.com,15000,3.2,instagram,education
    """

    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV format")

    try:
        # Read CSV content
        content = await file.read()
        csv_file = io.StringIO(content.decode('utf-8'))
        csv_reader = csv.DictReader(csv_file)

        imported_count = 0
        skipped_count = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):  # start=2 because row 1 is header
            try:
                # Validate required fields
                handle = row.get('handle', '').strip()
                if not handle:
                    errors.append(f"Row {row_num}: Missing handle")
                    skipped_count += 1
                    continue

                # Check if influencer already exists
                existing = db.query(TrafficSource).filter(
                    TrafficSource.user_id == current_user.id,
                    TrafficSource.influencer_handle == handle
                ).first()

                if existing:
                    logger.info(f"Influencer {handle} already exists, skipping")
                    skipped_count += 1
                    continue

                # Parse engagement rate (can be "4.5" or "4.5%" format)
                er_str = row.get('engagement_rate', '0').strip().replace('%', '')
                try:
                    engagement_rate = int(float(er_str) * 10000)  # Convert to basis points
                except ValueError:
                    engagement_rate = 0

                # Parse followers
                try:
                    followers = int(row.get('followers', '0').replace(',', ''))
                except ValueError:
                    followers = 0

                # Get platform (default to tiktok)
                platform = row.get('platform', 'tiktok').lower().strip()

                # Get niche/category
                niche = row.get('niche', '').strip()

                # Create TrafficSource record for influencer
                influencer = TrafficSource(
                    id=uuid.uuid4(),
                    user_id=current_user.id,
                    utm_source=platform,  # tiktok, instagram, youtube
                    utm_medium='influencer',
                    utm_campaign=f"{niche}_outreach" if niche else "influencer_outreach",
                    influencer_handle=handle,
                    influencer_email=row.get('email', '').strip() or None,
                    influencer_followers=followers,
                    influencer_engagement_rate=engagement_rate,
                    influencer_status='potential'  # potential, contacted, agreed, posted, rejected
                )

                db.add(influencer)
                imported_count += 1

                # Commit in batches of 100
                if imported_count % 100 == 0:
                    db.commit()
                    logger.info(f"Imported {imported_count} influencers...")

            except Exception as e:
                logger.error(f"Error processing row {row_num}: {e}")
                errors.append(f"Row {row_num}: {str(e)}")
                skipped_count += 1

        # Final commit
        db.commit()

        logger.info(f"✅ Import completed: {imported_count} imported, {skipped_count} skipped")

        return {
            "success": True,
            "imported": imported_count,
            "skipped": skipped_count,
            "errors": errors[:10] if errors else [],  # Return first 10 errors
            "message": f"Successfully imported {imported_count} influencers"
        }

    except Exception as e:
        logger.error(f"❌ CSV import failed: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.get("/list")
async def list_influencers(
    platform: str = None,
    min_followers: int = None,
    max_followers: int = None,
    status: str = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List influencers with filters.
    """
    query = db.query(TrafficSource).filter(
        TrafficSource.user_id == current_user.id,
        TrafficSource.utm_medium == 'influencer'
    )

    if platform:
        query = query.filter(TrafficSource.utm_source == platform.lower())

    if min_followers:
        query = query.filter(TrafficSource.influencer_followers >= min_followers)

    if max_followers:
        query = query.filter(TrafficSource.influencer_followers <= max_followers)

    if status:
        query = query.filter(TrafficSource.influencer_status == status)

    influencers = query.order_by(TrafficSource.influencer_followers.desc()).limit(limit).all()

    return [{
        "id": str(inf.id),
        "handle": inf.influencer_handle,
        "email": inf.influencer_email,
        "followers": inf.influencer_followers,
        "engagement_rate": (inf.influencer_engagement_rate or 0) / 10000,  # Convert back to percentage
        "platform": inf.utm_source,
        "status": inf.influencer_status,
        "niche": inf.utm_campaign.replace('_outreach', '') if inf.utm_campaign else None
    } for inf in influencers]


@router.put("/{influencer_id}/status")
async def update_influencer_status(
    influencer_id: str,
    status: str,  # potential, contacted, agreed, posted, rejected
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Update influencer status.
    """
    influencer = db.query(TrafficSource).filter(
        TrafficSource.id == uuid.UUID(influencer_id),
        TrafficSource.user_id == current_user.id
    ).first()

    if not influencer:
        raise HTTPException(status_code=404, detail="Influencer not found")

    influencer.influencer_status = status
    db.commit()

    return {
        "success": True,
        "influencer_id": str(influencer.id),
        "status": status
    }
