
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Booking, Event, User, Ticket
from ..schemas import BookingCreate, BookingResponse
from ..dependencies import require_roles


router = APIRouter(prefix="/api/bookings", tags=["Bookings"])


# CREATE BOOKING AND GENERATE TICKETS (ATTENDEES ONLY)
@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
def create_booking(
    booking_data: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("attendee"))
):
    # Lock the event row to prevent concurrent overbooking
    event = (
        db.query(Event)
        .filter(Event.id == booking_data.event_id)
        .with_for_update()
        .first()
    )

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if event.status != "upcoming":
        raise HTTPException(status_code=400, detail="Event is not available for booking")

    # Calculate the number of already confirmed seats
    existing_bookings = (
        db.query(Booking)
        .filter(
            Booking.event_id == event.id,
            Booking.status == "confirmed"
        )
        .all()
    )

    booked_seats = sum(booking.quantity for booking in existing_bookings)
    available_seats = event.capacity - booked_seats

    if booking_data.quantity > available_seats:
        raise HTTPException(
            status_code=400,
            detail=f"Only {available_seats} seats are available"
        )

    # Calculate payment and generate simulated payment reference
    total_amount = event.ticket_price * booking_data.quantity
    payment_reference = "PAY-" + secrets.token_hex(6).upper()

    # Create booking
    new_booking = Booking(
        quantity=booking_data.quantity,
        total_amount=total_amount,
        status="confirmed",
        payment_reference=payment_reference,
        attendee_id=current_user.id,
        event_id=event.id
    )

    db.add(new_booking)

    # Save booking temporarily to obtain its ID
    db.flush()

    # Generate one unique ticket for each booked seat
    for _ in range(booking_data.quantity):
        new_ticket = Ticket(
            booking_id=new_booking.id,
            event_id=event.id,
            attendee_id=current_user.id,
            qr_token=secrets.token_urlsafe(32),
            status="valid",
            checked_in=False
        )
        db.add(new_ticket)

    # Save booking and tickets together
    db.commit()
    db.refresh(new_booking)

    return new_booking


# VIEW MY BOOKING HISTORY
@router.get("/my-bookings", response_model=list[BookingResponse])
def get_my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("attendee"))
):
    return (
        db.query(Booking)
        .filter(Booking.attendee_id == current_user.id)
        .order_by(Booking.created_at.desc())
        .all()
    )
