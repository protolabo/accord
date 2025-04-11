import uuid
from collections import defaultdict


class ThreadRelationProcessor:
    """Processor for creating relations between messages in the same thread."""

    def __init__(self):
        pass

    def process_thread_relations(self, messages, threads):
        """
        Creates relations between messages in the same thread.

        Args:
        messages: Message dictionary
        threads: Thread dictionary

        Returns:
        list: List of created relations
        """
        # Group messages by thread_id
        thread_messages = defaultdict(list)
        processed_threads = 0
        relations = []

        # If the message belongs to a conversation (has a thread_id),
        # we add the message ID to the list of messages in that conversation in the thread_messages dictionary.

        for message_id, message in messages.items():
            thread_id = message.get("thread_id")
            if thread_id:
                thread_messages[thread_id].append(message_id)


        multi_message_threads = sum(1 for msgs in thread_messages.values() if len(msgs) > 1)
        print(
            f"Processing {multi_message_threads} threads with multiple messages (out of {len(thread_messages)} threads in total)"
        )


        for thread_id, message_ids in thread_messages.items():

            # Ignore threads with a single message
            if len(message_ids) <= 1:
                continue

            # Oget messages
            thread_msgs = [messages[mid] for mid in message_ids if mid in messages]


            sorted_messages = sorted(thread_msgs, key=lambda x: x.get("date", ""))

            # create relations PART_OF_THREAD
            for message in sorted_messages:
                if thread_id in threads:
                    thread = threads[thread_id]
                    relation = {
                        "id": str(uuid.uuid4()),
                        "type": "relation",
                        "source_id": message["id"],
                        "target_id": thread["id"],
                        "relation_type": "PART_OF_THREAD",
                        "weight": 1,
                    }
                    relations.append(relation)

            # Create relation  REPLIED_TO
            for i in range(1, len(sorted_messages)):
                previous = sorted_messages[i - 1]
                current = sorted_messages[i]

                # create a REPLIED_TO relation
                replied_relation = {
                    "id": str(uuid.uuid4()),
                    "type": "relation",
                    "source_id": current["id"],
                    "target_id": previous["id"],
                    "relation_type": "REPLIED_TO",
                    "weight": 1,
                }
                relations.append(replied_relation)


            processed_threads += 1
            if processed_threads % 100 == 0:
                print(f"Processed {processed_threads}/{multi_message_threads} multi-message threads")

        return relations