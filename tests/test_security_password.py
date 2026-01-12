"""Password security tests."""

import pytest
from app.models.user import User


def test_password_complexity():
    """Test password complexity validation."""
    user = User(email="test@example.com", first_name="Test", last_name="User")

    # Too short
    with pytest.raises(ValueError, match="at least 8 characters"):
        user.set_password("Short1!")

    # No uppercase
    with pytest.raises(ValueError, match="at least one uppercase"):
        user.set_password("lowercase1!")

    # No lowercase
    with pytest.raises(ValueError, match="at least one lowercase"):
        user.set_password("UPPERCASE1!")

    # No digit
    with pytest.raises(ValueError, match="at least one digit"):
        user.set_password("NoDigit!")

    # No special char
    with pytest.raises(ValueError, match="at least one special character"):
        user.set_password("NoSpecialChar1")

    # Valid password
    try:
        user.set_password("ValidPass1!")
        assert user.check_password("ValidPass1!")
    except ValueError:
        pytest.fail("Valid password raised ValueError")
