"""
API routes for Nexus Nebula Universe
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
import asyncio
from datetime import datetime

from ..models.database import get_db, User, Project, ProjectFile, Artifact, MarketplaceListing, Share
from ..services.auth import get_current_user
from ..services.ai_pipeline import generation_pipeline
from ..services.storage import supabase_storage
from ..utils.helpers import generate_share_url

router = APIRouter(prefix="/api")

# ============================================================================
# PROJECTS API
# ============================================================================

@router.get("/projects")
async def list_projects(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's projects"""
    projects = db.query(Project).filter(Project.owner_id == current_user["id"]).all()
    return [{"id": p.id, "name": p.name, "description": p.description, "is_public": p.is_public} for p in projects]

@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get project details"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user["id"]
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "is_public": project.is_public,
        "created_at": project.created_at.isoformat()
    }

@router.get("/projects/{project_id}/files")
async def get_project_files(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get project files"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user["id"]
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    files = db.query(ProjectFile).filter(ProjectFile.project_id == project_id).all()
    return [{"id": f.id, "path": f.path, "size": f.file_size, "mime_type": f.mime_type} for f in files]

@router.put("/projects/{project_id}/files")
async def update_project_files(
    project_id: str,
    files: List[Dict[str, str]],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update project files"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user["id"]
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Clear existing files
    db.query(ProjectFile).filter(ProjectFile.project_id == project_id).delete()

    # Add new files
    for file_data in files:
        file_obj = ProjectFile(
            id=str(uuid.uuid4()),
            project_id=project_id,
            path=file_data["path"],
            content=file_data["content"],
            file_size=len(file_data["content"]),
            mime_type="text/plain"
        )
        db.add(file_obj)

    db.commit()
    return {"status": "success"}

@router.post("/projects/{project_id}/share")
async def share_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create share link for project"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user["id"]
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    share_url = generate_share_url()

    share = Share(
        id=str(uuid.uuid4()),
        project_id=project_id,
        share_url=share_url,
        is_active=True
    )

    db.add(share)
    db.commit()

    return {"share_url": f"/share/{share_url}"}

# ============================================================================
# AI GENERATION API
# ============================================================================

@router.post("/generate")
async def generate_project(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate project using AI pipeline"""
    prompt = request.get("prompt", "")
    existing_files = request.get("existing_files", {})

    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    # Start generation in background
    background_tasks.add_task(run_generation, prompt, existing_files, current_user["id"], db)

    return {"status": "generation_started", "message": "Project generation has started"}

async def run_generation(prompt: str, existing_files: Dict[str, str], user_id: str, db: Session):
    """Run AI generation pipeline"""
    try:
        result = await generation_pipeline.generate(prompt, existing_files)

        if result["success"]:
            # Create project from generated artifacts
            project_id = str(uuid.uuid4())
            project = Project(
                id=project_id,
                name=f"Generated Project - {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                description=f"Generated from: {prompt[:100]}...",
                owner_id=user_id,
                is_public=False,
                metadata=result["metadata"]
            )

            db.add(project)

            # Add generated files
            if "code" in result["metadata"]:
                code_content = result["metadata"]["code"]["code"]
                # Parse and save files (simplified)
                if "```" in code_content:
                    # Extract code blocks
                    pass

            db.commit()

    except Exception as e:
        print(f"Generation failed: {e}")

# ============================================================================
# STUDIO API
# ============================================================================

@router.post("/studio/run")
async def run_code(
    request: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Run code in studio"""
    code = request.get("code", "")
    language = request.get("language", "javascript")

    if not code:
        raise HTTPException(status_code=400, detail="Code is required")

    try:
        # Simple code execution (in production, use proper sandboxing)
        if language == "javascript":
            # For demo purposes - in production use proper JS execution
            result = f"JavaScript execution simulated: {len(code)} characters"
        elif language == "python":
            # Execute Python code safely
            result = execute_python_code(code)
        else:
            result = f"Language {language} not supported yet"

        return {"output": result, "success": True}

    except Exception as e:
        return {"output": f"Error: {str(e)}", "success": False}

@router.post("/studio/terminal")
async def execute_terminal_command(
    request: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """Execute terminal command"""
    command = request.get("command", "")

    if not command:
        raise HTTPException(status_code=400, detail="Command is required")

    # Basic command validation (in production, use proper sandboxing)
    allowed_commands = ["ls", "pwd", "echo", "cat", "head", "tail", "grep", "wc"]

    if not any(command.startswith(cmd) for cmd in allowed_commands):
        return {"output": "Command not allowed for security reasons"}

    try:
        # Execute command (simplified - in production use proper sandboxing)
        import subprocess
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        output = result.stdout + result.stderr
        return {"output": output}

    except Exception as e:
        return {"output": f"Error: {str(e)}"}

def execute_python_code(code: str) -> str:
    """Execute Python code safely"""
    try:
        # Very basic execution - in production use proper sandboxing
        exec_globals = {}
        exec(code, exec_globals)
        return "Code executed successfully"
    except Exception as e:
        return f"Python error: {str(e)}"

# ============================================================================
# MARKETPLACE API
# ============================================================================

@router.get("/marketplace/listings")
async def get_marketplace_listings(
    q: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get marketplace listings"""
    query = db.query(MarketplaceListing).filter(MarketplaceListing.is_active == True)

    if q:
        query = query.filter(MarketplaceListing.title.contains(q))
    if category:
        query = query.filter(MarketplaceListing.tags.contains([category]))

    listings = query.all()
    return [{
        "id": l.id,
        "title": l.title,
        "description": l.description,
        "price": l.price,
        "tags": l.tags,
        "download_count": l.download_count
    } for l in listings]

@router.post("/marketplace/{listing_id}/download")
async def download_listing(
    listing_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download marketplace item"""
    listing = db.query(MarketplaceListing).filter(MarketplaceListing.id == listing_id).first()

    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    # Increment download count
    listing.download_count += 1
    db.commit()

    # Get signed URL for download
    artifact = db.query(Artifact).filter(Artifact.id == listing.artifact_id).first()
    if artifact:
        signed_url = await supabase_storage.create_signed_url(artifact.file_path)
        return {"download_url": signed_url}

    raise HTTPException(status_code=404, detail="Artifact not found")

# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "service": "Nexus Nebula API",
        "timestamp": datetime.utcnow().isoformat()
    }