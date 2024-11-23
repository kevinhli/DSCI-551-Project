import re
import spacy
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk import download

# Import extract_entities from new entity_extraction.py
from app.services.entity_extraction import extract_entities

from app.query_utils import (
    extract_fields_from_input,
    extract_table_from_input,
    FIELD_SYNONYMS,
    POTENTIAL_FIELDS,
    TABLE_SYNONYMS
)

# Ensure that necessary NLTK corpora are downloaded
download('stopwords')
download('punkt')

# Initialize spaCy language model
nlp = spacy.load("en_core_web_sm")
lemmatizer = WordNetLemmatizer()


def preprocess_input(user_input):
    # Tokenize input and filter stopwords
    tokens = word_tokenize(user_input)
    filtered_tokens = [
        lemmatizer.lemmatize(word) for word in tokens if word.lower() not in stopwords.words('english')
    ]
    return filtered_tokens


# Import extract_entities from new entity_extraction.py

def match_query_pattern(preprocessed_input):
    # Debugging the preprocessed input tokens
    print(f"[DEBUG] Preprocessed Input Tokens: {preprocessed_input}")

    # Join preprocessed input back to a single string for pattern matching
    joined_input = ' '.join(preprocessed_input).lower()
    print(f"[DEBUG] Processing Input: {joined_input}")

    # Extract the potential fields and table from the input dynamically
    aggregate_fields = extract_fields_from_input(joined_input)
    selected_table = extract_table_from_input(joined_input)

    # Debugging the extracted fields and table
    print(f"[DEBUG] Extracted aggregate_fields: {aggregate_fields}")
    print(f"[DEBUG] Extracted selected_table: {selected_table}")

    # Set default table if none is explicitly mentioned
    default_table = selected_table if selected_table else "transactions"
    print(f"[DEBUG] Default table set to: {default_table}")

    # Initialize group_by_field and order_by_field to None by default
    group_by_field = None
    order_by_field = None
    order_by_direction = 'ASC'  # Default to ascending if not specified

    # Identify group-by field if present (e.g., "each store location" or "by product category")
    if "each" in joined_input or "by" in joined_input:
        for field in POTENTIAL_FIELDS:
            if field in joined_input and field not in aggregate_fields:
                group_by_field = field
                break  # Assume only one group-by field for simplicity

    print(f"[DEBUG] group_by_field detected: {group_by_field}")

    # Order-by pattern extraction (widened to support variations like "ordered by" and "ordered")
    order_by_pattern = re.search(
        r'(?:order\s+by|ordered\s+by|ordered)\s+([a-zA-Z_]+)(?:\s+(asc|desc))?', joined_input, re.IGNORECASE
    )

    if order_by_pattern:
        # Debugging to see if we actually matched the pattern
        print(f"[DEBUG] ORDER BY pattern matched: {order_by_pattern.group()}")

        order_by_field = order_by_pattern.group(1)
        order_by_direction = order_by_pattern.group(
            2).upper() if order_by_pattern.group(2) else 'ASC'

        # Debug before normalization
        print(
            f"[DEBUG] Extracted order_by_field before normalization: {order_by_field}")
        print(f"[DEBUG] Extracted order_by_direction: {order_by_direction}")

        # Normalize order_by_field using FIELD_SYNONYMS if possible
        if order_by_field in FIELD_SYNONYMS:
            order_by_field = FIELD_SYNONYMS[order_by_field]
            print(
                f"[DEBUG] Normalized order_by_field using FIELD_SYNONYMS: {order_by_field}")

        # Split combined fields if necessary (like "transaction_qty, unit_price")
        if ',' in order_by_field:
            order_by_field = order_by_field.split(',')[0].strip()
            print(
                f"[DEBUG] Extracted first field from combined fields: {order_by_field}")

        # Validate that the order_by_field is a part of POTENTIAL_FIELDS
        if order_by_field not in POTENTIAL_FIELDS:
            print(
                f"[DEBUG] Order-by field '{order_by_field}' is not valid. Resetting.")
            order_by_field = None
    else:
        # Debug when the ORDER BY pattern is not matched
        print(f"[DEBUG] ORDER BY pattern not found in input: '{joined_input}'")

    # Final debug for order-by field and direction
    print(
        f"[DEBUG] Final order_by_field detected: {order_by_field}, order_by_direction: {order_by_direction}")

    # Match SQL pattern queries
    if re.search(r'\b(total|sum)\b', joined_input) and aggregate_fields:
        selected_aggregate_field = (
            "transaction_qty * unit_price"
            if "transaction_qty" in aggregate_fields and "unit_price" in aggregate_fields
            else next((f for f in aggregate_fields if f in ["transaction_qty", "unit_price"]), None)
        )

        print("[DEBUG] Matched AGGREGATE SUM query")
        return {
            "operation": "aggregate",
            "aggregate_function": "sum",
            "aggregate_field": selected_aggregate_field,
            "table": default_table,
            "group_by_field": group_by_field,
            "order_by_field": order_by_field,
            "order_by_direction": order_by_direction,
        }

    elif re.search(r'\b(average|avg)\b', joined_input) and aggregate_fields:
        selected_aggregate_field = (
            "transaction_qty * unit_price"
            if "transaction_qty" in aggregate_fields and "unit_price" in aggregate_fields
            else next((f for f in aggregate_fields if f in ["transaction_qty", "unit_price"]), None)
        )

        print("[DEBUG] Matched AVERAGE query")
        return {
            "operation": "aggregate",
            "aggregate_function": "average",
            "aggregate_field": selected_aggregate_field,
            "table": default_table,
            "group_by_field": group_by_field,
            "order_by_field": order_by_field,
            "order_by_direction": order_by_direction,
        }

    elif re.search(r'\b(max|maximum)\b', joined_input) and aggregate_fields:
        selected_aggregate_field = next((f for f in aggregate_fields if f in [
                                        "transaction_qty", "unit_price"]), None)

        print("[DEBUG] Matched MAXIMUM query")
        return {
            "operation": "aggregate",
            "aggregate_function": "max",
            "aggregate_field": selected_aggregate_field,
            "table": default_table,
            "group_by_field": group_by_field,
            "order_by_field": order_by_field,
            "order_by_direction": order_by_direction,
        }

    elif re.search(r'\b(min|minimum)\b', joined_input) and aggregate_fields:
        selected_aggregate_field = next((f for f in aggregate_fields if f in [
                                        "transaction_qty", "unit_price"]), None)

        print("[DEBUG] Matched MINIMUM query")
        return {
            "operation": "aggregate",
            "aggregate_function": "min",
            "aggregate_field": selected_aggregate_field,
            "table": default_table,
            "group_by_field": group_by_field,
            "order_by_field": order_by_field,
            "order_by_direction": order_by_direction,
        }

    elif re.search(r'\b(count)\b', joined_input):
        print("[DEBUG] Matched COUNT query")
        sql_query = f"SELECT COUNT(*) FROM {default_table}"

        return {
            "operation": "count",
            "table": default_table,
            "sql_query": sql_query
        }

    elif re.search(r'\b(show|list|get|select)\s*(all|messages|transactions|sales)?\b', joined_input):
        print("[DEBUG] Matched SELECT ALL query")
        return {
            "operation": "select_all",
            "table": default_table,
            "order_by_field": order_by_field,
            "order_by_direction": order_by_direction,
        }

    else:
        print("[DEBUG] No match found")
        return None


def process_query(query):
    """
    Processes the user query to generate a structured query pattern and extracts entities.

    Args:
        query (str): The raw user input query.

    Returns:
        dict: A dictionary containing the matched query pattern and extracted entities.
    """
    try:
        # Step 1: Preprocess the user input for consistent formatting
        preprocessed_input = preprocess_input(query)
        print(f"[DEBUG] Preprocessed Input: {preprocessed_input}")
    except Exception as e:
        raise ValueError(f"Error during preprocessing input: {str(e)}")

    try:
        # Step 2: Match the preprocessed input to a query pattern
        matched_query = match_query_pattern(preprocessed_input)
        print(f"[DEBUG] Matched Query Pattern: {matched_query}")
    except Exception as e:
        raise ValueError(f"Error during matching query pattern: {str(e)}")

    # Step 3: Extract entities from the original user input
    try:
        entities = extract_entities(query)
        print(f"[DEBUG] Extracted Entities: {entities}")
    except Exception as e:
        raise ValueError(f"Error during entity extraction: {str(e)}")

    # Check if a valid query pattern was found
    if not matched_query:
        raise ValueError("No valid query pattern found.")

    # Combine matched query and extracted entities into a response
    return {
        "matched_query": matched_query,
        "entities": entities
    }
