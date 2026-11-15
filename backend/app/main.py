
from fastapi import FastAPI

from .routers.admin import router as admin_router
from .database import Base, engine
from . import models
from .routers.auth import router as auth_router
from .routers.staff import router as staff_router
from .routers.venues import router as venues_router
from .routers.events import router as events_router

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EventSphere",
    description="University Event and Venue Booking Platform",
    version="1.0.0"
)

# Register authentication routes
app.include_router(auth_router)
# Register admin routes
app.include_router(admin_router)
# Register staff routes
app.include_router(staff_router)

app.include_router(venues_router)

app.include_router(events_router)

@app.get("/")
def home():
    return {
        "message": "Welcome to EventSphere!",
        "status": "Application is running successfully"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}

