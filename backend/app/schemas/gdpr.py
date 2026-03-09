import uuid
from datetime import datetime

from pydantic import BaseModel


class DataExportRequest(BaseModel):
    format: str = "json"  # "json" or "csv"


class DataExportResponse(BaseModel):
    export_id: str
    status: str
    data: dict | None = None
    created_at: datetime


class ErasureRequest(BaseModel):
    user_id: uuid.UUID
    reason: str
    confirm: bool = False


class ErasureResponse(BaseModel):
    user_id: uuid.UUID
    status: str
    anonymized_fields: list[str]
    retained_for_legal: list[str]
    processed_at: datetime


class RetentionPolicyConfig(BaseModel):
    default_retention_days: int = 2555  # ~7 years
    audit_log_retention_days: int = 2555
    email_retention_days: int = 365
    purge_soft_deleted_after_days: int = 90


class RetentionPolicyResponse(BaseModel):
    tenant_id: uuid.UUID
    config: RetentionPolicyConfig
    updated_at: datetime | None = None


class ProcessingRecordEntry(BaseModel):
    activity: str
    data_categories: list[str]
    purpose: str
    retention: str
    safeguards: str
