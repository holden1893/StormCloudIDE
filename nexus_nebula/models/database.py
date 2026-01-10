"""
Database models and configuration for Nexus Nebula Universe
Using SQLAlchemy with Supabase PostgreSQL
"""

from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/nexus_nebula")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "nexus_users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    avatar_url = Column(String)
    subscription_tier = Column(String, default="free")  # free, pro, team
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    projects = relationship("Project", back_populates="owner")
    artifacts = relationship("Artifact", back_populates="creator")

class Project(Base):
    __tablename__ = "nexus_projects"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    owner_id = Column(String, ForeignKey("nexus_users.id"), nullable=False)
    is_public = Column(Boolean, default=False)
    is_template = Column(Boolean, default=False)
    tags = Column(JSON, default=list)  # List of tags
    metadata = Column(JSON, default=dict)  # Additional project metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="projects")
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="project", cascade="all, delete-orphan")

class ProjectFile(Base):
    __tablename__ = "nexus_project_files"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("nexus_projects.id"), nullable=False)
    path = Column(String, nullable=False)  # File path within project
    content = Column(Text)  # File content (for small files)
    file_size = Column(Integer)  # File size in bytes
    mime_type = Column(String)
    is_binary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="files")

class Artifact(Base):
    __tablename__ = "nexus_artifacts"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("nexus_projects.id"), nullable=False)
    creator_id = Column(String, ForeignKey("nexus_users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    artifact_type = Column(String, nullable=False)  # code, image, video, document
    file_path = Column(String)  # Path in Supabase storage
    file_url = Column(String)  # Signed URL for access
    metadata = Column(JSON, default=dict)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="artifacts")
    creator = relationship("User", back_populates="artifacts")

class MarketplaceListing(Base):
    __tablename__ = "nexus_marketplace_listings"

    id = Column(String, primary_key=True)
    artifact_id = Column(String, ForeignKey("nexus_artifacts.id"), nullable=False)
    seller_id = Column(String, ForeignKey("nexus_users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Integer, default=0)  # Price in cents
    currency = Column(String, default="USD")
    tags = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    download_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Share(Base):
    __tablename__ = "nexus_shares"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("nexus_projects.id"), nullable=False)
    share_url = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"⚠️  Database initialization error: {e}")

if __name__ == "__main__":
    init_db()