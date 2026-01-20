"""
Simple Conversion Tracking - No auth required for client websites
"""

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from database.base import get_db
from database.models import Creative, Conversion, TrafficSource
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Simple Tracking"])


class ConversionEvent(BaseModel):
    creative_id: str  # UTM ID from URL
    event: str  # purchase, signup, trial_start
    revenue: float = 0
    customer_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/conversion")
async def track_conversion(
    event: ConversionEvent,
    request: Request
):
    """
    Track conversion from client website (no auth required).

    Called by JS snippet on client's website after purchase/signup.
    """
    from database.base import SessionLocal
    db = SessionLocal()

    try:
        # Find creative by ID
        try:
            creative_uuid = uuid.UUID(event.creative_id)
        except ValueError:
            # Maybe it's a UTM ID string, try to find traffic source
            traffic_source = db.query(TrafficSource).filter(
                TrafficSource.utm_id == event.creative_id
            ).first()

            if not traffic_source or not traffic_source.creative_id:
                logger.warning(f"Creative not found for ID: {event.creative_id}")
                raise HTTPException(status_code=404, detail="Creative not found")

            creative_uuid = traffic_source.creative_id
            traffic_source_id = traffic_source.id
        else:
            # Direct creative ID lookup
            traffic_source = None
            traffic_source_id = None

        # Get creative
        creative = db.query(Creative).filter(Creative.id == creative_uuid).first()

        if not creative:
            raise HTTPException(status_code=404, detail="Creative not found")

        # Update creative metrics
        creative.conversions = (creative.conversions or 0) + 1

        if event.revenue > 0:
            revenue_cents = int(event.revenue * 100)
            creative.revenue = (creative.revenue or 0) + revenue_cents

        # Calculate CVR
        if creative.clicks and creative.clicks > 0:
            creative.cvr = int((creative.conversions / creative.clicks) * 10000)

        # Save conversion event
        conversion = Conversion(
            id=uuid.uuid4(),
            traffic_source_id=traffic_source_id,
            user_id=creative.user_id,
            conversion_type=event.event,
            amount=int(event.revenue * 100) if event.revenue > 0 else 0,
            currency="USD",
            customer_id=event.customer_id,
            extra_data=event.metadata or {},
            created_at=datetime.utcnow()
        )

        db.add(conversion)
        db.commit()

        logger.info(f"✅ Conversion tracked: {event.event} for creative {creative.id} (${event.revenue})")

        return {
            "success": True,
            "creative_id": str(creative.id),
            "event": event.event,
            "revenue": event.revenue,
            "total_conversions": creative.conversions
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Conversion tracking failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/tracking/script")
async def get_tracking_script():
    """
    Serve the tracking JavaScript snippet.

    Usage: <script src="https://your-api.com/api/v1/tracking/script"></script>
    """
    with open("static/tracking.js", "r") as f:
        script = f.read()

    return {
        "script": script,
        "usage": """
        Add to your website <head>:
        <script src="https://creative-optimizer.vercel.app/api/v1/tracking/script"></script>

        Then track events:
        <script>
          // On purchase
          creativeOptimizer.trackPurchase(49.99, 'order_123');

          // On signup
          creativeOptimizer.trackSignup('user@email.com');

          // On trial start
          creativeOptimizer.trackTrial('user@email.com');
        </script>
        """
    }
