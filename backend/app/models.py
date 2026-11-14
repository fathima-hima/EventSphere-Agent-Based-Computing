
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Float,
    Text
)
from sqlalchemy.orm import relationship

from .database import Base


# 1. USERS TABLE
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)

    events = relationship("Event", back_populates="organiser")
    bookings = relationship("Booking", back_populates="attendee")


# 2. VENUES TABLE
class Venue(Base):
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    location = Column(String(255), nullable=False)
    capacity = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    is_available = Column(Boolean, default=True)

    events = relationship("Event", back_populates="venue")


# 3. EVENTS TABLE
class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    capacity = Column(Integer, nullable=False)
    ticket_price = Column(Float, default=0.0)
    status = Column(String(30), default="upcoming")

    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
    organiser_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    venue = relationship("Venue", back_populates="events")
    organiser = relationship("User", back_populates="events")
    bookings = relationship("Booking", back_populates="event")


# 4. BOOKINGS TABLE
class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String(30), default="confirmed")
    payment_reference = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    attendee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)

    attendee = relationship("User", back_populates="bookings")
    event = relationship("Event", back_populates="bookings")
