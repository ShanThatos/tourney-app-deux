import os
import re
import pytz
import random
import string
import stripe
from datetime import datetime
from functools import wraps
from flask import session, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

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

def dictify(result):
    return [{x[0]:x[1] for x in row.items()} for row in result]

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
    tourney = dictify(db.engine.execute("SELECT * FROM tourneys WHERE id = '%s'" % str(tourney_id)))
    if tourney[0]["coach_id"] == session["id"]: return True
    if session["admin_access"]: return True
    return False

def require_tourney_access(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not has_tourney_access(kwargs["tourney_id"]):
            return redirect(url_for('main.login', continueURL=request.url))
        return f(*args, **kwargs)
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
    if "T" in dt:
        date = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
    else:
        date = datetime.strptime(dt, "%Y-%m-%d")
    return date.strftime(outputFormat)

def ordinal(n):
    return "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])

CST_TZ = pytz.timezone("America/Chicago")
def current_time():
    return datetime.now(CST_TZ).replace(tzinfo=None)

def getDateTime(dt):
    if "T" in dt:
        return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
    return datetime.strptime(dt, "%Y-%m-%d")