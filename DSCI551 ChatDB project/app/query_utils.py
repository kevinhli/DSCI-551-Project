# query_utils.py

# Define common synonyms for fields
FIELD_SYNONYMS = {
    "sale": "transaction_qty, unit_price",
    "sales": "transaction_qty, unit_price",
    "location": "store_location",
    "store location": "store_location",
    "units": "transaction_qty",
    "product": "product_category",
    "date": "transaction_date",
    "total sales": "transaction_qty, unit_price",
    "store": "store_location",
    "user name": "user_name",
    "customer": "customer_name",
    "registration date": "registration_date",
    "product name": "product_name",
    "order date": "order_date"
}

# Define potential fields in the dataset
POTENTIAL_FIELDS = [
    "transaction_qty", "store_location", "unit_price",
    "product_category", "transaction_date", "user_name",
    "user_email", "registration_date", "customer_name",
    "product_name", "order_date"
]

# Define synonyms for table names
TABLE_SYNONYMS = {
    "sales": "transactions",
    "transactions": "transactions",
    "messages": "messages",
    "coffee_sales": "coffee_sales",
    "stores": "stores",
    "users": "users",
    "customers": "customers",
    "products": "products",
    "orders": "orders"
}


def extract_fields_from_input(input_text, context='general'):
    # Convert input to lowercase for case-insensitive matching
    input_text = input_text.lower()

    # To hold extracted fields
    extracted_fields = set()

    # Check for exact field matches first
    for field in POTENTIAL_FIELDS:
        if field.lower() in input_text:
            extracted_fields.add(field)

    # Check synonyms if exact match not found
    for synonym, actual_field in FIELD_SYNONYMS.items():
        if synonym.lower() in input_text:
            if ',' in actual_field:
                # Split fields if it contains multiple fields (e.g., "transaction_qty, unit_price")
                fields = [f.strip() for f in actual_field.split(',')]
                extracted_fields.update(fields)
            else:
                extracted_fields.add(actual_field)

    # Debug statement to print extracted fields before filtering
    print(
        f"[DEBUG] Extracted fields before filtering for context '{context}': {extracted_fields}")

    # If the context is aggregation, only return numeric fields
    if context == 'aggregation':
        # Define numeric fields explicitly
        numeric_fields = {"transaction_qty", "unit_price"}
        # Only keep numeric fields in the extracted fields set
        extracted_fields = extracted_fields.intersection(numeric_fields)

    # Debug statement to print extracted fields after filtering (for aggregation)
    print(
        f"[DEBUG] Extracted fields after filtering for context '{context}': {extracted_fields}")

    # Return extracted fields if any exist; otherwise, return None
    return list(extracted_fields) if extracted_fields else None


def extract_table_from_input(input_text):
    # Convert input to lowercase for case-insensitive matching
    input_text = input_text.lower()

    # Debug log to see input for extraction
    print(f"[DEBUG] Input for table extraction: '{input_text}'")

    # Sort synonyms by length in descending order to prioritize longer matches
    sorted_table_synonyms = sorted(
        TABLE_SYNONYMS.items(), key=lambda x: len(x[0]), reverse=True
    )

    # Check for table synonyms and match to actual table
    for synonym, actual_table in sorted_table_synonyms:
        if synonym in input_text:
            print(
                f"[DEBUG] Matched table synonym: '{synonym}' -> '{actual_table}'"
            )
            return actual_table

    # If no match found, return None
    print("[DEBUG] No table synonym matched. Unable to determine the table name.")
    return None
