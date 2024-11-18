# query_generator.py
from app.db import connect_mysql, connect_mongo
from nlp_processing import preprocess_input, match_query_pattern


def execute_query(query):
    if isinstance(query, str):  # SQL query
        connection = connect_mysql()
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
        connection.close()
        return result
    elif isinstance(query, dict):  # MongoDB query
        db = connect_mongo()
        collection = db[query['collection']]
        return list(collection.find())


def handle_user_query(user_input):
    preprocessed_input = preprocess_input(user_input)
    matched_query = match_query_pattern(preprocessed_input)
    if matched_query:
        result = execute_query(matched_query)
        return result
    else:
        return "No matching query pattern found."
