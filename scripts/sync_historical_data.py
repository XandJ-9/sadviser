import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.tasks.data_tasks import DataTasks

async def sync_data():
    print("Starting historical data sync...")
    tasks = DataTasks()
    await tasks.update_historical_data()
    print("Historical data sync completed.")

if __name__ == "__main__":
    asyncio.run(sync_data())
