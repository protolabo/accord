
from ..nlp.topic_extractor import extract_keywords
from ..stopword import stopwords as mystopwords


class TopicNodeManager:

    def __init__(self):
        self.stop_words = mystopwords()


    def extract_topics(self, email_data, topics_dict):
        """
        Extracts the subjects of an email.

        Args:
        email_data: Email data
        topics_dict: Dictionary of existing topics

        Returns:
        list: List of extracted topic nodes
        """


        subject = email_data.get("Subject", "")
        body_plain = email_data.get("Body", {}).get("plain", "")

        text = body_plain if body_plain else subject
        if not text:
            return []

        keywords = extract_keywords(text, subject, max_keywords=3, stop_words=self.stop_words)

        # Create or update topic nodes
        topics = []
        for keyword in keywords:
            topic_id = keyword.lower()

            if topic_id in topics_dict:
                topic = topics_dict[topic_id]
                topic["message_count"] += 1
            else:
                topic = {
                    "id": topic_id,
                    "type": "topic",
                    "name": keyword,
                    "message_count": 1,
                }
                topics_dict[topic_id] = topic

            topics.append(topic)

        return topics