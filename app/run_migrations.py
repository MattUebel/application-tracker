#!/usr/bin/env python3
"""
Script to run Alembic migrations programmatically.
This ensures the database is properly migrated on startup.
"""
import os
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@db/apptrackerdb")
# Convert async URL to sync URL for Alembic
SYNC_DATABASE_URL = DATABASE_URL.replace("+asyncpg", "")

def run_migrations():
    """Run Alembic migrations."""
    try:
        # Change to the app directory for alembic
        import os
        os.chdir('/app/app')
        
        # Set up Alembic configuration
        alembic_cfg = Config("alembic.ini")
        
        # Set the database URL in the config
        alembic_cfg.set_main_option("sqlalchemy.url", SYNC_DATABASE_URL)
        
        print("Running database migrations...")
        
        # Run the migrations
        command.upgrade(alembic_cfg, "head")
        
        print("Migrations completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error running migrations: {e}")
        return False

def check_database_tables():
    """Check if the main tables exist."""
    engine = create_engine(SYNC_DATABASE_URL)
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
            )
            tables = [row[0] for row in result.fetchall()]
            print(f"Existing tables: {tables}")
            return "job_applications" in tables
    except Exception as e:
        print(f"Error checking tables: {e}")
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    # Check if tables exist, if not run migrations
    if not check_database_tables():
        print("Tables not found, running migrations...")
        if not run_migrations():
            exit(1)
    else:
        print("Tables exist, checking if migrations need to be applied...")
        # Always try to run migrations to head in case there are pending ones
        if not run_migrations():
            exit(1)
    
    print("Database migration check completed!")
