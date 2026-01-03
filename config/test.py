from .base import *

# Test specific configuration
DEBUG = True
LOG_LEVEL = "DEBUG"

# Database configuration for testing
DATA_STORAGE = {
    "postgresql": {
        "host": "localhost",
        "port": 5432,
        "database": "sadviser_test",
        "user": "postgres",
        "password": "password"
    }
}
