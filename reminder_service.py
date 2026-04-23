from datetime import datetime, timedelta
from .models import db, Reminder


def get_user_reminders(user_id):
    return Reminder.query.filter_by(user_id=user_id).all()


def get_user_reminder_map(user_id):
    reminders = get_user_reminders(user_id)
    return {item.routine_type.lower(): item for item in reminders}


def upsert_reminder(user_id, routine_type, reminder_time, enabled):
    routine_type = (routine_type or "").strip().lower()
    reminder_time = (reminder_time or "").strip()
    existing = Reminder.query.filter_by(user_id=user_id, routine_type=routine_type).first()
    if existing:
        existing.reminder_time = reminder_time
        existing.enabled = bool(enabled)
        db.session.commit()
        return existing

    reminder = Reminder(
        user_id=user_id,
        routine_type=routine_type,
        reminder_time=reminder_time,
        enabled=bool(enabled),
    )
    db.session.add(reminder)
    db.session.commit()
    return reminder


def toggle_reminder(user_id, routine_type, enabled):
    reminder = Reminder.query.filter_by(user_id=user_id, routine_type=routine_type).first()
    if not reminder:
        return None
    reminder.enabled = bool(enabled)
    db.session.commit()
    return reminder


def serialize_reminder(reminder):
    return {
        "id": reminder.id,
        "type": reminder.routine_type,
        "time": reminder.reminder_time,
        "enabled": reminder.enabled,
    }


def get_next_reminder_text(reminders):
    enabled = [r for r in reminders if r.enabled and r.reminder_time]
    if not enabled:
        return "Not set"

    now = datetime.now()
    upcoming = []
    for reminder in enabled:
        hour, minute = [int(x) for x in reminder.reminder_time.split(":")]
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target < now:
            target = target + timedelta(days=1)
        upcoming.append((target, reminder))

    upcoming.sort(key=lambda item: item[0])
    next_time, reminder = upcoming[0]
    return f"{next_time.strftime('%I:%M %p')} ({reminder.routine_type.title()})"
