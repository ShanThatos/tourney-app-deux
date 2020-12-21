from flask import Flask
from flask_session import Session

app = Flask(__name__)

app.config["SECRET_KEY"] = "l_9FiY9e2fFPAiZK8kHQ68j-Zo75jTRQ7PIsRiM-wNY"
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.before_request
def before_request():
    pass

@app.after_request
def after_request(response):
    if response.headers["Content-Type"] == "text/html":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
    return response