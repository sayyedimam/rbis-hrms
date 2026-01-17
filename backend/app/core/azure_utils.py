import os
from azure.storage.blob.aio import BlobServiceClient
from fastapi import UploadFile, HTTPException
import logging

logger = logging.getLogger(__name__)

# Config
AZURE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME", "attendance-records")

def get_blob_service_client():
    if not AZURE_CONNECTION_STRING:
        logger.warning("AZURE_STORAGE_CONNECTION_STRING not set.")
        return None
    return BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)

async def upload_bytes_to_azure(content: bytes, filename: str, content_type: str = "application/octet-stream") -> str:
    """
    Uploads bytes content directly to Azure Blob Storage (Async).
    Returns the blob name.
    """
    client = get_blob_service_client()
    if not client:
        raise HTTPException(status_code=500, detail="Azure Storage not configured")
    
    try:
        async with client:
            container_client = client.get_container_client(CONTAINER_NAME)
            if not await container_client.exists():
                await container_client.create_container()

            blob_client = container_client.get_blob_client(filename)
            await blob_client.upload_blob(content, overwrite=True, content_type=content_type)
        
        return filename
    except Exception as e:
        logger.error(f"Failed to upload bytes to Azure: {e}")
        raise HTTPException(status_code=500, detail=f"Azure upload failed: {str(e)}")

async def upload_file_to_azure(file: UploadFile, filename: str) -> str:
    """
    Uploads a file to Azure Blob Storage and returns the blob name (or URL).
    Returns the blob name to be stored in the database.
    """
    client = get_blob_service_client()
    if not client:
        raise HTTPException(status_code=500, detail="Azure Storage not configured")
    
    try:
        async with client:
            container_client = client.get_container_client(CONTAINER_NAME)
            if not await container_client.exists():
                await container_client.create_container()

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
    client = get_blob_service_client()
    if not client:
        raise HTTPException(status_code=500, detail="Azure Storage not configured")
        
    try:
        async with client:
            container_client = client.get_container_client(CONTAINER_NAME)
            blob_client = container_client.get_blob_client(filename)
            
            if not await blob_client.exists():
                raise HTTPException(status_code=404, detail="File not found in Azure Storage")
                
            stream = await blob_client.download_blob()
            data = await stream.readall()
            return data
    except Exception as e:
        logger.error(f"Failed to download from Azure: {e}")
        raise split_exception(e)

def split_exception(e):
    if isinstance(e, HTTPException):
        return e
    return HTTPException(status_code=500, detail=str(e))
