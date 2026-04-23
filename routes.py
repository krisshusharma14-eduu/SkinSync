from datetime import date, datetime
from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for
from .models import db, Product, UserProfile, RoutineLog
from .logic import classify_skin_type, get_recommendations, analyze_ingredients, detect_conflicts, build_routine, weekly_consistency
from .reminder_service import (
    get_next_reminder_text,
    get_user_reminders,
    get_user_reminder_map,
    serialize_reminder,
    toggle_reminder,
    upsert_reminder,
)

main = Blueprint("main", __name__)


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return UserProfile.query.get(user_id)


@main.app_context_processor
def inject_shell_context():
    user = get_current_user()
    return {
        "shell_user": user,
        "active_endpoint": request.endpoint or "",
    }


@main.route("/")
def home():
    user = get_current_user()
    if user:
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")


@main.route("/signup", methods=["POST"])
def signup():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    if not username or not password:
        return redirect(url_for("main.home"))

    if UserProfile.query.filter_by(username=username).first():
        return redirect(url_for("main.home"))

    user = UserProfile(username=username, password=password)
    db.session.add(user)
    db.session.commit()
    session["user_id"] = user.id
    return redirect(url_for("main.quiz"))


@main.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    user = UserProfile.query.filter_by(username=username, password=password).first()
    if not user:
        return redirect(url_for("main.home"))

    session["user_id"] = user.id
    return redirect(url_for("main.dashboard"))


@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.home"))


@main.route("/quiz", methods=["GET", "POST"])
def quiz():
    user = get_current_user()
    if not user:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        concerns = request.form.getlist("concerns")
        budget = request.form.get("budget", "mid")
        answers = {
            "oil_level": request.form.get("oil_level"),
            "feel_after_wash": request.form.get("feel_after_wash"),
            "irritation": request.form.get("irritation"),
        }
        user.skin_type = classify_skin_type(answers)
        user.concerns = ",".join(concerns)
        user.budget = budget
        db.session.commit()
        return redirect(url_for("main.dashboard"))

    return render_template("quiz.html")


