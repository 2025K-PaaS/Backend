# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from db.session import engine
from db.base import Base
from routers import auth, users, points 

app = FastAPI(title="Circular Economy API - Auth", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(points.router) 

@app.get("/", tags=["health"])
def health():
    return {"ok": True}
