"""Flower configuration."""

import os

# Celery broker URL
broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")

# Flower basic authentication
basic_auth = [
    os.getenv("FLOWER_USER", "admin") + ":" + os.getenv("FLOWER_PASSWORD", "change_me")
]

# Port
port = int(os.getenv("FLOWER_PORT", "5555"))

# URL prefix for reverse proxy
url_prefix = os.getenv("FLOWER_URL_PREFIX", "")

# Persistent storage
persistent = True
db = os.getenv("FLOWER_DB", "flower.db")

# Max tasks to keep in memory
max_tasks = int(os.getenv("FLOWER_MAX_TASKS", "10000"))

# Enable events
enable_events = True

# Purge offline workers
purge_offline_workers = int(os.getenv("FLOWER_PURGE_OFFLINE_WORKERS", "60"))

# Auto-refresh interval (seconds)
auto_refresh = True
