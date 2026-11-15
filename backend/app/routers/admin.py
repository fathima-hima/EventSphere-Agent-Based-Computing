
from fastapi import APIRouter, Depends

from ..models import User
from ..dependencies import require_roles
from sqlalchemy import func
from ..models import Event, Venue, Booking, Ticket

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

@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    total_events = db.query(func.count(Event.id)).scalar() or 0
    total_venues = db.query(func.count(Venue.id)).scalar() or 0
    total_bookings = db.query(func.count(Booking.id)).scalar() or 0

    total_revenue = db.query(
        func.coalesce(func.sum(Booking.total_amount), 0)
    ).filter(
        Booking.status == "confirmed"
    ).scalar()

    total_checkins = db.query(func.count(Ticket.id)).filter(
        Ticket.checked_in == True
    ).scalar() or 0

    return {
        "total_events": total_events,
        "total_venues": total_venues,
        "total_bookings": total_bookings,
        "total_revenue": float(total_revenue),
        "total_checkins": total_checkins
    }