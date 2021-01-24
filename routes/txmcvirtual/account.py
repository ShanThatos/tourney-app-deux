import stripe
from flask import Blueprint, request, render_template
from extensions import *
from models import *

main = Blueprint("txmcvirtual.account", __name__, url_prefix="/txmcvirtual")

@main.route("/register", methods=["GET", "POST"])
@login_required
def txmcVirtualRegister(formData=None):
    if request.method == "GET":
        tourneys = Tourney.query.filter(
                Tourney.info["type"].astext == "txmcvirtual", 
                Tourney.close_date > current_time()
            ).order_by(Tourney.date.asc()).all()
        students = Coach.query.get(session["id"]).students.order_by(
            Student.grade.asc(), Student.first_name.asc(), 
            Student.last_name.asc()).all()
        return render_template("/txmcvirtual/register.html", tourneys=tourneys, students=students)
    elif request.method == "POST":
        data = parseRequestForm()
        tids = [x for x, y in data["tourney"].items() if y]
        stids = [x for x, y in data["student"].items() if any(y.values())]
        if not tids or not stids: return failJSON("Missing Arguments")
        tourneyCheck = Tourney.query.filter(
                Tourney.id.in_(tids), 
                Tourney.info["type"].astext == "txmcvirtual", 
                Tourney.close_date > current_time()
            ).count()
        if len(tids) != tourneyCheck:
            return failJSON("The tournament(s) you chose is no longer available. Please refresh your page.")
        studentCheck = Student.query.filter(
                Student.id.in_(stids), 
                Student.coach_id == session["id"]
            ).count()
        if len(stids) != studentCheck:
            return failJSON("You do not have permission to register one of the students.")
        tourneyCheck = TourneyCoach.query.filter(
                TourneyCoach.tourney_id.in_(tids), 
                TourneyCoach.coach_id == session["id"], 
                TourneyCoach.paid
            ).first()
        if tourneyCheck:
            return failJSON("You have already registered for one of those tournaments.")
            
        regData = [[stid, test, taking] for stid, tests in data["student"].items() for test, taking in tests.items() if taking]
        numTestsPerTourney = len(regData)
        regData = [[tid] + x for tid in tids for x in regData]
        line_items = {}
        for tourney in Tourney.query.filter(Tourney.id.in_(tids)).all():
            price_id = tourney.info["priceid"]
            line_items[price_id] = line_items.get(price_id, 0) + numTestsPerTourney
        line_items = [{ "price": price_id, "quantity": quantity } for price_id, quantity in line_items.items()]

        coach = Coach.query.get(session["id"])
        if not coach.stripe_id:
            coach.stripe_id = stripe.Customer.create(email=coach.email)["id"]
            db.session.commit()
        stripeSession = stripe.checkout.Session.create(
            success_url = os.environ.get("PROXY") + "/vtschedule?ty=1", 
            cancel_url = os.environ.get("PROXY") + "/txmcvirtual/register", 
            line_items=line_items,
            payment_method_types=["card"], 
            mode="payment", 
            customer=coach.stripe_id
        )
        order = Order(session_id=stripeSession["id"], info=regData)
        db.session.add(order)
        db.session.commit()
        return successJSON(
            stripe_message = "After closing this message, you will be redirected to the payment page. Your credit card information will not be stored on our servers. After your payment has been processed, you will not be allowed to change your registration.",
            stripe_session_id = stripeSession["id"], 
            api_key = STRIPE_PUBLIC_KEY
            )
