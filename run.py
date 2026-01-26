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
            table_exists = result.scalar()

            # Get current version if table exists
            current_alembic_version = None
            if table_exists:
                try:
                    result = conn.execute(text("SELECT version_num FROM alembic_version"))
                    current_alembic_version = result.scalar()
                    print(f"📌 Current alembic version: {current_alembic_version}")
                except:
                    pass

            # Only init if table doesn't exist OR version is None (empty table)
            if not table_exists or current_alembic_version is None:
                print("📝 Detecting current migration state...")

                # Check which columns exist to determine migration version
                # Check for influencers table (last migration)
                result = conn.execute(text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'influencers')"
                ))
                has_influencers = result.scalar()

                # Check for niche field (add_niche_weights_20260112)
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns
                        WHERE table_name = 'creatives' AND column_name = 'niche'
                    )
                """))
                has_niche = result.scalar()

                # Determine current migration version
                if has_influencers:
                    current_version = 'add_influencers_20260124'
                    print("✅ Detected: influencers table exists")
                elif has_niche:
                    current_version = 'add_niche_weights_20260112'
                    print("✅ Detected: niche field exists")
                else:
                    # Assume all older migrations are applied
                    current_version = 'add_niche_weights_20260112'
                    print("⚠️  Could not detect exact version, defaulting to add_niche_weights_20260112")

                # Create alembic_version table
                if not table_exists:
                    conn.execute(text("""
                        CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL PRIMARY KEY)
                    """))
                    conn.execute(text(f"""
                        INSERT INTO alembic_version (version_num) VALUES ('{current_version}')
                    """))
                else:
                    # Update existing empty table
                    conn.execute(text(f"""
                        INSERT INTO alembic_version (version_num) VALUES ('{current_version}')
                    """))
                conn.commit()
                print(f"✅ Initialized alembic_version to '{current_version}'")
            else:
                # Table exists and has a version - check if we need to fix it
                # If current version is too old and DB has newer tables, update it
                if current_alembic_version:
                    result = conn.execute(text(
                        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'influencers')"
                    ))
                    has_influencers = result.scalar()

                    if has_influencers and current_alembic_version != 'add_influencers_20260124':
                        print(f"⚠️  DB has influencers table but alembic version is {current_alembic_version}")
                        print("📝 Updating to correct version...")
                        conn.execute(text(f"""
                            UPDATE alembic_version SET version_num = 'add_influencers_20260124'
                        """))
                        conn.commit()
                        print("✅ Updated alembic_version to 'add_influencers_20260124'")

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
