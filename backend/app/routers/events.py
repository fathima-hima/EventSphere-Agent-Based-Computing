
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Event, Venue, User
from ..schemas import EventCreate, EventResponse, EventUpdate
from ..dependencies import require_roles

router = APIRouter(prefix="/api/events", tags=["Events"])


# CREATE EVENT (ADMIN ONLY)
@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    venue = db.query(Venue).filter(
        Venue.id == event_data.venue_id
    ).first()

    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    if not venue.is_available:
        raise HTTPException(status_code=400, detail="Venue is unavailable")

    if event_data.capacity > venue.capacity:
        raise HTTPException(
            status_code=400,
            detail="Event capacity cannot exceed venue capacity"
        )

    if event_data.end_time <= event_data.start_time:
        raise HTTPException(
            status_code=400,
            detail="End time must be after start time"
        )

    overlapping_event = db.query(Event).filter(
        Event.venue_id == event_data.venue_id,
        Event.start_time < event_data.end_time,
        Event.end_time > event_data.start_time
    ).first()

    if overlapping_event:
        raise HTTPException(
            status_code=400,
            detail="This venue already has an event during that time"
        )

    new_event = Event(
        title=event_data.title,
        description=event_data.description,
        start_time=event_data.start_time,
        end_time=event_data.end_time,
        capacity=event_data.capacity,
        ticket_price=event_data.ticket_price,
        venue_id=event_data.venue_id,
        organiser_id=current_user.id,
        status="upcoming"
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return new_event


# VIEW ALL EVENTS (PUBLIC)
@router.get("/", response_model=list[EventResponse])
def get_all_events(db: Session = Depends(get_db)):
    return db.query(Event).all()


# VIEW SINGLE EVENT (PUBLIC)
@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    return event


# UPDATE EVENT (ADMIN ONLY)
@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: int,
    event_data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    update_data = event_data.model_dump(exclude_unset=True)

    venue_id = update_data.get("venue_id", event.venue_id)
    start_time = update_data.get("start_time", event.start_time)
    end_time = update_data.get("end_time", event.end_time)
    capacity = update_data.get("capacity", event.capacity)

    venue = db.query(Venue).filter(Venue.id == venue_id).first()

    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    if not venue.is_available:
        raise HTTPException(status_code=400, detail="Venue is unavailable")

    if capacity > venue.capacity:
        raise HTTPException(status_code=400, detail="Event capacity exceeds venue capacity")

    if end_time <= start_time:
        raise HTTPException(status_code=400, detail="End time must be after start time")

    overlapping_event = db.query(Event).filter(
        Event.venue_id == venue_id,
        Event.id != event_id,
        Event.start_time < end_time,
        Event.end_time > start_time
    ).first()

    if overlapping_event:
        raise HTTPException(
            status_code=400,
            detail="This venue already has an event during that time"
        )

    for field, value in update_data.items():
        setattr(event, field, value)

    db.commit()
    db.refresh(event)

    return event


# DELETE EVENT (ADMIN ONLY)
@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    event = db.query(Event).filter(Event.id == event_id).first()

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.bookings:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete an event that has bookings"
        )

    db.delete(event)
    db.commit()

    return {"message": "Event deleted successfully"}
