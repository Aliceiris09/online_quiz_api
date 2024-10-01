from flask import Flask, request, jsonify
from config import Config
from models import db, User, Quizzes, Questions, Results
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize the database and migration tools
db.init_app(app)
migrate = Migrate(app, db)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

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
        logging.error(f"Error during registration: {str(e)}")
        return jsonify({"message": str(e)}), 500

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
        logging.error(f"Error during login: {str(e)}")
        return jsonify({"message": str(e)}), 500

# Create a new quiz
@app.route("/quizzes", methods=["POST"])
def create_quiz():
    try:
        data = request.get_json()
        title = data.get("title")
        description = data.get("description")
        questions_data = data.get("questions")

        if not title or not questions_data:
            return jsonify({"message": "Quiz title and questions are required"}), 400

        # Create the quiz
        quiz = Quizzes(title=title, description=description)
        db.session.add(quiz)
        db.session.flush()  # To get the quiz ID for questions

        # Create questions for the quiz
        for question_data in questions_data:
            text = question_data.get("text")
            options = question_data.get("options")
            correct_answer = question_data.get("correct_answer")

            if not text or not options or not correct_answer:
                return jsonify({"message": "Each question must have text, options, and a correct answer"}), 400

            question = Questions(
                quiz_id=quiz.id,
                text=text,
                options=options,
                correct_answer=correct_answer
            )
            db.session.add(question)

        db.session.commit()

        logging.debug(f"Quiz created successfully with ID {quiz.id}")
        return jsonify({"message": "Quiz created successfully", "quiz_id": quiz.id}), 201
    except Exception as e:
        logging.error(f"Error creating quiz: {str(e)}")
        return jsonify({"message": str(e)}), 500

# Get all available quizzes
@app.route("/quizzes", methods=["GET"])
def get_quizzes():
    try:
        quizzes = Quizzes.query.all()
        quizzes_list = []

        for quiz in quizzes:
            quizzes_list.append({
                "id": quiz.id,
                "title": quiz.title,
                "description": quiz.description,
                "questions_count": len(quiz.questions)
            })

        logging.debug(f"Fetched quizzes: {quizzes_list}")
        return jsonify(quizzes_list), 200
    except Exception as e:
        logging.error(f"Error fetching quizzes: {str(e)}")
        return jsonify({"message": str(e)}), 500

# Get details of a specific quiz (including questions)
@app.route("/quizzes/<int:quiz_id>", methods=["GET"])
def get_quiz_details(quiz_id):
    try:
        quiz = Quizzes.query.get_or_404(quiz_id)

        questions = []
        for question in quiz.questions:
            questions.append({
                "id": question.id,
                "text": question.text,
                "options": question.options
            })

        quiz_details = {
            "id": quiz.id,
            "title": quiz.title,
            "description": quiz.description,
            "questions": questions
        }

        logging.debug(f"Fetched quiz details for quiz ID {quiz.id}")
        return jsonify(quiz_details), 200
    except Exception as e:
        logging.error(f"Error fetching quiz details: {str(e)}")
        return jsonify({"message": str(e)}), 500

# Submit quiz answers
@app.route("/quizzes/<int:quiz_id>/submit", methods=["POST"])
def submit_quiz(quiz_id):
    try:
        data = request.get_json()
        logging.debug(f"Received submission data: {data}")  # Log received data

        user_id = data['user_id']
        answers = data['answers']

        quiz = Quizzes.query.get_or_404(quiz_id)
        total_questions = len(quiz.questions)

        score = 0
        for question in quiz.questions:
            if str(question.id) in answers and answers[str(question.id)] == question.correct_answer:
                score += 1

        result = Results(
            quiz_id=quiz_id,
            user_id=user_id,
            score=score,
            total_questions=total_questions
        )

        db.session.add(result)
        db.session.commit()

        logging.debug(f"Quiz result saved for user {user_id} with score {score}")

        return jsonify({
            "message": "Quiz submitted successfully",
            "score": score,
            "total_questions": total_questions
        }), 200
    except Exception as e:
        logging.error(f"Error submitting quiz: {str(e)}")
        return jsonify({"message": str(e)}), 500

# Get user's quiz results
@app.route("/users/<int:user_id>/results", methods=["GET"])
def get_user_results(user_id):
    try:
        results = Results.query.filter_by(user_id=user_id).all()
        results_list = []

        for result in results:
            quiz = Quizzes.query.get(result.quiz_id)
            results_list.append({
                "quiz_title": quiz.title,
                "score": result.score,
                "total_questions": result.total_questions
            })

        logging.debug(f"Fetched results for user ID {user_id}")
        return jsonify(results_list), 200
    except Exception as e:
        logging.error(f"Error fetching user results: {str(e)}")
        return jsonify({"message": str(e)}), 500

# Main entry point
if __name__ == "__main__":
    create_tables()  # Create tables if they don't exist
    app.run(debug=True)
