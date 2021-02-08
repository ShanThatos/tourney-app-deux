import re
import jinja2
import stripe
from flask import Blueprint, request, jsonify, session, render_template, Response
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
    return redirect("/students")

@main.route("/login", methods=["GET", "POST", "PUT"])
@require_form_keys("username password".split(" "))
@require_form_keys(["email"], method="PUT")
def login(formData=None):
    session.clear()
    if request.method == "GET":
        return render_template("/main/login.html")
    elif request.method == "POST":
        formData[0] = formData[0].lower()
        coach = Coach.query.filter(func.lower(Coach.email) == formData[0]).first()
        if not coach: 
            account = DataEntry.query.filter(func.lower(DataEntry.username) == formData[0]).first()
            if not account or account.password != formData[1]:
                return failJSON("Invalid Username/Password")
            session["dataentry_id"] = account.id
            session["tourney_id"] = account.tourney_id
            return redirect("/dataentry/scores")
        if not check_password_hash(coach.password, formData[1]):
            return failJSON("Invalid Username/Password")
        session["id"] = coach.id
        session["admin"] = coach.admin
        if not coach.students.first():
            return redirect(request.args.get("continueURL") or "/students")
        return redirect(request.args.get("continueURL") or "/")
    elif request.method == "PUT":
        formData[0] = formData[0].lower()
        coach = Coach.query.filter(func.lower(Coach.email) == formData[0]).first()
        if not coach:
            return failJSON("We could not find any accounts associated with that email")
        newpass = random_password(6)
        coach.password = generate_password_hash(newpass)
        db.session.commit()
        sendEmail(recipient=coach.email, subject="TXMC Online - Password Reset", 
            message=f"TXMC Update: \nYour password has been reset.\n\nNew Password: {newpass}\n\nAfter logging in go to your account settings to change your password.\n\n\t- TXMC Online"
        )
        return successJSON("Your password has been reset. Please check your email for your new password. After logging in go to your Account Settings to change your password.")
        

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
        students = Coach.query.get(session["id"]).students.order_by(Student.grade.asc(), Student.first_name.asc(), Student.last_name.asc()).all()
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

@main.route("/contact", methods=["GET", "POST"])
@require_form_keys(["message"])
def contact(formData=None):
    if request.method == "GET":
        return render_template("/main/contact.html")
    email = request.form.get("from", "Anonymous")
    sendEmail(recipient="texasmathcontests@gmail.com", 
        subject=f"Message - {email}", 
        message=f"Message from {email}\n\n{formData[0]}")
    return successJSON("Your message has been sent", redirect="/")

from .txmcvirtual.account import finishRegistration

@main.route("/webhook", methods=["POST"])
def webhook():
    try:
        event = stripe.Webhook.construct_event(
            request.get_data(), 
            request.environ.get("HTTP_STRIPE_SIGNATURE"), 
            STRIPE_ENDPOINT_SECRET
        )
    except ValueError as e:
        return {}, 400
    except stripe.error.SignatureVerificationError as e:
        return {}, 400
    if event["type"] == "checkout.session.completed":
        stripe_session_id = event["data"]["object"]["id"]
        order = Order.query.filter_by(session_id=stripe_session_id).first()
        if order.name == "txmcvirtualregister":
            finishRegistration(order.info)
            db.session.delete(order)
            db.session.commit()
    return {}