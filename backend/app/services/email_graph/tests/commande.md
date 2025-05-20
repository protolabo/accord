# Exécuter tous les tests
pytest -xvs tests/

# Exécuter une catégorie spécifique
pytest -xvs tests/models/

# Exécuter un fichier spécifique
pytest -xvs tests/test_processor.py

# Exécuter avec couverture de code
pytest --cov=backend.app.services.email_graph tests/