from flask import Flask, request, jsonify
from config import Config
from models import db, User, Quizzes, Questions, Results
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize the database and migration tools
db.init_app(app)
migrate = Migrate(app, db)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

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
        logging.error(f"Error during registration: {str(e)}")
        return jsonify({"message": str(e)}), 500

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
        logging.error(f"Error during login: {str(e)}")
        return jsonify({"message": str(e)}), 500

# Create a new quiz
@app.route("/quizzes", methods=["POST"])
def create_quiz():
    try:
        data = request.get_json()
        title = data.get("title")
        description = data.get("description")
        questions_data = data.get("questions")

        if not title or not questions_data:
            return jsonify({"message": "Quiz title and questions are required"}), 400

        # Create the quiz
        quiz = Quizzes(title=title, description=description)
        db.session.add(quiz)
        db.session.flush()  # To get the quiz ID for questions

        # Create questions for the quiz
        for question_data in questions_data:
            text = question_data.get("text")
            options = question_data.get("options")
            correct_answer = question_data.get("correct_answer")

            if not text or not options or not correct_answer:
                return jsonify({"message": "Each question must have text, options, and a correct answer"}), 400

            question = Questions(
                quiz_id=quiz.id,
                text=text,
                options=options,
                correct_answer=correct_answer
            )
            db.session.add(question)

        db.session.commit()

        logging.debug(f"Quiz created successfully with ID {quiz.id}")
        return jsonify({"message": "Quiz created successfully", "quiz_id": quiz.id}), 201
    except Exception as e:
        logging.error(f"Error creating quiz: {str(e)}")
        return jsonify({"message": str(e)}), 500

# Get all available quizzes
@app.route("/quizzes", methods=["GET"])
def get_quizzes():
    try:
        quizzes = Quizzes.query.all()
        quizzes_list = []

        for quiz in quizzes:
            quizzes_list.append({
                "id": quiz.id,
                "title": quiz.title,
                "description": quiz.description,
                "questions_count": len(quiz.questions)
            })

        logging.debug(f"Fetched quizzes: {quizzes_list}")
        return jsonify(quizzes_list), 200
    except Exception as e:
        logging.error(f"Error fetching quizzes: {str(e)}")
        return jsonify({"message": str(e)}), 500

# Get details of a specific quiz (including questions)
@app.route("/quizzes/<int:quiz_id>", methods=["GET"])
def get_quiz_details(quiz_id):
    try:
        quiz = Quizzes.query.get_or_404(quiz_id)

        questions = []
        for question in quiz.questions:
            questions.append({
                "id": question.id,
                "text": question.text,
                "options": question.options
            })

        quiz_details = {
            "id": quiz.id,
            "title": quiz.title,
            "description": quiz.description,
            "questions": questions
        }

        logging.debug(f"Fetched quiz details for quiz ID {quiz.id}")
        return jsonify(quiz_details), 200
    except Exception as e:
        logging.error(f"Error fetching quiz details: {str(e)}")
        return jsonify({"message": str(e)}), 500

# Submit quiz answers
@app.route("/quizzes/<int:quiz_id>/submit", methods=["POST"])
def submit_quiz(quiz_id):
    try:
        data = request.get_json()
        logging.debug(f"Received submission data: {data}")  # Log received data

        user_id = data['user_id']
        answers = data['answers']

        quiz = Quizzes.query.get_or_404(quiz_id)
        total_questions = len(quiz.questions)

        score = 0
        for question in quiz.questions:
            if str(question.id) in answers and answers[str(question.id)] == question.correct_answer:
                score += 1

        result = Results(
            quiz_id=quiz_id,
            user_id=user_id,
            score=score,
            total_questions=total_questions
        )

        db.session.add(result)
        db.session.commit()

        logging.debug(f"Quiz result saved for user {user_id} with score {score}")

        return jsonify({
            "message": "Quiz submitted successfully",
            "score": score,
            "total_questions": total_questions
        }), 200
    except Exception as e:
        logging.error(f"Error submitting quiz: {str(e)}")
        return jsonify({"message": str(e)}), 500

# Get user's quiz results
@app.route("/users/<int:user_id>/results", methods=["GET"])
def get_user_results(user_id):
    try:
        results = Results.query.filter_by(user_id=user_id).all()
        results_list = []

        for result in results:
            quiz = Quizzes.query.get(result.quiz_id)
            results_list.append({
                "quiz_title": quiz.title,
                "score": result.score,
                "total_questions": result.total_questions
            })

        logging.debug(f"Fetched results for user ID {user_id}")
        return jsonify(results_list), 200
    except Exception as e:
        logging.error(f"Error fetching user results: {str(e)}")
        return jsonify({"message": str(e)}), 500

# Main entry point
if __name__ == "__main__":
    create_tables()  # Create tables if they don't exist
    app.run(debug=True)
