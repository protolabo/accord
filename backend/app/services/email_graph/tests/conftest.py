import pytest
import networkx as nx
import json
from datetime import datetime, timedelta


@pytest.fixture
def empty_graph():
    """Retourne un graphe NetworkX vide."""
    return nx.MultiDiGraph()


@pytest.fixture
def sample_email_data():
    """Retourne un échantillon de données d'email."""
    return {
        "Message-ID": "msg123",
        "Thread-ID": "thread456",
        "Internal-Date": datetime.now().isoformat(),
        "From": "test.sender@example.com",
        "To": "recipient1@example.com, recipient2@example.com",
        "Cc": "cc1@example.com, cc2@example.com",
        "Bcc": "bcc@example.com",
        "Subject": "Test Email",
        "Snippet": "This is a test email",
        "Labels": ["inbox", "important"],
        "Categories": ["work"],
        "Attachments": []
    }


@pytest.fixture
def multiple_emails_data():
    """Retourne un jeu de données avec plusieurs emails."""
    base_date = datetime.now()
    return [
        {
            "Message-ID": f"msg{i}",
            "Thread-ID": f"thread{i // 3}",  # Groupe les emails par thread
            "Internal-Date": (base_date - timedelta(days=i)).isoformat(),
            "From": f"user{i % 5}@example.com",
            "To": f"recipient{(i + 1) % 5}@example.com, recipient{(i + 2) % 5}@example.com",
            "Cc": f"cc{i % 3}@example.com",
            "Subject": f"Test Email {i}",
            "Snippet": f"This is test email {i}"
        }
        for i in range(10)  # Crée 10 emails
    ]


@pytest.fixture
def sample_message_json():
    """Retourne un exemple de message JSON d'entrée."""
    return json.dumps({
        "mails": [
            {
                "Message-ID": "msg123",
                "Thread-ID": "thread456",
                "Internal-Date": datetime.now().isoformat(),
                "From": "test.sender@example.com",
                "To": "recipient1@example.com, recipient2@example.com",
                "Subject": "Test Email"
            }
        ],
        "central_user": "test.sender@example.com",
        "max_emails": 100
    })


@pytest.fixture
def populated_graph():
    """Retourne un graphe pré-rempli avec quelques noeuds et relations."""
    graph = nx.MultiDiGraph()

    # Ajouter quelques noeuds utilisateur
    graph.add_node(
        "user-1",
        type="user",
        email="user1@example.com",
        name="User One",
        domain="example.com",
        is_central_user=True,
        connection_strength=10.0
    )

    graph.add_node(
        "user-2",
        type="user",
        email="user2@example.com",
        name="User Two",
        domain="example.com",
        is_central_user=False,
        connection_strength=5.0
    )

    # Ajouter quelques noeuds message
    graph.add_node(
        "msg-1",
        type="message",
        thread_id="thread-1",
        date=datetime.now().isoformat(),
        from_email="user1@example.com",
        to=["user2@example.com"],
        subject="Test Message"
    )

    graph.add_node(
        "msg-2",
        type="message",
        thread_id="thread-1",
        date=(datetime.now() - timedelta(hours=1)).isoformat(),
        from_email="user2@example.com",
        to=["user1@example.com"],
        subject="Re: Test Message"
    )

    # Ajouter un noeud thread
    graph.add_node(
        "thread-1",
        type="thread",
        message_count=2,
        participants=["user1@example.com", "user2@example.com"],
        subject="Test Thread"
    )

    # Ajouter quelques relations
    graph.add_edge("user-1", "msg-1", type="SENT", weight=3.0)
    graph.add_edge("msg-1", "user-2", type="RECEIVED", weight=1.0)
    graph.add_edge("user-2", "msg-2", type="SENT", weight=1.0)
    graph.add_edge("msg-2", "user-1", type="RECEIVED", weight=1.0)
    graph.add_edge("msg-1", "thread-1", type="PART_OF_THREAD", weight=1.0)
    graph.add_edge("msg-2", "thread-1", type="PART_OF_THREAD", weight=1.0)

    return graph