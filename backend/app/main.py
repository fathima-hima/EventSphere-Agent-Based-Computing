
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from . import models

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import get_db
from .models import User, Event, Venue, Booking, Ticket
from .dependencies import require_roles

from .routers.auth import router as auth_router
from .routers.admin import router as admin_router
from .routers.staff import router as staff_router
from .routers.venues import router as venues_router
from .routers.events import router as events_router
from .routers.bookings import router as bookings_router
from .routers.tickets import router as tickets_router
from .routers.agents import router as agents_router
from .routers.waitlist import router as waitlist_router
from .routers.venue_hire import router as venue_hire_router


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EventSphere",
    description="University Event and Venue Booking Platform",
    version="1.0.0"
)

# API ROUTERS
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(staff_router)
app.include_router(venues_router)
app.include_router(events_router)
app.include_router(bookings_router)
app.include_router(tickets_router)
app.include_router(agents_router)
app.include_router(waitlist_router)
app.include_router(venue_hire_router)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# FRONTEND
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

app.mount(
    "/",
    StaticFiles(directory=str(FRONTEND_DIR), html=True),
    name="frontend"
)
