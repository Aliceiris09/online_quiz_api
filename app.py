from flask import Flask, request, jsonify
from config import Config
from models import db, User, Quizzes, Questions, Results
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize the database and migration tools
db.init_app(app)
migrate = Migrate(app, db)

# Create database tables if they don't exist
def create_tables():
    with app.app_context():
        db.create_all()

# User registration route
@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        # Validate input
        if not username or not password:
            return jsonify({"message": "Username and password are required"}), 400

        # Check if the user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({"message": "User already exists"}), 400

        # Create a new user
        new_user = User(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"message": str(e)}), 500  # Handle unexpected errors

# User login route
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        user = User.query.filter_by(username=username).first()

        if not user:
            return jsonify({"message": "User not found"}), 404

        if not check_password_hash(user.password, password):
            return jsonify({"message": "Invalid password"}), 401

        return jsonify({"message": "Login successful"}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500  # Handle unexpected errors

if __name__ == "__main__":
    create_tables()  # Create tables if they don't exist
    app.run(debug=True)
 