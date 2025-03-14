from sklearn.feature_extraction.text import TfidfVectorizer
import re
import json
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# nltk.download("stopwords")
# nltk.download("wordnet")

def preprocess_text(text):
    # minimisation, remove commas
    text = re.sub(r"[^a-zA-Z]", " ", text.lower())
    # split
    words = text.split()
    # stopword 
    lemmatizer = WordNetLemmatizer()
    words = [lemmatizer.lemmatize(word) for word in words if word not in stopwords.words("english")]
    return " ".join(words)

with open('data\enron_emails_pred.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

body = data[3].get("body", "")
X_train_clean = preprocess_text(body)
print(X_train_clean)
# X_test_clean = X_test.apply(preprocess_text)


# tfidf = TfidfVectorizer(max_features=1000) 
# X_train_tfidf = tfidf.fit_transform(X_train_clean)
# X_test_tfidf = tfidf.transform(X_test_clean)