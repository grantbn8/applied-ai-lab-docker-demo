from contextlib import asynccontextmanager

from fastapi import FastAPI

from .database import initialize
from .routes import router


@asynccontextmanager
async def lifespan(app):
    initialize()
    yield


app = FastAPI(title="Local Chat Lab", lifespan=lifespan)
app.include_router(router)
