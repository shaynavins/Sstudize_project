import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import create_tables, seed_sample_data
from backend.routers import students, roadmap, monitoring, hitl, dashboard, clickstream, system


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
app.include_router(clickstream.router)
app.include_router(system.router)


@app.middleware("http")
async def log_requests(request, call_next):
    import traceback as _tb
    start = time.time()
    status_code = 500
    error_detail = None
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as exc:
        error_detail = _tb.format_exc()
        from fastapi.responses import JSONResponse
        response = JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

    duration_ms = (time.time() - start) * 1000
    try:
        from analytics.logger import log_event
        path = str(request.url.path)
        # Log every API call
        log_event(
            event_type="api_call",
            details={"path": path, "method": request.method, "status": status_code},
            duration_ms=duration_ms,
        )
        # Additionally log errors (4xx/5xx) separately for the error tracker
        if status_code >= 400 or error_detail:
            log_event(
                event_type="api_error",
                details={
                    "path": path, "method": request.method,
                    "status": status_code,
                    "traceback": (error_detail or "")[:2000],
                },
                duration_ms=duration_ms,
            )
        # Log slow requests (>2s) as bottlenecks
        if duration_ms > 2000:
            log_event(
                event_type="slow_request",
                details={"path": path, "method": request.method, "status": status_code},
                duration_ms=duration_ms,
            )
    except Exception:
        pass
    return response


@app.get("/")
def root():
    return {"status": "ok", "app": "Sstudize", "version": "0.1.0"}
