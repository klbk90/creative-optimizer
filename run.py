#!/usr/bin/env python3
"""
Railway startup script - properly reads PORT from environment
"""
import os
import subprocess
import uvicorn
from sqlalchemy import create_engine, text

def init_alembic_if_needed():
    """Initialize alembic_version table if migrations fail due to existing columns"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("⚠️  DATABASE_URL not set, skipping alembic init")
        return

    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # Check if alembic_version exists
            result = conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')"
            ))
            exists = result.scalar()

            if not exists:
                print("📝 Initializing alembic_version table...")
                # Mark the version before the new influencers migration as current
                # This assumes all previous migrations were manually applied
                conn.execute(text("""
                    CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)
                """))
                # Mark as being at the last migration before influencers
                conn.execute(text("""
                    INSERT INTO alembic_version (version_num) VALUES ('add_niche_weights_20260112')
                """))
                conn.commit()
                print("✅ Initialized alembic_version to 'add_niche_weights_20260112'")
    except Exception as e:
        print(f"⚠️  Could not init alembic: {e}")


if __name__ == "__main__":
    # Initialize alembic if needed
    init_alembic_if_needed()

    # Run database migrations before starting server
    print("🔄 Running database migrations...")
    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("✅ Migrations completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e}")
        print("⚠️  Continuing anyway (migrations may already be applied)")

    port = int(os.getenv("PORT", "8000"))

    print(f"🚀 Starting uvicorn on port {port}")

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=port,
        workers=1,
        log_level="info"
    )
