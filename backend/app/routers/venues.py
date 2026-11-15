
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..schemas import VenueCreate, VenueResponse, VenueUpdate
from ..database import get_db
from ..models import Venue, User
from ..schemas import VenueCreate, VenueResponse
from ..dependencies import require_roles


# Router for venue management
router = APIRouter(
    prefix="/api/venues",
    tags=["Venues"]
)


# CREATE VENUE: Only admins can add new venues
@router.post(
    "/",
    response_model=VenueResponse,
    status_code=status.HTTP_201_CREATED
)
def create_venue(
    venue_data: VenueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    # Create a new venue using the submitted information
    new_venue = Venue(
        name=venue_data.name,
        location=venue_data.location,
        capacity=venue_data.capacity,
        description=venue_data.description,
        is_available=True
    )

    # Save the venue in the database
    db.add(new_venue)
    db.commit()
    db.refresh(new_venue)

    return new_venue


# GET ALL VENUES: Retrieve all venues from the database
@router.get("/", response_model=list[VenueResponse])
def get_all_venues(
    db: Session = Depends(get_db)
):
    venues = db.query(Venue).all()

    return venues


# UPDATE VENUE: Allow admins to modify existing venue details
@router.put("/{venue_id}", response_model=VenueResponse)
def update_venue(
    venue_id: int,
    venue_data: VenueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    # Find the venue using its ID
    venue = db.query(Venue).filter(Venue.id == venue_id).first()

    # Check whether the venue exists
    if not venue:
        raise HTTPException(
            status_code=404,
            detail="Venue not found"
        )

    # Update only the fields provided in the request
    update_data = venue_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(venue, field, value)

    # Save the updated venue
    db.commit()
    db.refresh(venue)

    return venue

# DELETE A VENUE (ADMIN ONLY)
@router.delete("/{venue_id}")
def delete_venue(
    venue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    venue = db.query(Venue).filter(Venue.id == venue_id).first()

    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")

    db.delete(venue)
    db.commit()

    return {"message": "Venue deleted successfully"}