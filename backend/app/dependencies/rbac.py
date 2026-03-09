from fastapi import Depends, HTTPException, Request, status

from app.dependencies.auth import get_current_user
from app.schemas.auth import CurrentUser


class RequirePermission:
    """FastAPI dependency that checks user has the required permission(s)."""

    def __init__(self, *permissions: str, allow_platform_admin: bool = False):
        self.permissions = permissions
        self.allow_platform_admin = allow_platform_admin

    async def __call__(
        self,
        request: Request,
        current_user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if "*" in self.permissions:
            return current_user
        if self.allow_platform_admin and current_user.is_platform_admin:
            return current_user

        for perm in self.permissions:
            if perm not in current_user.permissions:
                from app.middleware.metrics import permission_denied_total

                endpoint = request.url.path
                permission_denied_total.labels(
                    endpoint=endpoint,
                    tenant_id=str(current_user.tenant_id),
                    user_id=str(current_user.id),
                ).inc()

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {perm}",
                )
        return current_user
