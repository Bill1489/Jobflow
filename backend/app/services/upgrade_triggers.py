"""
Upgrade Trigger Service

Sends smart upgrade-trigger emails based on user behavior and subscription tier.
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.models.career import CareerProgress, SalaryBenchmark
from backend.app.services.email import EmailService


class UpgradeTriggerService:
    """Service for sending upgrade-trigger emails"""
    
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()
    
    def send_salary_check_teaser(self, user: User):
        """
        Send salary check teaser to FREE users.
        Shows current salary, blurs market data.
        """
        if user.subscription_plan != "free":
            return
        
        # Get career progress
        career = self.db.query(CareerProgress).filter(
            CareerProgress.user_id == user.id
        ).first()
        
        if not career:
            return
        
        # Get benchmark (for internal use, not shown to user)
        benchmark = self.db.query(SalaryBenchmark).filter(
            SalaryBenchmark.role == career.current_title,
            SalaryBenchmark.location == career.location,
            SalaryBenchmark.experience_level == career.seniority_level
        ).first()
        
        # Hint at being below market (creates FOMO)
        hint_below = benchmark and benchmark.is_below_market(career.current_salary)
        hint_text = "You may be below market average" if hint_below else "Market data available"
        
        # Send teaser email
        self.email_service.send_email(
            to=user.email,
            subject="💰 Your Q1 Salary Check is Ready",
            template="salary_check_teaser",
            data={
                "user_name": user.email.split("@")[0],
                "current_salary": career.current_salary,
                "currency": career.currency,
                "hint_text": hint_text,
                "similar_roles_count": 3,
                "upgrade_price": "$149/year",
                "upgrade_url": f"/billing/upgrade?plan=career&source=salary_check",
                "monthly_equivalent": "$12.42/month"
            }
        )
    
    def send_salary_check_full(self, user: User):
        """
        Send full salary check to PRO/CAREER users.
        Shows complete market data.
        """
        if user.subscription_plan == "free":
            return
        
        # Get career progress
        career = self.db.query(CareerProgress).filter(
            CareerProgress.user_id == user.id
        ).first()
        
        if not career:
            return
        
        # Get benchmark
        benchmark = self.db.query(SalaryBenchmark).filter(
            SalaryBenchmark.role == career.current_title,
            SalaryBenchmark.location == career.location,
            SalaryBenchmark.experience_level == career.seniority_level
        ).first()
        
        if not benchmark:
            return
        
        # Calculate position
        percentile = benchmark.get_percentile(career.current_salary)
        underpaid_pct = benchmark.get_underpaid_percentage(career.current_salary)
        
        # Send full email
        subject = "✅ Your salary is competitive!" if underpaid_pct == 0 else f"⚠️ You're {underpaid_pct:.0f}% below market!"
        
        self.email_service.send_email(
            to=user.email,
            subject=subject,
            template="salary_check_full",
            data={
                "user_name": user.email.split("@")[0],
                "current_salary": career.current_salary,
                "currency": career.currency,
                "market_avg": benchmark.avg_salary,
                "market_top_25": benchmark.top_25_salary,
                "market_top_10": benchmark.top_10_salary,
                "percentile": percentile,
                "underpaid_percentage": underpaid_pct,
                "next_review_date": career.next_salary_review_date.strftime("%B %Y") if career.next_salary_review_date else "Q3 2026"
            }
        )
    
    def send_promotion_readiness_teaser(self, user: User):
        """
        Send promotion readiness teaser to PRO users.
        Shows readiness score, blurs salary opportunity.
        """
        if user.subscription_plan != "pro":
            return
        
        # Get career progress
        career = self.db.query(CareerProgress).filter(
            CareerProgress.user_id == user.id
        ).first()
        
        if not career:
            return
        
        # Calculate readiness score
        months = career.calculate_months_in_role()
        tenure_score = min(months / 24, 1.0) * 30
        skills_score = min(len(career.skills_gained) / 5, 1.0) * 40
        leadership_score = min(career.leadership_projects / 3, 1.0) * 30
        total_score = int(tenure_score + skills_score + leadership_score)
        
        # Only send if score is high (70+)
        if total_score < 70:
            return
        
        # Send teaser email
        self.email_service.send_email(
            to=user.email,
            subject="🎯 You're Ready for Promotion!",
            template="promotion_readiness_teaser",
            data={
                "user_name": user.email.split("@")[0],
                "score": total_score,
                "months_in_role": months,
                "skills_gained": len(career.skills_gained),
                "leadership_count": career.leadership_projects,
                "next_level": career.next_seniority_level or "Senior",
                "roles_count": 847,  # Placeholder - would query job DB
                "avg_salary": "🔒 CAREER users see",
                "upgrade_price": "$149/year",
                "upgrade_url": f"/billing/upgrade?plan=career&source=promotion"
            }
        )
    
    def send_promotion_readiness_full(self, user: User):
        """
        Send full promotion readiness to CAREER users.
        Shows salary opportunities.
        """
        if user.subscription_plan != "career":
            return
        
        # Get career progress
        career = self.db.query(CareerProgress).filter(
            CareerProgress.user_id == user.id
        ).first()
        
        if not career:
            return
        
        # Calculate readiness
        months = career.calculate_months_in_role()
        tenure_score = min(months / 24, 1.0) * 30
        skills_score = min(len(career.skills_gained) / 5, 1.0) * 40
        leadership_score = min(career.leadership_projects / 3, 1.0) * 30
        total_score = int(tenure_score + skills_score + leadership_score)
        
        if total_score < 70:
            return
        
        # Get market salary for next level
        market_salary = None
        if career.next_seniority_level:
            benchmark = self.db.query(SalaryBenchmark).filter(
                SalaryBenchmark.role == career.current_title,
                SalaryBenchmark.location == career.location,
                SalaryBenchmark.experience_level == career.next_seniority_level
            ).first()
            if benchmark:
                market_salary = benchmark.avg_salary
        
        # Send full email
        self.email_service.send_email(
            to=user.email,
            subject=f"🎉 You're Ready for {career.next_seniority_level or 'Senior'} Role!",
            template="promotion_readiness_full",
            data={
                "user_name": user.email.split("@")[0],
                "score": total_score,
                "months_in_role": months,
                "market_salary": market_salary,
                "current_salary": career.current_salary,
                "potential_increase": market_salary - career.current_salary if market_salary else None,
                "roles_count": 847,
                "cta_url": "/career?tab=jobs"
            }
        )
    
    def send_network_fomo(self, user: User):
        """
        Send network FOMO email to FREE users.
        Shows others are getting promoted.
        """
        if user.subscription_plan != "free":
            return
        
        # Send FOMO email
        self.email_service.send_email(
            to=user.email,
            subject="👥 People Like You Are Getting Promoted",
            template="network_fomo",
            data={
                "user_name": user.email.split("@")[0],
                "location": "London, UK",  # Would use user's location
                "promotions_count": 3,
                "avg_increase_pct": 31,
                "avg_increase_amount": 24000,
                "upgrade_price": "$149/year",
                "upgrade_url": f"/billing/upgrade?source=fomo"
            }
        )
    
    def send_quarterly_review_teaser(self, user: User):
        """
        Send quarterly review teaser to FREE users.
        """
        if user.subscription_plan != "free":
            return
        
        self.email_service.send_email(
            to=user.email,
            subject="⏰ Time for Your Quarterly Review",
            template="quarterly_review_teaser",
            data={
                "user_name": user.email.split("@")[0],
                "months_since_start": 3,
                "free_features": ["1 salary check/year", "Basic market data", "No promotion alerts"],
                "career_features": ["4 salary checks/year", "Full market benchmarking", "Promotion alerts", "Passive job alerts", "Annual career report"],
                "special_offer": "$99 first year",
                "regular_price": "$149/year",
                "upgrade_url": f"/billing/upgrade?plan=career&source=quarterly&discount=first_year"
            }
        )
    
    def send_annual_report_teaser(self, user: User, year: int):
        """
        Send annual report teaser to FREE users.
        """
        if user.subscription_plan != "free":
            return
        
        # Get basic career info
        career = self.db.query(CareerProgress).filter(
            CareerProgress.user_id == user.id
        ).first()
        
        self.email_service.send_email(
            to=user.email,
            subject=f"📊 Your {year} Career Report is Ready",
            template="annual_report_teaser",
            data={
                "user_name": user.email.split("@")[0],
                "year": year,
                "current_company": career.current_company if career else "Your Company",
                "current_salary": career.current_salary if career else "£XX,XXX",
                "upgrade_price": "$149/year",
                "upgrade_url": f"/billing/upgrade?plan=career&source=annual_report"
            }
        )
