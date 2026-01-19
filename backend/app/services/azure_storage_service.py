import logging
from fastapi import UploadFile, HTTPException
from app.core.azure_utils import get_blob_service_client
from app.core.config import get_settings

logger = logging.getLogger(__name__)

async def upload_bytes_to_azure(content: bytes, filename: str, content_type: str = "application/octet-stream") -> str:
    """
    Uploads bytes content directly to Azure Blob Storage (Async).
    Returns the blob name.
    """
    settings = get_settings()
    client = get_blob_service_client()
    if not client:
        raise HTTPException(status_code=500, detail="Azure Storage not configured")
    
    try:
        container_client = client.get_container_client(settings.AZURE_CONTAINER_NAME)
        blob_client = container_client.get_blob_client(filename)
        await blob_client.upload_blob(
            content,
            overwrite=True,
            content_type=content_type)
        
        return filename
    except Exception as e:
        logger.error(f"Failed to upload bytes to Azure: {e}")
        raise HTTPException(status_code=500, detail=f"Azure upload failed: {str(e)}")

async def upload_file_to_azure(file: UploadFile, filename: str) -> str:
    """
    Uploads a file to Azure Blob Storage and returns the blob name (or URL).
    Returns the blob name to be stored in the database.
    """
    settings = get_settings()
    client = get_blob_service_client()
    if not client:
        raise HTTPException(status_code=500, detail="Azure Storage not configured")
    
    try:
        container_client = client.get_container_client(settings.AZURE_CONTAINER_NAME)
          
        blob_client = container_client.get_blob_client(filename)
            
        content_type = file.content_type or "application/octet-stream"
        content = await file.read()
            
        await blob_client.upload_blob(content, overwrite=True, content_type=content_type)
        await file.seek(0)
            
        return filename
    except Exception as e:
        logger.error(f"Failed to upload to Azure: {e}")
        raise HTTPException(status_code=500, detail=f"Azure upload failed: {str(e)}")

async def download_file_stream(filename: str) -> bytes:
    """
    Downloads file content from Azure and returns bytes.
    """
    settings = get_settings()
    client = get_blob_service_client()
    if not client:
        raise HTTPException(status_code=500, detail="Azure Storage not configured")

    try:
        container_client = client.get_container_client(settings.AZURE_CONTAINER_NAME)
        blob_client = container_client.get_blob_client(filename)

        if not await blob_client.exists():
            raise HTTPException(status_code=404, detail="File find in Azure Storage")

        stream = await blob_client.download_blob()
        data = await stream.readall()
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download from Azure: {e}")
        raise HTTPException(status_code=500, detail=f"Azure download failed: {str(e)}")

import asyncio

def upload_bytes_to_azure_sync(content: bytes, filename: str, content_type: str = "application/octet-stream") -> str:
    """Synchronous wrapper for upload_bytes_to_azure"""
    try:
        return asyncio.run(upload_bytes_to_azure(content, filename, content_type))
    except Exception as e:
        logger.error(f"Sync Azure upload failed: {e}")
        raise

def download_file_stream_sync(filename: str) -> bytes:
    """Synchronous wrapper for download_file_stream"""
    try:
        return asyncio.run(download_file_stream(filename))
    except Exception as e:
        logger.error(f"Sync Azure download failed: {e}")
        raise
