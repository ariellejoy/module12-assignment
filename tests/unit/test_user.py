
import pytest

from app.models.user import User


# ============================================================
# User Registration Tests
# ============================================================

def test_register_user(db_session, fake_user_data):
    """Test that a user can register successfully."""

    user = User.register(db_session, fake_user_data)

    assert user is not None
    assert user.username == fake_user_data["username"]
    assert user.email == fake_user_data["email"]
    assert user.first_name == fake_user_data["first_name"]
    assert user.last_name == fake_user_data["last_name"]

    # Password should be hashed, not stored as plaintext
    assert user.password != fake_user_data["password"]
    assert user.verify_password(fake_user_data["password"])

    assert user.is_active is True
    assert user.is_verified is False


def test_register_user_short_password(db_session, fake_user_data):
    """Test that registration fails with a password shorter than 6 characters."""

    fake_user_data["password"] = "12345"

    with pytest.raises(ValueError, match="Password must be at least 6 characters long"):
        User.register(db_session, fake_user_data)


def test_register_user_missing_password(db_session, fake_user_data):
    """Test that registration fails when password is missing."""

    fake_user_data["password"] = None

    with pytest.raises(ValueError, match="Password must be at least 6 characters long"):
        User.register(db_session, fake_user_data)


def test_register_duplicate_username(db_session, test_user, fake_user_data):
    """Test that duplicate usernames are rejected."""

    existing_user = test_user["user"]

    fake_user_data["username"] = existing_user.username

    with pytest.raises(ValueError, match="Username or email already exists"):
        User.register(db_session, fake_user_data)


def test_register_duplicate_email(db_session, test_user, fake_user_data):
    """Test that duplicate emails are rejected."""

    existing_user = test_user["user"]

    fake_user_data["email"] = existing_user.email

    with pytest.raises(ValueError, match="Username or email already exists"):
        User.register(db_session, fake_user_data)


# ============================================================
# Password Hashing Tests
# ============================================================

def test_hash_password():
    """Test that password hashing returns a different value."""

    password = "SecurePassword123"

    hashed_password = User.hash_password(password)

    assert hashed_password != password
    assert isinstance(hashed_password, str)


def test_verify_correct_password():
    """Test that the correct password is verified."""

    password = "SecurePassword123"

    hashed_password = User.hash_password(password)

    user = User(
        first_name="Test",
        last_name="User",
        username="testuser",
        email="test@example.com",
        password=hashed_password
    )

    assert user.verify_password(password) is True


def test_verify_incorrect_password():
    """Test that an incorrect password is rejected."""

    hashed_password = User.hash_password("SecurePassword123")

    user = User(
        first_name="Test",
        last_name="User",
        username="testuser",
        email="test@example.com",
        password=hashed_password
    )

    assert user.verify_password("WrongPassword123") is False


# ============================================================
# Authentication Tests
# ============================================================

def test_authenticate_with_username(db_session, test_user):
    """Test successful authentication using username."""

    user = test_user["user"]
    password = test_user["password"]

    result = User.authenticate(db_session, user.username, password)

    assert result is not None
    assert result["user"].id == user.id
    assert result["access_token"] is not None
    assert result["refresh_token"] is not None
    assert result["token_type"] == "bearer"


def test_authenticate_with_email(db_session, test_user):
    """Test successful authentication using email."""

    user = test_user["user"]
    password = test_user["password"]

    result = User.authenticate(db_session, user.email, password)

    assert result is not None
    assert result["user"].id == user.id


def test_authenticate_wrong_password(db_session, test_user):
    """Test that an incorrect password is rejected."""

    user = test_user["user"]

    result = User.authenticate(
        db_session,
        user.username,
        "WrongPassword123"
    )

    assert result is None


def test_authenticate_nonexistent_user(db_session):
    """Test that an unknown username is rejected."""

    result = User.authenticate(
        db_session,
        "nonexistent_user",
        "SomePassword123"
    )

    assert result is None


def test_authenticate_inactive_user(db_session, test_user):
    """Test that inactive users cannot authenticate."""

    user = test_user["user"]
    user.is_active = False
    db_session.flush()

    result = User.authenticate(
        db_session,
        user.username,
        test_user["password"]
    )

    assert result is None


# ============================================================
# Token Tests
# ============================================================

def test_create_access_token(test_user):
    """Test access token generation."""

    user = test_user["user"]

    token = User.create_access_token({"sub": str(user.id)})

    assert isinstance(token, str)
    assert len(token) > 0


def test_create_refresh_token(test_user):
    """Test refresh token generation."""

    user = test_user["user"]

    token = User.create_refresh_token({"sub": str(user.id)})

    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_valid_token(test_user):
    """Test verification of a valid access token."""

    user = test_user["user"]

    token = User.create_access_token({"sub": str(user.id)})

    verified_user_id = User.verify_token(token)

    assert verified_user_id == user.id


def test_verify_invalid_token():
    """Test that an invalid token is rejected."""

    result = User.verify_token("invalid.token.value")

    assert result is None
