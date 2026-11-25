# app/auth/dependencies.py

from fastapi import Depends, HTTPException, status
from app.auth.jwt import get_current_user
from app.models.user import User

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to ensure that the authenticated user exists
    and is active.

    The get_current_user dependency handles JWT validation
    and retrieves the actual user from the database.
    """

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    return current_user
