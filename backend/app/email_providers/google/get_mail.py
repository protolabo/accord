#!/usr/bin/env python3
"""
get_recent_emails.py - Script pour récupérer les derniers messages Gmail
-----------------------------------------------------------------------
Ce script se connecte à Gmail, récupère les messages les plus récents et affiche leurs détails.

Utilisation:
    python get_recent_emails.py [adresse_email] [--count NOMBRE] [--save]
"""

import os
import sys
import json
import webbrowser
import time
import argparse
from pathlib import Path

# Import des modules Gmail existants
from gmail_auth import GmailAuthManager
from gmail_service import GmailService
from settings import Config


def normalize_email_for_storage(email):
    """Normalise l'adresse email pour l'utiliser comme identifiant."""
    return email.lower().strip().replace("@", "_at_").replace(".", "_dot_")


def get_recent_messages(gmail_service, user_id, count=500):
    """
    Récupère les messages les plus récents de l'utilisateur.

    Args:
        gmail_service: Instance de GmailService
        user_id: Identifiant de l'utilisateur
        count: Nombre de messages à récupérer (défaut: 4)

    Returns:
        list: Liste des messages récupérés ou liste vide si aucun message
    """
    try:
        # Obtenir le service Gmail
        service = gmail_service.get_service(user_id)

        # Récupérer les messages les plus récents
        request = service.users().messages().list(
            userId='me',
            maxResults=count  # Nombre de messages souhaité
        )

        response = request.execute()
        message_items = response.get('messages', [])

        if not message_items:
            print("Aucun message trouvé.")
            return []

        messages = []
        print(f"Traitement de {len(message_items)} messages...")

        # Récupérer les détails de chaque message
        for i, message_item in enumerate(message_items, 1):
            print(f"Récupération du message {i}/{len(message_items)}...")
            message_id = message_item['id']
            email_data = gmail_service._get_email_details(service, message_id)
            if email_data:
                messages.append(email_data)

            # Petite pause pour éviter de dépasser les quotas API
            time.sleep(0.1)

        return messages

    except Exception as e:
        print(f"Erreur lors de la récupération des messages: {str(e)}")
        return []


def display_message(email_data, index=None, total=None):
    """
    Affiche les détails d'un message dans un format lisible.

    Args:
        email_data: Données du message à afficher
        index: Index du message dans la liste (optionnel)
        total: Nombre total de messages (optionnel)
    """
    if not email_data:
        return

    # En-tête du message avec numérotation si applicable
    header = " DERNIER MESSAGE "
    if index is not None and total is not None:
        header = f" MESSAGE {index}/{total} "

    print("\n" + "=" * 80)
    print(header.center(80))
    print("=" * 80)

    print(f"Date       : {email_data.get('Date', 'Non disponible')}")
    print(f"De         : {email_data.get('From', 'Non disponible')}")
    print(f"À          : {email_data.get('To', 'Non disponible')}")
    print(f"Sujet      : {email_data.get('Subject', 'Non disponible')}")
    print(f"Labels     : {', '.join(email_data.get('Labels', []))}")

    print("\nAPERÇU")
    print("-" * 80)
    print(email_data.get('Snippet', 'Aperçu non disponible'))
    print("-" * 80)

    # Afficher le corps du message
    body = email_data.get('Body', {})

    if body.get('plain'):
        print("\nCORPS DU MESSAGE (texte brut)")
        print("-" * 80)
        # Limiter l'affichage à un nombre raisonnable de lignes
        plain_text = body['plain']
        lines = plain_text.split('\n')
        if len(lines) > 15:  # Réduit à 15 lignes pour l'affichage multiple
            print('\n'.join(lines[:15]))
            print(f"\n[...{len(lines) - 15} lignes supplémentaires non affichées...]")
        else:
            print(plain_text)

    # Afficher les pièces jointes s'il y en a
    attachments = email_data.get('Attachments', [])
    if attachments:
        print("\nPIÈCES JOINTES")
        print("-" * 80)
        for i, attachment in enumerate(attachments, 1):
            print(f"{i}. {attachment.get('filename', 'Sans nom')} "
                  f"({attachment.get('mimeType', 'Type inconnu')}, "
                  f"{attachment.get('size', 0)} octets)")


def display_messages(messages):
    """
    Affiche une liste de messages.

    Args:
        messages: Liste des messages à afficher
    """
    if not messages:
        print("Aucun message à afficher.")
        return

    total = len(messages)
    for i, message in enumerate(messages, 1):
        display_message(message, i, total)

        # Ajouter un séparateur entre les messages, sauf après le dernier
        if i < total:
            print("\n" + "-" * 80 + "\n")


def parse_arguments():
    """Parse les arguments de ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Récupère et affiche les derniers messages Gmail."
    )
    parser.add_argument(
        "email",
        nargs="?",
        help="Adresse email Gmail à utiliser"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=500,
        help="Nombre de messages à récupérer (défaut: 4)"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Sauvegarder les messages dans un fichier JSON"
    )

    return parser.parse_args()


def main():
    """Fonction principale du script."""
    # Parser les arguments
    args = parse_arguments()

    # Demander l'email si non fourni
    email = args.email
    if not email:
        email = input("Entrez votre adresse email Gmail: ")

    user_id = normalize_email_for_storage(email)

    print(f"Utilisation de l'email: {email}")
    print(f"ID utilisateur: {user_id}")
    print(f"Nombre de messages à récupérer: {args.count}")

    # Instancier les services
    auth_manager = GmailAuthManager(Config.GOOGLE_CREDENTIALS_PATH, Config.TOKEN_DIR)
    gmail_service = GmailService(Config.GOOGLE_CREDENTIALS_PATH, Config.TOKEN_DIR)

    # Vérifier l'authentification
    print("Vérification de l'authentification...")
    is_auth = auth_manager.is_authenticated(user_id)

    if not is_auth:
        print("Utilisateur non authentifié. Lancement du processus d'authentification...")
        auth_url = auth_manager.get_auth_url(user_id)

        print("\n=================================================")
        print("IMPORTANT: Votre serveur FastAPI doit être démarré!")
        print("Exécutez 'python main.py' dans un autre terminal")
        print("=================================================\n")

        print(f"URL d'authentification: {auth_url}")

        # Proposer d'ouvrir l'URL
        choice = input("Ouvrir l'URL dans le navigateur? (o/n): ")
        if choice.lower() in ["o", "oui", "y", "yes"]:
            webbrowser.open(auth_url)

        print("\nSuivez les instructions dans le navigateur.")
        input("Appuyez sur Entrée une fois l'authentification terminée...")

        # Vérifier à nouveau
        is_auth = auth_manager.is_authenticated(user_id)

    if not is_auth:
        print("Échec de l'authentification. Vérifiez les erreurs et réessayez.")
        sys.exit(1)

    print("Authentification réussie!")

    # Récupérer les messages récents
    print(f"Récupération des {args.count} derniers messages...")
    messages = get_recent_messages(gmail_service, user_id, args.count)

    if messages:
        # Afficher les messages
        #display_messages(messages)

        # Sauvegarder si demandé
        if True:
            filename = f"messages_recents_{user_id}_{int(time.time())}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
            print(f"\nMessages sauvegardés dans {filename}")
    else:
        print("Aucun message n'a pu être récupéré.")


if __name__ == "__main__":
    main()