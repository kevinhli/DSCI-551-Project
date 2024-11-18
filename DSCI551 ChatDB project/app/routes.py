from flask import request, jsonify
from app.db import connect_mysql, connect_mongo
from services.query_generator import generate_query
from services.nlp_processing import process_query


def init_routes(app):
    @app.route('/')
    def index():
        return "Welcome to ChatDB"

    @app.route('/submit_query', methods=['POST'])
    def submit_query():
        user_query = request.form['query']
        db_type = request.form['db_type']  # 'sql' or 'nosql'
        
        # Process the user query using NLP
        query_pattern = process_query(user_query)
        
        # Generate the appropriate SQL/NoSQL query
        final_query = generate_query(query_pattern, db_type)

        # Execute the query and return results
        if db_type == 'sql':
            conn = connect_mysql()
            # Execute MySQL query here
        else:
            conn = connect_mongo()
            # Execute MongoDB query here

        return jsonify({"query": final_query, "results": "Query Results here"})
