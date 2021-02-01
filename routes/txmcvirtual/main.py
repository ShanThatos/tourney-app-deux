from flask import Blueprint, request, render_template
from extensions import *
from models import *

main = Blueprint("txmcvirtual", __name__)

@main.route("/vtschedule")
def vtschedule():
    return render_template("/txmcvirtual/schedule.html")