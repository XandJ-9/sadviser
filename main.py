import uvicorn
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    uvicorn.run("service.main:app", host="0.0.0.0", port=8001, reload=True)
