"""
Migration script to add invite_token column to groups table.
Run this once to update existing databases.
"""
import uuid
from sqlalchemy import text
from app.database import engine

def run_migration():
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='groups' AND column_name='invite_token'
        """))

        if result.fetchone():
            print("✓ invite_token column already exists")
            return

        # Add the column
        print("Adding invite_token column...")
        conn.execute(text("""
            ALTER TABLE groups
            ADD COLUMN invite_token VARCHAR UNIQUE NOT NULL DEFAULT gen_random_uuid()::text
        """))
        conn.commit()

        print("✓ Migration completed successfully")

if __name__ == "__main__":
    run_migration()
