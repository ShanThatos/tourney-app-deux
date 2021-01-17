from flask import Blueprint, render_template
from extensions import *
from models import *

main = Blueprint("tourney", __name__, url_prefix="/tournaments")

@main.route("/")
def tourneyIndex():
    return render_template("/tourneys/index.html", data = dictify(db.engine.execute(scripts["tourney_index"])))