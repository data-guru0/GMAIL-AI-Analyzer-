import json
import os
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, session, current_app
from werkzeug.utils import secure_filename
from . import db
from .models import User, UserRequirement, EmailLog
from .auth import get_current_user

api_bp = Blueprint("api", __name__)
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt", "md"}

def api_login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@api_bp.route("/stats")
@api_login_required
def get_stats():
    user_id = session["user_id"]
    total = EmailLog.query.filter_by(user_id=user_id).count()
    kept = EmailLog.query.filter_by(user_id=user_id, action="keep").count()
    deleted = EmailLog.query.filter_by(user_id=user_id, action="delete").count()
    labeled = EmailLog.query.filter(
        EmailLog.user_id == user_id,
        EmailLog.action.like("label:%")
    ).count()

    label_logs = EmailLog.query.filter(
        EmailLog.user_id == user_id,
        EmailLog.label_applied.isnot(None)
    ).all()

    label_counts = {}
    for log in label_logs:
        label_counts[log.label_applied] = label_counts.get(log.label_applied, 0) + 1

    return jsonify({
        "total": total,
        "kept": kept,
        "deleted": deleted,
        "labeled": labeled,
        "label_counts": label_counts,
    })

@api_bp.route("/activity")
@api_login_required
def get_activity():
    user_id = session["user_id"]
    limit = request.args.get("limit", 50, type=int)
    logs = EmailLog.query.filter_by(user_id=user_id).order_by(EmailLog.analyzed_at.desc()).limit(limit).all()
    return jsonify({"logs": [log.to_dict() for log in logs]})

@api_bp.route("/requirements", methods=["GET"])
@api_login_required
def get_requirements():
    user_id = session["user_id"]
    req = UserRequirement.query.filter_by(user_id=user_id).order_by(UserRequirement.created_at.desc()).first()
    if not req:
        return jsonify({"requirements": None})
    return jsonify({"requirements": req.to_dict()})

@api_bp.route("/requirements/upload", methods=["POST"])
@api_login_required
def upload_requirements():
    from .document_parser import extract_text_from_file, parse_requirements_with_ai, extract_label_names
    user_id = session["user_id"]
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "File type not supported. Use PDF, DOCX, or TXT."}), 400

    filename = secure_filename(file.filename)
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    filepath = os.path.join(upload_folder, f"user_{user_id}_{filename}")
    file.save(filepath)

    try:
        raw_text = extract_text_from_file(filepath)
        parsed = parse_requirements_with_ai(raw_text)
        labels = extract_label_names(parsed)

        existing = UserRequirement.query.filter_by(user_id=user_id).first()
        if existing:
            existing.filename = filename
            existing.raw_text = raw_text
            existing.parsed_requirements = json.dumps(parsed)
            existing.labels = json.dumps(labels)
            existing.updated_at = datetime.utcnow()
        else:
            req = UserRequirement(
                user_id=user_id,
                filename=filename,
                raw_text=raw_text,
                parsed_requirements=json.dumps(parsed),
                labels=json.dumps(labels),
            )
            db.session.add(req)
        db.session.commit()
        os.remove(filepath)

        return jsonify({
            "success": True,
            "requirements": {
                "filename": filename,
                "parsed": parsed,
                "labels": labels,
            }
        })
    except Exception as e:
        logger.error(str(e))
        if os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({"error": str(e)}), 500

@api_bp.route("/user")
@api_login_required
def get_user():
    user = get_current_user()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()})
