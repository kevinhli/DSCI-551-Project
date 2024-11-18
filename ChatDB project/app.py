from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit_query', methods=['POST'])
def submit_query():
    query = request.form['query']
    db_type = request.form['db_type']

    # Logic to process query and generate SQL/NoSQL based on db_type
    # You can add more complex logic here later

    result = {
        'query': query,
        'generated_query': f"Generated query for {db_type}: {query}",
        'result': [
            {'Field': 'Name', 'Value': 'John Doe'},
            {'Field': 'Age', 'Value': '30'},
            {'Field': 'Location', 'Value': 'California'}
        ]
    }
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
