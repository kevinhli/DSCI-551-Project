#nlp_processing.py
from app.db import connect_mysql, connect_mongo  # Use full path import
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re  # Import re for regular expression matching
import spacy
from nltk.stem import WordNetLemmatizer
# Ensure you have spaCy and the language model installed
nlp = spacy.load("en_core_web_sm")

lemmatizer = WordNetLemmatizer()
def preprocess_input(user_input):
    tokens = word_tokenize(user_input)
    filtered_tokens = [
        lemmatizer.lemmatize(word) for word in tokens if word.lower() not in stopwords.words('english')
    ]
    return filtered_tokens


def match_query_pattern(preprocessed_input):
    joined_input = ' '.join(preprocessed_input).lower()
    print(f"Processing Input: {joined_input}")  # Debugging print

    # Check for command patterns
    if re.search(r'\b(count|total)\b', joined_input):
        print("Matched COUNT query")  # Debugging print
        return "SELECT COUNT(*) FROM messages;"  # SQL count query
    elif re.search(r'\b(show|average)\b', joined_input):
        print("Matched AVERAGE query")  # Debugging print
        return "SELECT AVG(some_field) FROM messages;"  # SQL average query
    elif re.search(r'\b(find|search|get|show)\b', joined_input):
        print("Matched FIND query")  # Debugging print
        return "SELECT * FROM messages;"  # Default SQL query
    elif re.search(r'\b(insert|add)\b', joined_input):
        print("Matched INSERT query")  # Debugging print
        return {"action": "insert", "collection": "messages", "data": {"content": "your_message"}}
    elif re.search(r'\b(delete|remove)\b', joined_input):
        print("Matched DELETE query")  # Debugging print
        return {"action": "delete", "collection": "messages", "filter": {"content": "your_message"}}
    else:
        print("No match found")  # Debugging print
        return None



def extract_entities(user_input):
    doc = nlp(user_input)
    return [(ent.text, ent.label_) for ent in doc.ents]
