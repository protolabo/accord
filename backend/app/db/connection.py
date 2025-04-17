import sys
import os

from motor.motor_asyncio import AsyncIOMotorClient
import sys
from pathlib import Path
from beanie import init_beanie


# Calculer root 
current_dir = Path(__file__).resolve().parent  # folder of connection.py
root_dir = current_dir.parent.parent  # root folser
sys.path.append(str(root_dir))

# import local files
from app.db.models import User, Email
from app.core.config import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.DB_NAME]

async def init_db():
    await init_beanie(
        database=db,
        document_models=[User, Email]
    )


def get_db():
    return db

if __name__ == "__main__":
    print(db)