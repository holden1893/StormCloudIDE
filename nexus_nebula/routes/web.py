"""
Web routes for Nexus Nebula Universe (HTML pages)
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from ..models.database import get_db, Project, Share
from ..services.auth import get_current_user_optional

router = APIRouter()
templates = Jinja2Templates(directory="nexus_nebula/templates")

# ============================================================================
# MAIN PAGES
# ============================================================================

@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Home page"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "current_user": current_user,
        "title": "Nexus Nebula Universe - AI-Powered Development Platform"
    })

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """User dashboard"""
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=302)

    # Get user's projects
    projects = db.query(Project).filter(Project.owner_id == current_user["id"]).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_user": current_user,
        "projects": projects
    })

@router.get("/studio", response_class=HTMLResponse)
async def studio(
    request: Request,
    project_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Studio IDE"""
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=302)

    project = None
    if project_id:
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.owner_id == current_user["id"]
        ).first()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    return templates.TemplateResponse("studio.html", {
        "request": request,
        "current_user": current_user,
        "project": project
    })

@router.get("/marketplace", response_class=HTMLResponse)
async def marketplace(
    request: Request,
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Marketplace"""
    # Get featured listings (simplified)
    from ..models.database import MarketplaceListing
    listings = db.query(MarketplaceListing).filter(
        MarketplaceListing.is_active == True
    ).limit(20).all()

    return templates.TemplateResponse("marketplace.html", {
        "request": request,
        "current_user": current_user,
        "listings": listings
    })

@router.get("/projects", response_class=HTMLResponse)
async def projects(
    request: Request,
    current_user: dict = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Projects page"""
    if not current_user:
        return RedirectResponse(url="/auth/login", status_code=302)

    projects = db.query(Project).filter(Project.owner_id == current_user["id"]).all()

    return templates.TemplateResponse("projects.html", {
        "request": request,
        "current_user": current_user,
        "projects": projects
    })

# ============================================================================
# AUTH PAGES
# ============================================================================

@router.get("/auth/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "title": "Login - Nexus Nebula Universe"
    })

@router.get("/auth/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Register page"""
    return templates.TemplateResponse("auth/register.html", {
        "request": request,
        "title": "Register - Nexus Nebula Universe"
    })

# ============================================================================
# SHARE PAGES
# ============================================================================

@router.get("/share/{share_url}", response_class=HTMLResponse)
async def share_page(
    request: Request,
    share_url: str,
    db: Session = Depends(get_db)
):
    """Public share page"""
    share = db.query(Share).filter(
        Share.share_url == share_url,
        Share.is_active == True
    ).first()

    if not share:
        raise HTTPException(status_code=404, detail="Share not found")

    project = db.query(Project).filter(Project.id == share.project_id).first()

    if not project or not project.is_public:
        raise HTTPException(status_code=404, detail="Project not available")

    return templates.TemplateResponse("share.html", {
        "request": request,
        "project": project,
        "share": share
    })

# ============================================================================
# UTILITY PAGES
# ============================================================================

@router.get("/docs", response_class=HTMLResponse)
async def docs(request: Request):
    """Documentation page"""
    return templates.TemplateResponse("docs.html", {
        "request": request,
        "title": "Documentation - Nexus Nebula Universe"
    })

@router.get("/support", response_class=HTMLResponse)
async def support(request: Request):
    """Support page"""
    return templates.TemplateResponse("support.html", {
        "request": request,
        "title": "Support - Nexus Nebula Universe"
    })

@router.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    """Privacy policy page"""
    return templates.TemplateResponse("privacy.html", {
        "request": request,
        "title": "Privacy Policy - Nexus Nebula Universe"
    })