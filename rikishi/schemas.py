from datetime import datetime

from ninja import Field, Schema


class DivisionSchema(Schema):
    slug: str
    name: str
    level: int


class RankSchema(Schema):
    slug: str
    division: str
    title: str
    level: int
    order: int
    direction: str


class HeyaSchema(Schema):
    slug: str
    name: str


class ShusshinSchema(Schema):
    slug: str
    name: str
    international: bool


class RikishiSchema(Schema):
    position: int
    id: str
    api_id: int
    name: str
    name_jp: str
    rank: str = Field(None, alias="rank.name")
    heya: str = Field(None, alias="heya.name")
    shusshin: str = Field(None, alias="shusshin.name")
    height: float
    weight: float
    glicko_rating: float = Field(None, alias="glicko.rating")
    birth_date: datetime = None
    debut: datetime = None
    # intai: datetime = None
