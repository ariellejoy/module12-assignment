import pytest
from jose import jwt 
import redis.asyncio as redis

from unittest.mock import patch
from fastapi import HTTPException, status
from app.auth.dependencies import get_current_user, get_current_active_user
from app.schemas.user import UserResponse
from app.models.user import User
from app.schemas.token import TokenType
from app.auth.jwt import create_token
from app.core.config import get_settings
from uuid import uuid4
from datetime import datetime, timezone, timedelta

settings = get_settings()

# Sample user data dictionaries for testing
sample_user_data = {
    "id": uuid4(),
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "is_active": True,
    "is_verified": True,
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow()
}

inactive_user_data = {
    "id": uuid4(),
    "username": "inactiveuser",
    "email": "inactive@example.com",
    "first_name": "Inactive",
    "last_name": "User",
    "is_active": False,
    "is_verified": False,
    "created_at": datetime.now(timezone.utc),
    "updated_at": datetime.now(timezone.utc)
}

# Fixture for mocking token verification
@pytest.fixture
def mock_verify_token():
    with patch.object(User, 'verify_token') as mock:
        yield mock

# Test get_current_user with valid token and complete payload
@pytest.mark.asyncio
async def test_get_current_user_valid_token_existing_user(
    db_session,
    test_user
):
    token = create_token(
        user_id=test_user.id,
        token_type=TokenType.ACCESS
    )

    result = await get_current_user(
        token=token,
        db=db_session
    )

    assert result is not None
    assert result.id == test_user.id

# Test get_current_user with invalid token (returns None)
@pytest.mark.asyncio
async def test_get_current_user_invalid_token(db_session):

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            token="invalid.token.value",
            db=db_session
        )

    assert exc_info.value.status_code == 401

# Test get_current_user with valid token but incomplete payload (simulate missing fields)
@pytest.mark.asyncio
async def test_get_current_user_valid_token_incomplete_payload(
    db_session
):
    payload = {
        "type": TokenType.ACCESS.value,
        "jti": "test-jti-123",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15)
    }

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            token=token,
            db=db_session
        )

    assert exc_info.value.status_code == 401

# Test get_current_active_user with an active user
def test_get_current_active_user_active(test_user):

    test_user.is_active = True

    result = get_current_active_user(
        current_user=test_user
    )

    assert result == test_user
    assert result.is_active is True

# Test get_current_active_user with an inactive user
def test_get_current_active_user_inactive(test_user):

    test_user.is_active = False

    with pytest.raises(HTTPException) as exc_info:
        get_current_active_user(
            current_user=test_user
        )

    assert exc_info.value.status_code == 400