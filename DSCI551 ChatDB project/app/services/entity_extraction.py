import spacy

# Initialize spaCy language model
nlp = spacy.load("en_core_web_sm")


def extract_entities(user_input):
    # Extract entities from the user's input using spaCy
    doc = nlp(user_input)
    return [(ent.text, ent.label_) for ent in doc.ents]
