from flask import Blueprint, request, render_template
from extensions import *
from models import *

main = Blueprint("tourney.account", __name__, url_prefix="/tournaments")

@main.route("/<int:tourney_id>/myregistrations")
@login_required
@require_tourney_exists
def myregistrations(tourney_id, tourney=None):
    pass