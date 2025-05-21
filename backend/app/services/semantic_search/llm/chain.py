from langchain.chains import LLMChain
from backend.app.services.semantic_search.llm.parsers import create_fixing_parser
from backend.app.services.semantic_search.llm.prompts import create_query_prompt
from backend.app.services.semantic_search.config import get_llm_config


def create_semantic_parsing_chain():
    """
    Crée une chaîne complète pour le parsing sémantique

    Returns:
        LLMChain: Chaîne configurée pour le parsing sémantique
    """
    # Utiliser le LLM configuré
    llm = get_llm_config()

    # Créer le parser avec correction automatique
    fixing_parser = create_fixing_parser(llm)

    # Créer le prompt avec instructions de format
    prompt = create_query_prompt(fixing_parser)

    # Assembler la chaîne
    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        output_parser=fixing_parser,
        verbose=True
    )

    return chain