from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = 'My FastAPI App'

    debug: bool = Field(True)
    database_url: str = Field('sqlite://db.sqlite3')


settings = Settings()
