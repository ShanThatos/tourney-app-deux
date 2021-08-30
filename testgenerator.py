import random
import re
import math
import extensions as ext
from models import *
from decimal import Decimal as D, getcontext
from fractions import Fraction as frac

db = ext.db
ALL_TESTS = ["NS", "GM", "GS"]
QUESTIONS_PER_TEST = {"NS": 80, "GM": 50, "GS": 50}
CHOICES_PER_TEST = {"NS": 0, "GM": 5, "GS": 5}
REPEAT_THRESHOLD = {"NS": 10, "GM": 50, "GS": 50}
questionLocations = {}
for level in ["E", "M"]:
    for test in ALL_TESTS:
        questionLocations[level + test] = [[] for _ in range(QUESTIONS_PER_TEST[test] + 1)]
    
if __name__ == "__main__":
    qData = QuestionType.query.order_by(QuestionType.id).all()
    allQuestions = {}
    for question in qData:
        allQuestions[question.test + ":" + question.name] = question
        for modifier in question.info["modifiers"]:
            name, value = re.split(" +", modifier + " ", 1)
            if name == "locations":
                level, value = value.split(" ", 1)
                key = level.upper() + question.test.upper()
                for loc in value.split(" "):
                    if "-" in loc:
                        start, end = list(map(int, loc.split("-")))
                        for i in range(start, end + 1):
                            questionLocations[key][i].append(question.name)
                    elif loc.isdigit():
                        questionLocations[key][int(loc)].append(question.name)

def generateTest(level, test, seed=random.randint(0, 2**31)):
    questions = []
    info = { "level": level, "test": test, "seed": seed, "questions": questions }
    rng = random.Random(seed)

    notafter = set()
    groups = set()
    lastFew = [None for _ in range(REPEAT_THRESHOLD[test])]

    for i in range(1, QUESTIONS_PER_TEST[test] + 1):
        qOptions = questionLocations[level + test][i].copy()
        rng.shuffle(qOptions)
        valid = False
        while qOptions and not valid:
            qType = allQuestions[test + ":" + qOptions.pop(0)]
            if qType in lastFew:
                continue
            question = generateQuestion(qType.test, qType.name, qType.info, rng=rng)
            valid = True
            for naTest in question["notafter"]:
                if naTest in notafter:
                    valid = False
            for groupTest in question["groups"]:
                if groupTest in groups:
                    valid = False
        if valid:
            questions.append(question)
            notafter.add(question["name"])
            groups.update(question["groups"])
            lastFew = lastFew[1:] + [question["name"]]
        else:
            print("Unable to generate test")
            return None
    
    return info

def generateQuestion(question, rng=random.Random()):
    return generateQuestion(question.test, question.name, question.info, rng=rng)
def generateQuestion(qtest, qname, qinfo, rng=random.Random()):
    for modifier in qinfo["modifiers"]:
        name, value = re.split(" +", modifier + " ", 1)
        if name == "decimalcontext":
            getcontext().prec = int(value)
    
    globs = globals() | { "rng": rng }
    valid = False
    while not valid:
        valid = True
        result = { "name": qname }
        vars = {}
        for var in qinfo["vars"]:
            vars[var["name"]] = eval(var["value"], globs, vars)
        result["answer"] = processFString(qinfo["answer"], vars, globs).strip()
        result["statement"] = processFString(rng.choice(qinfo["statements"]), vars, globs)
        if CHOICES_PER_TEST[qtest]:
            choices = []
            numChoices = CHOICES_PER_TEST[qtest]
            attempts = 0
            while len(choices) != numChoices:
                attempts += 1
                if attempts == 11:
                    valid = False
                    break
                for choiceExpression in qinfo["choices"]:
                    choice = processFString(choiceExpression, vars, globs)
                    if isinstance(choice, list): choices.extend(choice)
                    else: choices.append(choice)
                choices = rng.shuffle(list(set([str(x).strip() for x in choices])))
                if len(choices) < numChoices - 1:
                    choices = []
                    continue
                answerIndex = rng.randrange(0, numChoices)
                choices.insert(answerIndex, result["answer"])
                choices = choices[0:numChoices]
                for str in ["All of the above", "None of the above"]:
                    if str in choices:
                        choices.remove(str)
                        if str == result["answer"]:
                            answerIndex = len(choices)
                        choices.append(str)
            if valid:
                result["choices"] = choices
                result["answerIndex"] = answerIndex
                result["answerStr"] = chr(ord("A") + answerIndex)
        
        mods = { "notafter": [], "groups": [] }
        result["units"] = ""
        for modifier in qinfo["modifiers"]:
            name, value = re.split(" +", modifier + " ", 1)
            if name == "restriction" and not eval(value, globs, vars):
                valid = False
            if name == "inputtype":
                mods[name] = value.split(";")
            if name == "units":
                result["units"] = processFString(value, vars, globs)
            if name == "latexify":
                result["statement"] = "$" + result["statement"] + "$"
                result["answer"] = "$" + result["answer"] + "$"
                if "choices" in result:
                    result["choices"] = ["$" + x + "$" for x in result["choices"]]
            if name == "notafter":
                mods["notafter"].extend(value.split(";"))
            if name == "groupwith":
                mods["groups"].extend(value.split(";"))
        result["modifiers"] = mods
        result["vars"] = vars
    return result

