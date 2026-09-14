from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import aziende, funzioni, calcolo, export

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Workforce Planning Tool — API",
    description="Motore di calcolo FTE multi-settore per aziende italiane. Fase 1 MVP: settore Manifattura.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(aziende.router)
app.include_router(funzioni.router)
app.include_router(calcolo.router)
app.include_router(export.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "workforce-planning-tool-api"}
