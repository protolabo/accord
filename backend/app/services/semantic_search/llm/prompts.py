from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate


def create_query_prompt(parser):
    """
    Crée un template de prompt pour la transformation de requêtes

    Args:
        parser: Parser qui fournira les instructions de format

    Returns:
        ChatPromptTemplate: Template de prompt prêt à l'emploi
    """
    system_template = """
    Tu es AccordParse, un assistant qui transforme les requêtes
    d'email en JSON structuré. Ton travail est de comprendre l'intention
    de l'utilisateur et de la traduire en requête formelle.

    Même si la requête est vague ou incomplète, essaie de déduire
    l'intention la plus probable.

    Réponds UNIQUEMENT par du JSON valide suivant ce format:

    {format_instructions}
    """

    # from langchain
    system_message_prompt = SystemMessagePromptTemplate.from_template(
        system_template,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    # Partie pour la requête utilisateur
    human_template = "{query}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    # Assemblage du prompt complet
    chat_prompt = ChatPromptTemplate.from_messages([
        system_message_prompt,
        human_message_prompt
    ])

    return chat_prompt