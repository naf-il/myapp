
import os
import time

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

app = Flask(__name__)

# Database configuration
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "student_db")
DB_USER = os.getenv("POSTGRES_USER", "admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# Student database model
class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    course = db.Column(db.String(100))


# Home endpoint
@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to Student Management System API",
        "status": "Running successfully"
    })


# Health check endpoint
@app.route("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({
            "status": "healthy",
            "database": "connected"
        }), 200
    except OperationalError:
        db.session.rollback()
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected"
        }), 503


# Add a new student
@app.route("/api/students", methods=["POST"])
def add_student():
    data = request.get_json(silent=True) or {}

    name = data.get("name")
    email = data.get("email")
    course = data.get("course")

    if not name or not email or not course:
        return jsonify({
            "error": "Name, email and course are required"
        }), 400

    student = Student(
        name=name,
        email=email,
        course=course
    )

    try:
        db.session.add(student)
        db.session.commit()

        return jsonify({
            "message": "Student added successfully",
            "student_id": student.id
        }), 201

    except Exception:
        db.session.rollback()
        return jsonify({
            "error": "Could not add student. Check whether the email already exists."
        }), 409


# Get all students
@app.route("/api/students", methods=["GET"])
def get_students():
    students = Student.query.order_by(Student.id).all()

    return jsonify([
        {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "course": student.course
        }
        for student in students
    ])


if __name__ == "__main__":
    # Wait for database initialization
    for attempt in range(10):
        try:
            with app.app_context():
                db.create_all()
                print("Database connected successfully!")
            break
        except OperationalError:
            print("Waiting for database...")
            time.sleep(3)
    else:
        raise RuntimeError("Could not connect to the database")

    app.run(host="0.0.0.0", port=5000)

