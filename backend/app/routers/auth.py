
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ..dependencies import get_current_user

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserResponse, UserLogin, TokenResponse
from ..security import (
    hash_password,
    verify_password,
    create_access_token
)
router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    # Check whether the email is already registered
    email = str(user_data.email).lower()

    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email is already registered"
        )

    # Hash the password
    hashed_password = hash_password(user_data.password)

    # Create a new attendee account
    new_user = User(
        full_name=user_data.full_name,
        email=email,
        password_hash=hashed_password,
        role="attendee",
        is_active=True
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email is already registered"
        )

    return new_user

@router.post("/login", response_model=TokenResponse)
def login_user(
    credentials: UserLogin,
    db: Session = Depends(get_db)
):
    email = str(credentials.email).lower()

    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(
        credentials.password, user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Account is inactive"
        )

    token = create_access_token({"sub": str(user.id)})

    return {
        "access_token": token,
        "token_type": "bearer"
    }

    # AUTHENTICATED USER: Return the details of the currently logged-in user
@router.get("/me", response_model=UserResponse)
def read_current_user(
    current_user: User = Depends(get_current_user)
):
    return current_user