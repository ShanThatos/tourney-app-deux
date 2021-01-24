import re
from flask import Blueprint, request, render_template
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import *
from models import *
from sqlalchemy import func

main = Blueprint("account", __name__)

@main.route("/account", methods=["GET", "DELETE", "POST"])
@login_required
@require_form_keys("name email phone school_name".split(" "))
def account(formData=None):
    if request.method == "GET":
        return render_template("/account/index.html", coach = Coach.query.get(session["id"]))
    elif request.method == "DELETE":
        Tourney.query.filter_by(coach_id=session["id"]).delete(synchronize_session=False)
        Student.query.filter_by(coach_id=session["id"]).delete(synchronize_session=False)
        db.session.delete(Coach.query.get(session["id"]))
        db.session.commit()
        return successJSON(redirect="/")
    elif request.method == "POST":
        account = Coach.query.get(session["id"])
        formData[1] = formData[1].lower()
        formData[2] = re.sub("[^0-9]", "", formData[2])
        if account.email.lower() != formData[1] and Coach.query.filter(func.lower(Coach.email) == formData[1]).first():
            return failJSON("An account with that email already exists")
        account.name = formData[0]
        account.email = formData[1]
        account.phone = formData[2]
        account.school_name = formData[3]
        db.session.commit()
        return successJSON("Your changes have been saved")

@main.route("/account/changepassword", methods=["GET", "POST"])
@login_required
@require_form_keys("old new newre".split(" "))
def changepassword(formData=None):
    if request.method == "GET":
        return render_template("/account/changepassword.html")
    elif request.method == "POST":
        print(formData)
        account = Coach.query.get(session["id"])
        if not check_password_hash(account.password, formData[0]):
            return failJSON("Incorrect Password")
        if len(formData[1]) < 5: return failJSON("Password is too short")
        if formData[1] != formData[2]:
            return failJSON("Your new password does not match the confirmation")
        account.password = generate_password_hash(formData[1])
        db.session.commit()
        return successJSON(redirect="/account")