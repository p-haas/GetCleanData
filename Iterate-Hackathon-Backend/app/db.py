# app/db.py
from typing import Optional

from pymongo import MongoClient

from .config import settings

_mongo_client: Optional[MongoClient] = None


def get_mongo_client() -> MongoClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(settings.mongodb_uri)
    return _mongo_client