@main.route("/dashboard")
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for("main.home"))

    concerns = [c.strip() for c in (user.concerns or "").split(",") if c.strip()]
    recommendations = get_recommendations(user.skin_type or "combination", concerns, user.budget or "mid")
    routine = build_routine(recommendations)
    weekly = weekly_consistency(user.id)
    reminders = get_user_reminders(user.id)
    today_log = RoutineLog.query.filter_by(user_id=user.id, log_date=date.today()).first()
    routine_done = int(bool(today_log and today_log.morning_done)) + int(bool(today_log and today_log.night_done))
    routine_total = 2
    next_reminder = get_next_reminder_text(reminders)

    concern_bonus = min(len(concerns) * 5, 15)
    glow_score = min(100, 60 + weekly["streak"] * 8 + concern_bonus + (routine_done * 6))

    product_matcher_items = [
        {"brand": "Minimalist", "name": "2% Salicylic Acid Cleanser", "category": "Cleanser", "price": "INR 299", "url": "https://beminimalist.co/products/2-salicylic-acid-cleanser"},
        {"brand": "Dot & Key", "name": "Cica Calming Blemish Clearing Face Wash", "category": "Cleanser", "price": "INR 349", "url": "https://www.dotandkey.com/products/cica-calming-blemish-clearing-face-wash"},
        {"brand": "Plum", "name": "Green Tea Pore Cleansing Face Wash", "category": "Cleanser", "price": "INR 345", "url": "https://plumgoodness.com/products/green-tea-pore-cleansing-face-wash"},
        {"brand": "Minimalist", "name": "10% Niacinamide Face Serum", "category": "Serum", "price": "INR 599", "url": "https://beminimalist.co/products/niacinamide-10"},
        {"brand": "Dot & Key", "name": "10% Niacinamide + Cica Skin Clarifying Serum", "category": "Serum", "price": "INR 599", "url": "https://www.dotandkey.com/products/10-niacinamide-cica-skin-clarifying-serum"},
        {"brand": "Plum", "name": "2% Niacinamide & Rice Water Serum", "category": "Serum", "price": "INR 499", "url": "https://plumgoodness.com/products/2-niacinamide-rice-water-serum"},
        {"brand": "Minimalist", "name": "Vitamin B5 10% Moisturizer", "category": "Moisturizer", "price": "INR 299", "url": "https://beminimalist.co/products/vitamin-b5-10-moisturizer"},
        {"brand": "Dot & Key", "name": "Barrier Repair Hydrating Gel", "category": "Moisturizer", "price": "INR 495", "url": "https://www.dotandkey.com/products/barrier-repair-hydrating-gel"},
        {"brand": "Plum", "name": "Green Tea Oil-Free Moisturizer", "category": "Moisturizer", "price": "INR 470", "url": "https://plumgoodness.com/products/green-tea-oil-free-moisturizer"},
        {"brand": "Minimalist", "name": "SPF 50 PA++++ Multi-Vitamin Sunscreen", "category": "Sunscreen", "price": "INR 399", "url": "https://beminimalist.co/products/spf-50-sunscreen"},
        {"brand": "Dot & Key", "name": "Watermelon Cooling Sunscreen SPF 50+", "category": "Sunscreen", "price": "INR 495", "url": "https://www.dotandkey.com/products/watermelon-cooling-sunscreen-spf-50"},
        {"brand": "Plum", "name": "Rice Water & Niacinamide Sunscreen SPF 50", "category": "Sunscreen", "price": "INR 499", "url": "https://plumgoodness.com/products/rice-water-niacinamide-sunscreen-spf-50"},
    ]
    reminder_map = get_user_reminder_map(user.id)
    tracker_completion = len([day for day in weekly["days"] if day["done"]])
    weekly_days = []
    for day in weekly["days"]:
        parsed = datetime.strptime(day["date"], "%Y-%m-%d")
        weekly_days.append(
            {
                "date": day["date"],
                "done": day["done"],
                "weekday": parsed.strftime("%a"),
            }
        )
    morning_reminder = reminder_map.get("morning")
    night_reminder = reminder_map.get("night")
    missed_routine = False
    if today_log:
        done_today = bool(today_log.morning_done and today_log.night_done)
        has_active = bool((morning_reminder and morning_reminder.enabled) or (night_reminder and night_reminder.enabled))
        if has_active and not done_today and datetime.now().hour >= 21:
            missed_routine = True

    history_logs = (
        RoutineLog.query.filter_by(user_id=user.id)
        .order_by(RoutineLog.log_date.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "dashboard.html",
        user=user,
        recommendations=recommendations,
        routine=routine,
        weekly=weekly,
        reminders=reminders,
        morning_reminder=morning_reminder,
        night_reminder=night_reminder,
        today_log=today_log,
        routine_done=routine_done,
        routine_total=routine_total,
        next_reminder=next_reminder,
        glow_score=glow_score,
        product_matcher_items=product_matcher_items,
        reminder_map=reminder_map,
        weekly_days=weekly_days,
        tracker_completion=tracker_completion,
        missed_routine=missed_routine,
        history_logs=history_logs,
    )


@main.route("/ingredient-checker", methods=["GET", "POST"])
def ingredient_checker():
    user = get_current_user()
    if not user:
        return redirect(url_for("main.home"))

    report = None
    product_name = ""
    if request.method == "POST":
        product_name = request.form.get("product_name", "").strip()
        manual_ingredients = request.form.get("ingredients", "").strip()

        ingredients = []
        if product_name:
            product = Product.query.filter(Product.name.ilike(product_name)).first()
            if product:
                ingredients = [i.strip() for i in product.ingredients.split(",")]

        if manual_ingredients:
            ingredients.extend([i.strip() for i in manual_ingredients.split(",") if i.strip()])

        report = analyze_ingredients(ingredients, user.skin_type or "combination")

    return render_template("ingredient_checker.html", report=report, product_name=product_name)


@main.route("/conflict-checker", methods=["GET", "POST"])
def conflict_checker():
    user = get_current_user()
    if not user:
        return redirect(url_for("main.home"))

    conflicts = []
    selected_products = []
    products = Product.query.all()

    if request.method == "POST":
        selected_ids = [int(pid) for pid in request.form.getlist("product_ids")]
        selected_products = Product.query.filter(Product.id.in_(selected_ids)).all() if selected_ids else []
        conflicts = detect_conflicts(selected_products)

    return render_template("conflict_checker.html", products=products, conflicts=conflicts, selected_products=selected_products)


@main.route("/track", methods=["POST"])
def track():
    user = get_current_user()
    if not user:
        return redirect(url_for("main.home"))

    morning_done = bool(request.form.get("morning_done"))
    night_done = bool(request.form.get("night_done"))

    log = RoutineLog.query.filter_by(user_id=user.id, log_date=date.today()).first()
    if not log:
        log = RoutineLog(user_id=user.id, log_date=date.today())
        db.session.add(log)

    log.morning_done = morning_done
    log.night_done = night_done
    db.session.commit()
    return redirect(url_for("main.dashboard"))


@main.route("/reminders", methods=["POST"])
def reminders():
    user = get_current_user()
    if not user:
        return redirect(url_for("main.home"))

    routine_type = request.form.get("routine_type", "")
    reminder_time = request.form.get("reminder_time", "")
    enabled = request.form.get("enabled") == "on"
    upsert_reminder(user.id, routine_type, reminder_time, enabled)
    return redirect(url_for("main.dashboard", reminder_saved=1))


@main.route("/api/reminders")
def reminders_api():
    user = get_current_user()
    if not user:
        return jsonify([])

    reminders = get_user_reminders(user.id)
    return jsonify([serialize_reminder(item) for item in reminders])


@main.route("/api/reminders/save", methods=["POST"])
def save_reminder_api():
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "message": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    routine_type = payload.get("type", "")
    reminder_time = payload.get("time", "")
    enabled = bool(payload.get("enabled", True))
    reminder = upsert_reminder(user.id, routine_type, reminder_time, enabled)
    return jsonify({"ok": True, "message": "Reminder saved successfully", "reminder": serialize_reminder(reminder)})


@main.route("/api/reminders/toggle", methods=["POST"])
def toggle_reminder_api():
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "message": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    routine_type = (payload.get("type") or "").strip().lower()
    enabled = bool(payload.get("enabled"))
    reminder = toggle_reminder(user.id, routine_type, enabled)
    if not reminder:
        return jsonify({"ok": False, "message": "Reminder not found"}), 404
    return jsonify({"ok": True, "message": "Reminder status updated", "reminder": serialize_reminder(reminder)})


@main.route("/profile")
def profile():
    user = get_current_user()
    if not user:
        return redirect(url_for("main.home"))
    return render_template("profile.html", user=user)
