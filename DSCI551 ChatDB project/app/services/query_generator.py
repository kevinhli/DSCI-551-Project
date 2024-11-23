# app/services/query_generator.py

from bson import ObjectId
from app.db import connect_mysql, connect_mongo
from app.services.nlp_processing import preprocess_input, match_query_pattern
from app.query_utils import extract_fields_from_input, extract_table_from_input, POTENTIAL_FIELDS

def validate_field_and_table(db_type, table_name, field_name=None):
    if db_type == 'sql':
        connection = connect_mysql()
        try:
            with connection.cursor() as cursor:
                # Check if table exists
                cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
                if not cursor.fetchone():
                    raise ValueError(f"Table '{table_name}' does not exist.")

                # Check if field exists, if provided
                if field_name:
                    cursor.execute(
                        f"SHOW COLUMNS FROM {table_name} LIKE '{field_name}'")
                    if not cursor.fetchone():
                        raise ValueError(
                            f"Field '{field_name}' does not exist in table '{table_name}'.")
        except Exception as e:
            raise ValueError(f"Validation error: {str(e)}")
        finally:
            connection.close()
    elif db_type == 'nosql':
        db = connect_mongo()
        collection = db[table_name]
        # Here you could add field validation based on the schema
        # if your MongoDB collections follow a specific schema.

# Function to generate SQL or NoSQL query based on user input


def generate_query(query_pattern, db_type):
    # Extract table/collection name, aggregate field, group-by field, order-by field, and order-by direction
    table_name = query_pattern.get('table')
    aggregate_field = query_pattern.get('aggregate_field')
    group_by_field = query_pattern.get('group_by_field')
    order_by_field = query_pattern.get('order_by_field')
    order_by_direction = query_pattern.get('order_by_direction', 'ASC')
    filter_criteria = query_pattern.get('filter', {})

    # Validate collection/table name
    if not table_name:
        raise ValueError(
            "Table or collection name is required for this operation."
        )

    # Handle SELECT ALL operation
    if query_pattern['operation'] == 'select_all':
        if db_type == 'sql':
            query = f"SELECT * FROM {table_name}"
            if order_by_field:
                query += f" ORDER BY {order_by_field} {order_by_direction}"
            return query
        elif db_type == 'nosql':
            # Assuming filter_criteria is already well-formed
            return {"operation": "find", "collection": table_name, "filter": filter_criteria}
        else:
            raise ValueError(
                f"Unsupported database type for select_all: {db_type}"
            )

    # Handle COUNT operation
    if query_pattern['operation'] == 'count':
        if db_type == 'sql':
            query = f"SELECT COUNT(*) AS total_count FROM {table_name}"
            return query
        elif db_type == 'nosql':
            # Add the ability to use filter criteria if available
            return {"operation": "count", "collection": table_name, "filter": filter_criteria}
        else:
            raise ValueError(
                f"Unsupported database type for count: {db_type}"
            )

    # AGGREGATE operations
    if query_pattern['operation'] == 'aggregate':
        aggregate_function = query_pattern.get('aggregate_function')

        if not aggregate_field:
            raise ValueError("Aggregate field is required for this operation.")

        if db_type == 'sql':
            # Handle special case where aggregate_field is an expression (like "transaction_qty * unit_price")
            if isinstance(aggregate_field, list):
                aggregate_field = ' * '.join(aggregate_field)

            if aggregate_function in ['sum', 'average', 'max', 'min']:
                function_sql = {
                    'sum': 'SUM',
                    'average': 'AVG',
                    'max': 'MAX',
                    'min': 'MIN'
                }[aggregate_function]

                alias_name = f"{aggregate_function}_value"

                if group_by_field:
                    query = f"SELECT {group_by_field}, {function_sql}({aggregate_field}) AS {alias_name} FROM {table_name} GROUP BY {group_by_field}"
                else:
                    query = f"SELECT {function_sql}({aggregate_field}) AS {alias_name} FROM {table_name}"

                if order_by_field:
                    query += f" ORDER BY {order_by_field} {order_by_direction}"

                return query

            else:
                raise ValueError(
                    f"Unsupported aggregate function: {aggregate_function}"
                )

        elif db_type == 'nosql':
            group_id = f"${group_by_field}" if group_by_field else None
            pipeline = [
                {"$match": {aggregate_field: {"$exists": True}}},
                {"$group": {"_id": group_id}}
            ]

            if aggregate_function in ['average', 'sum', 'max', 'min']:
                operation_field = {
                    'average': '$avg',
                    'sum': '$sum',
                    'max': '$max',
                    'min': '$min'
                }[aggregate_function]
                pipeline[-1]["$group"][f"{aggregate_function}_{aggregate_field}"] = {
                    operation_field: f"${aggregate_field}"
                }

                if order_by_field:
                    sort_direction = 1 if order_by_direction.lower() == 'asc' else -1
                    pipeline.append(
                        {"$sort": {order_by_field: sort_direction}}
                    )

            else:
                raise ValueError(
                    f"Unsupported aggregate function: {aggregate_function}"
                )

            return {
                "operation": "aggregate",
                "collection": table_name,
                "pipeline": pipeline
            }

    raise ValueError(
        f"Unsupported operation or database type: {query_pattern['operation']}, {db_type}"
    )


def execute_query(query):
    if isinstance(query, tuple):  # SQL query with parameters
        connection = connect_mysql()
        try:
            with connection.cursor() as cursor:
                cursor.execute(query[0], query[1])
                result = cursor.fetchall()
            connection.commit()
        except Exception as e:
            raise ValueError(f"SQL execution error: {str(e)}")
        finally:
            connection.close()
        return result
    elif isinstance(query, dict):  # MongoDB query (NoSQL)
        db = connect_mongo()
        collection = db[query['collection']]
        try:
            if query.get('operation') == 'count':
                result = collection.count_documents(query.get('filter', {}))
            elif query.get('operation') == 'find':
                result = list(collection.find(query.get('filter', {})))

                # Convert ObjectId to string for each document to make '_id' field readable
                for doc in result:
                    # Print document before processing for better debugging
                    print(f"[DEBUG] Document before processing: {doc}")

                    if '_id' in doc:
                        print(
                            f"[DEBUG] Type of _id before conversion: {type(doc['_id'])}")

                        if isinstance(doc['_id'], ObjectId):
                            doc['_id'] = str(doc['_id'])
                            print(
                                f"[DEBUG] Converted ObjectId to string: {doc['_id']}")

                    # Print document after processing for better debugging
                    print(f"[DEBUG] Document after processing: {doc}")

            elif query.get('operation') == 'aggregate':
                result = list(collection.aggregate(query.get('pipeline', [])))
            else:
                raise ValueError(
                    f"Unsupported MongoDB operation: {query.get('operation')}")
        except Exception as e:
            raise ValueError(f"NoSQL execution error: {str(e)}")

        # Adding a debug statement to show the final result before returning
        print(f"[DEBUG] Result after processing: {result}")
        return result
    else:
        raise ValueError("Unsupported query type.")




def handle_user_query(user_input, db_type):
    # Preprocess the user input and match it to a query pattern
    preprocessed_input = preprocess_input(user_input)
    matched_query = match_query_pattern(preprocessed_input)

    if matched_query:
        # Generate the query based on the matched pattern and db_type
        try:
            final_query = generate_query(matched_query, db_type)
            # Execute the query and return the result
            result = execute_query(final_query)
            return result
        except Exception as e:
            return f"Error: {str(e)}"
    else:
        return "No matching query pattern found."
