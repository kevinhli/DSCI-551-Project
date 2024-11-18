from flask import Flask
from app.db import connect_mysql, connect_mongo  # Ensure db.py is in app
from app.routes import main_routes  # Import routes

app = Flask(__name__)

# Connect to databases
mysql_connection = connect_mysql()
mongo_db = connect_mongo()

# Register routes
app.register_blueprint(main_routes)

if __name__ == "__main__":
    app.run(debug=True)
