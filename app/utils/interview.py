from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from typing import Optional
from dateutil import parser
import pytz
from icalendar import Calendar, Event, Alarm
from .scheduler import scheduler
from app import models  # adjust import to your project
from app.database import SessionLocal  # small helper to create DB sessions in scheduled jobs
from app.utils.utils import send_mail  
from datetime import timezone


from app.enums.timezones import TimezoneEnum

ALIAS_MAP = {
    # UTC equivalents
    "GMT": "Etc/UTC",
    "UTC": "Etc/UTC",
    "Z": "Etc/UTC", 
    
    # US time zones
    "PST": "America/Los_Angeles",  # Pacific Standard
    "PDT": "America/Los_Angeles",  # Pacific Daylight
    "MST": "America/Denver",       # Mountain Standard
    "MDT": "America/Denver",       # Mountain Daylight
    "CST": "America/Chicago",      # Central Standard
    "CDT": "America/Chicago",      # Central Daylight
    "EST": "America/New_York",     # Eastern Standard
    "EDT": "America/New_York",     # Eastern Daylight

    # Europe
    "BST": "Europe/London",        # British Summer Time
    "CET": "Europe/Paris",         # Central European Time
    "CEST": "Europe/Paris",        # Central European Summer

    # Africa
    "WAT": "Africa/Lagos",         # West Africa Time
    "CAT": "Africa/Harare",        # Central Africa Time
    "EAT": "Africa/Nairobi",       # East Africa Time

    # Asia
    "IST": "Asia/Kolkata",         # India Standard Time
    "PKT": "Asia/Karachi",         # Pakistan Standard
    "WIB": "Asia/Jakarta",         # Western Indonesia
    "WITA": "Asia/Makassar",       # Central Indonesia
    "WIT": "Asia/Jayapura",        # Eastern Indonesia
    "SGT": "Asia/Singapore",       
    "HKT": "Asia/Hong_Kong",
    "JST": "Asia/Tokyo",
    "KST": "Asia/Seoul",

    # Australia
    "AEST": "Australia/Sydney",
    "AEDT": "Australia/Sydney",
    "ACST": "Australia/Adelaide",
    "ACDT": "Australia/Adelaide",
    "AWST": "Australia/Perth",
    
    "AST_ARABIA": "Asia/Riyadh",
    "CST_CHINA": "Asia/Shanghai",
}
def resolve_to_iana(tz_str: str) -> str:
    
    """
    Map recruiter-provided timezone string (abbreviation or IANA) to a valid IANA timezone.
    """
    tz_str = tz_str.strip().upper()
    if tz_str in ALIAS_MAP:
        return ALIAS_MAP[tz_str]

    try:
        # if it's already a valid IANA name (like "America/New_York")
        ZoneInfo(tz_str)
        return tz_str
    except Exception:
        raise ValueError(f"Unknown or unsupported timezone: {tz_str}")


def parse_local_datetime(dt_str: str, recruiter_iana: str) -> datetime:
    """
    Parse dt_str and return a timezone-aware datetime in recruiter tz.
    Accepts ISO strings or flexible date formats.
    """
    raw = parser.parse(dt_str)
    tz = ZoneInfo(recruiter_iana)

    if raw.tzinfo is None:
        # naive => assume recruiter tz
        local_dt = raw.replace(tzinfo=tz)
    else:
        # aware => convert to recruiter tz
        local_dt = raw.astimezone(tz)
    return local_dt

def make_ics(application, start_dt_local, recruiter_iana, duration_minutes=60):
    """
    Create a simple ICS bytes object. start_dt_local should be tz-aware (recruiter tz).
    We'll put DTSTART/DTEND with timezone-aware datetimes.
    """
    """
    start_dt_local: tz-aware datetime in recruiter tz (ZoneInfo)
    returns: bytes of the .ics file
    """
    cal = Calendar()
    cal.add("prodid", "-//YourApp//Interview//EN")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "REQUEST")

    ev = Event()
    ev.add("uid", f"application-{application.id}@yourapp")
    ev.add("summary", f"Interview: {application.job_title} — {application.company}")
    ev.add("dtstart", start_dt_local)
    ev.add("dtend", start_dt_local + timedelta(minutes=duration_minutes))
