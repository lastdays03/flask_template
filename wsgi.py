"""WSGI entry point for production."""

import os
from app import create_app

from app.websocket import socketio

app = create_app(os.getenv("FLASK_ENV", "production"))

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
