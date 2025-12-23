"""
Pydantic schemas for API responses
"""
from typing import List, Optional
from pydantic import BaseModel


class DriveInfoResponse(BaseModel):
    """Response model for drive information"""
    name: str
    path: str


from typing import Literal

class FolderInfoResponse(BaseModel):
    """Response model for folder contents"""
    name: str
    path: str
    is_directory: bool
    size: Optional[int] = None
    modified: Optional[float] = None
    children_count: Optional[int] = None


class ImagePreviewResponse(BaseModel):
    """Response model for image preview"""
    content: bytes
    content_type: str = "image/jpeg"


class FileItem(BaseModel):
    """Base model for file system items"""
    name: str
    path: str
    type: str
    size: Optional[int] = None
    modified: Optional[float] = None
    children_count: Optional[int] = None


class QueueItemRequest(BaseModel):
    """Request model for adding items to processing queue"""
    path: str
    recursive: bool = False


class ProcessCommonPhotosRequest(BaseModel):
    """Request model for processing common photos"""
    paths: List[str]
    output_dir: str
    quality_threshold: float = 0.75


class TaskResponse(BaseModel):
    """Response model for task status"""
    id: str
    status: str  # "pending", "running", "completed", "failed"
    progress: Optional[int] = None
    message: Optional[str] = None
    created_at: Optional[float] = None
    completed_at: Optional[float] = None
