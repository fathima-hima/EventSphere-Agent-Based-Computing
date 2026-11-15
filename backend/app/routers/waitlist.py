
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..database import get_db
from ..models import WaitlistEntry, Event, User
from ..dependencies import require_roles
from ..agents.system import create_agent_system

router = APIRouter(prefix="/api/waitlist", tags=["Waitlist"])


class WaitlistCreate(BaseModel):
    event_id: int
    quantity: int = Field(default=1, gt=0, le=10)


# JOIN WAITLIST
@router.post("/join")
def join_waitlist(
    data: WaitlistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("attendee"))
):
    event = db.query(Event).filter(Event.id == data.event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    entry = WaitlistEntry(
        attendee_id=current_user.id,
        event_id=event.id,
        quantity=data.quantity,
        status="waiting"
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return {
        "message": "Successfully joined the waitlist",
        "waitlist_id": entry.id,
        "status": entry.status
    }


# VIEW MY WAITLIST ENTRIES
@router.get("/my-entries")
def my_waitlist_entries(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("attendee"))
):
    entries = db.query(WaitlistEntry).filter(
        WaitlistEntry.attendee_id == current_user.id
    ).all()

    return [
        {
            "id": entry.id,
            "event_id": entry.event_id,
            "quantity": entry.quantity,
            "status": entry.status,
            "expires_at": entry.expires_at
        }
        for entry in entries
    ]


# PROCESS EXPIRED OFFERS (ADMIN)
@router.post("/process-expired")
def process_expired_offers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    bus = create_agent_system(db)

    return bus.send(
        sender="Admin",
        receiver="WaitlistAgent",
        performative="REQUEST",
        content={"action": "expire_offers"}
    )
