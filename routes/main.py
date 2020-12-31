import re
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
    formData[2] = re.sub("[^0-9]", "", formData[2])
    if formData[-2] != formData[-1]: return failJSON("Passwords do not match")
    if len(formData[-2]) < 5: return failJSON("Password is too short")
    formData[-2] = generate_password_hash(formData[-2])
    if Coach.query.filter(func.lower(Coach.email) == func.lower(formData[1])).first(): 
        return failJSON("Email is already registered")
    coach = Coach(formData[:-1])
    print(coach.id)
    session["id"] = coach.id
    db.session.add(coach)
    db.session.commit()
    return failJSON("HEY THERE")

@main.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "GET":
        return "login"
    formData = [request.form.get(x) for x in ["username", "password"]]
    coachData = db.execute("SELECT coach_id, coach_pass FROM coaches WHERE LOWER(coach_email) = LOWER(%s)", formData[0])
    if not coachData or not check_password_hash(coachData[0]["coach_pass"], formData[1]):
        return failJSON("Invalid Username & Password")
    session["coach_id"] = coachData[0]["coach_id"]
    return successJSON(redirect=request.args.get("continueURL") or "/")
