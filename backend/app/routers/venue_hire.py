
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..database import get_db
from ..models import Venue, Event, VenueHireRequest, User
from ..dependencies import require_roles

router = APIRouter(prefix="/api/venue-hire", tags=["Private Venue Hire"])


class VenueHireCreate(BaseModel):
    venue_id: int
    event_title: str = Field(min_length=2, max_length=150)
    start_time: datetime
    end_time: datetime
    expected_attendees: int = Field(gt=0)


# REQUEST PRIVATE VENUE HIRE
@router.post("/")
def request_venue_hire(
    data: VenueHireCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("attendee"))
):
    venue = db.query(Venue).filter(Venue.id == data.venue_id).first()

    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    if data.end_time <= data.start_time:
        raise HTTPException(status_code=400, detail="Invalid booking time")

    if data.expected_attendees > venue.capacity:
        raise HTTPException(status_code=400, detail="Venue capacity exceeded")

    # Check existing event conflicts
    conflict = db.query(Event).filter(
        Event.venue_id == venue.id,
        Event.start_time < data.end_time,
        Event.end_time > data.start_time
    ).first()

    # Simulated pricing: Rs. 100 per expected attendee
    estimated_price = data.expected_attendees * 100

    hire_request = VenueHireRequest(
        user_id=current_user.id,
        venue_id=venue.id,
        event_title=data.event_title,
        start_time=data.start_time,
        end_time=data.end_time,
        expected_attendees=data.expected_attendees,
        estimated_price=estimated_price,
        status="pending" if conflict else "approved",
        admin_decision=(
            "Admin review required because the venue has a scheduling conflict"
            if conflict else
            "Venue hire provisionally approved"
        )
    )

    db.add(hire_request)
    db.commit()
    db.refresh(hire_request)

    return {
        "request_id": hire_request.id,
        "venue": venue.name,
        "estimated_price": estimated_price,
        "status": hire_request.status,
        "decision": hire_request.admin_decision
    }


# ADMIN VIEW ALL HIRE REQUESTS
@router.get("/")
def get_hire_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    requests = db.query(VenueHireRequest).order_by(
        VenueHireRequest.created_at.desc()
    ).all()

    return requests
