# optimized_graph_test.py
import json
import os
import re
import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter


class OptimizedGraphQueryTool:
    """Tool for testing and querying an optimized email connection graph."""

    def __init__(self, graph_dir):
        """
        Initialize the tool with a graph directory.

        Args:
            graph_dir: Path to the directory containing graph component files
        """
        # Ensure graph_dir is a Path object
        self.graph_dir = Path(graph_dir)
        if not self.graph_dir.exists():
            raise ValueError(f"Graph directory {graph_dir} does not exist")

        # Load graph components from files
        self.graph = self._load_graph(self.graph_dir)

        # Create indexes for quick access
        self.user_map = {user["id"]: user for user in self.graph["users"]}
        self.email_to_user = {user["email"]: user for user in self.graph["users"]}
        self.message_map = {msg["id"]: msg for msg in self.graph["messages"]}
        self.thread_map = {thread["id"]: thread for thread in self.graph["threads"]}
        self.topic_map = {topic["id"]: topic for topic in self.graph["topics"]}

        # Get the central user
        self.central_user = self.graph.get("central_user", None)
        if self.central_user:
            print(f"Central user: {self.central_user['email']}")
        else:
            # Try to find central user from metadata
            metadata = self._load_json_file(self.graph_dir / "metadata.json")
            if metadata and "central_user_email" in metadata:
                central_email = metadata["central_user_email"]
                for user in self.graph["users"]:
                    if user.get("email") == central_email:
                        self.central_user = user
                        print(f"Central user: {central_email}")
                        break

            if not self.central_user:
                print("Warning: No central user found in the graph")


        # Build relation indexes
        self._build_relation_indexes()

    def _load_graph(self, graph_dir):
        """Load graph components from the optimized directory structure."""
        # Ensure graph_dir is a Path object
        if isinstance(graph_dir, str):
            graph_dir = Path(graph_dir)

        graph = {
            "users": [],
            "messages": [],
            "threads": [],
            "topics": [],
            "relations": []
        }

        # Phase 1: Load base components
        phase1_dir = graph_dir / "phase1"
        if phase1_dir.exists():
            # Load from phase1 directory
            for component in ["users", "messages", "threads", "topics"]:
                component_file = phase1_dir / f"{component}.json"
                if component_file.exists():
                    component_data = self._load_json_file(component_file)
                    if component_data:
                        graph[component] = list(component_data.values())
                        print(f"Loaded {len(graph[component])} {component} from phase1")
        else:
            # Try to load from root directory if phase1 doesn't exist
            for component in ["users", "messages", "threads", "topics"]:
                component_file = graph_dir / f"{component}.json"
                if component_file.exists():
                    component_data = self._load_json_file(component_file)
                    if component_data:
                        if isinstance(component_data, dict):
                            graph[component] = list(component_data.values())
                        else:
                            graph[component] = component_data
                        print(f"Loaded {len(graph[component])} {component}")

        # Load relations from thread_relations.json and similarity_relations.json
        thread_relations_file = graph_dir / "thread_relations.json"
        if thread_relations_file.exists():
            thread_relations = self._load_json_file(thread_relations_file)
            if thread_relations:
                graph["relations"].extend(thread_relations)
                print(f"Loaded {len(thread_relations)} thread relations")

        similarity_relations_file = graph_dir / "similarity_relations.json"
        if similarity_relations_file.exists():
            similarity_relations = self._load_json_file(similarity_relations_file)
            if similarity_relations:
                graph["relations"].extend(similarity_relations)
                print(f"Loaded {len(similarity_relations)} similarity relations")

        # Check if we have all components
        if not graph["users"] or not graph["messages"] or not graph["threads"]:
            print("Warning: Some critical graph components are missing")

        return graph

    def _load_json_file(self, file_path):
        """Load and parse a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {str(e)}")
            return None

    def _build_relation_indexes(self):
        """Build indexes for quick relation lookups."""
        # Index for relations source -> [relations]
        self.source_relations = defaultdict(list)
        # Index for relations target -> [relations]
        self.target_relations = defaultdict(list)
        # Index for relations by type
        self.relation_types = defaultdict(list)

        # Also build specific indexes for message and thread relations
        self.message_relations = defaultdict(list)
        self.thread_relations = defaultdict(list)

        for relation in self.graph["relations"]:
            source_id = relation["source_id"]
            target_id = relation["target_id"]
            relation_type = relation["relation_type"]

            self.source_relations[source_id].append(relation)
            self.target_relations[target_id].append(relation)
            self.relation_types[relation_type].append(relation)

            # Add to message relations if this is a message-related relation
            if source_id in self.message_map or target_id in self.message_map:
                if source_id in self.message_map:
                    self.message_relations[source_id].append(relation)
                if target_id in self.message_map:
                    self.message_relations[target_id].append(relation)

            # Add to thread relations if this is a thread-related relation
            if source_id in self.thread_map or target_id in self.thread_map:
                if source_id in self.thread_map:
                    self.thread_relations[source_id].append(relation)
                if target_id in self.thread_map:
                    self.thread_relations[target_id].append(relation)

    # Helper function to safely get message attributes with defaults
    def _get_message_attr(self, message, attr, default="[Content not available]"):
        """Safely get message attributes with a default value for missing content."""
        return message.get(attr, default)

    def print_graph_summary(self):
        """Display a summary of the optimized graph."""
        print("\n===== GRAPH SUMMARY =====")
        print(f"Total users: {len(self.graph['users'])}")
        print(f"Total messages: {len(self.graph['messages'])}")
        print(f"Total threads: {len(self.graph['threads'])}")
        print(f"Total topics: {len(self.graph['topics'])}")
        print(f"Total relations: {len(self.graph['relations'])}")

        # Count messages involving the central user
        central_messages = [m for m in self.graph["messages"] if m.get("involves_central_user", False)]
        print(f"Messages involving central user: {len(central_messages)}")

        # Count threads involving the central user
        central_threads = [t for t in self.graph["threads"] if t.get("involves_central_user", False)]
        print(f"Threads involving central user: {len(central_threads)}")

        # Display relation type distribution
        relation_counts = Counter([r["relation_type"] for r in self.graph["relations"]])
        print("\nRelation type distribution:")
        for rel_type, count in relation_counts.most_common():
            print(f"  - {rel_type}: {count}")

        # Display most frequent domains
        domains = Counter([user.get("domain", "unknown") for user in self.graph["users"]])
        print("\nMost frequent domains:")
        for domain, count in domains.most_common(5):
            print(f"  - {domain}: {count} users")

        # Display most popular topics
        topic_counts = Counter([(topic["name"], topic.get("message_count", 0)) for topic in self.graph["topics"]])
        print("\nMost popular topics:")
        for (topic_name, count), _ in topic_counts.most_common(5):
            print(f"  - {topic_name}: {count} messages")

    def find_user_messages(self, email=None, sent_only=False, received_only=False, limit=10):
        """
        Find all messages of a specific user.

        Args:
            email: User's email (uses central user by default)
            sent_only: If True, show only sent messages
            received_only: If True, show only received messages
            limit: Maximum number of messages to display
        """
        if not email and self.central_user:
            email = self.central_user["email"]

        if not email:
            print("No user specified and no central user found")
            return

        user = self.email_to_user.get(email)
        if not user:
            print(f"User {email} not found in the graph")
            return

        print(f"\n===== MESSAGES FOR {email} =====")

        # Find all messages sent by this user
        sent_messages = []
        if not received_only:
            for relation in self.relation_types.get("SENT", []):
                if relation["source_id"] == user["id"]:
                    message_id = relation.get("message_id", relation["target_id"])
                    if message_id in self.message_map:
                        sent_messages.append(self.message_map[message_id])

            print(f"Messages sent: {len(sent_messages)}")

        # Find all messages received by this user
        received_messages = []
        if not sent_only:
            for relation in self.relation_types.get("RECEIVED", []):
                if relation["target_id"] == user["id"]:
                    message_id = relation.get("message_id", relation["source_id"])
                    if message_id in self.message_map:
                        received_messages.append(self.message_map[message_id])

            # Also add messages where user is in CC
            for relation in self.relation_types.get("CC", []):
                if relation["target_id"] == user["id"]:
                    message_id = relation.get("message_id", relation["source_id"])
                    if message_id in self.message_map:
                        received_messages.append(self.message_map[message_id])

            print(f"Messages received: {len(received_messages)}")

        # Display recent sent messages
        if sent_messages and not received_only:
            print("\nRecent sent messages:")
            sorted_sent = sorted(sent_messages, key=lambda m: m.get("date", ""), reverse=True)
            for i, message in enumerate(sorted_sent[:limit], 1):
                # Use placeholders for missing content
                subject = self._get_message_attr(message, "subject", "[No subject]")
                date = self._get_message_attr(message, "date", "[No date]")
                snippet = self._get_message_attr(message, "snippet", "[No preview available]")

                print(f"{i}. {date} - {subject}")
                print(f"   To: {', '.join(message.get('to', []))}")
                if message.get('cc'):
                    print(f"   Cc: {', '.join(message.get('cc', []))}")
                print(f"   Message ID: {message['id']}")
                print(f"   {snippet}")
                print()

        # Display recent received messages
        if received_messages and not sent_only:
            print("\nRecent received messages:")
            sorted_received = sorted(received_messages, key=lambda m: m.get("date", ""), reverse=True)
            for i, message in enumerate(sorted_received[:limit], 1):
                # Use placeholders for missing content
                subject = self._get_message_attr(message, "subject", "[No subject]")
                date = self._get_message_attr(message, "date", "[No date]")
                snippet = self._get_message_attr(message, "snippet", "[No preview available]")

                print(f"{i}. {date} - {subject}")
                print(f"   From: {message.get('from', 'Unknown')}")
                print(f"   Message ID: {message['id']}")
                print(f"   {snippet}")
                print()

    def find_conversations_between_users(self, email1, email2=None):
        """
        Find all conversations between two users.

        Args:
            email1: First user's email
            email2: Second user's email (uses central user by default)
        """
        if not email2 and self.central_user:
            email2 = self.central_user["email"]

        if not email2:
            print("No second user specified and no central user found")
            return

        user1 = self.email_to_user.get(email1)
        user2 = self.email_to_user.get(email2)

        if not user1:
            print(f"User {email1} not found in the graph")
            return

        if not user2:
            print(f"User {email2} not found in the graph")
            return

        print(f"\n===== CONVERSATIONS BETWEEN {email1} AND {email2} =====")

        # Find threads where both users are participants
        common_threads = []
        for thread in self.graph["threads"]:
            participants = [p.lower().strip() for p in thread.get("participants", [])]
            email1_norm = email1.lower().strip()
            email2_norm = email2.lower().strip()

            if email1_norm in participants and email2_norm in participants:
                common_threads.append(thread)

        if not common_threads:
            print(f"No conversations found between {email1} and {email2}")
            return

        # Sort threads by last message date (most recent first)
        sorted_threads = sorted(common_threads, key=lambda t: t.get("last_message_date", ""), reverse=True)

        # Display threads
        for i, thread in enumerate(sorted_threads, 1):
            # Use placeholders for missing content
            subject = self._get_message_attr(thread, "subject", "[No subject]")

            print(f"{i}. Subject: {subject}")
            print(f"   - Last message: {thread.get('last_message_date', 'Unknown')}")
            print(f"   - Number of messages: {thread.get('message_count', 0)}")

            # Find some messages in this thread
            thread_messages = []
            for msg in self.graph["messages"]:
                if msg.get("thread_id") == thread["id"]:
                    thread_messages.append(msg)

            # Sort by date and display a sample
            if thread_messages:
                sorted_messages = sorted(thread_messages, key=lambda m: m.get("date", ""))
                print("   - Message samples:")
                for j, msg in enumerate(sorted_messages[:3], 1):
                    from_user = msg.get("from", "")
                    # Determine if it's user1, user2 or someone else
                    sender_tag = ""
                    if from_user.lower() == email1.lower():
                        sender_tag = f"[{email1}]"
                    elif from_user.lower() == email2.lower():
                        sender_tag = f"[{email2}]"

                    # Get message snippet with placeholder if missing
                    snippet = self._get_message_attr(msg, "snippet", "[No preview available]")
                    print(f"     {j}. {msg.get('date', 'Unknown')} {sender_tag}: {snippet}")
            print()

    def search_by_topic(self, topic_name, limit=10):
        """
        Search for messages by topic.

        Args:
            topic_name: Topic name to search for
            limit: Maximum number of messages to display
        """
        print(f"\n===== SEARCH BY TOPIC: '{topic_name}' =====")

        # Find matching topics (case-insensitive)
        matching_topics = []
        for topic in self.graph["topics"]:
            if topic_name.lower() in topic["name"].lower():
                matching_topics.append(topic)

        if not matching_topics:
            print(f"No topics found for '{topic_name}'")
            return

        # Display found topics
        print(f"Topics found: {len(matching_topics)}")
        for topic in matching_topics:
            print(f"- {topic['name']} ({topic.get('message_count', 0)} messages)")

        # Find messages with HAS_TOPIC relations
        all_messages = []
        for topic in matching_topics:
            topic_id = topic["id"]
            # Find relations where this topic is the target
            for relation in self.relation_types.get("HAS_TOPIC", []):
                if relation["target_id"] == topic_id:
                    message_id = relation["source_id"]
                    if message_id in self.message_map:
                        all_messages.append(self.message_map[message_id])

        # Deduplicate messages (a message can have multiple topics)
        unique_messages = {msg["id"]: msg for msg in all_messages}

        # Sort by date (most recent first) and display
        sorted_messages = sorted(unique_messages.values(), key=lambda m: m.get("date", ""), reverse=True)

        print(f"\nMessages found: {len(sorted_messages)}")
        for i, message in enumerate(sorted_messages[:limit], 1):
            # Use placeholders for missing content
            subject = self._get_message_attr(message, "subject", "[No subject]")
            snippet = self._get_message_attr(message, "snippet", "[No preview available]")

            print(f"{i}. {message.get('date', 'No date')} - {subject}")
            print(f"   From: {message.get('from', 'Unknown')}")
            to_str = ', '.join(message.get('to', []))
            if len(to_str) > 50:
                to_str = to_str[:47] + "..."
            print(f"   To: {to_str}")
            print(f"   Message ID: {message['id']}")
            print(f"   {snippet}")

            # Display thread info
            thread_id = message.get("thread_id")
            if thread_id in self.thread_map:
                thread = self.thread_map[thread_id]
                thread_subject = self._get_message_attr(thread, "subject", "[No subject]")
                print(f"   Thread: {thread_subject} ({thread.get('message_count', 0)} messages)")
            print()

    def find_similar_messages(self, message_id, limit=5):
        """
        Find messages similar to a given message.

        Args:
            message_id: ID of the reference message
            limit: Maximum number of similar messages to display
        """
        if message_id not in self.message_map:
            print(f"Message {message_id} not found in the graph")
            return

        reference_message = self.message_map[message_id]
        # Use placeholders for missing content
        subject = self._get_message_attr(reference_message, "subject", "[No subject]")
        print(f"\n===== MESSAGES SIMILAR TO: '{subject}' =====")

        # Find SIMILAR_CONTENT relations
        similar_messages = []
        for relation in self.relation_types.get("SIMILAR_CONTENT", []):
            if relation["source_id"] == message_id:
                target_id = relation["target_id"]
                if target_id in self.message_map:
                    similar_messages.append((self.message_map[target_id], relation.get("similarity_score", 0)))
            elif relation["target_id"] == message_id:
                source_id = relation["source_id"]
                if source_id in self.message_map:
                    similar_messages.append((self.message_map[source_id], relation.get("similarity_score", 0)))

        if not similar_messages:
            print("No similar messages found")
            return

        # Sort by similarity score (highest first)
        sorted_similar = sorted(similar_messages, key=lambda x: x[1], reverse=True)

        # Display similar messages
        print(f"Similar messages found: {len(sorted_similar)}")
        for i, (message, score) in enumerate(sorted_similar[:limit], 1):
            # Use placeholders for missing content
            msg_subject = self._get_message_attr(message, "subject", "[No subject]")
            snippet = self._get_message_attr(message, "snippet", "[No preview available]")

            print(f"{i}. Similarity: {score:.2f} - {msg_subject}")
            print(f"   Date: {message.get('date', 'No date')}")
            print(f"   From: {message.get('from', 'Unknown')}")
            print(f"   Message ID: {message['id']}")
            print(f"   {snippet}")
            print()

    def find_user_connections(self, email=None, limit=10):
        """
        Find a user's connections (who they communicate with).

        Args:
            email: User's email (uses central user by default)
            limit: Maximum number of connections to display
        """
        if not email and self.central_user:
            email = self.central_user["email"]

        if not email:
            print("No user specified and no central user found")
            return

        user = self.email_to_user.get(email)
        if not user:
            print(f"User {email} not found in the graph")
            return

        print(f"\n===== CONNECTIONS FOR {email} =====")

        # Count communications with each person
        connections = defaultdict(lambda: {"sent": 0, "received": 0, "cc": 0, "total": 0})

        # Messages sent (EMAILED, EMAILED_CC, EMAILED_BCC)
        for relation_type in ["EMAILED", "EMAILED_CC", "EMAILED_BCC"]:
            for relation in self.relation_types.get(relation_type, []):
                if relation["source_id"] == user["id"] and relation["target_id"] in self.user_map:
                    target_user = self.user_map[relation["target_id"]]
                    connections[target_user["email"]]["sent"] += 1
                    connections[target_user["email"]]["total"] += 1

        # Messages received
        for relation in self.relation_types.get("EMAILED", []):
            if relation["target_id"] == user["id"] and relation["source_id"] in self.user_map:
                source_user = self.user_map[relation["source_id"]]
                connections[source_user["email"]]["received"] += 1
                connections[source_user["email"]]["total"] += 1

        # Messages in copy
        for relation in self.relation_types.get("EMAILED_CC", []):
            if relation["target_id"] == user["id"] and relation["source_id"] in self.user_map:
                source_user = self.user_map[relation["source_id"]]
                connections[source_user["email"]]["cc"] += 1
                connections[source_user["email"]]["total"] += 1

        if not connections:
            print("No connections found")
            return

        # Sort by total communications (highest first)
        sorted_connections = sorted(
            [(email, data) for email, data in connections.items()],
            key=lambda x: x[1]["total"],
            reverse=True
        )

        # Display connections
        print(f"Connections found: {len(sorted_connections)}")
        for i, (connected_email, data) in enumerate(sorted_connections[:limit], 1):
            connected_user = self.email_to_user.get(connected_email, {})
            name = connected_user.get("name", "Unknown")
            domain = connected_user.get("domain", "Unknown")

            print(f"{i}. {connected_email} ({name})")
            print(f"   - Domain: {domain}")
            print(f"   - Total communications: {data['total']}")
            print(f"   - Messages sent: {data['sent']}")
            print(f"   - Messages received: {data['received']}")
            print(f"   - In copy: {data['cc']}")
            print()

    def analyze_thread(self, thread_id):
        """
        Detailed analysis of a conversation thread.

        Args:
            thread_id: ID of the thread to analyze
        """
        if thread_id not in self.thread_map:
            print(f"Thread {thread_id} not found in the graph")
            return

        thread = self.thread_map[thread_id]
        # Use placeholders for missing content
        subject = self._get_message_attr(thread, "subject", "[No subject]")
        print(f"\n===== THREAD ANALYSIS: '{subject}' =====")

        # Basic information
        print(f"ID: {thread['id']}")
        print(f"Subject: {subject}")
        print(f"Number of messages: {thread.get('message_count', 0)}")
        print(f"Last message date: {thread.get('last_message_date', 'Unknown')}")
        print(f"Involves central user: {thread.get('involves_central_user', False)}")

        # Participants
        print(f"\nParticipants ({len(thread.get('participants', []))}):")
        for participant in thread.get('participants', []):
            user = self.email_to_user.get(participant.lower().strip())
            if user:
                print(f"- {user['email']} ({user.get('name', 'Unknown')})")
            else:
                print(f"- {participant}")

        # Thread topics
        print(f"\nThread topics:")
        for topic_name in thread.get('topics', []):
            print(f"- {topic_name}")

        # Thread messages
        thread_messages = []
        for msg in self.graph["messages"]:
            if msg.get("thread_id") == thread_id:
                thread_messages.append(msg)

        if thread_messages:
            # Sort by date
            sorted_messages = sorted(thread_messages, key=lambda m: m.get("date", ""))

            print(f"\nMessage timeline:")
            for i, msg in enumerate(sorted_messages, 1):
                # Use placeholders for missing content
                snippet = self._get_message_attr(msg, "snippet", "[No preview available]")

                print(f"{i}. {msg.get('date', 'No date')} - From: {msg.get('from', 'Unknown')}")
                recipients = ', '.join(msg.get('to', []))
                if len(recipients) > 50:
                    recipients = recipients[:47] + "..."
                print(f"   To: {recipients}")
                if msg.get('cc'):
                    cc = ', '.join(msg.get('cc', []))
                    if len(cc) > 50:
                        cc = cc[:47] + "..."
                    print(f"   Cc: {cc}")
                print(f"   Message ID: {msg['id']}")
                print(f"   {snippet}")
                print()

    def find_threads_by_topic(self, topic_name, limit=5):
        """
        Find threads by topic.

        Args:
            topic_name: Topic name to search for
            limit: Maximum number of threads to display
        """
        print(f"\n===== THREADS BY TOPIC: '{topic_name}' =====")

        # Collect all threads with this topic
        matching_threads = []
        for thread in self.graph["threads"]:
            if "topics" in thread:
                for topic in thread["topics"]:
                    if topic_name.lower() in topic.lower():
                        matching_threads.append(thread)
                        break

        if not matching_threads:
            print(f"No threads found for topic '{topic_name}'")
            return

        # Sort by last message date (most recent first)
        sorted_threads = sorted(matching_threads, key=lambda t: t.get("last_message_date", ""), reverse=True)

        print(f"Threads found: {len(sorted_threads)}")
        for i, thread in enumerate(sorted_threads[:limit], 1):
            # Use placeholders for missing content
            subject = self._get_message_attr(thread, "subject", "[No subject]")

            print(f"{i}. {subject}")
            print(f"   - Last message: {thread.get('last_message_date', 'Unknown')}")
            print(f"   - Number of messages: {thread.get('message_count', 0)}")
            print(f"   - Participants: {len(thread.get('participants', []))}")

            # Display some participants
            participants = thread.get('participants', [])
            if participants:
                sample = participants[:3]
                participant_str = ', '.join(sample)
                if len(participants) > 3:
                    participant_str += f" and {len(participants) - 3} others"
                print(f"   - Sample participants: {participant_str}")

            # Display all thread topics
            topics = thread.get('topics', [])
            if topics:
                print(f"   - Topics: {', '.join(topics)}")
            print()

    def full_text_search(self, query, context_user=None, limit=10):
        """
        Perform a comprehensive search through indexed email messages using spaCy and fuzzy matching.

        This function searches for messages matching the query terms, including handling:
        - Exact word matches
        - Entity recognition (names, organizations, etc.)
        - Fuzzy matching for typos and spelling variations
        - Special handling for subject-only searches

        Args:
            query: Text to search for
            context_user: Email of a user to contextualize the search results
            limit: Maximum number of results to display

        Returns:
            None (displays results to console)
        """
        print(f"\n===== SEARCH: '{query}' =====")

        # Check if we have indices loaded
        if not hasattr(self, 'word_index') or not self.word_index:
            self._load_indices()

        if not self.word_index:
            print("Warning: Search indices not available. Results will be limited.")
            return

        # Check for subject-only search flag
        subject_only = any(prefix in query.lower() for prefix in ["subject:", "sujet:"])
        if subject_only:
            # Remove the subject: prefix for processing
            query = re.sub(r'(subject:|sujet:)\s*', '', query, flags=re.IGNORECASE)
            print("Searching in subject lines only")

        # Process the query with spaCy
        query_data = self._process_query(query)

        # Display query terms for debugging
        print(f"Search terms: {', '.join(query_data['tokens'])}")
        if query_data['entities']:
            print(f"Detected entities: {', '.join(query_data['entities'])}")

        # ===== PHASE 1: Collect matching message IDs =====
        matches = self._find_matching_messages(query_data, subject_only)

        if not matches:
            print(f"No messages found matching '{query}'")
            return

        # ===== PHASE 2: Score and rank results =====
        scored_results = self._score_search_results(matches, query_data, context_user)

        # ===== PHASE 3: Display results =====
        print(f"Found {len(scored_results)} messages matching your search")
        self._display_search_results(scored_results, limit)

    def _process_query(self, query):
        """
        Process a search query using spaCy (or fallback to basic processing).

        Args:
            query: Search query text

        Returns:
            dict: Processed query data with tokens, entities, and additional metadata
        """
        result = {
            'tokens': [],
            'entities': [],
            'original': query,
            'fuzzy_tokens': []
        }

        # Try to use spaCy if available
        try:
            import spacy
            try:
                # Try French model first, fall back to English
                nlp = spacy.load("fr_core_news_sm")
            except:
                try:
                    nlp = spacy.load("en_core_web_sm")
                except:
                    return self._fallback_query_processing(query)

            # Process with spaCy
            doc = nlp(query)

            # Extract normalized tokens (excluding punctuation and stopwords)
            custom_stopwords = {
                "bonjour", "cordialement", "merci", "salutations", "le", "la", "les",
                "un", "une", "et", "est", "de", "du", "des", "pour", "dans", "avec",
                "hello", "regards", "thanks", "thank", "you", "please", "the", "a", "an"
            }

            # Extract tokens
            for token in doc:
                if (not token.is_punct and not token.is_space and
                        token.lemma_.lower() not in custom_stopwords):
                    result['tokens'].append(token.lemma_.lower())

            # Extract entities
            for ent in doc.ents:
                result['entities'].append(ent.text.lower())

        except ImportError:
            # Fallback if spaCy is not available
            return self._fallback_query_processing(query)

        # Add fuzzy matching variations
        if result['tokens']:
            for token in result['tokens']:
                if len(token) >= 3:  # Only do fuzzy matching for meaningful terms
                    result['fuzzy_tokens'].extend(self._find_similar_terms(token))

        return result

    def _fallback_query_processing(self, query):
        """
        Basic query processing for when spaCy is not available.

        Args:
            query: Search query text

        Returns:
            dict: Processed query data with basic tokenization
        """
        # Basic tokenization
        tokens = re.findall(r'\b\w+\b', query.lower())

        # Remove common stopwords
        stopwords = {"le", "la", "les", "un", "une", "et", "est", "de", "du", "des",
                     "the", "a", "an", "and", "is", "of", "for", "to", "in", "with"}

        filtered_tokens = [token for token in tokens if len(token) > 2 or token not in stopwords]

        return {
            'tokens': filtered_tokens,
            'entities': [],
            'original': query,
            'fuzzy_tokens': []
        }

    def _find_similar_terms(self, word, max_distance=1):
        """
        Find terms in the word index that are similar to the given word.

        Args:
            word: The word to find similar terms for
            max_distance: Maximum Levenshtein distance to consider a match

        Returns:
            list: Similar terms found in the index
        """
        similar_terms = []

        # Only attempt fuzzy matching on reasonably sized words
        if len(word) < 3:
            return similar_terms

        # For efficiency, only check words of similar length
        for term in self.word_index:
            # Skip very short terms or large length differences
            if len(term) < 3 or abs(len(term) - len(word)) > 2:
                continue

            # Calculate edit distance
            if self._levenshtein_distance(word, term) <= max_distance:
                similar_terms.append(term)

        return similar_terms

    def _levenshtein_distance(self, s1, s2):
        """
        Calculate the Levenshtein (edit) distance between two strings.

        Args:
            s1: First string
            s2: Second string

        Returns:
            int: Edit distance between the strings
        """
        # Base case: empty strings
        if len(s1) == 0:
            return len(s2)
        if len(s2) == 0:
            return len(s1)

        # Initialize matrix
        d = [[0 for _ in range(len(s2) + 1)] for _ in range(len(s1) + 1)]

        # Fill first row and column
        for i in range(len(s1) + 1):
            d[i][0] = i
        for j in range(len(s2) + 1):
            d[0][j] = j

        # Fill rest of matrix
        for i in range(1, len(s1) + 1):
            for j in range(1, len(s2) + 1):
                cost = 0 if s1[i - 1] == s2[j - 1] else 1
                d[i][j] = min(
                    d[i - 1][j] + 1,  # deletion
                    d[i][j - 1] + 1,  # insertion
                    d[i - 1][j - 1] + cost  # substitution
                )

        return d[len(s1)][len(s2)]

    def _find_matching_messages(self, query_data, subject_only=False):
        """
        Find messages that match the query terms.

        Args:
            query_data: Processed query information
            subject_only: Whether to search only in subject lines

        Returns:
            dict: Message ID to match metadata mapping
        """
        matches = {}  # message_id -> match metadata

        # Initialize indices if they don't exist (compatibility with existing code)
        if not hasattr(self, 'word_index'):
            self.word_index = {}
        if not hasattr(self, 'entity_index'):
            self.entity_index = {}
        if not hasattr(self, 'subject_index'):
            self.subject_index = {}

        # Search in appropriate indices based on subject_only flag
        search_indices = [self.subject_index] if subject_only else [self.word_index]

        # Search for exact token matches
        for token in query_data['tokens']:
            for index in search_indices:
                if token in index:
                    for msg_id in index[token]:
                        if msg_id not in matches:
                            matches[msg_id] = {'exact_matches': 0, 'fuzzy_matches': 0, 'entity_matches': 0}
                        matches[msg_id]['exact_matches'] += 1

        # Search for entity matches (unless subject-only search)
        if not subject_only and self.entity_index:
            for entity in query_data['entities']:
                if entity in self.entity_index:
                    for msg_id in self.entity_index[entity]:
                        if msg_id not in matches:
                            matches[msg_id] = {'exact_matches': 0, 'fuzzy_matches': 0, 'entity_matches': 0}
                        matches[msg_id]['entity_matches'] += 1

        # Search for fuzzy matches
        for token in query_data['fuzzy_tokens']:
            for index in search_indices:
                if token in index:
                    for msg_id in index[token]:
                        if msg_id not in matches:
                            matches[msg_id] = {'exact_matches': 0, 'fuzzy_matches': 0, 'entity_matches': 0}
                        matches[msg_id]['fuzzy_matches'] += 1

        # Filter to only include message IDs that exist in the message map
        return {msg_id: metadata for msg_id, metadata in matches.items() if msg_id in self.message_map}

    def _score_search_results(self, matches, query_data, context_user=None):
        """
        Score search results based on relevance factors.

        Args:
            matches: Dictionary of message IDs and match metadata
            query_data: Processed query information
            context_user: Optional user email for contextual relevance

        Returns:
            list: Tuples of (message, score) sorted by descending score
        """
        scored_results = []

        for msg_id, match_data in matches.items():
            message = self.message_map[msg_id]
            score = self._calculate_relevance_score(message, match_data, query_data, context_user)
            scored_results.append((message, score))

        # Sort by score (descending)
        return sorted(scored_results, key=lambda x: x[1], reverse=True)

    def _calculate_relevance_score(self, message, match_data, query_data, context_user=None):
        """
        Calculate a relevance score for a search result.

        Args:
            message: The message object
            match_data: Metadata about how the message matched the query
            query_data: Processed query information
            context_user: Optional user email for contextual relevance

        Returns:
            float: Relevance score
        """
        score = 1.0  # Base score

        # Factor 1: Number of exact matches
        score += match_data['exact_matches'] * 2.0

        # Factor 2: Entity matches (higher weight)
        score += match_data['entity_matches'] * 3.0

        # Factor 3: Fuzzy matches (lower weight)
        score += match_data['fuzzy_matches'] * 0.5

        # Factor 4: Subject matches
        # Check if this message's ID is in the subject index for any query token
        subject_match = False
        if hasattr(self, 'subject_index') and self.subject_index:
            for token in query_data['tokens']:
                if token in self.subject_index and message['id'] in self.subject_index[token]:
                    subject_match = True
                    break

        if subject_match:
            score *= 2.0  # Double the score for subject matches

        # Factor 5: Recency
        try:
            message_date = datetime.fromisoformat(message.get("date", ""))
            days_old = (datetime.now() - message_date).days
            if days_old < 30:  # Within a month
                score *= 1.3
            elif days_old < 90:  # Within 3 months
                score *= 1.1
        except (ValueError, TypeError):
            pass

        # Factor 6: Has attachment if query mentions attachments
        attachment_terms = {"attach", "pièce", "document", "fichier", "file"}
        if any(term in query_data['original'].lower() for term in attachment_terms):
            if message.get("has_attachment", False):
                score *= 1.5

        # Factor 7: User context
        if context_user:
            # Prioritize messages where the context user is sender or recipient
            if context_user == message.get("from", ""):
                score *= 1.8  # User is sender
            elif context_user in message.get("to", []):
                score *= 1.5  # User is direct recipient
            elif context_user in message.get("cc", []):
                score *= 1.2  # User is in CC

        return score

    def _display_search_results(self, scored_results, limit):
        """
        Display search results in a formatted way.

        Args:
            scored_results: List of (message, score) tuples
            limit: Maximum number of results to display
        """
        for i, (message, score) in enumerate(scored_results[:limit], 1):
            # Get thread subject as a fallback for message subject
            thread_subject = ""
            if message.get("thread_id") in self.thread_map:
                thread = self.thread_map[message.get("thread_id")]
                thread_subject = self._get_message_attr(thread, "subject", "[No subject]")

            # Use thread subject when message subject is not available
            subject = self._get_message_attr(message, "subject", thread_subject or "[No subject]")

            print(f"{i}. Message ID: {message['id']} (Relevance: {score:.2f})")
            print(f"   - Date: {message.get('date', 'Unknown')}")
            print(f"   - From: {message.get('from', 'Unknown')}")
            print(f"   - Subject: {subject}")
            print(f"   - Has attachments: {message.get('has_attachment', False)}")

            # Show recipients
            to_list = ', '.join(message.get('to', []))
            if len(to_list) > 50:
                to_list = to_list[:47] + "..."
            print(f"   - To: {to_list}")

            # Display thread information
            thread = self.thread_map.get(message.get("thread_id"))
            if thread:
                print(f"   - Thread: {thread_subject}")
                print(f"   - Messages in thread: {thread.get('message_count', 0)}")
            print()

    def _load_indices(self):
        """Load search indices from the indices directory."""
        indices_dir = os.path.join(self.graph_dir, "indices")

        if not os.path.exists(indices_dir):
            print("No indices directory found.")
            return False

        try:
            # Helper function to load an index
            def load_index(filename):
                file_path = os.path.join(indices_dir, filename)
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Convert lists back to sets
                        return {key: set(values) for key, values in data.items()}
                return {}

            # Load each index
            self.word_index = load_index("word_index.json")
            self.entity_index = load_index("entity_index.json")
            self.subject_index = load_index("subject_index.json")

            print(f"Loaded search indices:")
            print(f"- Word index: {len(self.word_index)} terms")
            print(f"- Entity index: {len(self.entity_index)} entities")
            print(f"- Subject index: {len(self.subject_index)} terms")

            return True
        except Exception as e:
            print(f"Error loading indices: {str(e)}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Test tool for optimized email graph')
    parser.add_argument('--graph-dir', type=str, default="output/graph",
                        help='Path to the directory containing graph components')
    parser.add_argument('--command', type=str, choices=[
        'summary', 'user_messages', 'conversations', 'topic_search',
        'similar_messages', 'connections', 'thread_analysis',
        'threads_by_topic', 'full_text_search'
    ],
                        default='summary', help='Command to execute')
    parser.add_argument('--email', type=str, help='Email address for user-related commands')
    parser.add_argument('--email2', type=str, help='Second email address for conversations command')
    parser.add_argument('--topic', type=str, help='Topic name for topic-related commands')
    parser.add_argument('--message-id', type=str, help='Message ID for similar_messages command')
    parser.add_argument('--thread-id', type=str, help='Thread ID for thread_analysis command')
    parser.add_argument('--query', type=str, help='Search text for full_text_search command')
    parser.add_argument('--limit', type=int, default=10, help='Limit of results to display')

    args = parser.parse_args()

    # Create the test tool
    try:
        # Enable detailed error tracing
        import traceback
        try:
            query_tool = OptimizedGraphQueryTool(args.graph_dir)
        except Exception as e:
            print(f"Error initializing graph query tool: {str(e)}")
            traceback.print_exc()
            sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

    # Execute the specified command
    if args.command == 'summary':
        query_tool.print_graph_summary()

    elif args.command == 'user_messages':
        query_tool.find_user_messages(args.email, limit=args.limit)

    elif args.command == 'conversations':
        if not args.email:
            print("--email is required for the conversations command")
            return
        query_tool.find_conversations_between_users(args.email, args.email2)

    elif args.command == 'topic_search':
        if not args.topic:
            print("--topic is required for the topic_search command")
            return
        query_tool.search_by_topic(args.topic, limit=args.limit)

    elif args.command == 'similar_messages':
        if not args.message_id:
            print("--message-id is required for the similar_messages command")
            return
        query_tool.find_similar_messages(args.message_id, limit=args.limit)

    elif args.command == 'connections':
        query_tool.find_user_connections(args.email, limit=args.limit)

    elif args.command == 'thread_analysis':
        if not args.thread_id:
            print("--thread-id is required for the thread_analysis command")
            return
        query_tool.analyze_thread(args.thread_id)

    elif args.command == 'threads_by_topic':
        if not args.topic:
            print("--topic is required for the threads_by_topic command")
            return
        query_tool.find_threads_by_topic(args.topic, limit=args.limit)

    elif args.command == 'full_text_search':
        if not args.query:
            print("--query is required for the full_text_search command")
            return
        query_tool.full_text_search(args.query, context_user=args.email, limit=args.limit)


if __name__ == "__main__":
    main()