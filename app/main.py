from fastapi import FastAPI
from app.api import endpoints
from app.middleware.logging import add_logging_middleware

app = FastAPI()


app.include_router(endpoints.router)

add_logging_middleware(app)
