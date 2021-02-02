import jinja2
import json
from flask import Blueprint, request, render_template
from extensions import *
from models import *
from sqlalchemy import func

main = Blueprint("admin", __name__, url_prefix="/admin")

@main.route("/tournaments/create", methods=["GET", "POST"])
@admin_required
def create():
    if request.method == "GET":
        return render_template("/tourneys/create.html", coaches=Coach.query.all())
    elif request.method == "POST":
        tourney = Tourney(parseRequestForm())
        db.session.add(tourney)
        db.session.commit()
        return successJSON(redirect="/tournaments")

students_table = jinja2.Template(open("templates/admin/macros/schoolgroupMacros.html").read()).module.students_table
schools_select = jinja2.Template(open("templates/admin/macros/schoolgroupMacros.html").read()).module.schools_select
school_card = jinja2.Template(open("templates/admin/macros/schoolgroupMacros.html").read()).module.school_card
@main.route("/schoolgroups", methods=["GET", "PATCH", "PUT", "POST", "DELETE"])
@admin_required
@require_form_keys(["student_id"], method="PATCH")
@require_form_keys(["school_name"], method="PUT")
@require_form_keys(["school", "ids"], method="POST")
@require_form_keys(["school_id"], method="DELETE")
def schoolgroups(formData=None):
    if request.method == "GET":
        return render_template("/admin/schoolgroups.html", schools = School.query.order_by(School.name).all(), students = Student.query.all())
    elif request.method == "PATCH":
        Student.query.get(formData[0]).school_id = None
        db.session.commit()
        return successJSON(html=students_table(Student.query.all()))
    elif request.method == "PUT":
        if School.query.filter(func.lower(School.name) == formData[0].lower()).first():
            return failJSON("A group with that name already exists")
        school = School(name=formData[0])
        db.session.add(school)
        db.session.commit()
        return successJSON(html=schools_select(School.query.order_by(School.name).all()), html2=school_card(school))
    elif request.method == "POST":
        formData[1] = json.loads(formData[1])
        Student.query.filter(Student.id.in_(formData[1])).update({Student.school_id : formData[0]}, synchronize_session = False)
        db.session.commit()
        return successJSON(html=students_table(Student.query.all()), id2=formData[0], html2=school_card(School.query.get(formData[0])))
    elif request.method == "DELETE":
        school = School.query.get(formData[0])
        school.students.update({Student.school_id : None}, synchronize_session = False)
        db.session.delete(school)
        db.session.commit()
        return successJSON(html=students_table(Student.query.all()), html2=schools_select(School.query.order_by(School.name).all()))

@main.route("/accounts", methods=["GET", "POST"])
@admin_required
@require_form_keys(["admin", "coach_id"], method="POST")
def accounts(formData=None):
    if request.method == "GET":
        return render_template("admin/accounts.html", coaches=Coach.query.order_by(Coach.id.asc()).all())
    elif request.method == "POST":
        session["id"] = int(formData[1])
        session["admin"] = formData[0] == 'true'
        return successJSON(redirect="/")