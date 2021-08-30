import json
import jinja2
import random
from flask import Blueprint, request, render_template
from extensions import *
from models import *
from testgenerator import *

main = Blueprint("virtualtest", __name__, url_prefix="/virtualtest")

@main.route("/ns")
def virtualNSTest():
    return render_template("/virtualtest/nsvirtual.html", title="Test")

def processQuestionData():
    data = parseRequestForm()
    if "statement" not in data:
        return None, None, None, "Missing statement"
    if "questiondisplayname" not in data:
        return None, None, None, "Missing display name"

    info = { "vars": [], "statements": [], "answer": data["answer"], "choices": [], "modifiers": []}
    info["displayname"] = data["questiondisplayname"].strip()
    if "varname" in data:
        for vi, name in data["varname"].items():
            info["vars"].append({ "name": name, "value": data["varval"][vi] })
    for si, statement in data["statement"].items():
        info["statements"].append(statement)
    if "choices" in data:
        for ci, choice in data["choices"].items():
            info["choices"].append(choice)
    if "modifiers" in data:
        for mi, mod in data["modifiers"].items():
            if mod.strip() not in ["", "locations", "restriction", "notafter", "inputtype", "groupwith", "latexify?", "reference", "units", "decimalcontext"]:
                info["modifiers"].append(mod)
    
    return data["test"], data["questionname"], info, None

@main.route("/addquestion", methods=["GET", "POST"])
@admin_required
def addquestion():
    if request.method == "GET":
        if dup := request.args.get("dup"):
            return render_template("/virtualtest/editquestion.html", title="Add Question", question=QuestionType.query.get(dup))
        return render_template("/virtualtest/editquestion.html", title="Add Question")
    else:
        test, name, info, fail = processQuestionData()
        if fail: return failJSON(fail)
        if QuestionType.query.filter_by(test=test, name=name).first():
            return failJSON("A question with that id already exists for that test")

        question = QuestionType()
        question.test = test
        question.name = name
        question.info = info
        db.session.add(question)
        db.session.commit()
        return successJSON("Question added", redirect="/virtualtest/allquestions")

@main.route("/editquestion/<int:question_id>", methods=["GET", "POST"])
@admin_required
def editquestion(question_id):
    question = QuestionType.query.get(question_id)
    if not question: 
        return failJSON("Question does not exist")
    if request.method == "GET":
        return render_template("/virtualtest/editquestion.html", question=question, title="Edit Question")
    else:
        test, name, info, fail = processQuestionData()
        if fail: return failJSON(fail)
        if QuestionType.query.filter(QuestionType.id != question.id, QuestionType.test == test, QuestionType.name == name).first():
            return failJSON("A question with that id already exists for that test")

        question.test = test
        question.name = name
        question.info = info
        db.session.commit()
        return successJSON("Question updated", redirect="/virtualtest/allquestions")

@main.route("/allquestions")
@admin_required
def allquestions():
    return render_template("/virtualtest/allquestions.html", questions=QuestionType.query.order_by(QuestionType.id).all(), prettify=json.dumps)

virtualTestMacros = jinja2.Template(open("templates/virtualtest/macros/virtualtestMacros.html").read()).module
nsquestionMacro = virtualTestMacros.nsquestions
@main.route("/previewquestion/<int:question_id>", methods=["GET", "POST"])
@admin_required
def previewquestion(question_id):
    count = int(request.args.get("count", 1))
    seed = int(request.args.get("seed", random.randint(0, 2**64)))
    rng = random.Random(seed)
    if request.method == "GET":
        return nsquestionMacro([generateQuestion(QuestionType.query.get(question_id), rng=rng) for _ in range(count)], includeAnswer=True)
    else:
        test, name, info, fail = processQuestionData()
        if fail: return failJSON(fail)
        return successJSON(html=nsquestionMacro([generateQuestion(test, name, info, rng=rng) for _ in range(count)], includeAnswer=True))
