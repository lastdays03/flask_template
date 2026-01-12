"""Email tasks."""
from app.extensions import celery
from app.models.user import User


@celery.task(bind=True, max_retries=3)
def send_welcome_email(self, user_id):
    """Send welcome email to new user."""
    try:
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # TODO: Implement actual email sending
        # For now, just log
        print(f"Sending welcome email to {user.email}")

        return f"Welcome email sent to {user.email}"

    except Exception as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2**self.request.retries)


@celery.task(bind=True, max_retries=3)
def send_password_reset_email(self, user_id, token):
    """Send password reset email."""
    try:
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # TODO: Implement actual email sending
        print(f"Sending password reset email to {user.email}")

        return f"Password reset email sent to {user.email}"

    except Exception as e:
        raise self.retry(exc=e, countdown=2**self.request.retries)


@celery.task
def send_notification(user_id, message):
    """Send notification email."""
    user = User.query.get(user_id)
    if not user:
        return f"User {user_id} not found"

    # TODO: Implement actual email sending
    print(f"Sending notification to {user.email}: {message}")

    return f"Notification sent to {user.email}"
