"""
Career Celery Tasks

Background tasks for career progression features:
- Quarterly salary reviews
- Promotion readiness checks
- Passive job alerts
- Annual career reports
- Salary benchmark updates
"""

from celery import Task
from datetime import datetime, timedelta, date
from sqlalchemy import and_
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models.user import User
from backend.app.models.career import CareerProgress, CareerHistory, SalaryBenchmark
from backend.app.services.upgrade_triggers import UpgradeTriggerService
from backend.app.services.email import EmailService


class CareerTask(Task):
    """Base class for career tasks with DB session management"""
    
    _db = None
    
    @property
    def db(self):
        if self._db is None:
            self._db = SessionLocal()
        return self._db
    
    def after_run(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


# Task 1: Quarterly Salary Reviews

def run_quarterly_salary_reviews():
    """
    Send quarterly salary review emails to all due users.
    FREE: Teaser version
    PRO/CAREER: Full version
    """
    db = SessionLocal()
    try:
        email_service = EmailService()
        upgrade_service = UpgradeTriggerService(db)
        
        # Find users due for review
        due_users = db.query(User).filter(
            User.next_salary_review_date <= datetime.utcnow(),
            User.employment_status == "employed"
        ).all()
        
        count = 0
        for user in due_users:
            try:
                if user.subscription_plan == "free":
                    upgrade_service.send_salary_check_teaser(user)
                else:
                    upgrade_service.send_salary_check_full(user)
                
                # Schedule next review (3 months)
                user.next_salary_review_date = datetime.utcnow() + timedelta(days=90)
                count += 1
            except Exception as e:
                print(f"Error sending salary review to {user.email}: {e}")
        
        db.commit()
        print(f"Sent {count} quarterly salary reviews")
        
    finally:
        db.close()


# Task 2: Promotion Readiness Checks

def check_promotion_readiness():
    """
    Check promotion readiness for all users.
    Sends alerts when users are ready (score >= 70).
    PRO: Teaser version (upsell CAREER)
    CAREER: Full version
    """
    db = SessionLocal()
    try:
        upgrade_service = UpgradeTriggerService(db)
        
        # Find users 18+ months in role who haven't been alerted
        careers = db.query(CareerProgress).filter(
            CareerProgress.months_in_role >= 18
        ).all()
        
        count = 0
        for career in careers:
            user = db.query(User).filter(User.id == career.user_id).first()
            if not user:
                continue
            
            # Calculate readiness score
            months = career.calculate_months_in_role()
            tenure_score = min(months / 24, 1.0) * 30
            skills_score = min(len(career.skills_gained) / 5, 1.0) * 40
            leadership_score = min(career.leadership_projects / 3, 1.0) * 30
            total_score = int(tenure_score + skills_score + leadership_score)
            
            # Only alert if score >= 70
            if total_score >= 70:
                try:
                    if user.subscription_plan == "pro":
                        upgrade_service.send_promotion_readiness_teaser(user)
                    elif user.subscription_plan == "career":
                        upgrade_service.send_promotion_readiness_full(user)
                    count += 1
                except Exception as e:
                    print(f"Error sending promotion alert to {user.email}: {e}")
        
        print(f"Sent {count} promotion readiness alerts")
        
    finally:
        db.close()


# Task 3: Passive Job Alerts

def send_passive_job_alerts():
    """
    Send passive job alerts to CAREER users.
    Only shows exceptional opportunities (20%+ better).
    """
    db = SessionLocal()
    try:
        email_service = EmailService()
        
        # Get CAREER users who are employed
        career_users = db.query(User).filter(
            User.subscription_plan == "career",
            User.employment_status == "employed"
        ).all()
        
        count = 0
        for user in career_users:
            try:
                career = db.query(CareerProgress).filter(
                    CareerProgress.user_id == user.id
                ).first()
                
                if not career:
                    continue
                
                # Find jobs 20%+ better (placeholder - would query jobs table)
                min_salary = career.current_salary * 1.20
                
                # In production, query jobs table for matching roles
                # jobs = db.query(Job).filter(
                #     Job.salary_min >= min_salary,
                #     Job.seniority_level == career.next_seniority_level
                # ).limit(3).all()
                
                # Placeholder: send email with mock data
                email_service.send_email(
                    to=user.email,
                    subject="🎯 3 Exceptional Opportunities This Week",
                    template="passive_alerts",
                    data={
                        "user_name": user.email.split("@")[0],
                        "current_salary": career.current_salary,
                        "min_salary": int(min_salary),
                        "jobs": [
                            {"title": f"Senior {career.current_title}", "company": "Top Company", "salary": int(min_salary * 1.1)},
                            {"title": f"Lead {career.current_title}", "company": "Great Startup", "salary": int(min_salary * 1.2)},
                            {"title": f"Staff {career.current_title}", "company": "Tech Giant", "salary": int(min_salary * 1.3)}
                        ],
                        "cta_url": "/dashboard?tab=jobs"
                    }
                )
                count += 1
            except Exception as e:
                print(f"Error sending passive alert to {user.email}: {e}")
        
        print(f"Sent {count} passive job alerts")
        
    finally:
        db.close()


# Task 4: Annual Career Reports

def generate_annual_career_reports():
    """
    Generate annual career reports for all users.
    FREE: Teaser version
    CAREER: Full PDF report
    """
    db = SessionLocal()
    try:
        email_service = EmailService()
        upgrade_service = UpgradeTriggerService(db)
        
        # Get all users with career tracking
        users = db.query(User).filter(
            User.career_started_at != None
        ).all()
        
        current_year = datetime.utcnow().year
        
        count = 0
        for user in users:
            try:
                if user.subscription_plan == "free":
                    upgrade_service.send_annual_report_teaser(user, current_year - 1)
                elif user.subscription_plan == "career":
                    # Send full report
                    email_service.send_email(
                        to=user.email,
                        subject=f"📊 Your {current_year - 1} Annual Career Report",
                        template="annual_report_full",
                        data={
                            "user_name": user.email.split("@")[0],
                            "year": current_year - 1,
                            "pdf_url": f"/api/v1/career/annual-report/{current_year - 1}/pdf"
                        }
                    )
                count += 1
            except Exception as e:
                print(f"Error sending annual report to {user.email}: {e}")
        
        print(f"Sent {count} annual career reports")
        
    finally:
        db.close()


# Task 5: Salary Benchmark Updates

def update_salary_benchmarks():
    """
    Update salary benchmarks weekly.
    Aggregates user data + external APIs.
    """
    db = SessionLocal()
    try:
        # Aggregate user-reported data
        user_data = db.query(
            CareerProgress.current_title,
            CareerProgress.location,
            CareerProgress.seniority_level,
            func.avg(CareerProgress.current_salary),
            func.min(CareerProgress.current_salary),
            func.max(CareerProgress.current_salary),
            func.count(CareerProgress.id)
        ).filter(
            User.opt_in_data_sharing == True
        ).join(User).group_by(
            CareerProgress.current_title,
            CareerProgress.location,
            CareerProgress.seniority_level
        ).all()
        
        count = 0
        for role, location, level, avg, min, max, sample_count in user_data:
            if not avg:
                continue
            
            # Get or create benchmark
            benchmark = db.query(SalaryBenchmark).filter(
                SalaryBenchmark.role == role,
                SalaryBenchmark.location == location,
                SalaryBenchmark.experience_level == level
            ).first()
            
            if benchmark:
                # Update with weighted average
                old_sample = benchmark.sample_size
                new_sample = sample_count
                total_sample = old_sample + new_sample
                
                benchmark.avg_salary = int((benchmark.avg_salary * old_sample + avg * new_sample) / total_sample)
                benchmark.sample_size = total_sample
                benchmark.last_updated = datetime.utcnow()
            else:
                # Create new benchmark
                benchmark = SalaryBenchmark(
                    role=role,
                    location=location,
                    experience_level=level,
                    min_salary=int(min),
                    avg_salary=int(avg),
                    max_salary=int(max),
                    median_salary=int(avg),  # Placeholder
                    top_25_salary=int(avg * 1.15),  # Placeholder
                    top_10_salary=int(avg * 1.30),  # Placeholder
                    sample_size=sample_count,
                    source="user_data"
                )
                db.add(benchmark)
            
            count += 1
        
        db.commit()
        print(f"Updated {count} salary benchmarks")
        
    finally:
        db.close()


# Task 6: Email Scheduler

def schedule_user_emails():
    """
    Schedule monthly/quarterly/yearly emails for all users.
    """
    db = SessionLocal()
    try:
        upgrade_service = UpgradeTriggerService(db)
        
        users = db.query(User).filter(User.is_active == True).all()
        
        for user in users:
            try:
                if user.subscription_plan == "free":
                    # Monthly teasers
                    upgrade_service.send_salary_check_teaser(user)
                    upgrade_service.send_network_fomo(user)
                elif user.subscription_plan == "pro":
                    # Monthly promotion upsell
                    upgrade_service.send_promotion_readiness_teaser(user)
                elif user.subscription_plan == "career":
                    # Monthly passive alerts
                    # (handled by send_passive_job_alerts task)
                    pass
            except Exception as e:
                print(f"Error scheduling emails for {user.email}: {e}")
        
        print(f"Scheduled emails for {len(users)} users")
        
    finally:
        db.close()


# Import func for the query
from sqlalchemy import func
