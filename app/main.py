from fastapi import FastAPI

from app.routes import auth, bookings, properties

from app.worker.app import app as celery_app

app = FastAPI(
    title="Booking Service API",
    description="API for booking service",
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(bookings.router)
app.include_router(properties.router)


@app.get("/")
async def root():
    return {
        "message": "Booking Service API",
        "docs": "/docs",
        "endpoints": {
            "auth": "/auth",
            "bookings": "/bookings",
            "properties": "/properties",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}
