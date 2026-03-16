from flask import Blueprint, render_template, session, redirect, url_for
from .auth import get_current_user

main_bp = Blueprint("main", __name__)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated

@main_bp.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    return render_template("dashboard.html", user=user)

@main_bp.route("/requirements")
@login_required
def requirements():
    user = get_current_user()
    return render_template("requirements.html", user=user)
