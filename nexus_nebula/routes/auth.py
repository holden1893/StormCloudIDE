"""
Authentication routes for Nexus Nebula Universe
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import json

from ..models.database import get_db, User
from ..services.auth import register_user, login_user, logout_user, get_current_user_optional

router = APIRouter(prefix="/api/auth")

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        result = await register_user(request.email, request.password, request.name)

        # Create user in database if not exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if not existing_user:
            user = User(
                id=result["user"]["id"],
                email=request.email,
                name=request.name
            )
            db.add(user)
            db.commit()

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Login user"""
    try:
        return await login_user(request.email, request.password)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/logout")
async def logout():
    """Logout user"""
    try:
        return await logout_user("")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user_optional)):
    """Get current user information"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return current_user

# ============================================================================
# WEB AUTH ROUTES (HTML REDIRECTS)
# ============================================================================

@router.post("/web/register")
async def web_register(
    request: Request,
    name: str = None,
    email: str = None,
    password: str = None,
    db: Session = Depends(get_db)
):
    """Web registration endpoint"""
    if not all([name, email, password]):
        return RedirectResponse(url="/auth/register?error=missing_fields", status_code=302)

    try:
        result = await register_user(email, password, name)

        # Create user in database
        user = User(
            id=result["user"]["id"],
            email=email,
            name=name
        )
        db.add(user)
        db.commit()

        # Set token in session (simplified - in production use proper session management)
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie("auth_token", result["access_token"], httponly=True)
        return response

    except Exception as e:
        return RedirectResponse(url=f"/auth/register?error={str(e)}", status_code=302)

@router.post("/web/login")
async def web_login(
    request: Request,
    email: str = None,
    password: str = None
):
    """Web login endpoint"""
    if not all([email, password]):
        return RedirectResponse(url="/auth/login?error=missing_fields", status_code=302)

    try:
        result = await login_user(email, password)

        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie("auth_token", result["access_token"], httponly=True)
        return response

    except Exception as e:
        return RedirectResponse(url=f"/auth/login?error={str(e)}", status_code=302)

@router.post("/web/logout")
async def web_logout():
    """Web logout endpoint"""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("auth_token")
    return response