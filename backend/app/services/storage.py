"""Object storage abstraction — local filesystem or S3-compatible."""

import logging
import re
import tempfile
import uuid
from pathlib import Path

from app.config import settings

# Writable base path; falls back to temp dir if configured path has permission issues
_storage_base: Path | None = None

logger = logging.getLogger("shipflow.storage")

# blob_id format: UUID.extension (e.g. abc123.pdf). No path separators or ..
_BLOB_ID_PATTERN = re.compile(r"^[a-fA-F0-9\-]{36}\.[a-zA-Z0-9]+$")


def _validate_blob_id(blob_id: str) -> None:
    """Validate blob_id to prevent path traversal. Raises ValueError if invalid."""
    if not blob_id or ".." in blob_id or "/" in blob_id or "\\" in blob_id:
        raise ValueError("Invalid blob_id: path traversal or separators not allowed")
    if not _BLOB_ID_PATTERN.match(blob_id):
        raise ValueError("Invalid blob_id: must be UUID.extension format")


async def store_blob(data: bytes, extension: str = "pdf") -> str:
    """Store binary data and return a blob_id / path reference."""
    blob_id = f"{uuid.uuid4()}.{extension}"

    if settings.storage_backend == "s3":
        return await _store_s3(blob_id, data)

    return await _store_local(blob_id, data)


async def get_blob(blob_id: str) -> bytes | None:
    _validate_blob_id(blob_id)
    if settings.storage_backend == "s3":
        return await _get_s3(blob_id)
    return await _get_local(blob_id)


def _get_storage_base() -> Path:
    """Return resolved storage base, using temp dir if configured path is not writable."""
    global _storage_base
    if _storage_base is not None:
        return _storage_base
    base = Path(settings.storage_local_path).resolve()
    try:
        base.mkdir(parents=True, exist_ok=True)
        test_file = base / ".shipflow_write_test"
        test_file.write_bytes(b"")
        test_file.unlink()
    except (PermissionError, OSError) as e:
        logger.warning(
            "Storage path %s not writable (%s). Using temp dir. Set STORAGE_LOCAL_PATH to a writable path to fix.",
            base,
            e,
        )
        base = Path(tempfile.gettempdir()) / "shipflow_storage"
        base.mkdir(parents=True, exist_ok=True)
    _storage_base = base
    return base


async def _store_local(blob_id: str, data: bytes) -> str:
    base = _get_storage_base()
    file_path = base / blob_id
    file_path.write_bytes(data)
    logger.info("Stored blob locally: %s (%d bytes)", blob_id, len(data))
    return blob_id


async def _get_local(blob_id: str) -> bytes | None:
    base = _get_storage_base()
    file_path = (base / blob_id).resolve()
    if not str(file_path).startswith(str(base) + "/") and not str(file_path).startswith(
        str(base) + "\\"
    ):
        raise ValueError("Invalid blob_id: path escapes storage directory")
    if not file_path.exists():
        return None
    return file_path.read_bytes()


async def _store_s3(blob_id: str, data: bytes) -> str:
    try:
        import boto3

        client = boto3.client(
            "s3",
            region_name=settings.storage_s3_region or None,
            aws_access_key_id=settings.storage_s3_access_key or None,
            aws_secret_access_key=settings.storage_s3_secret_key or None,
            endpoint_url=settings.storage_s3_endpoint_url or None,
        )
        client.put_object(
            Bucket=settings.storage_s3_bucket,
            Key=blob_id,
            Body=data,
            ContentType="application/pdf",
        )
        logger.info("Stored blob in S3: %s (%d bytes)", blob_id, len(data))
        return blob_id
    except Exception:
        logger.exception("Failed to store blob in S3")
        raise


async def _get_s3(blob_id: str) -> bytes | None:
    try:
        import boto3

        client = boto3.client(
            "s3",
            region_name=settings.storage_s3_region or None,
            aws_access_key_id=settings.storage_s3_access_key or None,
            aws_secret_access_key=settings.storage_s3_secret_key or None,
            endpoint_url=settings.storage_s3_endpoint_url or None,
        )
        response = client.get_object(Bucket=settings.storage_s3_bucket, Key=blob_id)
        return response["Body"].read()
    except Exception:
        logger.exception("Failed to get blob from S3: %s", blob_id)
        return None
