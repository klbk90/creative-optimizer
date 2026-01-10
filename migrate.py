from database.base import engine
from sqlalchemy import text

conn = engine.connect()
try:
    print("Adding analysis fields to creatives table...")
    conn.execute(text("ALTER TABLE creatives ADD COLUMN IF NOT EXISTS analysis_status VARCHAR(20) DEFAULT 'pending'"))
    conn.execute(text("ALTER TABLE creatives ADD COLUMN IF NOT EXISTS is_benchmark BOOLEAN DEFAULT FALSE"))
    conn.execute(text("ALTER TABLE creatives ADD COLUMN IF NOT EXISTS deeply_analyzed BOOLEAN DEFAULT FALSE"))
    conn.execute(text("ALTER TABLE creatives ADD COLUMN IF NOT EXISTS ai_reasoning TEXT"))
    conn.execute(text("ALTER TABLE creatives ADD COLUMN IF NOT EXISTS analysis_cost_cents INTEGER DEFAULT 0"))
    conn.execute(text("ALTER TABLE creatives ADD COLUMN IF NOT EXISTS analysis_triggered_at TIMESTAMP"))
    conn.execute(text("ALTER TABLE creatives ADD COLUMN IF NOT EXISTS analyzed_at TIMESTAMP"))
    conn.commit()
    print("✅ Migration complete!")
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()
finally:
    conn.close()
