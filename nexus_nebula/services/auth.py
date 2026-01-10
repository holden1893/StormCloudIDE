"""
Authentication service using Supabase Auth
"""

import os
from supabase import create_client, Client
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import jwt
from datetime import datetime, timedelta

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
security = HTTPBearer(auto_error=False)

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated (optional)"""
    if not credentials:
        return None

    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        return None

    # Get user from Supabase
    try:
        user_response = supabase.auth.get_user(token)
        if user_response.user:
            return {
                "id": user_response.user.id,
                "email": user_response.user.email,
                "name": user_response.user.user_metadata.get("name", "User"),
                "avatar_url": user_response.user.user_metadata.get("avatar_url"),
                "subscription_tier": "free"  # Default tier
            }
    except Exception:
        pass

    return None

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """Get current user (required authentication)"""
    user = await get_current_user_optional(credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

async def register_user(email: str, password: str, name: str) -> Dict[str, Any]:
    """Register new user with Supabase"""
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "name": name
                }
            }
        })

        if response.user:
            # Create access token
            token = create_access_token({"sub": response.user.id})

            return {
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "name": name
                }
            }
        else:
            raise HTTPException(status_code=400, detail="Registration failed")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration error: {str(e)}")

async def login_user(email: str, password: str) -> Dict[str, Any]:
    """Login user with Supabase"""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response.user and response.session:
            # Create access token
            token = create_access_token({"sub": response.user.id})

            return {
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "name": response.user.user_metadata.get("name", "User")
                }
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")

    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Login error: {str(e)}")

async def logout_user(token: str):
    """Logout user"""
    try:
        supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        return {"message": f"Logout error: {str(e)}"}