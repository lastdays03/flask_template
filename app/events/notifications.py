"""WebSocket event handlers."""
from flask_socketio import emit, join_room
from flask_jwt_extended import decode_token
from app.websocket import socketio


@socketio.on('connect')
def handle_connect(auth):
    """Handle client connection."""
    try:
        # Verify JWT token (expecting auth dict with token)
        token = auth.get('token') if auth else None
        
        if token:
            decoded = decode_token(token)
            user_id = decoded['sub']  # This is the string user_id we set in auth_service

            # Join user's personal room
            join_room(f'user_{user_id}')
            emit('connected', {'message': 'Connected successfully'})
            return True
        else:
            return False
    except Exception as e:
        print(f'Connection error: {e}')
        return False


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    pass


@socketio.on('subscribe_notifications')
def handle_subscribe(data):
    """Subscribe to notification channel."""
    channel = data.get('channel')
    if channel:
        join_room(channel)
        emit('subscribed', {'channel': channel})


@socketio.on('send_message')
def handle_message(data):
    """Handle incoming message."""
    message = data.get('message')
    room = data.get('room', 'general')

    emit('new_message', {
        'message': message,
        'room': room
    }, room=room)


def send_notification_to_user(user_id, message):
    """Send notification to specific user."""
    socketio.emit(
        'notification',
        {'message': message},
        room=f'user_{user_id}'
    )
