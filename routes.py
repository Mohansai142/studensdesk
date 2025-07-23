from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
import uuid
import json
from werkzeug.utils import secure_filename
from database.db_utils import DB_FILE
from image_to_text import extract_text_from_image, extract_marks_from_text

app_routes = Blueprint("app_routes", __name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # To access columns by name
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home
@app_routes.route("/")
def index():
    return render_template("index.html")

# Register
@app_routes.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        conn = get_db_connection()
        try:
            conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
            conn.commit()
            flash("Registration successful. Please login.")
            return redirect(url_for("app_routes.login"))
        except:
            flash("Username already exists.")
        finally:
            conn.close()
    return render_template("register.html")

# Login
@app_routes.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        conn.close()

        if user:
            session["username"] = user["username"]
            session["role"] = user["role"]

            if user["role"] == "teacher":
                return redirect(url_for("app_routes.upload"))
            else:
                return redirect(url_for("app_routes.dashboard"))

        flash("Invalid username or password.")
    return render_template("login.html")

# Student Dashboard
@app_routes.route("/dashboard")
def dashboard():
    if "username" not in session:
        flash("Login first.")
        return redirect(url_for("app_routes.login"))

    if session.get("role") != "student":
        flash("Only students can access dashboard.")
        return redirect(url_for("app_routes.upload"))

    username = session["username"]
    conn = get_db_connection()
    marks = conn.execute("SELECT subject, score FROM marks WHERE LOWER(username)=LOWER(?)", (username,)).fetchall()
    conn.close()

    subjects = [row["subject"] for row in marks]
    scores = [row["score"] for row in marks]

    return render_template("dashboard.html", username=username, marks=marks, subjects=subjects, scores=scores)

# Upload for Teacher
@app_routes.route("/upload", methods=["GET", "POST"])
def upload():
    if "username" not in session:
        flash("Login first.")
        return redirect(url_for("app_routes.login"))

    if session.get("role") != "teacher":
        flash("Only teachers can upload marks.")
        return redirect(url_for("app_routes.dashboard"))

    if request.method == "POST":
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash('Invalid file type. Only PNG, JPG, JPEG allowed.')
            return redirect(request.url)

        try:
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(file_path)

            raw_text = extract_text_from_image(file_path)
            if not raw_text:
                flash("No text found in image.")
                os.remove(file_path)
                return redirect(url_for("app_routes.upload"))

            marks_json = extract_marks_from_text(raw_text)
            try:
                marks_dict = json.loads(marks_json)

                # ✅ Expecting student_name inside marks_dict
                if not isinstance(marks_dict, dict) or "student_name" not in marks_dict:
                    raise ValueError("Missing or invalid student_name in extracted data")

                student_name = marks_dict.pop("student_name").strip()

                if not student_name:
                    flash("Student name not found in the answer sheet.")
                    return redirect(url_for("app_routes.upload"))

                conn = get_db_connection()
                for subject, score in marks_dict.items():
                    try:
                        clean_score = int(float(score)) if str(score).replace('.', '', 1).isdigit() else 0
                        conn.execute(
                            "INSERT INTO marks (username, subject, score) VALUES (?, ?, ?)",
                            (student_name, subject.strip(), clean_score)
                        )
                    except (ValueError, AttributeError):
                        continue
                conn.commit()
                conn.close()

                flash(f"Marks successfully saved for {student_name}!")
                return render_template("result.html", marks=marks_dict, raw_text=raw_text)

            except (json.JSONDecodeError, ValueError):
                flash("Could not parse marks or student name.")
                return render_template("debug.html", raw_text=raw_text, raw_response=marks_json)

        except Exception as e:
            flash(f"Error: {str(e)}")
            return redirect(url_for("app_routes.upload"))
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    return render_template("upload.html")

# Logout
@app_routes.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("role", None)
    flash("Logged out.")
    return redirect(url_for("app_routes.login"))
