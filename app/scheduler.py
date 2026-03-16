import json
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

_scheduler = BackgroundScheduler(daemon=True)

def process_all_users(app):
    with app.app_context():
        from .models import User, UserRequirement, EmailLog
        from .gmail_service import get_gmail_service, fetch_new_emails, get_email_details
        from .ai_agent.agent import analyze_and_act
        from . import db

        users = User.query.all()
        for user in users:
            requirement = UserRequirement.query.filter_by(user_id=user.id).order_by(
                UserRequirement.created_at.desc()
            ).first()

            if not requirement or not requirement.parsed_requirements:
                continue

            requirements = json.loads(requirement.parsed_requirements)

            try:
                service = get_gmail_service(user)
                since = datetime.utcnow() - timedelta(minutes=10)
                messages = fetch_new_emails(service, since_datetime=since, max_results=20)

                for msg_meta in messages:
                    msg_id = msg_meta["id"]
                    existing = EmailLog.query.filter_by(
                        user_id=user.id, gmail_msg_id=msg_id
                    ).first()
                    if existing:
                        continue

                    try:
                        email_details = get_email_details(service, msg_id)
                        result = analyze_and_act(email_details, requirements, service)

                        action_str = result.get("action", "keep")
                        label_applied = None
                        if action_str.startswith("label:"):
                            raw_label = action_str.split(":", 1)[1]
                            label_applied = raw_label.strip(" \"'[](){}<>")

                        log_entry = EmailLog(
                            user_id=user.id,
                            gmail_msg_id=msg_id,
                            subject=email_details.get("subject", ""),
                            sender=email_details.get("sender", ""),
                            action=action_str,
                            label_applied=label_applied,
                            ai_reasoning=result.get("reasoning", ""),
                        )
                        db.session.add(log_entry)
                        db.session.commit()

                    except Exception as e:
                        logger.error(e)

            except Exception as e:
                logger.error(e)

def start_scheduler(app):
    if not _scheduler.running:
        _scheduler.start()

    job_id = "global_email_monitor"
    if _scheduler.get_job(job_id):
        _scheduler.remove_job(job_id)

    _scheduler.add_job(
        func=process_all_users,
        trigger=IntervalTrigger(minutes=1),
        id=job_id,
        args=[app],
        replace_existing=True,
        max_instances=1,
    )
