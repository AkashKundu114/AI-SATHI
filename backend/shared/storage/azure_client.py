from __future__ import annotations

import logging
import os

from shared.config.settings import get_settings

logger = logging.getLogger("azure_client")

_azure_blob_service = None


def get_azure_blob_service():
    global _azure_blob_service
    if _azure_blob_service is not None:
        return _azure_blob_service

    s = get_settings()
    conn_str = getattr(s, "azure_storage_connection_string", None) or os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    if not conn_str:
        logger.info("AZURE_STORAGE_CONNECTION_STRING not set — using local storage fallback")
        return None

    try:
        from azure.storage.blob import BlobServiceClient
        _azure_blob_service = BlobServiceClient.from_connection_string(conn_str)
        return _azure_blob_service
    except Exception as exc:
        logger.warning("Failed to initialize Azure BlobServiceClient: %s", exc)
        return None


async def upload_azure_blob(container_name: str, blob_name: str, data: bytes, content_type: str = "application/octet-stream") -> str | None:
    service = get_azure_blob_service()
    if not service:
        return None

    try:
        container_client = service.get_container_client(container_name)
        if not container_client.exists():
            container_client.create_container()

        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(data, overwrite=True, content_type=content_type)
        return blob_client.url
    except Exception as exc:
        logger.exception("upload_azure_blob error for %s/%s: %s", container_name, blob_name, exc)
        return None
