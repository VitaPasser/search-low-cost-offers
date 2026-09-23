from sqlalchemy import create_engine

from src.utils.models import BaseModel

engine = create_engine("sqlite:///./data/db.sqlite")
BaseModel.metadata.create_all(engine)
