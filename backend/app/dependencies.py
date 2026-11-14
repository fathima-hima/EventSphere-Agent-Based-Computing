
# Import required libraries
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError

# Import database, user model and JWT settings
from .database import get_db
from .models import User
from .security import SECRET_KEY, ALGORITHM


# Bearer authentication scheme to receive JWT tokens
bearer_scheme = HTTPBearer()


# AUTHENTICATION: Verify the JWT token and identify the logged-in user
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    try:
        # Decode and verify the JWT token
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        # Extract the user ID from the token
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token"
            )

        user_id = int(user_id)

    # Handle invalid or expired tokens
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    # Retrieve the user from the database and check account status
    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User not found or inactive"
        )

    return user


# AUTHORIZATION: Check whether the logged-in user has an allowed role
def require_roles(*allowed_roles):
    def role_checker(
        current_user: User = Depends(get_current_user)
    ):
        # Reject users whose roles are not permitted
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )

        return current_user

    return role_checker
