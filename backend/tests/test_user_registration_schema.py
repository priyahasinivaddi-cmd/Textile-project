import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate


@pytest.mark.parametrize("role", ["admin", "manager", "manufacturer", "operator"])
def test_registration_accepts_supported_roles(role):
    user = UserCreate(name="Test User", email="test@example.test", password="password123", role=role)
    assert user.role == role


def test_registration_rejects_unknown_roles():
    with pytest.raises(ValidationError):
        UserCreate(name="Test User", email="test@example.test", password="password123", role="superuser")
