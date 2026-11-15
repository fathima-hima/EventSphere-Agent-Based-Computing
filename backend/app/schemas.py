
from pydantic import BaseModel, EmailStr, ConfigDict, Field


# User registration request
class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


# User response
class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: str
    is_active: bool

    # Convert SQLAlchemy objects into Pydantic responses
    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# VENUE SCHEMAS

# Data required when creating a new venue
class VenueCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    location: str = Field(min_length=3, max_length=255)
    capacity: int = Field(gt=0)
    description: str | None = None


# Data returned when viewing a venue
class VenueResponse(BaseModel):
    id: int
    name: str
    location: str
    capacity: int
    description: str | None
    is_available: bool

    model_config = ConfigDict(from_attributes=True)


# Data accepted when updating a venue
class VenueUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    location: str | None = Field(default=None, min_length=3, max_length=255)
    capacity: int | None = Field(default=None, gt=0)
    description: str | None = None
    is_available: bool | None = None

from datetime import datetime

# EVENT SCHEMAS

class EventCreate(BaseModel):
    title: str = Field(min_length=2, max_length=150)
    description: str | None = None
    start_time: datetime
    end_time: datetime
    capacity: int = Field(gt=0)
    ticket_price: float = Field(ge=0)
    venue_id: int


class EventResponse(BaseModel):
    id: int
    title: str
    description: str | None
    start_time: datetime
    end_time: datetime
    capacity: int
    ticket_price: float
    status: str
    venue_id: int
    organiser_id: int

    model_config = ConfigDict(from_attributes=True)


class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    capacity: int | None = Field(default=None, gt=0)
    ticket_price: float | None = Field(default=None, ge=0)
    venue_id: int | None = None

    # BOOKING SCHEMAS

class BookingCreate(BaseModel):
    event_id: int
    quantity: int = Field(gt=0, le=10)


class BookingResponse(BaseModel):
    id: int
    quantity: int
    total_amount: float
    status: str
    payment_reference: str | None
    attendee_id: int
    event_id: int

    model_config = ConfigDict(from_attributes=True)