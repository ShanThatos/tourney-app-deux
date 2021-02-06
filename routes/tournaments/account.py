from flask import Blueprint, request, render_template
from extensions import *
from models import *

main = Blueprint("tourney.account", __name__, url_prefix="/tournaments")
