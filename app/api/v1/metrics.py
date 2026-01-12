"""Metrics API endpoint."""
from flask import Response
from flask_restx import Namespace, Resource
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

api = Namespace("metrics", description="Prometheus metrics")


@api.route("")
class Metrics(Resource):
    """Prometheus metrics endpoint."""

    @api.doc(security=None)  # Public endpoint
    def get(self):
        """
        Export Prometheus metrics.

        Returns metrics in Prometheus text format.
        """
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
