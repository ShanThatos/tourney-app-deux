import os
import extensions

from flask import Flask, request, redirect, session, render_template
from flask_session import Session
from flask_migrate import Migrate
from dotenv import load_dotenv

from extensions import *
from models import *

from routes.main import main as mainRoutes
from routes.tournaments.main import main as tourneyMainRoutes
from routes.tournaments.owner import main as tourneyOwnerRoutes
from routes.admin import main as adminRoutes


load_dotenv()
app = Flask(__name__)

app.config["SECRET_KEY"] = "l_9FiY9e2fFPAiZK8kHQ68j-Zo75jTRQ7PIsRiM-wNY"
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.config["CACHE_STATIC_FILES"] = False

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {"pool_pre_ping": True}
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
db.init_app(app)

app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

Migrate(app, db)

@app.before_request
def before_request():
    if not request.is_secure and app.env != "development":
        return redirect(request.url.replace("http://", "https://", 1), code=301)

@app.after_request
def after_request(response):
    response.headers["Current-URL"] = request.url
    if response.headers["Content-Type"] == "text/html" or not app.config["CACHE_STATIC_FILES"]:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
    return response

@app.errorhandler(404)
def page_not_found(e):
    return render_template("/main/404.html")

for route in [mainRoutes, adminRoutes, tourneyOwnerRoutes, tourneyMainRoutes]:
    app.register_blueprint(route)

app.add_template_global(extensions, name="ext")

if __name__ == "__main__":
    app.env = "development"
    app.run("0.0.0.0", 80, debug=True)