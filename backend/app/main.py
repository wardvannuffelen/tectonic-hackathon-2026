from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.data.store import store
from app.routers import (
    auth_router,
    chat_router,
    forecast_router,
    goals_router,
    savings_router,
    scenario_router,
    transactions_router,
)

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    store.build()
    yield


app = FastAPI(title="Wat als? - Financiële toekomstsimulator", lifespan=lifespan)

for router in (
    auth_router.router,
    transactions_router.router,
    forecast_router.router,
    scenario_router.router,
    goals_router.router,
    savings_router.router,
    chat_router.router,
):
    app.include_router(router, prefix="/api")

app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
