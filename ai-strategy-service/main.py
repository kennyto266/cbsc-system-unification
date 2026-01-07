"""
AI Strategy Service - Main Entry Point
FastAPI service for AI-powered trading strategy generation
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import strategy

app = FastAPI(
    title="AI Strategy Service",
    description="Generate trading strategies using GLM 4.7 AI",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(strategy.router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI Strategy Service is running",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ai-strategy-service",
        "version": "0.1.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
