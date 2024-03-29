from datetime import timedelta
import jinja2
import extensions
from flask import Blueprint, render_template, session
from extensions import *
from models import *
from sqlalchemy import func

main = Blueprint("tourney", __name__, url_prefix="/tournaments")

@main.route("/")
def tourneyIndex():
    coachData = None
    if "id" in session:
        coachData = execute("tourney_index_coach_info", session["id"])[0]["data"]
    if request.args.get("past"):
        data = Tourney.query.filter(Tourney.date < current_time()).order_by(Tourney.date.asc()).all()
    else:
        data = Tourney.query.filter(Tourney.date >= (current_time() - timedelta(days=3))).order_by(Tourney.date.asc()).all()
    return render_template("/tourneys/index.html", data = data, coachData = coachData)

resultsMacros = jinja2.Template(open("templates/tourneys/macros/resultsMacros.html").read()).module
individual_grade_test = resultsMacros.individual_grade_test
individual_grade_top_gun = resultsMacros.individual_grade_top_gun
individual_level_test = resultsMacros.individual_level_test
sweepstakes_test = resultsMacros.sweepstakes_test
@main.route("/<int:tourney_id>/results", methods=["GET", "POST"])
@require_tourney_exists
@require_form_keys(["resultstype"])
def results(tourney_id, tourney=None, formData=None):
    if not has_tourney_access(tourney_id) and current_time() < getDateTime(tourney["info"]["results_open"]):
        return redirect("/tournaments")
    if request.method == "GET":
        return render_template("/tourneys/results.html", tourney=tourney)
    elif request.method == "POST":
        type, grade, test = formData[0].split("-")
        if type == "I" and grade.isnumeric() and test in ["NS", "CA", "GM", "GS"]:
            return successJSON(html=individual_grade_test(tourney_id, int(grade), test, ext=extensions))
        if type == "I" and grade.isnumeric() and test == "O":
            return successJSON(html=individual_grade_top_gun(tourney_id, int(grade), ext=extensions))
        if type == "I" and grade in "EM" and test in ["NS", "CA", "GM", "GS"]:
            return successJSON(html=individual_level_test(tourney_id, grade, test, ext=extensions))
        if type == "S" and grade in "EM" and test in ["NS", "CA", "GM", "GS"]:
            return successJSON(html=sweepstakes_test(tourney_id, grade, test, ext=extensions))
        print(type, grade, test)
        return successJSON(html="<h2>Results Not Available Yet</h2>")