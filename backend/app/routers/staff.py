
from fastapi import APIRouter, Depends

from ..models import User
from ..dependencies import require_roles

# Router for gate staff operations
router = APIRouter(
    prefix="/api/staff",
    tags=["Gate Staff"]
)


# STAFF DASHBOARD: Allow access only to gate staff
@router.get("/dashboard")
def staff_dashboard(
    current_user: User = Depends(require_roles("gate_staff"))
):
    return {
        "message": "Welcome to the EventSphere Gate Staff Dashboard!",
        "staff_name": current_user.full_name,
        "role": current_user.role
    }
