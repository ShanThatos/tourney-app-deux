import os
import re
import pytz
import random
import string
import stripe
import smtplib
import datetime
from functools import wraps
from flask import session, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()

stripe.api_key = os.environ.get("STRIPE_API_KEY")
STRIPE_PUBLIC_KEY = os.environ.get("STRIPE_PUBLIC_KEY")
STRIPE_ENDPOINT_SECRET = os.environ.get("STRIPE_ENDPOINT_SECRET")

PROXY = os.environ.get("PROXY")

db = SQLAlchemy()

scripts = {}
with open('procs.sql', 'r') as file:
    scriptName = ""
    query = []
    for line in file.readlines():
        line = line.strip()
        if not scriptName:
            scriptName = line
        else:
            query.append(line)
            if line.endswith(";"):
                scripts[scriptName] = " ".join(query)
                scriptName = ""
                query.clear()

def sendEmail(recipient=None, subject=None, message=None):
    msg = MIMEMultipart()
    msg["From"] = "TXMC Online - TexasMathContests"
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.attach(MIMEText(message))
    s = smtplib.SMTP("smtp.gmail.com", 587)
    s.starttls()
    s.login("texasmathcontests@gmail.com", os.environ.get("GMAIL_APP_PASSWORD"))
    s.sendmail("texasmathcontests@gmail.com", recipient, msg.as_string())
    s.quit()


def failJSON(*args):
    if len(args) == 1:
        return {"status" : "Failure", "message" : args[0]}
    return {"status" : "Failure"}
def successJSON(*args, **kwargs):
    ret = {"status" : "Success"} | kwargs
    if args:
        ret["message"] = args[0]
    return ret

def parseRequestForm(required=[]):
    ret = {}
    form = request.form.to_dict()
    for key in form:
        val = form[key]
        val = int(val) if val.isnumeric() else val
        if key not in required and not val: 
            continue
        val = val == "true" if val in ["true", "false"] else val
        allKeys = [x for x in re.split("[\\[\\]]+", key) if x]
        cn = ret
        for i, subkey in enumerate(allKeys):
            if subkey.isnumeric():
                subkey = int(subkey)
            if i == len(allKeys) - 1:
                cn[subkey] = val
            else:
                cn[subkey] = cn.get(subkey, {})
                cn = cn[subkey]
    return ret

def _fix(arg):
    if type(arg) is str and arg.isnumeric():
        return int(arg)
    elif type(arg) is list:
        return [_fix(x) for x in arg]
    elif type(arg) is dict:
        return {_fix(x):_fix(y) for x,y in arg.items()}
    return arg
def dictify(result):
    return [{_fix(x[0]):_fix(x[1]) for x in row.items()} for row in result]

def _normalize(arg):
    if type(arg) is list:
        return "(" + ",".join([_normalize(x) for x in arg]) + ")"
    return f"'{arg}'"
def execute(scriptName, *args, **kwargs):
    script = scripts[scriptName].strip().removesuffix(";")
    tokens = re.split(" +", script)
    ci = 0
    for i in range(len(tokens)):
        token = tokens[i]
        if re.fullmatch(r"%s", token):
            tokens[i] = _normalize(args[ci])
            ci += 1
        elif match := re.fullmatch(r":([a-zA-Z]\w*)", token):
            tokens[i] = _normalize(kwargs[match.group(1)])
    return dictify(db.engine.execute(" ".join(tokens) + ";"))

def require_form_keys(keys, method="POST"):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method != method:
                return f(*args, **kwargs)
            formData = [request.form.get(x).strip() for x in keys if request.form.get(x)]
            if request.method == method and any([not x for x in formData]):
                return failJSON("Missing arguments")
            return f(*args, **kwargs, formData=formData)
        return decorated_function
    return decorator

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "id" not in session:
            return redirect(url_for('main.login', continueURL=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "id" not in session:
            return redirect(url_for('main.login', continueURL=request.url))
        if not session["admin"]:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

def has_tourney_access(tourney_id):
    if "id" not in session: return False
    if session["admin"]: return True
    tourney = dictify(db.engine.execute("SELECT *, ARRAY(SELECT coach_id FROM tourneycollabs tc WHERE tc.tourney_id = t.id) AS collabs FROM tourneys t WHERE id = '%s';" % str(tourney_id)))[0]
    if tourney["coach_id"] == session["id"]: return True
    if session["id"] in tourney["collabs"]: return True
    return False

def require_tourney_access(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not has_tourney_access(kwargs["tourney_id"]):
            return redirect(url_for('main.login', continueURL=request.url))
        return f(*args, **kwargs)
    return decorated_function

def require_tourney_exists(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tourney = dictify(db.engine.execute("SELECT * FROM tourneys WHERE id = '%s'" % str(kwargs["tourney_id"])))
        if not tourney:
            return redirect("/tournaments")
        return f(*args, **kwargs, tourney=tourney[0])
    return decorated_function

def random_password(length):
    characters = "".join([x for x in string.ascii_letters + string.digits if x not in "iIlLoO10"])
    return "".join([random.choice(characters) for i in range(length)])

def groupsof(n, k):
    if not k: return []
    ret = [[]]
    for el in k:
        if len(ret[-1]) < n:
            ret[-1].append(el)
        else:
            ret.append([el])
    return ret

def formatDateTime(dt, outputFormat):
    if isinstance(dt, (datetime.datetime, datetime.date)): return dt.strftime(outputFormat)
    if "T" in dt:
        date = datetime.datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
    else:
        date = datetime.datetime.strptime(dt, "%Y-%m-%d")
    return date.strftime(outputFormat)

def ordinal(n):
    return "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])

CST_TZ = pytz.timezone("America/Chicago")
def current_time():
    return datetime.datetime.now(CST_TZ).replace(tzinfo=None)

def getDateTime(dt):
    if isinstance(dt, (datetime.datetime, datetime.date)): return dt
    if "T" in dt:
        if dt.count(":") == 1:
            return datetime.datetime.strptime(dt, "%Y-%m-%dT%H:%M")
        return datetime.datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
    return datetime.datetime.strptime(dt, "%Y-%m-%d")