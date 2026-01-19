import logging
from azure.storage.blob.aio import BlobServiceClient
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

def get_blob_service_client():
    if not settings.AZURE_STORAGE_CONNECTION_STRING:
        logger.warning("AZURE_STORAGE_CONNECTION_STRING not set.")
        return None
    return BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)

