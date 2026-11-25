from app.models.user import User

def test_register_user_success(client, db_session, fake_user_data):

    response = client.post(
        "/users/register",
        json={
            **fake_user_data,
            "confirm_password": fake_user_data["password"]
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == fake_user_data["username"]
    assert data["email"] == fake_user_data["email"]
    assert data["first_name"] == fake_user_data["first_name"]
    assert data["last_name"] == fake_user_data["last_name"]

    # Verify user was saved in the database
    user = db_session.query(User).filter(
        User.username == fake_user_data["username"]
    ).first()

    assert user is not None
    assert user.email == fake_user_data["email"]

    # Verify password was hashed
    assert user.password != fake_user_data["password"]
    assert user.verify_password(fake_user_data["password"])

def test_register_duplicate_username(client, test_user):

    response = client.post(
        "/users/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": "different@example.com",
            "username": test_user.username,
            "password": "Password123",
            "confirm_password": "Password123"
        }
    )

    assert response.status_code == 400

def test_register_duplicate_email(client, test_user):

    response = client.post(
        "/users/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": test_user.email,
            "username": "different_username",
            "password": "Password123",
            "confirm_password": "Password123"
        }
    )

    assert response.status_code == 400

def test_register_password_mismatch(client, fake_user_data):

    user_data = {
        **fake_user_data,
        "confirm_password": "DifferentPassword123"
    }

    response = client.post(
        "/users/register",
        json=user_data
    )

    assert response.status_code == 422

def test_register_short_password(client, fake_user_data):

    user_data = {
        **fake_user_data,
        "password": "123",
        "confirm_password": "123"
    }

    response = client.post(
        "/users/register",
        json=user_data
    )

    assert response.status_code == 400

def test_login_success_username(client, test_user):

    password = "TestPassword123"

    test_user.password = User.hash_password(password)

    response = client.post(
        "/users/login",
        json={
            "username": test_user.username,
            "password": password
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"] is not None
    assert data["refresh_token"] is not None
    assert data["token_type"] == "bearer"
    assert data["username"] == test_user.username
    assert data["user_id"] == str(test_user.id)

def test_login_success_email(client, test_user):

    password = "TestPassword123"

    test_user.password = User.hash_password(password)

    response = client.post(
        "/users/login",
        json={
            "username": test_user.email,
            "password": password
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["access_token"] is not None
    assert data["refresh_token"] is not None
    assert data["email"] == test_user.email

def test_login_invalid_password(client, test_user):

    response = client.post(
        "/users/login",
        json={
            "username": test_user.username,
            "password": "WrongPassword123"
        }
    )

    assert response.status_code == 401

def test_login_updates_last_login(client, db_session, test_user):

    password = "TestPassword123"

    test_user.password = User.hash_password(password)
    test_user.last_login = None

    db_session.commit()

    response = client.post(
        "/users/login",
        json={
            "username": test_user.username,
            "password": password
        }
    )

    assert response.status_code == 200

    db_session.refresh(test_user)

    assert test_user.last_login is not None
