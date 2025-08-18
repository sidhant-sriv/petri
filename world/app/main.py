from fastapi import FastAPI
from . import models
from .db import engine
from .routers import api

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(api.router, prefix="/api")


@app.get("/")
def read_root():
    return {"status": "World is running"}
