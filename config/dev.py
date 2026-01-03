from .base import *

# Development specific configuration
DEBUG = True
LOG_LEVEL = "DEBUG"

# Database configuration for development
DATA_STORAGE = {
    "postgresql": {
        "host": "localhost",
        "port": 5432,
        "database": "sadviser_dev",
        "user": "postgres",
        "password": "password"
    }
}
