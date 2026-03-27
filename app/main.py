from fastapi import FastAPI
from app.core.database import mongodb, neo4j_db
from app.core.config import settings


# Initialize the Fast Api application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description = "Backend API for the Adaptive Learning Platform, providing endpoints for user management, content delivery.",
    version="1.0.0"
    )

# Startup evemt: Open database connections when the server boots
@app.on_event("startup")
async def startup_event():
    print(f"Starting {settings.PROJECT_NAME}...")
    # Connect to MongoDB Atlas
    if mongodb.connect():
        print("MongoDB Atlas connection established at startup.")
    else:
        print("Failed to connect to MongoDB Atlas at startup.")
        
    # Connect to Neo4j AuraDB
    if neo4j_db.connect():
        print("Neo4j AuraDB connection established at startup.")
    else:
        print("Failed to connect to Neo4j AuraDB at startup.")
    
# Shutdown event: Close database connections when the server shuts down
@app.on_event("shutdown")
async def shutdown_event():
    print(f"Shutting down {settings.PROJECT_NAME}...")
    # Close MongoDB connection
    neo4j_db.close()
    # Note: pymongo handles its own connection pooling and cleanup automatically
    print("Database connections closed.")

# Basic health check endpoint to verify everything is running
@app.get("/health", tags = ["System"])
async def health_check():
    return {
        "status": "online",
        "project": settings.PROJECT_NAME,
        "databases": {
            "mongodb": "connected" if mongodb.client else "disconnected",
            "neo4j": "connected" if neo4j_db.driver else "disconnected"
        }
}