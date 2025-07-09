from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from app.core.settings import settings

MODELS = ['app.project.models']

TORTOISE_ORM = {
    'connections': {'default': settings.database_url},
    'apps': {
        'models': {
            'models': [*MODELS, 'aerich.models'],
            'default_connection': 'default',
        },
    },
}


def register_database(app: FastAPI):
    register_tortoise(
        app,
        db_url=settings.database_url,
        modules={'models': MODELS},
        generate_schemas=False,
        add_exception_handlers=True,
    )
