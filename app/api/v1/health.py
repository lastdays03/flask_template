"""Health check API."""

from datetime import datetime
from flask import current_app
from flask_restx import Namespace, Resource
from app.extensions import db
import redis

api = Namespace("health", description="Health check operations")


@api.route("")
class HealthCheck(Resource):
    """Health check resource."""

    def get(self):
        """Check service health."""
        from sqlalchemy import text

        status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {},
            "version": "1.0.0",
        }

        # Check database
        try:
            db.session.execute(text("SELECT 1"))
            status["services"]["database"] = "ok"
        except Exception as e:
            status["services"]["database"] = "error"
            status["status"] = "unhealthy"
            current_app.logger.error(f"Database health check failed: {e}")

        # Check Redis
        try:
            r = redis.from_url(current_app.config["REDIS_URL"])
            r.ping()
            status["services"]["redis"] = "ok"
        except Exception as e:
            status["services"]["redis"] = "error"
            status["status"] = "unhealthy"
            current_app.logger.error(f"Redis health check failed: {e}")

        # Check Celery (basic check)
        try:
            from app.extensions import celery

            inspect = celery.control.inspect()
            if inspect.active() is not None:
                status["services"]["celery"] = "ok"
            else:
                status["services"]["celery"] = "no workers"
        except Exception as e:
            status["services"]["celery"] = "error"
            current_app.logger.error(f"Celery health check failed: {e}")

        return status, 200 if status["status"] == "healthy" else 503
