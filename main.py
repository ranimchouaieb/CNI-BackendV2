from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import auth, formations, cycles, inscriptions, certifications
from routers import users, profiles, messages, supports, dashboard, pdf, ai
from routers import rapports_absence, uploads

app = FastAPI(
    title="CNI Smart Training Path",
    description="Plateforme intelligente de gestion des formations — Centre National de l'Informatique",
    version="2.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.env == "development" else settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Handlers d'exceptions globaux ─────────────────────────────────────────────
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(LookupError)
async def lookup_error_handler(request: Request, exc: LookupError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,           prefix="/auth",           tags=["Auth"])
app.include_router(formations.router,     prefix="/formations",     tags=["Formations"])
app.include_router(cycles.router,         prefix="/cycles",         tags=["Cycles"])
app.include_router(inscriptions.router,   prefix="/inscriptions",   tags=["Inscriptions"])
app.include_router(certifications.router, prefix="/certifications", tags=["Certifications"])
app.include_router(users.router,          prefix="/users",          tags=["Users"])
app.include_router(profiles.router,       prefix="/profiles",       tags=["Profiles"])
app.include_router(messages.router,       prefix="/messages",       tags=["Messages"])
app.include_router(supports.router,       prefix="/supports",       tags=["Supports"])
app.include_router(dashboard.router,      prefix="/dashboard",      tags=["Dashboard"])
app.include_router(pdf.router,            prefix="/pdf",            tags=["PDF"])
app.include_router(ai.router,             prefix="/ai",             tags=["IA"])
app.include_router(rapports_absence.router, prefix="/rapports-absence", tags=["Rapports Absence"])
app.include_router(uploads.router,        prefix="/uploads",        tags=["Uploads"])


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}
