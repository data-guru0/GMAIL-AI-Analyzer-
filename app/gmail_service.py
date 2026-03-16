import base64
import email as email_lib
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from flask import current_app
from . import db
from .models import User

def get_credentials(user: User) -> Credentials:
    creds = Credentials(
        token=user.access_token,
        refresh_token=user.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=current_app.config["GOOGLE_CLIENT_ID"],
        client_secret=current_app.config["GOOGLE_CLIENT_SECRET"],
        scopes=current_app.config["GMAIL_SCOPES"],
    )

    if user.token_expiry and datetime.utcnow() >= user.token_expiry - timedelta(minutes=5):
        creds.refresh(Request())
        user.access_token = creds.token
        if creds.expiry:
            user.token_expiry = creds.expiry
        db.session.commit()

    return creds

def get_gmail_service(user: User):
    creds = get_credentials(user)
    return build("gmail", "v1", credentials=creds)

def fetch_new_emails(service, since_datetime: datetime = None, max_results: int = 20):
    query = "in:inbox"
    if since_datetime:
        epoch = int(since_datetime.timestamp())
        query += f" after:{epoch}"

    result = service.users().messages().list(
        userId="me",
        q=query,
        maxResults=max_results,
    ).execute()

    messages = result.get("messages", [])
    return messages

def get_email_details(service, msg_id: str) -> dict:
    msg = service.users().messages().get(
        userId="me",
        id=msg_id,
        format="full",
    ).execute()

    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}

    subject = headers.get("Subject", "(No Subject)")
    sender = headers.get("From", "unknown")
    date = headers.get("Date", "")
    snippet = msg.get("snippet", "")

    body = _extract_body(msg.get("payload", {}))

    return {
        "id": msg_id,
        "subject": subject,
        "sender": sender,
        "date": date,
        "snippet": snippet,
        "body": body[:3000],
        "labels": msg.get("labelIds", []),
    }

def _extract_body(payload: dict) -> str:
    body_text = ""
    mime_type = payload.get("mimeType", "")

    if mime_type == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            body_text = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")

    elif mime_type == "text/html" and not body_text:
        data = payload.get("body", {}).get("data", "")
        if data:
            html = base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
            import re
            body_text = re.sub(r"<[^>]+>", " ", html)

    elif "parts" in payload:
        for part in payload["parts"]:
            part_text = _extract_body(part)
            if part_text:
                body_text += part_text + "\n"

    return body_text.strip()

def trash_email(service, msg_id: str):
    return service.users().messages().trash(userId="me", id=msg_id).execute()

def get_or_create_label(service, name: str) -> str:
    result = service.users().labels().list(userId="me").execute()
    labels = result.get("labels", [])

    for label in labels:
        if label["name"].lower() == name.lower():
            return label["id"]

    label_body = {
        "name": name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show",
    }
    created = service.users().labels().create(userId="me", body=label_body).execute()
    return created["id"]

def apply_label(service, msg_id: str, label_id: str):
    return service.users().messages().modify(
        userId="me",
        id=msg_id,
        body={"addLabelIds": [label_id]},
    ).execute()
