"""
Domain models for the application
"""
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class FolderInfo:
    """Domain model for file/folder information"""
    name: str
    path: Path
    size: Optional[int] = None
    modified: Optional[float] = None
    children_count: Optional[int] = None


@dataclass
class Face:
    """Domain model for detected face"""
    image_path: Path
    embedding: List[float]
    bbox: Optional[List[float]] = None
    quality: Optional[float] = None


@dataclass
class ClusteringResult:
    """Domain model for clustering results"""
    clusters: List[List[Face]]
    metrics: Optional[dict] = None
