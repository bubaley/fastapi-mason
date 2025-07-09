from fastapi import FastAPI

from app.core.database import register_database
from app.project.views import router as project_router

app = FastAPI(
    title='My FastAPI Project',
    version='1.0.0',
    description='REST API with FastAPI, Tortoise ORM and Aerich',
)
register_database(app)

app.include_router(project_router)
