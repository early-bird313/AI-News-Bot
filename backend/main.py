import os
import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database import init_db, get_stats
from app.api import router as api_router
from app.scheduler import scheduler_engine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing SQLite database...")
    init_db()
    
    logger.info("Starting background scheduler...")
    scheduler_engine.start()
    
    # Check if DB is empty, run initial fetch if needed
    stats = get_stats()
    if stats["total_news"] == 0:
        logger.info("Database is empty. Scheduling initial news crawl...")
        asyncio.create_task(scheduler_engine.run_news_crawler())
        
    yield
    
    # Shutdown
    logger.info("Stopping background scheduler...")
    scheduler_engine.shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan
)

# CORS middleware for development frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)

# Mount static frontend if dist exists
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Allow API routes to be handled by router
        if full_path.startswith("api/"):
            return None
        index_file = FRONTEND_DIST / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "Frontend not built yet. Run `npm run build` in frontend folder."}
else:
    @app.get("/")
    async def root():
        return {
            "message": "AI News Monitoring Backend is running!",
            "dashboard_url": "http://localhost:5173",
            "api_docs": "http://localhost:8000/docs",
            "status": "http://localhost:8000/api/status"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
