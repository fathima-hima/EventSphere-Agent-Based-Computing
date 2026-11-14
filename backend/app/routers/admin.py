
from fastapi import APIRouter, Depends

from ..models import User
from ..dependencies import require_roles

# Router for administrator-only operations
router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"]
)


# ADMIN DASHBOARD: Allow access only to administrators
@router.get("/dashboard")
def admin_dashboard(
    current_user: User = Depends(require_roles("admin"))
):
    return {
        "message": "Welcome to the EventSphere Admin Dashboard!",
        "admin_name": current_user.full_name,
        "role": current_user.role
    }
