
from pymongo import MongoClient
from pymongo.server_api import ServerApi

from app.core.config import settings

client = None
database = None


def get_database():
    global client, database

    if database is not None:
        return database

    if not settings.MONGODB_URL:
        raise RuntimeError("MONGODB_URL is not configured.")

    client = MongoClient(
        settings.MONGODB_URL,
        server_api=ServerApi("1"),
        serverSelectionTimeoutMS=5000,
    )

    database = client[settings.MONGODB_DATABASE]
    return database


def check_database_connection():
    db = get_database()
    db.command("ping")
    return True
