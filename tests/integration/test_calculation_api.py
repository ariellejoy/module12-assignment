
import uuid
import pytest

def create_test_calculation(client, auth_headers):
    """Helper function to create a calculation for integration tests."""

    response = client.post(
        "/calculations",
        json={
            "type": "addition",
            "inputs": [10, 5]
        },
        headers=auth_headers
    )

    assert response.status_code == 201
    return response.json()

def test_create_calculation(client, auth_headers):
    """Test successfully creating a new calculation."""

    response = client.post(
        "/calculations",
        json={
            "type": "addition",
            "inputs": [10, 5]
        },
        headers=auth_headers
    )

    assert response.status_code == 201

    data = response.json()

    assert data["type"] == "addition"
    assert data["inputs"] == [10.0, 5.0]
    assert data["result"] == 15.0
    assert "id" in data
    assert "user_id" in data
    assert "created_at" in data
    assert "updated_at" in data

def test_create_calculation_with_different_types(client, auth_headers
):
    """Test creating calculations using all supported operations."""

    test_cases = [
        ("addition", [10, 5], 15),
        ("subtraction", [10, 5], 5),
        ("multiplication", [10, 5], 50),
        ("division", [10, 2], 5)
    ]

    for calculation_type, inputs, expected in test_cases:
        response = client.post(
            "/calculations",
            json={
                "type": calculation_type,
                "inputs": inputs
            },
            headers=auth_headers
        )

        print(f"\nCalculation: {calculation_type}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        assert response.status_code == 201
        assert response.json()["result"] == expected

def test_create_calculation_invalid_type(client, auth_headers):
    """Test that unsupported calculation types return HTTP 422."""

    response = client.post(
        "/calculations",
        json={
            "type": "exponentiation",
            "inputs": [2, 3]
        },
        headers=auth_headers
    )

    assert response.status_code == 422

def test_create_calculation_insufficient_inputs(client, auth_headers
):
    """Test that fewer than two inputs return HTTP 422."""

    response = client.post(
        "/calculations",
        json={
            "type": "addition",
            "inputs": [10]
        },
        headers=auth_headers
    )

    assert response.status_code == 422

def test_create_calculation_division_by_zero(client, auth_headers
):
    """Test that division by zero returns HTTP 422 during schema validation."""

    response = client.post(
        "/calculations",
        json={
            "type": "division",
            "inputs": [10, 0]
        },
        headers=auth_headers
    )

    assert response.status_code == 422

def test_create_calculation_missing_inputs(client, auth_headers):
    """Test that missing inputs return HTTP 422."""

    response = client.post(
        "/calculations",
        json={
            "type": "addition"
        },
        headers=auth_headers
    )

    assert response.status_code == 422

def test_list_calculations(client, auth_headers):
    """Test retrieving all calculations belonging to the user."""

    create_test_calculation(client, auth_headers)

    response = client.get(
        "/calculations",
        headers=auth_headers
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1

def test_get_calculation_by_id(client, auth_headers):
    """Test retrieving one calculation using its UUID."""

    created = create_test_calculation(client, auth_headers)
    calculation_id = created["id"]

    response = client.get(
        f"/calculations/{calculation_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json()["id"] == calculation_id
    assert response.json()["type"] == "addition"
    assert response.json()["result"] == 15.0

def test_get_calculation_invalid_uuid(client, auth_headers):
    """Test that an invalid UUID returns HTTP 400."""

    response = client.get(
        "/calculations/not-a-valid-uuid",
        headers=auth_headers
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid calculation id format."

def test_get_nonexistent_calculation(client, auth_headers):
    """Test that a nonexistent calculation returns HTTP 404."""

    nonexistent_id = str(uuid.uuid4())

    response = client.get(
        f"/calculations/{nonexistent_id}",
        headers=auth_headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Calculation not found."

def test_update_calculation(client, auth_headers):
    """Test successfully updating an existing calculation."""

    created = create_test_calculation(client, auth_headers)
    calculation_id = created["id"]

    response = client.put(
        f"/calculations/{calculation_id}",
        json={
            "inputs": [20, 10]
        },
        headers=auth_headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == calculation_id
    assert data["inputs"] == [20.0, 10.0]
    assert data["result"] == 30.0

def test_update_calculation_division_by_zero(client, auth_headers
):
    """Test that updating division inputs to include zero returns HTTP 400."""

    created = client.post(
        "/calculations",
        json={
            "type": "division",
            "inputs": [10, 2]
        },
        headers=auth_headers
    )

    assert created.status_code == 201
    calculation_id = created.json()["id"]

    response = client.put(
        f"/calculations/{calculation_id}",
        json={
            "inputs": [10, 0]
        },
        headers=auth_headers
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot divide by zero."

def test_update_calculation_insufficient_inputs(client, auth_headers
):
    """Test that updating with fewer than two inputs returns HTTP 422."""

    created = create_test_calculation(client, auth_headers)
    calculation_id = created["id"]

    response = client.put(
        f"/calculations/{calculation_id}",
        json={
            "inputs": [10]
        },
        headers=auth_headers
    )

    assert response.status_code == 422

def test_update_nonexistent_calculation(client, auth_headers):
    """Test updating a nonexistent calculation returns HTTP 404."""

    nonexistent_id = str(uuid.uuid4())

    response = client.put(
        f"/calculations/{nonexistent_id}",
        json={
            "inputs": [20, 10]
        },
        headers=auth_headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Calculation not found."

def test_delete_calculation(client, auth_headers):
    """Test successfully deleting a calculation."""

    created = create_test_calculation(client, auth_headers)
    calculation_id = created["id"]

    response = client.delete(
        f"/calculations/{calculation_id}",
        headers=auth_headers
    )

    assert response.status_code == 204
    assert response.content == b""

    # Confirm that the calculation no longer exists.
    get_response = client.get(
        f"/calculations/{calculation_id}",
        headers=auth_headers
    )

    assert get_response.status_code == 404

def test_delete_nonexistent_calculation(client, auth_headers):
    """Test deleting a nonexistent calculation returns HTTP 404."""

    nonexistent_id = str(uuid.uuid4())

    response = client.delete(
        f"/calculations/{nonexistent_id}",
        headers=auth_headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Calculation not found."

def test_delete_calculation_invalid_uuid(client, auth_headers):
    """Test deleting with an invalid UUID returns HTTP 400."""

    response = client.delete(
        "/calculations/invalid-id",
        headers=auth_headers
    )

    assert response.status_code == 400

def test_list_calculations_without_authentication(client):
    """Test that unauthenticated requests return HTTP 401."""

    response = client.get("/calculations")

    assert response.status_code == 401

def test_create_calculation_without_authentication(client):
    """Test that unauthenticated creation returns HTTP 401."""

    response = client.post(
        "/calculations",
        json={
            "type": "addition",
            "inputs": [10, 5]
        }
    )

    assert response.status_code == 401

def test_user_cannot_retrieve_another_users_calculation(client, auth_headers, second_auth_headers
):
    """User B cannot retrieve a calculation belonging to User A."""

    # User A creates a calculation.
    created = client.post(
        "/calculations",
        json={
            "type": "addition",
            "inputs": [10, 5]
        },
        headers=auth_headers
    )

    assert created.status_code == 201
    calculation_id = created.json()["id"]

    # User B attempts to retrieve User A's calculation.
    response = client.get(
        f"/calculations/{calculation_id}",
        headers=second_auth_headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Calculation not found."

def test_user_cannot_update_another_users_calculation(client, auth_headers, second_auth_headers
):
    """User B cannot update a calculation belonging to User A."""

    # User A creates a calculation.
    created = client.post(
        "/calculations",
        json={
            "type": "addition",
            "inputs": [10, 5]
        },
        headers=auth_headers
    )

    assert created.status_code == 201
    calculation_id = created.json()["id"]

    # User B attempts to update User A's calculation.
    response = client.put(
        f"/calculations/{calculation_id}",
        json={
            "inputs": [100, 50]
        },
        headers=second_auth_headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Calculation not found."

    # Confirm User A's original calculation remains unchanged.
    original = client.get(
        f"/calculations/{calculation_id}",
        headers=auth_headers
    )

    assert original.status_code == 200
    assert original.json()["inputs"] == [10.0, 5.0]
    assert original.json()["result"] == 15.0

def test_user_cannot_delete_another_users_calculation(client, auth_headers, second_auth_headers
):
    """User B cannot delete a calculation belonging to User A."""

    # User A creates a calculation.
    created = client.post(
        "/calculations",
        json={
            "type": "multiplication",
            "inputs": [10, 5]
        },
        headers=auth_headers
    )

    assert created.status_code == 201
    calculation_id = created.json()["id"]

    # User B attempts to delete User A's calculation.
    response = client.delete(
        f"/calculations/{calculation_id}",
        headers=second_auth_headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Calculation not found."

    # Confirm User A's calculation still exists.
    original = client.get(
        f"/calculations/{calculation_id}",
        headers=auth_headers
    )

    assert original.status_code == 200
    assert original.json()["result"] == 50.0

def test_users_only_see_their_own_calculations(client, auth_headers, second_auth_headers
):
    """Each user should only see their own calculations."""

    # User A creates a calculation.
    user_a_calculation = client.post(
        "/calculations",
        json={
            "type": "addition",
            "inputs": [10, 5]
        },
        headers=auth_headers
    )

    # User B creates a calculation.
    user_b_calculation = client.post(
        "/calculations",
        json={
            "type": "multiplication",
            "inputs": [4, 5]
        },
        headers=second_auth_headers
    )

    assert user_a_calculation.status_code == 201
    assert user_b_calculation.status_code == 201

    user_a_id = user_a_calculation.json()["id"]
    user_b_id = user_b_calculation.json()["id"]

    # Retrieve User A's calculations.
    response_a = client.get(
        "/calculations",
        headers=auth_headers
    )

    # Retrieve User B's calculations.
    response_b = client.get(
        "/calculations",
        headers=second_auth_headers
    )

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    user_a_ids = [item["id"] for item in response_a.json()]
    user_b_ids = [item["id"] for item in response_b.json()]

    # Verify ownership separation.
    assert user_a_id in user_a_ids
    assert user_b_id not in user_a_ids

    assert user_b_id in user_b_ids
    assert user_a_id not in user_b_ids
