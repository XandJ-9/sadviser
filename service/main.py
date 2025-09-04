from fastapi import FastAPI
from .api.api_router import router

app=FastAPI()

app.include_router(router)


