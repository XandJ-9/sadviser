import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.tasks.strategy_tasks import StrategyTasks

async def validate():
    print("Starting strategy validation...")
    tasks = StrategyTasks()
    await tasks.run_backtests()
    print("Strategy validation completed.")

if __name__ == "__main__":
    asyncio.run(validate())
