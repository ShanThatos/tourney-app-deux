import re
import jinja2
from flask import Blueprint, request, jsonify, session, render_template
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import func
from extensions import *
from models import *

main = Blueprint("main", __name__)

@main.route("/")
def index():
    return render_template("/main/index.html")

@main.route("/register", methods=["GET", "POST"])
@require_form_keys("coachname email number school password retypepassword".split(" "))
def register(formData=None):
    session.clear()
    if request.method == "GET":
        return render_template("/main/register.html")
    formData[1] = formData[1].lower()
    formData[2] = re.sub("[^0-9]", "", formData[2])
    if formData[-2] != formData[-1]: return failJSON("Passwords do not match")
    if len(formData[-2]) < 5: return failJSON("Password is too short")
    formData[-2] = generate_password_hash(formData[-2])
    if Coach.query.filter(func.lower(Coach.email) == formData[1]).first():
        return failJSON("Email is already registered")
    coach = Coach(formData[:-1])
    db.session.add(coach)
    db.session.commit()
    session["id"] = coach.id
    session["admin"] = coach.admin
    if not coach.students:
        return redirect("/students")
    return redirect("/")

@main.route("/login", methods=["GET", "POST"])
@require_form_keys("username password".split(" "))
def login(formData=None):
    session.clear()
    if request.method == "GET":
        return render_template("/main/login.html")
    coach = Coach.query.filter(func.lower(Coach.email) == formData[0].lower()).first()
    if not coach or not check_password_hash(coach.password, formData[1]):
        return failJSON("Invalid Username/Password")
    session["id"] = coach.id
    session["admin"] = coach.admin
    if not coach.students:
        return redirect(request.args.get("continueURL") or "/students")
    return redirect(request.args.get("continueURL") or "/")

@main.route("/logout")
def logout():
    session.clear()
    return redirect("/")

student_row = jinja2.Template(open("templates/main/macros/studentMacros.html").read()).module.student_row
@main.route("/students", methods=["GET", "PUT", "DELETE", "POST"])
@login_required
@require_form_keys("first_name last_name grade".split(" "), method="PUT")
@require_form_keys(["stid"], method="DELETE")
@require_form_keys("id first_name last_name grade".split(" "))
def students(formData=None):
    if request.method == "GET":
        students = sorted(Coach.query.get(session["id"]).students, key=lambda n: (n.grade, n.first_name, n.last_name))
        return render_template("/main/students.html", students=students)
    elif request.method == "PUT":
        if not formData[2].isnumeric(): return failJSON("Invalid Grade, requires only numbers")
        student = Student(formData + [session["id"]])
        db.session.add(student)
        db.session.commit()
        return successJSON(html=student_row(student))
    elif request.method == "DELETE":
        student = Student.query.get(formData[0])
        if student.coach_id != session["id"]: return failJSON("This student does not belong to you")
        db.session.delete(student)
    elif request.method == "POST":
        if not formData[3].isnumeric(): return failJSON("Invalid Grade, requires only numbers")
        formData[3] = int(formData[3])
        if not (3 <= formData[3] <= 8): return failJSON("Invalid Grade")
        student = Student.query.get(formData[0])
        if student.coach_id != session["id"]: return failJSON("This student does not belong to you")
        student.first_name = formData[1]
        student.last_name = formData[2]
        student.grade = formData[3]
    db.session.commit()
    return successJSON()
