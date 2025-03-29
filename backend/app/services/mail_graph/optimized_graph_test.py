import json
import sys
import argparse
from pathlib import Path
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

        if True:
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

            # error : thread save gmail_thread_name
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