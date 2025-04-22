import os
import sys
from emailParser import EnronEmailParser
from generatorMail import generate_massive_dataset

def main():
    # Chemins des fichiers
    csv_path = 'emails.csv'
    json_path = 'emails.json'
    output_dir = 'mockdata'
    

    if not os.path.exists(csv_path):
        print(f"ERREUR: Le fichier de données Enron '{csv_path}' n'est pas disponible.")
        print("Veuillez télécharger les données Enron et les placer dans le répertoire courant.")
        sys.exit(1)
    
    # Étape 1: Parser les emails Enron
    print(f"Étape 1: Analyse des emails Enron depuis '{csv_path}'...")
    parser = EnronEmailParser(csv_path)
    parser.process_dataset(json_path, max_emails=100_000)
    print(f"Analyse terminée. Données stockées dans '{json_path}'.")
    
    # Vérifier si le fichier JSON a été correctement créé
    if not os.path.exists(json_path):
        print(f"ERREUR: La création du fichier JSON '{json_path}' a échoué.")
        sys.exit(1)
    

    print("\nÉtape 2: Génération de 1000 emails fictifs...")
    generate_massive_dataset(1000, output_dir)
    print(f"Génération terminée. Emails fictifs stockés dans le répertoire '{output_dir}'.")
    
    print("\nProcessus complet terminé avec succès!")

if __name__ == "__main__":
    print("=== GÉNÉRATEUR D'EMAILS POUR LE PROJET ACCORD ===")
    main()
