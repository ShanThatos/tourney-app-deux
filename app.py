import os
from flask import Flask, request, redirect, session, render_template
from flask_session import Session
from flask_migrate import Migrate
from dotenv import load_dotenv

from extensions import db
from models import *
from routes.main import main as mainRoutes

load_dotenv()
app = Flask(__name__)

app.config["SECRET_KEY"] = "l_9FiY9e2fFPAiZK8kHQ68j-Zo75jTRQ7PIsRiM-wNY"
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.config["CACHE_STATIC_FILES"] = False

app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
db.init_app(app)

migrate = Migrate(app, db)

@app.before_request
def before_request():
    if "id" in session:
        session["admin"] = Coach.query.get(session["id"]).admin
    if not request.is_secure and app.env != "development":
        url = request.url.replace("http://", "https://", 1)
        code = 301
        return redirect(url, code=code)

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
    return render_template("/main/404.html"), 404

app.register_blueprint(mainRoutes)

if __name__ == "__main__":
    app.env = "development"
    app.run("0.0.0.0", 80, debug=True)