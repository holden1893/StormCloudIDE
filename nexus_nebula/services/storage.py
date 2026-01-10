"""
Supabase Storage Service for file uploads and downloads
"""

import os
from supabase import create_client, Client
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime
import uuid

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

class SupabaseStorage:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

        self.client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        self.bucket_name = "nexus-nebula-artifacts"

    async def upload_file(self, file: BinaryIO, filename: str, content_type: str = None) -> Dict[str, Any]:
        """Upload file to Supabase storage"""
        try:
            # Generate unique filename
            file_extension = filename.split('.')[-1] if '.' in filename else ''
            unique_filename = f"{uuid.uuid4()}.{file_extension}"

            # Upload file
            file_content = file.read()
            response = self.client.storage.from_(self.bucket_name).upload(
                unique_filename,
                file_content,
                file_options={
                    "content-type": content_type or "application/octet-stream",
                    "cache-control": "3600"
                }
            )

            if response.status_code != 200:
                raise Exception(f"Upload failed: {response.json()}")

            # Get public URL
            public_url = self.client.storage.from_(self.bucket_name).get_public_url(unique_filename)

            # Create signed URL for secure access
            signed_url_response = self.client.storage.from_(self.bucket_name).create_signed_url(
                unique_filename,
                expires_in=3600  # 1 hour
            )

            return {
                "filename": unique_filename,
                "original_filename": filename,
                "file_path": unique_filename,
                "public_url": public_url,
                "signed_url": signed_url_response.get("signedURL"),
                "size": len(file_content),
                "uploaded_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise Exception(f"File upload failed: {str(e)}")

    async def download_file(self, file_path: str) -> bytes:
        """Download file from Supabase storage"""
        try:
            response = self.client.storage.from_(self.bucket_name).download(file_path)
            return response
        except Exception as e:
            raise Exception(f"File download failed: {str(e)}")

    async def delete_file(self, file_path: str) -> bool:
        """Delete file from Supabase storage"""
        try:
            response = self.client.storage.from_(self.bucket_name).remove([file_path])
            return response.status_code == 200
        except Exception as e:
            raise Exception(f"File deletion failed: {str(e)}")

    async def create_signed_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Create signed URL for secure file access"""
        try:
            response = self.client.storage.from_(self.bucket_name).create_signed_url(
                file_path,
                expires_in=expires_in
            )
            return response.get("signedURL")
        except Exception as e:
            raise Exception(f"Signed URL creation failed: {str(e)}")

    async def list_files(self, path: str = "") -> list:
        """List files in storage bucket"""
        try:
            response = self.client.storage.from_(self.bucket_name).list(path=path)
            return response
        except Exception as e:
            raise Exception(f"File listing failed: {str(e)}")

# Global storage service instance
supabase_storage = SupabaseStorage()