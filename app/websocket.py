"""WebSocket configuration."""
from flask_socketio import SocketIO

# Initialize SocketIO with CORS support
socketio = SocketIO(cors_allowed_origins="*")
