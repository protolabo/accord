import json
import os
from cryptography.fernet import Fernet
from datetime import datetime


class EmailStorage:
    def __init__(self, storage_dir="temp_storage", encryption_key=None):
        """Initialise le stockage JSON crypté pour les emails.

        Args:
            storage_dir: Répertoire pour stocker les fichiers JSON
            encryption_key: Clé de cryptage. Si None, une nouvelle clé est générée
        """
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

        # Gestion de la clé de cryptage
        if encryption_key:
            self.key = encryption_key
        else:
            key_path = os.path.join(storage_dir, "storage_key.key")
            if os.path.exists(key_path):
                with open(key_path, "rb") as key_file:
                    self.key = key_file.read()
            else:
                self.key = Fernet.generate_key()
                with open(key_path, "wb") as key_file:
                    key_file.write(self.key)

        self.cipher = Fernet(self.key)