from flask import Blueprint, request, jsonify
from models import db, Quizzes, Questions, Results

questions_bp = Blueprint('questions', __name__)

@questions_bp.route('/create_quiz_with_questions', methods=['POST'])
def create_quiz_with_questions():
    try:
        data = request.get_json()
        quiz_title = data.get('title')
        questions_data = data.get('questions')

        # Create a new quiz
        new_quiz = Quizzes(title=quiz_title)
        db.session.add(new_quiz)
        db.session.commit()  # Commit to get the quiz ID

        # Create questions
        for question in questions_data:
            question_text = question.get('question_text')
            answer = question.get('answer')
            new_question = Questions(quiz_id=new_quiz.id, question_text=question_text, answer=answer)
            db.session.add(new_question)

        db.session.commit()  # Commit all questions

        return jsonify({"message": "Quiz and questions created successfully."}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500

@questions_bp.route('/quizzes', methods=['GET'])
def get_quizzes():
    try:
        quizzes = Quizzes.query.all()
        return jsonify([{"id": quiz.id, "title": quiz.title} for quiz in quizzes]), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@questions_bp.route('/quiz/<int:quiz_id>', methods=['GET'])
def get_quiz_details(quiz_id):
    try:
        quiz = Quizzes.query.get(quiz_id)
        if not quiz:
            return jsonify({"message": "Quiz not found"}), 404

        questions = Questions.query.filter_by(quiz_id=quiz_id).all()
        quiz_data = {
            "id": quiz.id,
            "title": quiz.title,
            "questions": [{"id": question.id, "text": question.question_text} for question in questions]
        }
        return jsonify(quiz_data), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@questions_bp.route('/submit_answers', methods=['POST'])
def submit_answers():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        quiz_id = data.get('quiz_id')
        answers = data.get('answers')  # List of answers submitted by the user

        # Logic to calculate score based on the submitted answers
        correct_answers = Questions.query.filter_by(quiz_id=quiz_id).all()
        score = sum(1 for question in correct_answers if question.answer in answers)

        # Save results to Results table (not shown here; ensure you have a Results model)
        new_result = Results(user_id=user_id, quiz_id=quiz_id, score=score)
        db.session.add(new_result)
        db.session.commit()

        return jsonify({"message": "Answers submitted successfully", "score": score}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 500
