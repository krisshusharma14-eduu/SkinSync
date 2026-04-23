from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    category = db.Column(db.String(40), nullable=False)
    skin_types = db.Column(db.String(120), nullable=False)
    concerns = db.Column(db.String(200), nullable=False)
    budget = db.Column(db.String(20), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)


class IngredientRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ingredient = db.Column(db.String(120), unique=True, nullable=False)
    safety = db.Column(db.String(20), nullable=False)
    note = db.Column(db.Text, nullable=False)
    avoid_for = db.Column(db.String(120), nullable=True)


class ConflictRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ingredient_a = db.Column(db.String(120), nullable=False)
    ingredient_b = db.Column(db.String(120), nullable=False)
    warning = db.Column(db.Text, nullable=False)


class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(120), nullable=False)
    skin_type = db.Column(db.String(40), nullable=True)
    concerns = db.Column(db.String(200), nullable=True)
    budget = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class RoutineLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user_profile.id"), nullable=False)
    log_date = db.Column(db.Date, default=date.today, nullable=False)
    morning_done = db.Column(db.Boolean, default=False)
    night_done = db.Column(db.Boolean, default=False)


class Reminder(db.Model):
    __tablename__ = "reminders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user_profile.id"), nullable=False)
    routine_type = db.Column(db.String(20), nullable=False)
    reminder_time = db.Column(db.String(10), nullable=False)
    enabled = db.Column(db.Boolean, default=True)
