import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import create_tables, seed_sample_data
from backend.routers import students, roadmap, monitoring, hitl, dashboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("app backend starting")
    create_tables()
    seed_sample_data()
    print("Backend ready")
    yield
    print("shutting down backend")


app = FastAPI(
    title="Sstudize API",
    description="Personalized Study Roadmap Generation System",
    version="0.1.0",
    lifespan=lifespan,
)

#allow frontend to call api
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(students.router)
app.include_router(roadmap.router)
app.include_router(monitoring.router)
app.include_router(hitl.router)
app.include_router(dashboard.router)


@app.middleware("http")
async def log_requests(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    try:
        from analytics.logger import log_event
        log_event(
            event_type="api_call",
            details={"path": str(request.url.path), "method": request.method, "status": response.status_code},
            duration_ms=duration_ms,
        )
    except Exception:
        pass
    return response


@app.get("/")
def root():
    return {"status": "ok", "app": "Sstudize", "version": "0.1.0"}
