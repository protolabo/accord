from motor.motor_asyncio import AsyncIOMotorClient
import sys
from pathlib import Path

# Calculer root 
current_dir = Path(__file__).resolve().parent  # connection.py所在目录
root_dir = current_dir.parent.parent  # 上两级目录（项目根目录）
sys.path.append(str(root_dir))

# import local files
from app.core.config import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.DB_NAME]

def get_db():
    return db

if __name__ == "__main__":
    print(get_db())