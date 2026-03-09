import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MailConnectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    provider: str
    display_email: str | None
    status: str
    error_message: str | None
    last_sync_at: datetime | None
    created_at: datetime
    updated_at: datetime | None


class ImapConnectionCreate(BaseModel):
    imap_host: str
    imap_port: int = 993
    imap_user: str
    imap_password: str
