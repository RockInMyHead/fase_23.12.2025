"""
File system operations service
"""
from .local import LocalFileService
from .base import FileService


def get_file_service() -> FileService:
    """Get file service instance"""
    return LocalFileService()


__all__ = ["LocalFileService", "FileService", "get_file_service"]
