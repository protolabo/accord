import os
from backend.app.utils.absolute_path import get_file_path

def delete_token_file():
    file_path = get_file_path("backend/app/email_providers/google/tokens/user_at_accord_dot_com.json")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"Fichier supprimé avec succès : {file_path}")
        except Exception as e:
            print(f"Erreur lors de la suppression du fichier : {e}")
    else:
        print(f"Le fichier n'existe pas : {file_path}")


#if __name__ == "__main__":
#    delete_token_file()
