"""Prometheus metrics."""
from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_flask_exporter import PrometheusMetrics

# Custom business metrics
user_registrations = Counter(
    "user_registrations_total", "Total number of user registrations"
)

user_logins = Counter("user_logins_total", "Total number of successful user logins")

failed_logins = Counter("failed_logins_total", "Total number of failed login attempts")

active_users = Gauge("active_users_count", "Number of currently active users")

api_request_duration = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["method", "endpoint", "status"],
)

celery_task_duration = Histogram(
    "celery_task_duration_seconds",
    "Celery task duration in seconds",
    ["task_name", "status"],
)

cache_hits = Counter("cache_hits_total", "Total number of cache hits", ["cache_type"])

cache_misses = Counter(
    "cache_misses_total", "Total number of cache misses", ["cache_type"]
)


def init_metrics(app):
    """Initialize Prometheus metrics."""
    # Flask-RESTX conflicts with PrometheusMetrics auto-discovery
    # So we disable default metrics and add custom ones
    metrics = PrometheusMetrics(
        app,
        path=None,  # Disable default /metrics endpoint
        export_defaults=True,
        defaults_prefix="flask",
    )

    # Add application info
    app_info = Info("flask_app", "Flask application information")
    app_info.info(
        {"version": "1.0.0", "environment": app.config.get("ENV", "production")}
    )

    return metrics
