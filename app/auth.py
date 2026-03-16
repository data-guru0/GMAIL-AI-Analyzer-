import hashlib
import os
import secrets
import base64
from datetime import datetime
from flask import Blueprint, redirect, request, session, url_for, current_app
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from . import db
from .models import User

auth_bp = Blueprint("auth", __name__)

os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")


def _generate_pkce():
    code_verifier = secrets.token_urlsafe(96)
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


def build_flow(app):
    client_config = {
        "web": {
            "client_id": app.config["GOOGLE_CLIENT_ID"],
            "client_secret": app.config["GOOGLE_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [f"{app.config['APP_URL']}/callback"],
        }
    }
    flow = Flow.from_client_config(
        client_config,
        scopes=app.config["GMAIL_SCOPES"],
        redirect_uri=f"{app.config['APP_URL']}/callback",
    )
    return flow


@auth_bp.route("/login")
def login():
    flow = build_flow(current_app._get_current_object())
    code_verifier, code_challenge = _generate_pkce()
    session["code_verifier"] = code_verifier
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        code_challenge=code_challenge,
        code_challenge_method="S256",
    )
    session["oauth_state"] = state
    return redirect(auth_url)


@auth_bp.route("/callback")
def callback():
    flow = build_flow(current_app._get_current_object())
    code_verifier = session.pop("code_verifier", None)
    
    try:
        flow.fetch_token(
            authorization_response=request.url,
            code_verifier=code_verifier,
        )
    except Exception as e:
        # If the user refreshes the callback page, or the server reloads and the session clears
        return redirect(url_for("auth.login"))
    credentials = flow.credentials
    user_info_service = build("oauth2", "v2", credentials=credentials)
    user_info = user_info_service.userinfo().get().execute()

    google_id = user_info["id"]
    email = user_info["email"]
    name = user_info.get("name", "")
    picture = user_info.get("picture", "")

    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User(google_id=google_id, email=email, name=name, picture=picture)
        db.session.add(user)
    else:
        user.name = name
        user.picture = picture
        user.last_login = datetime.utcnow()

    user.access_token = credentials.token
    user.refresh_token = credentials.refresh_token or user.refresh_token
    if credentials.expiry:
        user.token_expiry = credentials.expiry

    db.session.commit()

    session["user_id"] = user.id
    session["user_email"] = user.email
    session["user_name"] = user.name
    session["user_picture"] = user.picture

    return redirect(url_for("main.dashboard"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)
