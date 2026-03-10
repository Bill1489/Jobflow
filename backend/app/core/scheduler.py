"""
Celery Beat Scheduler Configuration

Scheduled tasks for career progression features:
- Quarterly salary reviews (every 3 months)
- Promotion readiness checks (monthly)
- Passive job alerts (weekly)
- Annual career reports (yearly)
- Salary benchmark updates (weekly)
"""

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Quarterly salary reviews (1st of January, April, July, October at 9:00 AM)
    "quarterly-salary-reviews": {
        "task": "backend.app.tasks.career_tasks.run_quarterly_salary_reviews",
        "schedule": crontab(minute=0, hour=9, day_of_month=1, month_of_year="1,4,7,10"),
        "options": {"queue": "career"},
    },
    
    # Promotion readiness checks (1st of every month at 10:00 AM)
    "promotion-readiness-checks": {
        "task": "backend.app.tasks.career_tasks.check_promotion_readiness",
        "schedule": crontab(minute=0, hour=10, day_of_month=1),
        "options": {"queue": "career"},
    },
    
    # Passive job alerts (every Monday at 11:00 AM)
    "passive-job-alerts": {
        "task": "backend.app.tasks.career_tasks.send_passive_job_alerts",
        "schedule": crontab(minute=0, hour=11, day_of_week=1),
        "options": {"queue": "career"},
    },
    
    # Annual career reports (January 1st at 9:00 AM)
    "annual-career-reports": {
        "task": "backend.app.tasks.career_tasks.generate_annual_career_reports",
        "schedule": crontab(minute=0, hour=9, day_of_month=1, month_of_year=1),
        "options": {"queue": "career"},
    },
    
    # Salary benchmark updates (every Sunday at 2:00 AM)
    "salary-benchmark-updates": {
        "task": "backend.app.tasks.career_tasks.update_salary_benchmarks",
        "schedule": crontab(minute=0, hour=2, day_of_week=0),
        "options": {"queue": "career"},
    },
    
    # Monthly email scheduling (15th of every month at 8:00 AM)
    "monthly-email-scheduling": {
        "task": "backend.app.tasks.career_tasks.schedule_user_emails",
        "schedule": crontab(minute=0, hour=8, day_of_month=15),
        "options": {"queue": "career"},
    },
}
