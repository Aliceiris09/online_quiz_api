from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    quizzes = db.relationship('Quizzes', backref='user', lazy=True)

class Quizzes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    questions = db.relationship('Questions', backref='quiz', lazy=True)
    description = db.Column(db.String(255), nullable=True)

class Questions(db.Model):
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'))
    id = db.Column(db.Integer, primary_key=True)
    options = db.Column(db.String(80), nullable=False)
    correct_answer = db.Column(db.String(80), nullable=False)
    text = db.Column(db.String(80), nullable=False)  # Correct field name

class Results(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)   
    score = db.Column(db.Integer)
    total_questions = db.Column(db.Integer, nullable=False)