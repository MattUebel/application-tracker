import os
import asyncio
import time
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import OperationalError

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@db/apptrackerdb")
MAX_TRIES = 30
WAIT_SECONDS = 2

async def check_db_connection_async():
    engine = create_async_engine(DATABASE_URL)
    for i in range(MAX_TRIES):
        try:
            async with engine.connect() as connection:
                # You can optionally execute a simple query here, e.g., await connection.execute(text("SELECT 1"))
                print("Database connection successful.")
                return True
        except (OperationalError, ConnectionRefusedError, OSError) as e: # Added OSError for cases like host not found initially
            print(f"Database connection attempt {i+1}/{MAX_TRIES} failed: {e}")
            if i < MAX_TRIES - 1:
                print(f"Retrying in {WAIT_SECONDS} seconds...")
                await asyncio.sleep(WAIT_SECONDS) # Use asyncio.sleep
            else:
                print("Max retries reached. Could not connect to the database.")
                return False
        finally:
            await engine.dispose() # Dispose the engine when done
    return False

if __name__ == "__main__":
    if not asyncio.run(check_db_connection_async()):
        exit(1)  # Exit with error code if connection failed
    print("Proceeding to start application...") 