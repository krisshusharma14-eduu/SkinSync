from flask import Flask
from .models import db
from .routes import main


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "skinsync-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///skinsync.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        from .seed_data import seed_database

        db.create_all()
        seed_database()

    app.register_blueprint(main)
    return app
