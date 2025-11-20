"""
Authentication router - OAuth2 token endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Optional

from ..middleware.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()


@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 token endpoint for authentication.
    
    Default credentials:
    - Username: admin, Password: secret
    - Username: recruiter, Password: secret
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
    }


@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_active_user)):
    """Get current authenticated user information."""
    return {
        "username": current_user["username"],
        "email": current_user["email"],
        "role": current_user["role"]
    }


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_active_user)):
    """
    Logout endpoint (client should discard token).
    """
    return {
        "message": "Successfully logged out",
        "username": current_user["username"]
    }
