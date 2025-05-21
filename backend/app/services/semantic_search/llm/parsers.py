from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from backend.app.services.semantic_search.models.query_schemas import EmailQuery


def create_pydantic_parser():
    """Crée un parser Pydantic pour la structure EmailQuery"""

    """
    convertit le texte JSON généré par le LLM en objet Python validé (EmailQuery)
    """
    return PydanticOutputParser(pydantic_object=EmailQuery)


def create_fixing_parser(llm):
    """
    Si le LLM génère un JSON mal formé, ce parser utilise le LLM lui-même pour corriger les erreurs

    Args:
        llm: Instance du modèle de langage à utiliser pour la correction

    Returns:
        OutputFixingParser: Parser avec capacité d'auto-correction
    """
    base_parser = create_pydantic_parser()
    return OutputFixingParser.from_llm(
        parser=base_parser,
        llm=llm
    )