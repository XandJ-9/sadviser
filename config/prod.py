from .base import *

# Production specific configuration
DEBUG = False
LOG_LEVEL = "INFO"

# Database configuration for production
DATA_STORAGE = {
    "postgresql": {
        "host": "prod-db-host",
        "port": 5432,
        "database": "sadviser_prod",
        "user": "postgres",
        "password": "secure_password"
    }
}
