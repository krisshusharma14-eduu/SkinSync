from datetime import date, timedelta
from .models import Product, IngredientRule, ConflictRule, RoutineLog


def parse_csv_field(value):
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def classify_skin_type(answers):
    oily_points = 0
    dry_points = 0
    sensitive_points = 0

    if answers.get("oil_level") == "high":
        oily_points += 2
    elif answers.get("oil_level") == "medium":
        oily_points += 1

    if answers.get("feel_after_wash") == "tight":
        dry_points += 2

    if answers.get("irritation") == "often":
        sensitive_points += 2
    elif answers.get("irritation") == "sometimes":
        sensitive_points += 1

    if sensitive_points >= 2:
        return "sensitive"
    if oily_points >= 2 and dry_points >= 2:
        return "combination"
    if oily_points > dry_points:
        return "oily"
    if dry_points > oily_points:
        return "dry"
    return "combination"


def get_recommendations(skin_type, concerns, budget):
    concerns_set = {c.lower() for c in concerns}
    picks = {"cleanser": None, "moisturizer": None, "sunscreen": None, "serum": None}

    for product in Product.query.all():
        p_skin_types = set(parse_csv_field(product.skin_types))
        p_concerns = set(parse_csv_field(product.concerns))
        if skin_type.lower() not in p_skin_types and "all" not in p_skin_types:
            continue
        if budget and budget.lower() != product.budget.lower() and product.budget.lower() != "all":
            continue

        overlap = len(concerns_set.intersection(p_concerns))
        cat = product.category.lower()
        if picks[cat] is None or overlap > picks[cat][1]:
            picks[cat] = (product, overlap)

    for cat in list(picks):
        if picks[cat] is not None:
            picks[cat] = picks[cat][0]
    return picks


def analyze_ingredients(ingredients, skin_type):
    safe, harmful, cautions = [], [], []
    rules = {r.ingredient.lower(): r for r in IngredientRule.query.all()}

    for ingredient in ingredients:
        key = ingredient.strip().lower()
        if not key:
            continue
        rule = rules.get(key)
        if not rule:
            safe.append({"ingredient": ingredient, "note": "No major concern found in sample database."})
            continue

        item = {"ingredient": ingredient, "note": rule.note}
        avoid_for = [x.strip().lower() for x in (rule.avoid_for or "").split(",") if x.strip()]
        if skin_type.lower() in avoid_for:
            item["note"] += f" Avoid for {skin_type} skin."

        if rule.safety == "harmful":
            harmful.append(item)
        elif rule.safety == "caution":
            cautions.append(item)
        else:
            safe.append(item)

    return {"safe": safe, "harmful": harmful, "cautions": cautions}


def detect_conflicts(products):
    all_ingredients = []
    for product in products:
        all_ingredients.extend(parse_csv_field(product.ingredients))

    unique_ingredients = set(all_ingredients)
    conflicts = []
    for rule in ConflictRule.query.all():
        a = rule.ingredient_a.lower()
        b = rule.ingredient_b.lower()
        if a in unique_ingredients and b in unique_ingredients:
            conflicts.append({"pair": f"{rule.ingredient_a} + {rule.ingredient_b}", "warning": rule.warning})
    return conflicts


def build_routine(recommendations):
    morning, night = [], []
    cleanser = recommendations.get("cleanser")
    serum = recommendations.get("serum")
    moisturizer = recommendations.get("moisturizer")
    sunscreen = recommendations.get("sunscreen")

    if cleanser:
        morning.append(f"Cleanser: {cleanser.name}")
        night.append(f"Cleanser: {cleanser.name}")
    if serum:
        morning.append(f"Serum: {serum.name}")
        night.append(f"Serum: {serum.name}")
    if moisturizer:
        morning.append(f"Moisturizer: {moisturizer.name}")
        night.append(f"Moisturizer: {moisturizer.name}")
    if sunscreen:
        morning.append(f"Sunscreen: {sunscreen.name}")

    return {"morning": morning, "night": night}


def weekly_consistency(user_id):
    today = date.today()
    start = today - timedelta(days=6)
    logs = RoutineLog.query.filter(RoutineLog.user_id == user_id, RoutineLog.log_date >= start).all()
    log_map = {log.log_date.isoformat(): log for log in logs}

    output, streak = [], 0
    for i in range(7):
        day = start + timedelta(days=i)
        log = log_map.get(day.isoformat())
        done = bool(log and log.morning_done and log.night_done)
        output.append({"date": day.isoformat(), "done": done})

    for item in reversed(output):
        if item["done"]:
            streak += 1
        else:
            break
    return {"days": output, "streak": streak}
