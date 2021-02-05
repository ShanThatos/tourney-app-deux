import jinja2
from flask import Blueprint, request, render_template
from extensions import *
from models import *
from sqlalchemy import func

main = Blueprint("tourney.owner", __name__, url_prefix="/tournaments")

@main.route("/<int:tourney_id>/edit", methods=["GET", "POST"])
@require_tourney_access
def tourneyEdit(tourney_id):
    tourney = Tourney.query.get(tourney_id)
    if request.method == "GET":
        return render_template("/tourneys/edit.html", coaches = Coach.query.all(), tourney = tourney)
    elif request.method == "POST":
        tourney.update(parseRequestForm())
        db.session.commit()
        return successJSON("Changes have been saved")

collab_row = jinja2.Template(open("templates/tourneys/macros/createMacros.html").read()).module.collab_row
@main.route("/<int:tourney_id>/collaborators", methods=["PUT", "DELETE"])
@require_tourney_access
@require_form_keys(["coach_id"], method="PUT")
@require_form_keys(["coach_id"], method="DELETE")
def tourneyCollaborators(tourney_id, formData=None):
    coach = Coach.query.get(formData[0])
    tourney = Tourney.query.get(tourney_id)
    if tourney.owner.id == coach.id: return failJSON("This coach is the owner")
    if request.method == "PUT":
        if coach in tourney.collaborators: return failJSON("This coach is already a collaborator")
        tourney.collaborators.append(coach)
        ret = successJSON(html=collab_row(coach, tourney))
    elif request.method == "DELETE":
        if coach not in tourney.collaborators: return failJSON("This coach is not a collaborator")
        tourney.collaborators.remove(coach)
        ret = successJSON(id=coach.id)
    db.session.add(tourney)
    db.session.commit()
    return ret

data_entry_row = jinja2.Template(open("templates/tourneys/macros/createMacros.html").read()).module.data_entry_row
@main.route("/<int:tourney_id>/dataentry", methods=["GET", "PUT", "DELETE"])
@require_tourney_access
@require_form_keys(["username"], method="PUT")
@require_form_keys(["id"], method="DELETE")
def tourneyDataEntry(tourney_id, formData=None):
    if request.method == "GET":
        id = request.args.get("id")
        if not id: return redirect("/")
        account = DataEntry.query.get(id)
        if account.tourney_id != tourney_id: return redirect("/")
        session.clear()
        session["dataentry_id"] = id
        session["tourney_id"] = account.tourney_id
        return redirect("/dataentry")
    elif request.method == "PUT":
        formData[0] = formData[0].lower()
        if DataEntry.query.filter(func.lower(DataEntry.username) == formData[0]).first():
            return failJSON("An account with that username already exists (It may exist for another tournament)")
        account = DataEntry(formData[0], tourney_id)
        db.session.add(account)
        db.session.commit()
        return successJSON(html=data_entry_row(account))
    elif request.method == "DELETE":
        account = DataEntry.query.get(formData[0])
        if not account: return failJSON("That account does not exist")
        if tourney_id != account.tourney_id: return failJSON("That account does not belong to you")
        db.session.delete(account)
        db.session.commit()
        return successJSON(id=account.id)

@main.route("/<int:tourney_id>/attending", methods=["GET", "POST"])
@require_tourney_access
@require_form_keys(["coach_id", "paid", "comments"])
def tourneyAttending(tourney_id, formData=None):
    if request.method == "GET":
        tourney = Tourney.query.get(tourney_id)
        data = execute("tourney_attending", tourney_id)
        return render_template("/tourneys/attending.html", tourney=tourney, data=data)
    elif request.method == "POST":
        formData[1] = formData[1] == "true"
        if len(formData) == 2: formData.append("")
        tc = TourneyCoach.query.filter_by(tourney_id=tourney_id, coach_id=formData[0]).first()
        tc.paid = formData[1]
        tc.comments = formData[2]
        db.session.commit()
        return successJSON("Your changes have been saved")