#     ev.add("dtstamp", datetime.utcnow())
    ev.add("dtstamp", datetime.now(timezone.utc))


     # 30-min before
    alarm_30 = Alarm()
    alarm_30.add("action", "DISPLAY")
    alarm_30.add("description", "Interview reminder — 30 min before")
    alarm_30.add("trigger", timedelta(minutes=-30))
    ev.add_component(alarm_30)

    cal.add_component(ev)
    return cal.to_ical()

def send_interview_reminder(application_id: int, reminder_type: str):
    """
    reminder_type: "confirmation", "day_before_9am", "day_of_9am", "30min_before"
    This function will be scheduled; it needs to open its own DB session.
    """
    db = SessionLocal()
    try:
        app_obj = db.query(models.Application).filter(models.Application.id == application_id).first()
        if not app_obj:
            return

        user = db.query(models.User).filter(models.User.id == app_obj.user_id).first()
        if not user:
            return

        # parse stored UTC and user tz
        utc_dt = app_obj.interview_date_utc
        if utc_dt is None or utc_dt.tzinfo is None:
            return
        
        user_iana = user.timezone or "UTC"
        local_dt = utc_dt.astimezone(ZoneInfo(user_iana))
        pretty = local_dt.strftime("%A, %B %d, %Y at %I:%M %p %Z")

        subjects = {
            "confirmation": "Interview Scheduled",
            "day_before_9am": "Reminder: Interview tomorrow",
            "day_of_9am": "Reminder: Interview today",
            "30min_before": "Reminder: Interview in 30 minutes",
        }
        subject = subjects.get(reminder_type, "Interview Reminder")

        body_html = f"""
        <p>Hello {getattr(user, 'username', user.email)},</p>
        <p>Your interview for <b>{app_obj.job_title}</b> at <b>{app_obj.company}</b> is scheduled on:</p>
        <p><b>📅 {pretty}</b></p>
        <p>Good luck!</p>
        """

        send_mail(subject=subject, body=body_html, to_email=user.email, html=True)
    finally:
        db.close()

def schedule_reminders_for_application(application, utc_dt, user_iana):
    """
    Schedule the three reminders:
    - 1 day before at 09:00 user local time
    - day of at 09:00 user local time
    - 30 minutes before interview exact time (UTC-30min)
    All jobs scheduled in UTC (scheduler timezone is UTC).
    """
    user_tz = ZoneInfo(user_iana)
    user_local_interview = utc_dt.astimezone(user_tz)  # applies tz

    # 1) 1 day before at 09:00 local
    day_before_date = (user_local_interview.date() - timedelta(days=1))
    run_local_day_before = datetime.combine(day_before_date, time(hour=9, minute=0), tzinfo=user_tz)
    run_utc_day_before = run_local_day_before.astimezone(ZoneInfo("UTC"))

    # 2) day-of at 09:00 local
    run_local_day_of = datetime.combine(user_local_interview.date(), time(hour=9, minute=0), tzinfo=user_tz)
    run_utc_day_of = run_local_day_of.astimezone(ZoneInfo("UTC"))

    # 3) 30 minutes before interview (easy: utc_dt - 30m)
    run_utc_30min = utc_dt - timedelta(minutes=30)

    now_utc = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))

    # schedule only if in the future
    if run_utc_day_before > now_utc:
        scheduler.add_job(send_interview_reminder, "date",
                          run_date=run_utc_day_before,
                          args=[application.id, "day_before_9am"],
                          id=f"appl_{application.id}_day_before",
                          replace_existing=True)

    if run_utc_day_of > now_utc:
        scheduler.add_job(send_interview_reminder, "date",
                          run_date=run_utc_day_of,
                          args=[application.id, "day_of_9am"],
                          id=f"appl_{application.id}_day_of",
                          replace_existing=True)

    if run_utc_30min > now_utc:
        scheduler.add_job(send_interview_reminder, "date",
                          run_date=run_utc_30min,
                          args=[application.id, "30min_before"],
                          id=f"appl_{application.id}_30min",
                          replace_existing=True)