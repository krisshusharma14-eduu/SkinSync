from .models import db, Product, IngredientRule, ConflictRule, UserProfile


def seed_database():
    if Product.query.first():
        return

    db.session.add(UserProfile(username="demo", password="demo123", skin_type="combination", concerns="acne,pigmentation", budget="mid"))

    products = [
        Product(name="Gentle Glow Cleanser", category="cleanser", skin_types="all,sensitive", concerns="acne,dryness", budget="low", ingredients="glycerin,niacinamide,panthenol", description="Mild gel cleanser for daily use."),
        Product(name="Oil Control Foam", category="cleanser", skin_types="oily,combination", concerns="acne,pores", budget="mid", ingredients="salicylic acid,green tea extract,glycerin", description="Foaming cleanser for excess oil."),
        Product(name="Barrier Calm Moisturizer", category="moisturizer", skin_types="dry,sensitive,combination", concerns="dryness,redness", budget="mid", ingredients="ceramides,hyaluronic acid,squalane", description="Repairs and supports skin barrier."),
        Product(name="Hydra Light Moisturizer", category="moisturizer", skin_types="oily,combination", concerns="acne,dryness", budget="low", ingredients="glycerin,niacinamide,aloe vera", description="Oil-free lightweight hydration."),
        Product(name="Daily Shield SPF 50", category="sunscreen", skin_types="all", concerns="pigmentation,sun damage", budget="mid", ingredients="zinc oxide,niacinamide,vitamin e", description="Broad spectrum mineral sunscreen."),
        Product(name="Matte UV Fluid SPF 40", category="sunscreen", skin_types="oily,combination", concerns="pigmentation,acne", budget="low", ingredients="octinoxate,silica,green tea extract", description="Matte finish daily sunscreen."),
        Product(name="Bright Balance Serum", category="serum", skin_types="all", concerns="pigmentation,dullness", budget="mid", ingredients="vitamin c,niacinamide,ferulic acid", description="Brightening antioxidant serum."),
        Product(name="Clear Night Serum", category="serum", skin_types="oily,combination", concerns="acne,texture", budget="high", ingredients="retinol,niacinamide,squalane", description="Night serum for acne marks and texture."),
    ]

    ingredient_rules = [
        IngredientRule(ingredient="niacinamide", safety="safe", note="Supports skin barrier and helps uneven tone.", avoid_for=""),
        IngredientRule(ingredient="glycerin", safety="safe", note="Hydrating humectant suitable for most skin types.", avoid_for=""),
        IngredientRule(ingredient="retinol", safety="caution", note="Effective anti-aging/acne active that can irritate.", avoid_for="sensitive"),
        IngredientRule(ingredient="vitamin c", safety="caution", note="Can sting sensitive skin in high concentrations.", avoid_for="sensitive"),
        IngredientRule(ingredient="fragrance", safety="harmful", note="Common irritant linked to sensitivity flare-ups.", avoid_for="sensitive,acne"),
        IngredientRule(ingredient="alcohol denat", safety="harmful", note="May over-dry and disrupt skin barrier.", avoid_for="dry,sensitive"),
        IngredientRule(ingredient="salicylic acid", safety="caution", note="Useful for acne but may dry skin with overuse.", avoid_for="dry"),
    ]

    conflict_rules = [
        ConflictRule(ingredient_a="Retinol", ingredient_b="Vitamin C", warning="Use in separate routines to reduce irritation risk."),
        ConflictRule(ingredient_a="Retinol", ingredient_b="Salicylic Acid", warning="Combining may over-exfoliate and damage barrier."),
        ConflictRule(ingredient_a="Vitamin C", ingredient_b="AHA", warning="Potential irritation when layered together for sensitive users."),
    ]

    db.session.add_all(products + ingredient_rules + conflict_rules)
    db.session.commit()
