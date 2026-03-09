from fastapi import Depends, HTTPException, status

from app.config import settings
from app.dependencies.auth import get_current_user
from app.schemas.auth import CurrentUser


async def get_platform_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    admin_emails = [
        e.strip().lower()
        for e in settings.platform_admin_emails.split(",")
        if e.strip()
    ]
    if current_user.email.lower() not in admin_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "PLATFORM_ADMIN_REQUIRED",
                    "message": "Platform admin access required",
                }
            },
        )
    return current_user
