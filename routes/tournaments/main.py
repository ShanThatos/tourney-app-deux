from flask import Blueprint, render_template, session
from extensions import *
from models import *

main = Blueprint("tourney", __name__, url_prefix="/tournaments")

@main.route("/")
def tourneyIndex():
    coachData = None
    if "id" in session:
        coachData = execute("tourney_index_coach_info", session["id"])[0]["data"]
    data = Tourney.query.order_by(Tourney.date.asc()).all()
    return render_template("/tourneys/index.html", data = data, coachData = coachData)