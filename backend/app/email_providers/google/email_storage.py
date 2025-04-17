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

    def save_emails(self, user_id, emails):
        """Sauvegarde les emails d'un utilisateur dans un fichier JSON crypté."""
        data = {
            "user_id": user_id,
            "collection_date": datetime.utcnow().isoformat(),
            "emails": emails
        }

        json_data = json.dumps(data)
        encrypted_data = self.cipher.encrypt(json_data.encode('utf-8'))

        file_path = os.path.join(self.storage_dir, f"{user_id}_emails.enc")
        with open(file_path, "wb") as file:
            file.write(encrypted_data)

        return file_path

    def load_emails(self, user_id):
        """Charge les emails d'un utilisateur depuis un fichier JSON crypté."""
        file_path = os.path.join(self.storage_dir, f"{user_id}_emails.enc")

        if not os.path.exists(file_path):
            return None

        with open(file_path, "rb") as file:
            encrypted_data = file.read()

        decrypted_data = self.cipher.decrypt(encrypted_data)
        data = json.loads(decrypted_data.decode('utf-8'))

        return data["emails"]

    def save_intelligent_structure(self, user_id, structure_type, data):
        """Sauvegarde une structure de données dérivée (graphe, classification, etc.)."""
        json_data = json.dumps(data)
        encrypted_data = self.cipher.encrypt(json_data.encode('utf-8'))

        file_path = os.path.join(self.storage_dir, f"{user_id}_{structure_type}.enc")
        with open(file_path, "wb") as file:
            file.write(encrypted_data)

        return file_path

    def load_intelligent_structure(self, user_id, structure_type):
        """Charge une structure de données dérivée."""
        file_path = os.path.join(self.storage_dir, f"{user_id}_{structure_type}.enc")

        if not os.path.exists(file_path):
            return None

        with open(file_path, "rb") as file:
            encrypted_data = file.read()

        decrypted_data = self.cipher.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode('utf-8'))

    def cleanup_raw_emails(self, user_id):
        """Supprime les emails bruts après traitement."""
        file_path = os.path.join(self.storage_dir, f"{user_id}_emails.enc")
        if os.path.exists(file_path):
            os.remove(file_path)