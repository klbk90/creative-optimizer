"""
Create anonymous user for MVP uploads.
"""
import uuid
from datetime import datetime
from database.base import SessionLocal
from database.models import User

def create_anonymous_user():
    """Create anonymous user with fixed UUID."""
    db = SessionLocal()

    # Check if user already exists
    existing = db.query(User).filter(User.id == uuid.UUID('00000000-0000-0000-0000-000000000001')).first()

    if existing:
        print(f"✅ Anonymous user already exists: {existing.email}")
        db.close()
        return

    # Create anonymous user
    user = User(
        id=uuid.UUID('00000000-0000-0000-0000-000000000001'),
        email='anonymous@creative-optimizer.app',
        password_hash='dummy_hash',  # Not used for anonymous
        is_active=True,
        created_at=datetime.utcnow()
    )

    db.add(user)
    db.commit()
    db.close()

    print(f"✅ Anonymous user created: {user.email}")

if __name__ == '__main__':
    create_anonymous_user()
