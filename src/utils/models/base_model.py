from sqlmodel import SQLModel, Field


class BaseModel(SQLModel, table=False):
    __table_args__ = {'extend_existing': True}
    id: int|None = Field(default=None, primary_key=True)
