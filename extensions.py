from functools import wraps
from flask import session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy

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

def require_form_keys(keys):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method != "POST":
                return f(*args, **kwargs)
            formData = [request.form.get(x) for x in keys]
            if request.method == "POST" and any([not x for x in formData]):
                return failJSON("Missing arguments")
            return f(*args, **kwargs, formData=formData)
        return decorated_function
    return decorator

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "id" not in session:
            return redirect(url_for('login', continueURL=request.url))
        return f(*args, **kwargs)
    return decorated_function