def processFString(fstring_text, locals, globals=globals()):
    fstring_text = fstring_text.replace("{", "{{").replace("}", "}}")
    depth = 0
    text = []
    for i in range(len(fstring_text)):
        ch = fstring_text[i]
        if ch == "[":
            if depth == 0:
                ch = "{"
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                ch = "}"
        text.append(ch)
    text = "".join(text)
    return eval(f'f{repr(text)}', globals or {}, locals or {})

def formatEstimation(answer, jax=True):
    if jax: return f"${formatEstimation(answer, jax=False)}$"
    return f"{int(answer * .95)} - {int(answer * 1.05)}"

def formatDecimal(num, den, jax=True):
    if jax: return f"${formatDecimal(num, den, jax=False)}$"
    if num % den == 0:
        return str(num // den)
    if den < 0:
        num *= -1
        den *= -1
    neg = False
    if num < 0:
        neg = True
        num *= -1
    ret = "." if num // den == 0 else (str(num // den) + ".")
    num %= den
    dec = ""
    divs = []
    while num:
        num *= 10
        if num in divs:
            index = divs.index(num)
            ret += dec[:index] + "\\overline{" + dec[index:] + "}"
            break
        else:
            dec += str(num // den)
            ret += str(num // den)
            divs.append(num)
            num %= den
    if neg:
        ret = "-" + ret
    return ret
def isRepeatingDecimal(num, den):
    return "\\overline" in formatDecimal(num, den)

"""
    Different types are: 
        fraction, mixednumber, decimal, money, all
"""
def format(n, type, jax=True, places=3):
    if jax: return f"${format(n, type, jax=False)}$"
    if type == "fraction":
        if not isinstance(n, frac) or n.numerator % n.denominator == 0: 
            raise Exception("Not a valid fraction")
        neg = False
        if n < 0:
            n *= -1
            neg = True
        return ("-" if neg else "") + f"\\frac{{{n.numerator}}}{{{n.denominator}}}"
    if type == "mixednumber":
        if not isinstance(n, frac) or n.numerator % n.denominator == 0: 
            raise Exception("Not a valid fraction")
        neg = False
        if n < 0:
            n *= -1
            neg = True
        whole = n.numerator // n.denominator
        if whole == 0:
            raise Exception("Not a valid mixed number")
        n.numerator %= n.denominator
        return ("-" if neg else "") + f"{whole}\\frac{{{n.numerator}}}{{{n.denominator}}}"
    if type == "decimal":
        if isinstance(n, frac):
            if isRepeatingDecimal(n.numerator, n.denominator):
                raise Exception("Found repeating decimal")
            return formatDecimal(n.numerator, n.denominator, jax=jax)
        return formatDecimal(int(n * 10**places), 10**places, jax=jax)
    if type == "money":
        return f"{n:.2f}"
    if type == "all":
        if not isinstance(n, frac): raise Exception("Expecting fraction")
        if n.numerator % n.denominator == 0:
            return str(n.numerator // n.denominator)
        ret = []
        for fmt in ["decimal", "fraction", "mixednumber"]:
            try: ret.append(format(n, fmt, jax=False))
            except: pass
        if not ret: raise Exception("0 formats created")
        if len(ret) == 1: return ret[0]
        if len(ret) == 2: return ret[0] + "\\text{ or }" + ret[1]
        if len(ret) == 3: return ret[0] + ", " + ret[1] + "\\text{ or }" + ret[2]
    raise Exception("Unsupported format")


