import asyncio
import asyncpg
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.base import DATA_STORAGE

async def init_db():
    print("Initializing database...")
    config = DATA_STORAGE["postgresql"]
    
    # Connect to default database to create the target database if not exists
    # This part is tricky with asyncpg, usually we assume db exists or we connect to 'postgres'
    # For now, let's assume the DB exists and we just create tables
    
    try:
        conn = await asyncpg.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            database=config["database"]
        )
        
        # Read SQL file
        sql_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sql", "create_tables.sql")
        with open(sql_path, "r") as f:
            sql = f.read()
            
        await conn.execute(sql)
        print("Database initialized successfully.")
        await conn.close()
        
    except Exception as e:
        print(f"Error initializing database: {e}")

if __name__ == "__main__":
    asyncio.run(init_db())
