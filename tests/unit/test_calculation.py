
import pytest
import uuid

from app.models.calculation import Calculation

# A test user ID for creating calculation objects
TEST_USER_ID = uuid.uuid4()

def test_create_addition():
    calculation = Calculation.create(
        calculation_type="addition",
        user_id=TEST_USER_ID,
        inputs=[10, 5]
    )

    assert calculation.get_result() == 15

def test_create_subtraction():
    calculation = Calculation.create(
        calculation_type="subtraction",
        user_id=TEST_USER_ID,
        inputs=[10, 5]
    )

    assert calculation.get_result() == 5

def test_create_multiplication():
    calculation = Calculation.create(
        calculation_type="multiplication",
        user_id=TEST_USER_ID,
        inputs=[10, 5]
    )

    assert calculation.get_result() == 50

def test_create_division():
    calculation = Calculation.create(
        calculation_type="division",
        user_id=TEST_USER_ID,
        inputs=[10, 2]
    )

    assert calculation.get_result() == 5

def test_unsupported_calculation_type(self):
    with pytest.raises(ValueError, match="Unsupported calculation type"):
        Calculation.create(
            calculation_type="exponentiation",
            user_id=TEST_USER_ID,
            inputs=[2, 3]
        )

def test_inputs_must_be_a_list(self):
    calculation = Calculation.create(
        calculation_type="addition",
        user_id=TEST_USER_ID,
        inputs="10,5"
    )

    with pytest.raises(ValueError, match="Inputs must be a list"):
        calculation.get_result()

def test_inputs_must_contain_at_least_two_numbers():
    calculation = Calculation.create(
        calculation_type="addition",
        user_id=TEST_USER_ID,
        inputs=[10]
    )

    with pytest.raises(ValueError, match="at least two numbers"):
        calculation.get_result()

def test_division_by_zero(self):
    calculation = Calculation.create(
        calculation_type="division",
        user_id=TEST_USER_ID,
        inputs=[10, 0]
    )

    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calculation.get_result()

def test_multiple_number_addition():
    calculation = Calculation.create(
        calculation_type="addition",
        user_id=TEST_USER_ID,
        inputs=[10, 5, 3, 2]
    )

    assert calculation.get_result() == 20

def test_multiple_number_subtraction():
    calculation = Calculation.create(
        calculation_type="subtraction",
        user_id=TEST_USER_ID,
        inputs=[20, 5, 3]
    )

    assert calculation.get_result() == 12

def test_multiple_number_division():
    calculation = Calculation.create(
        calculation_type="division",
        user_id=TEST_USER_ID,
        inputs=[100, 2, 5]
    )

    assert calculation.get_result() == 10

@pytest.mark.parametrize(
    "calculation_type, inputs, expected",
    [
        ("addition", [10, 5], 15),
        ("subtraction", [10, 5], 5),
        ("multiplication", [10, 5], 50),
        ("division", [10, 2], 5),
        ("addition", [10, 5, 3], 18),
        ("subtraction", [20, 5, 3], 12),
        ("multiplication", [2, 3, 4], 24),
        ("division", [100, 2, 5], 10),
    ]
)
def test_calculation_results(calculation_type, inputs, expected):
    """Test that each calculation type produces the correct result."""

    calculation = Calculation.create(
        calculation_type=calculation_type,
        user_id=TEST_USER_ID,
        inputs=inputs
    )

    assert calculation.get_result() == expected


def test_calculation_type_is_case_insensitive():
    """Test that calculation types accept uppercase letters."""

    calculation = Calculation.create(
        calculation_type="ADDITION",
        user_id=TEST_USER_ID,
        inputs=[10, 5]
    )

    assert calculation.get_result() == 15


def test_unsupported_calculation_type():
    """Test that unsupported calculation types raise ValueError."""

    with pytest.raises(ValueError, match="Unsupported calculation type"):
        Calculation.create(
            calculation_type="exponentiation",
            user_id=TEST_USER_ID,
            inputs=[2, 3]
        )


@pytest.mark.parametrize(
    "inputs",
    [
        "10,5",
        10,
        None
    ]
)
def test_inputs_must_be_a_list(inputs):
    """Test that inputs must be provided as a list."""

    calculation = Calculation.create(
        calculation_type="addition",
        user_id=TEST_USER_ID,
        inputs=inputs
    )

    with pytest.raises(ValueError, match="Inputs must be a list"):
        calculation.get_result()


@pytest.mark.parametrize(
    "inputs",
    [
        [],
        [10]
    ]
)
def test_at_least_two_inputs_are_required(inputs):
    """Test that calculations require at least two inputs."""

    calculation = Calculation.create(
        calculation_type="addition",
        user_id=TEST_USER_ID,
        inputs=inputs
    )

    with pytest.raises(ValueError, match="at least two numbers"):
        calculation.get_result()


def test_division_by_zero():
    """Test that division by zero raises ValueError."""

    calculation = Calculation.create(
        calculation_type="division",
        user_id=TEST_USER_ID,
        inputs=[10, 0]
    )

    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calculation.get_result()


def test_division_by_zero_in_multiple_inputs():
    """Test that zero is detected in any denominator."""

    calculation = Calculation.create(
        calculation_type="division",
        user_id=TEST_USER_ID,
        inputs=[100, 2, 0]
    )

    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calculation.get_result()


def test_negative_numbers():
    """Test that calculations support negative numbers."""

    calculation = Calculation.create(
        calculation_type="addition",
        user_id=TEST_USER_ID,
        inputs=[-10, 5]
    )

    assert calculation.get_result() == -5


def test_decimal_numbers():
    """Test that calculations support decimal values."""

    calculation = Calculation.create(
        calculation_type="addition",
        user_id=TEST_USER_ID,
        inputs=[10.5, 3.5]
    )

    assert calculation.get_result() == 14.0

