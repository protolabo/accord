"""
Moteur LLM basé sur Mistral 7B GGUF pour parser les requêtes en langage naturel.
Optimisé avec inférence rapide et faible consommation.
"""

import json
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass

# Import du système LangChain
from .utils.langchain_helpers import get_langchain_parser

# Import conditionnel pour compatibilité
try:
    from llama_cpp import Llama

    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    print("llama-cpp-python non disponible, utilisation du fallback")


@dataclass
class LLMConfig:
    """Configuration du modèle LLM"""
    model_path: str = ""
    n_ctx: int = 8192  # Contexte augmenté
    n_threads: int = -1  # Auto-détection threads
    n_gpu_layers: int = 32  # GPU layers
    temperature: float = 0.05  # Plus déterministe
    max_tokens: int = 300  # Réponses plus longues

    use_mmap: bool = True
    use_mlock: bool = True  # OK sur serveur
    low_vram: bool = False  # Pas de contrainte VRAM


class MistralQueryParser:
    """
    Parser de requêtes utilisant Mistral 7B en mode GGUF avec LangChain parsing.
    Transforme le langage naturel en structure JSON sémantique.
    """

    def __init__(self, config: LLMConfig = None):
        self.config = config or LLMConfig()
        self.model: Optional[Llama] = None

        # Initialiser le parser LangChain
        self.langchain_parser = get_langchain_parser()

        self._load_model()

    def _load_model(self):
        """Charge le modèle Mistral 7B GGUF"""
        if not LLAMA_CPP_AVAILABLE:
            print("⚠️ llama-cpp-python non disponible, parser désactivé")
            return

        try:
            # Configuration optimisée serveur
            self.model = Llama(
                model_path=self.config.model_path,
                n_ctx=self.config.n_ctx,
                n_threads=self.config.n_threads,
                n_gpu_layers=self.config.n_gpu_layers,
                use_mmap=self.config.use_mmap,
                use_mlock=self.config.use_mlock,
                low_vram=self.config.low_vram,
                verbose=False
            )
            print("✅ Modèle Mistral 7B chargé avec succès")
        except Exception as e:
            print(f"❌ Erreur lors du chargement du modèle: {e}")
            self.model = None

    def _build_prompt(self, query: str, user_context: Dict[str, Any] = None) -> str:
        """Construit un prompt plus strict pour forcer la sortie JSON pure."""

        # Instructions LangChain (gardées pour compatibilité)
        format_instructions = self.langchain_parser.get_format_instructions()

        system_prompt = f"""[INST] Tu dois analyser une requête email et retourner UNIQUEMENT du JSON valide.

    IMPORTANT: Réponds SEULEMENT avec le JSON, AUCUN autre texte.

    TYPES:
    - semantic: recherche générale
    - contact: recherche par personne/email  
    - time_range: recherche temporelle
    - topic: recherche par sujet
    - combined: requête mixte

    EXEMPLES:
    emails de Marie → {{"query_type": "contact", "semantic_text": "emails", "filters": {{"contact_name": "Marie"}}}}
    factures hier → {{"query_type": "combined", "semantic_text": "factures", "filters": {{"topic_ids": ["facturation"], "date_from": "2024-01-28"}}}}
    emails test → {{"query_type": "semantic", "semantic_text": "emails test", "filters": {{}}}}

    Query: {query}

    Réponse (JSON uniquement): [/INST]"""

        return system_prompt

    def parse_query(self, query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Parse une requête en langage naturel vers structure sémantique avec LangChain.

        Args:
            query: Requête utilisateur en langage naturel
            user_context: Contexte utilisateur optionnel

        Returns:
            Dict contenant la structure sémantique parsée
        """
        if not self.model:
            # Fallback simple si modèle non disponible
            return self._fallback_parser(query)

        start_time = time.time()

        try:
            prompt = self._build_prompt(query, user_context)

            # Génération avec paramètres optimisés
            response = self.model(
                prompt,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                stop=["[/INST]", "\n\n", "Query:"],
                echo=False
            )

            response_text = response['choices'][0]['text'].strip()
            print(f"🔍 Réponse LLM brute: {response_text}")

            # Parser avec LangChain (validation + correction auto)
            try:
                parsed_response = self.langchain_parser.parse_llm_output(response_text)
                parsing_time = (time.time() - start_time) * 1000

                # Déterminer la méthode réellement utilisée
                parsing_method = 'langchain' if self.langchain_parser.is_available else 'manual_json'

                # Ajouter métadonnées
                parsed_response['_meta'] = {
                    'parsing_time_ms': parsing_time,
                    'model_used': 'mistral-7b',
                    'original_query': query,
                    'parsing_method': parsing_method
                }
                print("utilisation de langchain ")
                return parsed_response

            except Exception as parsing_error:
                print(f"⚠️ Erreur parsing LangChain: {parsing_error}")
                print(f"⚠️ Réponse brute: {response_text}")

                # Fallback sur parsing JSON manuel
                try:
                    parsed_response = json.loads(response_text)
                    parsing_time = (time.time() - start_time) * 1000

                    parsed_response['_meta'] = {
                        'parsing_time_ms': parsing_time,
                        'model_used': 'mistral-7b',
                        'original_query': query,
                        'parsing_method': 'manual_json'
                    }
                    return parsed_response

                except json.JSONDecodeError:
                    print(f"⚠️ Réponse JSON invalide: {response_text}")
                    return self._fallback_parser(query)

        except Exception as e:
            print(f"❌ Erreur lors de la génération LLM: {e}")
            return self._fallback_parser(query)

    def _fallback_parser(self, query: str) -> Dict[str, Any]:
        """
        Parser de fallback basique utilisant des règles simples.
        Utilisé si le modèle LLM n'est pas disponible ou échoue.
        """
        query_lower = query.lower()

        # Détection de patterns simples
        filters = {}
        query_type = "semantic"

        # Détection temporelle
        if any(word in query_lower for word in
               ["hier", "aujourd'hui", "semaine", "mois", "yesterday", "today", "week", "month"]):
            query_type = "time_range"

        # Détection de contacts
        if any(word in query_lower for word in ["de", "par", "expéditeur", "from", "sender", "@"]):
            query_type = "contact"
            # Extraction basique du nom après "de"
            import re
            contact_match = re.search(r'\b(?:de|from)\s+([A-Za-z]+)', query_lower)
            if contact_match:
                filters["contact_name"] = contact_match.group(1).title()

        # Détection pièces jointes
        if any(word in query_lower for word in ["pièce jointe", "fichier", "pdf", "image", "attachment", "file"]):
            filters["has_attachments"] = True

        # Détection topics
        if any(word in query_lower for word in ["facture", "bill", "newsletter", "promotion"]):
            query_type = "topic"

        return {
            "query_type": query_type,
            "semantic_text": query,
            "filters": filters,
            "limit": 10,
            "_meta": {
                "parsing_time_ms": 1.0,
                "model_used": "fallback",
                "original_query": query,
                "parsing_method": "fallback"
            }
        }


# Instance globale pour réutilisation
_parser_instance: Optional[MistralQueryParser] = None


def get_query_parser() -> MistralQueryParser:
    """Singleton pour éviter de recharger le modèle"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = MistralQueryParser()
    return _parser_instance