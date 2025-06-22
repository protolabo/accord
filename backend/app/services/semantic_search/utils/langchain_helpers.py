"""
Helpers LangChain sélectifs pour Accord.
Utilise uniquement les composants utiles de LangChain sans adopter tout le framework.
Focus sur les parsers structurés et la validation de sortie.
"""

from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel, ValidationError
import json

# Import conditionnel de LangChain
try:
    from langchain.output_parsers import PydanticOutputParser
    from langchain.schema import OutputParserException

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class StructuredQueryOutput(BaseModel):
    """Modèle Pydantic pour sortie LLM structurée"""
    query_type: str
    semantic_text: str
    filters: Dict[str, Any] = {}
    confidence: float = 0.5
    reasoning: Optional[str] = None


class LangChainQueryParser:
    """
    Parser utilisant LangChain pour structurer les sorties LLM.
    Fallback gracieux si LangChain non disponible.
    """

    def __init__(self):
        self.parser = None
        self.is_available = False

        if LANGCHAIN_AVAILABLE:
            try:
                self.parser = PydanticOutputParser(pydantic_object=StructuredQueryOutput)
                self.is_available = True
                print("✅ LangChain parser initialisé avec succès")
            except Exception as e:
                print(f"⚠️ Erreur initialisation LangChain parser: {e}")
                self.is_available = False
        else:
            print("⚠️ LangChain non disponible")

    def get_format_instructions(self) -> str:
        """Retourne les instructions de formatage pour le LLM"""
        if self.parser and self.is_available:
            return self.parser.get_format_instructions()

        # Fallback manuel
        return """
Réponds avec un JSON strictement dans ce format:
{
    "query_type": "semantic|contact|time_range|topic|thread|combined",
    "semantic_text": "texte principal de recherche",
    "filters": {
        "contact_email": "email@example.com",
        "contact_name": "Nom Contact", 
        "date_from": "YYYY-MM-DD",
        "date_to": "YYYY-MM-DD",
        "topic_ids": ["topic1", "topic2"],
        "has_attachments": true/false
    },
    "confidence": 0.8,
    "reasoning": "explication optionnelle"
}
"""

    def parse_llm_output(self, llm_output: str) -> Dict[str, Any]:
        """
        Parse la sortie LLM en structure validée

        Args:
            llm_output: Sortie brute du LLM

        Returns:
            Dictionnaire structuré et validé
        """

        if self.parser and self.is_available:
            try:
                # Tentative avec parser LangChain
                parsed = self.parser.parse(llm_output)
                print("✅ Parsing LangChain réussi")
                return parsed.dict()

            except OutputParserException as e:
                print(f"⚠️ Erreur parsing LangChain: {e}")
                # Fallback vers parsing manuel
                return self._manual_json_parse(llm_output)

            except Exception as e:
                print(f"⚠️ Erreur inattendue LangChain: {e}")
                return self._manual_json_parse(llm_output)

        # Si LangChain pas disponible, utiliser parsing manuel
        return self._manual_json_parse(llm_output)

    def _manual_json_parse(self, text: str) -> Dict[str, Any]:
        """Parse JSON manuel avec nettoyage et validation"""

        # Nettoyer le texte
        text = text.strip()

        # Extraire JSON du texte si entouré d'autre contenu
        json_start = text.find('{')
        json_end = text.rfind('}') + 1

        if json_start != -1 and json_end > json_start:
            json_text = text[json_start:json_end]
        else:
            json_text = text

        try:
            parsed = json.loads(json_text)

            # Validation basique
            if not isinstance(parsed, dict):
                raise ValueError("Sortie n'est pas un dictionnaire")

            # Assurer les champs requis avec validation
            validated_parsed = self._validate_parsed_output(parsed)
            print("✅ Parsing JSON manuel réussi")
            return validated_parsed

        except (json.JSONDecodeError, ValueError) as e:
            print(f"⚠️ Erreur parsing JSON manuel: {e}")

            # Fallback ultime
            return {
                "query_type": "semantic",
                "semantic_text": text[:100],  # Utiliser début du texte
                "filters": {},
                "confidence": 0.1,
                "reasoning": f"Fallback parsing - erreur: {str(e)}"
            }

    def _validate_parsed_output(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Valide et nettoie la sortie parsée"""

        # Utiliser Pydantic pour validation si disponible
        if LANGCHAIN_AVAILABLE:
            try:
                validated = StructuredQueryOutput(**parsed)
                return validated.dict()
            except ValidationError as e:
                print(f"⚠️ Erreur validation Pydantic: {e}")

        # Validation manuelle
        cleaned = {}

        # query_type
        valid_types = ['semantic', 'contact', 'time_range', 'topic', 'thread', 'combined']
        cleaned['query_type'] = parsed.get('query_type', 'semantic')
        if cleaned['query_type'] not in valid_types:
            cleaned['query_type'] = 'semantic'

        # semantic_text
        text = parsed.get('semantic_text', '')
        cleaned['semantic_text'] = str(text).strip()[:500]  # Limiter longueur

        # filters
        filters = parsed.get('filters', {})
        cleaned['filters'] = self._validate_filters(filters)

        # confidence
        confidence = parsed.get('confidence', 0.5)
        try:
            cleaned['confidence'] = max(0.0, min(1.0, float(confidence)))
        except (ValueError, TypeError):
            cleaned['confidence'] = 0.5

        # reasoning (optionnel)
        reasoning = parsed.get('reasoning')
        if reasoning:
            cleaned['reasoning'] = str(reasoning)[:200]

        return cleaned

    def _validate_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Valide et nettoie les filtres"""

        if not isinstance(filters, dict):
            return {}

        cleaned_filters = {}

        # contact_email
        email = filters.get('contact_email')
        if email and isinstance(email, str) and '@' in email:
            cleaned_filters['contact_email'] = email.lower().strip()

        # contact_name
        name = filters.get('contact_name')
        if name and isinstance(name, str):
            cleaned_filters['contact_name'] = name.strip()

        # Dates
        for date_field in ['date_from', 'date_to']:
            date_val = filters.get(date_field)
            if date_val and isinstance(date_val, str):
                # Validation format YYYY-MM-DD
                if len(date_val) == 10 and date_val.count('-') == 2:
                    try:
                        parts = date_val.split('-')
                        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                        if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                            cleaned_filters[date_field] = date_val
                    except ValueError:
                        pass

        # topic_ids
        topics = filters.get('topic_ids')
        if topics and isinstance(topics, list):
            valid_topics = [str(t) for t in topics if t]
            if valid_topics:
                cleaned_filters['topic_ids'] = valid_topics[:10]  # Limiter nombre

        # Booléens
        for bool_field in ['has_attachments', 'is_unread', 'is_important']:
            bool_val = filters.get(bool_field)
            if isinstance(bool_val, bool):
                cleaned_filters[bool_field] = bool_val
            elif isinstance(bool_val, str):
                if bool_val.lower() in ['true', '1', 'yes', 'oui']:
                    cleaned_filters[bool_field] = True
                elif bool_val.lower() in ['false', '0', 'no', 'non']:
                    cleaned_filters[bool_field] = False

        return cleaned_filters


class QueryValidationHelper:
    """Helper pour validation et nettoyage des requêtes (conservé pour compatibilité)"""

    @staticmethod
    def validate_query_structure(query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Utilise le nouveau parser pour validation"""
        parser = get_langchain_parser()
        return parser._validate_parsed_output(query_data)


# Instances globales
_langchain_parser: Optional[LangChainQueryParser] = None


def get_langchain_parser() -> LangChainQueryParser:
    """Récupère l'instance singleton du parser LangChain"""
    global _langchain_parser
    if _langchain_parser is None:
        _langchain_parser = LangChainQueryParser()
    return _langchain_parser