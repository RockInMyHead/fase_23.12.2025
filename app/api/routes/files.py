"""
File system operations API routes
"""
from pathlib import Path
from typing import List, Optional
from urllib.parse import unquote
import asyncio

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from ...core.logging import get_logger
from ...models.schemas import FolderInfoResponse, ImagePreviewResponse
from ...services.file_service import get_file_service

logger = get_logger(__name__)
router = APIRouter()


@router.get("/folder")
async def get_folder_info(path: str = Query(..., description="Folder path")):
    """
    Get folder contents

    Args:
        path: URL-encoded folder path
    """
    try:
        decoded_path = unquote(path)
        folder_path = Path(decoded_path)

        logger.info("GET /folder path=%s (raw: %s)", folder_path, path)
        logger.info("Path exists: %s, is_dir: %s", folder_path.exists(), folder_path.is_dir() if folder_path.exists() else "N/A")

        if not folder_path.exists():
            logger.error("Path does not exist: %s", folder_path)
            raise HTTPException(status_code=404, detail="Folder not found")
        if not folder_path.is_dir():
            logger.error("Path is not a directory: %s", folder_path)
            raise HTTPException(status_code=400, detail="Path is not a directory")

        file_service = get_file_service()
        logger.info("Calling file_service.get_folder_contents for %s", folder_path)
        contents = await file_service.get_folder_contents(folder_path)
        logger.info("file_service returned %d items", len(contents))

        out: List[FolderInfoResponse] = []
        for item in contents:
            p = item.path if isinstance(item.path, Path) else Path(item.path)
            is_dir = p.is_dir()

            out.append(FolderInfoResponse(
                name=item.name,
                path=str(p),
                is_directory=is_dir,
                size=item.size,
                modified=item.modified,
                children_count=item.children_count
            ))

        logger.info("Returning %d items for path %s", len(out), folder_path)

        # Подсчитываем изображения для совместимости со старым API
        image_count = sum(1 for item in out if not item.is_directory and any(item.name.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']))

        return {
            "path": str(folder_path),
            "contents": out,
            "image_count": image_count
        }

    except HTTPException:
        logger.error("HTTPException for path %s: %s", path, str(e))
        raise
    except Exception as e:
        logger.exception("Failed to get folder info for %s", path)
        raise HTTPException(status_code=500, detail=str(e))


@router.api_route("/image/preview", methods=["GET", "HEAD"])
async def get_image_preview(path: str = Query(..., description="Image path"), size: int = Query(150, ge=50, le=1000)):
    """
    Get image preview

    Args:
        path: URL-encoded image path
        size: Preview size in pixels
    """
    try:
        # Decode URL path
        decoded_path = unquote(path)
        image_path = Path(decoded_path)

        logger.info("GET/HEAD /image/preview path=%s, exists=%s, suffix=%s", image_path, image_path.exists(), image_path.suffix)

        if not image_path.exists():
            logger.warning("Image not found: %s", image_path)
            raise HTTPException(status_code=404, detail="Image not found")

        # For HEAD requests, just check if preview can be generated
        from fastapi import Request
        from fastapi.responses import Response

        # Check if it's a HEAD request
        # Since we can't access request directly, check if preview exists
        file_service = get_file_service()
        logger.info("Calling file_service.get_image_preview for %s", image_path)
        preview = file_service.get_image_preview(image_path, size)
        logger.info("file_service returned preview: %s", preview is not None)

        if preview is None:
            logger.warning("Failed to generate preview for %s", image_path)
            # For HEAD requests, return 404 if preview can't be generated
            raise HTTPException(status_code=404, detail="Preview not available")

        # For successful cases, return appropriate response
        return ImagePreviewResponse(
            content=preview,
            content_type="image/jpeg"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get image preview for %s", path)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/folder")
async def create_folder(
    path: str = Query(..., description="Parent directory path"),
    name: str = Query(..., description="New folder name")
):
    """
    Create new folder

    Args:
        path: Parent directory path
        name: New folder name
    """
    try:
        parent_path = Path(path)
        if not parent_path.exists() or not parent_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid parent directory")

        file_service = get_file_service()
        new_folder = await file_service.create_folder(parent_path, name)

        return {
            "success": True,
            "path": str(new_folder)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create folder {name} in {path}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/item")
async def delete_item(path: str = Query(..., description="Path to delete")):
    """
    Delete file or folder

    Args:
        path: Path to delete
    """
    try:
        # Decode URL path
        decoded_path = unquote(path)
        item_path = Path(decoded_path)

        if not item_path.exists():
            raise HTTPException(status_code=404, detail="Item not found")

        file_service = get_file_service()
        await file_service.delete_item(item_path)

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete item {path}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/move")
async def move_item(
    srcPath: str = Query(..., description="Source path"),
    destPath: str = Query(..., description="Destination path")
):
    """
    Move file or folder

    Args:
        srcPath: Source path
        destPath: Destination path
    """
    try:
        source_path = Path(srcPath)
        dest_path = Path(destPath)

        if not source_path.exists():
            raise HTTPException(status_code=404, detail="Source item not found")

        file_service = get_file_service()
        await file_service.move_item(source_path, dest_path)

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to move item from {srcPath} to {destPath}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
