from datetime import datetime
from . import db

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(256), unique=True, nullable=False)
    email = db.Column(db.String(256), unique=True, nullable=False)
    name = db.Column(db.String(256), nullable=True)
    picture = db.Column(db.String(512), nullable=True)
    access_token = db.Column(db.Text, nullable=True)
    refresh_token = db.Column(db.Text, nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    requirements = db.relationship("UserRequirement", backref="user", lazy=True, cascade="all, delete-orphan")
    email_logs = db.relationship("EmailLog", backref="user", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "picture": self.picture,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class UserRequirement(db.Model):
    __tablename__ = "user_requirements"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename = db.Column(db.String(256), nullable=True)
    raw_text = db.Column(db.Text, nullable=True)
    parsed_requirements = db.Column(db.Text, nullable=True)
    labels = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "filename": self.filename,
            "parsed_requirements": json.loads(self.parsed_requirements) if self.parsed_requirements else None,
            "labels": json.loads(self.labels) if self.labels else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

class EmailLog(db.Model):
    __tablename__ = "email_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    gmail_msg_id = db.Column(db.String(256), nullable=False)
    subject = db.Column(db.String(512), nullable=True)
    sender = db.Column(db.String(256), nullable=True)
    action = db.Column(db.String(50), nullable=False, default="kept")
    label_applied = db.Column(db.String(256), nullable=True)
    ai_reasoning = db.Column(db.Text, nullable=True)
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "gmail_msg_id": self.gmail_msg_id,
            "subject": self.subject,
            "sender": self.sender,
            "action": self.action,
            "label_applied": self.label_applied,
            "ai_reasoning": self.ai_reasoning,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
        }
