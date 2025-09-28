from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import create_tables
from .routes.auth import router as auth_router

app = FastAPI(title="Bulq API", version="0.1.0")

# Include routers
app.include_router(auth_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Create database tables and seed data on startup."""
    create_tables()

    # Create seed data if in development
    import os
    if os.getenv("ENV") == "development":
        try:
            from ..seed_data import create_seed_data
            create_seed_data()
        except ImportError:
            print("Warning: Could not import seed data. Skipping seed data creation.")

@app.get("/")
async def hello_world():
    return {"message": "Hello World from Bulq Backend!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/db-health")
async def db_health_check():
    """Check database connectivity."""
    try:
        from .database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
