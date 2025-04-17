import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
import sys
from pathlib import Path
from beanie import init_beanie
import certifi
import urllib.parse

# Calculer root 
current_dir = Path(__file__).resolve().parent  # folder of connection.py
root_dir = current_dir.parent.parent  # root folser
sys.path.append(str(root_dir))

# import local files
from app.db.models import User, Email
from app.core.config import settings


try:
    # Récupère l'URI de MongoDB depuis les paramètres
    mongodb_uri = settings.MONGO_URI
    
    
    if not mongodb_uri.endswith('/'):
        mongodb_uri += '/'
    
    if settings.DB_NAME not in mongodb_uri:
        mongodb_uri += settings.DB_NAME
    
    
    client = AsyncIOMotorClient(
        mongodb_uri,
        tlsCAFile=certifi.where(),  
        serverSelectionTimeoutMS=10000,  
        connectTimeoutMS=30000, 
        socketTimeoutMS=45000,  
        tls=True,  
        retryWrites=True,  
        w="majority",  
        tlsAllowInvalidCertificates=False,  
        maxPoolSize=50,  
        minPoolSize=10,  
    )
    print(f"Tentative de connexion à MongoDB Atlas: {mongodb_uri}")
    db = client[settings.DB_NAME]
except Exception as e:
    print(f"Erreur lors de la connexion à MongoDB: {str(e)}")

    from pymongo.errors import ServerSelectionTimeoutError
    print("Utilisation d'une base de données simulée pour le développement")
 
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["accord_dev"]

async def init_db():
    try:
        await init_beanie(
            database=db,
            document_models=[User, Email]
        )
        print("Connexion à la base de données établie avec succès!")
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données: {str(e)}")

        raise

def get_db():
    return db

if __name__ == "__main__":
    print(db)