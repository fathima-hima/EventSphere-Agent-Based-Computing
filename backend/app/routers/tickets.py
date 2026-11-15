
from io import BytesIO

import qrcode

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Ticket, Booking, Event, User
from ..dependencies import require_roles


router = APIRouter(prefix="/api/tickets", tags=["Tickets"])


# VIEW MY TICKETS (ATTENDEE)
@router.get("/my-tickets")
def get_my_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("attendee"))
):
    tickets = (
        db.query(Ticket)
        .filter(Ticket.attendee_id == current_user.id)
        .all()
    )

    return [
        {
            "ticket_id": ticket.id,
            "event_id": ticket.event_id,
            "booking_id": ticket.booking_id,
            "qr_token": ticket.qr_token,
            "status": ticket.status,
            "checked_in": ticket.checked_in
        }
        for ticket in tickets
    ]


# GENERATE QR CODE IMAGE
@router.get("/{ticket_id}/qr")
def generate_qr(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("attendee"))
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.attendee_id == current_user.id
    ).first()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    if ticket.status != "valid":
        raise HTTPException(status_code=400, detail="Ticket is not valid")

    qr = qrcode.make(ticket.qr_token)

    image_buffer = BytesIO()
    qr.save(image_buffer, format="PNG")
    image_buffer.seek(0)

    return StreamingResponse(
        image_buffer,
        media_type="image/png"
    )


# REQUEST BODY FOR GATE SCANNING
class CheckInRequest(BaseModel):
    qr_token: str
    event_id: int


# SCAN TICKET (GATE STAFF ONLY)
@router.post("/check-in")
def check_in_ticket(
    scan_data: CheckInRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("gate_staff"))
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.qr_token == scan_data.qr_token)
        .with_for_update()
        .first()
    )

    if not ticket:
        raise HTTPException(status_code=404, detail="Invalid ticket")

    if ticket.event_id != scan_data.event_id:
        raise HTTPException(
            status_code=400,
            detail="Ticket belongs to another event"
        )

    if ticket.status != "valid":
        raise HTTPException(status_code=400, detail="Ticket is cancelled or invalid")

    if ticket.checked_in:
        raise HTTPException(
            status_code=400,
            detail="Ticket has already been used"
        )

    ticket.checked_in = True
    ticket.checked_in_at = __import__("datetime").datetime.utcnow()

    db.commit()

    return {
        "message": "Check-in successful",
        "ticket_id": ticket.id,
        "event_id": ticket.event_id,
        "checked_in_by": current_user.full_name
    }
