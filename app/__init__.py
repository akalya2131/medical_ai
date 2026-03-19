import os
from pathlib import Path

from flask import Flask, g, redirect, session, url_for

from app.ml import ensure_model
from app.models import User, db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    instance_path = Path(app.instance_path)
    instance_path.mkdir(parents=True, exist_ok=True)

    default_db_path = instance_path / "patient_risk.db"
    default_model_path = Path(app.root_path).parent / "risk_model.joblib"

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key-change-me"),
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{default_db_path}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=False,
        MODEL_PATH=str(default_model_path),
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from app.auth import auth_bp
    from app.main import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    @app.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")
        g.user = db.session.get(User, user_id) if user_id else None

    @app.route("/")
    def index():
        if g.user:
            return redirect(url_for("main.dashboard"))
        return redirect(url_for("auth.login"))

    with app.app_context():
        db.create_all()
        ensure_model(app.config["MODEL_PATH"])

    return app
