# backend/app/services/ai/tests/test_pipeline.py
import sys
import os
import json
import unittest

# Ajoutez le répertoire parent au chemin
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.services.ai.pipeline import process_email


class TestPipeline(unittest.TestCase):
    def test_action_email(self):
        action_email = {
            "Subject": "Confirmation de rendez-vous",
            "Body": {
                "plain": "Bonjour,\n\nVeuillez confirmer votre rendez-vous prévu le 15 mai à 14h00.\n\nCordialement,\nService des rendez-vous"
            }
        }
        result = process_email(action_email)
        self.assertEqual(result["main_class"], ["Action"])
        self.assertTrue(len(result["sub_classes"]) > 0)

    def test_information_email(self):
        info_email = {
            "Subject": "Mise à jour de notre politique de confidentialité",
            "Body": {
                "plain": "Cher utilisateur,\n\nNous avons mis à jour notre politique de confidentialité. Aucune action n'est requise de votre part.\n\nCordialement,\nL'équipe"
            }
        }
        result = process_email(info_email)
        self.assertEqual(result["main_class"], ["Informations"])

    def test_thread_email(self):
        thread_email = {
            "Subject": "À propos de notre discussion",
            "Body": {
                "plain": "Bonjour,\n\nMerci pour votre message. C'était un plaisir de discuter avec vous hier.\n\nCordialement,\nJean"
            }
        }
        result = process_email(thread_email)
        self.assertEqual(result["main_class"], ["Threads"])

    def test_empty_values(self):
        # Test avec des valeurs vides ou nulles
        empty_email = {
            "Subject": "",
            "Body": ""
        }
        result = process_email(empty_email)
        self.assertTrue(isinstance(result["main_class"], list))
        self.assertTrue(isinstance(result["sub_classes"], list))

    def test_real_example(self):
        # Test avec l'exemple fourni
        """
        real_email = {
            "Subject": "Two-Factor Authentication Code",
            "Body": {
                "plain": "Hello Sheila,\n\nTo ensure that only you have attempted to log into your account, kindly confirm the below entry code: 468302. If this wasn't an action initiated by yourself, it could indicate unauthorized access.\n\nSecurity Team\n\n--\nAlexander Smith\nMarketing Director\nMarketing\nGmail\nTel: 745.591.7649x424"
            }
        }
        result = process_email(real_email)
        print(f"Classification de l'exemple réel: {result}")
        self.assertEqual(result["main_class"], ["Action"])
        """

        real_email = {
            "Subject": "Two-Factor Authentication Code",
            "Body": {
                "plain": "Hello Sheila,\n\nTo ensure that only you have attempted to log into your account, kindly confirm the below entry code: 468302. If this wasn't an action initiated by yourself, it could indicate unauthorized access.\n\nSecurity Team\n\n--\nAlexander Smith\nMarketing Director\nMarketing\nGmail\nTel: 745.591.7649x424",
            }
        }
        result = process_email(real_email)
        print(f"Classification de l'exemple réel: {result}")
        self.assertEqual(result["main_class"], ["Action"])


if __name__ == '__main__':
    unittest.main()