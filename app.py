from flask import Flask
from routes import app_routes
from database.db_utils import init_db  # ⬅️ import this

app = Flask(__name__)
app.secret_key = "123456789"

init_db()  # ⬅️ initialize the database

app.register_blueprint(app_routes)

if __name__ == "__main__":
    app.run(debug=True)
