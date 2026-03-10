"""
Career Progression Models

Tracks user career growth, salary benchmarks, and goals.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON, Date
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class CareerProgress(Base):
    """
    Tracks user's current career progression.
    One record per user (updated when they change roles).
    """
    __tablename__ = "career_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Current role details
    current_company = Column(String(255), nullable=False)
    current_title = Column(String(255), nullable=False)
    current_salary = Column(Integer, nullable=False)  # Annual salary in local currency
    currency = Column(String(3), default="GBP")  # GBP, USD, EUR, etc.
    seniority_level = Column(String(50), nullable=False)  # junior, mid, senior, staff, principal, lead
    started_at = Column(Date, nullable=False)
    location = Column(String(255), nullable=False)  # e.g., "London, UK"
    
    # Progress tracking
    next_seniority_level = Column(String(50))  # Target level
    months_in_role = Column(Integer, default=0)
    promotions_count = Column(Integer, default=0)
    skills_gained = Column(JSON, default=list)  # List of skills gained in this role
    leadership_projects = Column(Integer, default=0)  # Number of leadership projects
    
    # Review cycle
    next_salary_review_date = Column(DateTime)
    last_anniversary_date = Column(DateTime)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="career_progress")
    history = relationship("CareerHistory", back_populates="user", order_by="CareerHistory.ended_at.desc()")
    goals = relationship("CareerGoal", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CareerProgress(user_id={self.user_id}, company={self.current_company}, title={self.current_title})>"
    
    def calculate_months_in_role(self):
        """Calculate months since role started"""
        if self.started_at:
            delta = datetime.utcnow().date() - self.started_at
            self.months_in_role = int(delta.days / 30)
            return self.months_in_role
        return 0
    
    def is_due_for_review(self):
        """Check if salary review is due"""
        if self.next_salary_review_date:
            return datetime.utcnow() >= self.next_salary_review_date
        return False
    
    def is_promotion_ready(self):
        """Check if user is ready for promotion (18+ months)"""
        return self.months_in_role >= 18


class CareerHistory(Base):
    """
    Archived career history.
    Created when user updates their current role.
    """
    __tablename__ = "career_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Role details
    company = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    salary = Column(Integer, nullable=False)
    currency = Column(String(3), default="GBP")
    seniority_level = Column(String(50), nullable=False)
    location = Column(String(255), nullable=False)
    
    # Timeline
    started_at = Column(Date, nullable=False)
    ended_at = Column(Date, nullable=False)
    
    # Achievements
    achievements = Column(JSON, default=list)  # List of achievements in this role
    skills_gained = Column(JSON, default=list)  # Skills gained
    leadership_count = Column(Integer, default=0)  # Leadership projects
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="career_history")
    
    def __repr__(self):
        return f"<CareerHistory(company={self.company}, title={self.title}, {self.started_at} - {self.ended_at})>"
    
    def get_tenure_months(self):
        """Calculate tenure in months"""
        if self.started_at and self.ended_at:
            delta = self.ended_at - self.started_at
            return int(delta.days / 30)
        return 0
    
    def get_salary_growth(self, previous_role):
        """Calculate salary growth from previous role"""
        if previous_role and previous_role.salary:
            growth = self.salary - previous_role.salary
            growth_pct = (growth / previous_role.salary) * 100
            return {"absolute": growth, "percentage": round(growth_pct, 1)}
        return None


class SalaryBenchmark(Base):
    """
    Market salary data by role, location, and experience level.
    Aggregated from user data + external APIs.
    """
    __tablename__ = "salary_benchmarks"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Key dimensions
    role = Column(String(255), nullable=False, index=True)  # e.g., "Software Engineer"
    location = Column(String(255), nullable=False, index=True)  # e.g., "London, UK"
    experience_level = Column(String(50), nullable=False, index=True)  # junior, mid, senior, etc.
    
    # Salary data (annual, in GBP equivalent)
    min_salary = Column(Integer, nullable=False)
    avg_salary = Column(Integer, nullable=False)
    max_salary = Column(Integer, nullable=False)
    top_25_salary = Column(Integer)  # 75th percentile
    top_10_salary = Column(Integer)  # 90th percentile
    median_salary = Column(Integer)  # 50th percentile
    
    # Data quality
    sample_size = Column(Integer, default=0)  # Number of data points
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Sources
    source = Column(String(50), default="user_data")  # user_data, levels_fyi, glassdoor, linkedin
    currency = Column(String(3), default="GBP")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SalaryBenchmark({self.role}, {self.location}, {self.experience_level})>"
    
    def get_percentile(self, salary):
        """Calculate what percentile a salary falls into"""
        if salary >= self.top_10_salary:
            return 90
        elif salary >= self.top_25_salary:
            return 75
        elif salary >= self.avg_salary:
            return 60
        elif salary >= self.median_salary:
            return 50
        else:
            return int((salary / self.avg_salary) * 50)
    
    def is_below_market(self, salary):
        """Check if salary is below market average"""
        return salary < self.avg_salary
    
    def get_underpaid_percentage(self, salary):
        """Calculate how underpaid a salary is"""
        if salary >= self.avg_salary:
            return 0
        return round(((self.avg_salary - salary) / self.avg_salary) * 100, 1)


class CareerGoal(Base):
    """
    User's career goals for tracking.
    """
    __tablename__ = "career_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Goal type
    goal_type = Column(String(50), nullable=False)  # promotion, salary, skills, company, work_life_balance
    
    # Target details
    target_title = Column(String(255))  # e.g., "Senior Software Engineer"
    target_salary = Column(Integer)  # Target annual salary
    target_company = Column(String(255))  # Dream company
    target_location = Column(String(255))  # Target location
    
    # Timeline
    target_date = Column(Date)  # Goal deadline
    
    # Progress tracking
    progress = Column(Integer, default=0)  # 0-100%
    status = Column(String(20), default="active")  # active, achieved, abandoned, paused
    
    # Action items
    action_items = Column(JSON, default=list)  # List of actions to achieve goal
    completed_actions = Column(JSON, default=list)  # Completed actions
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    achieved_at = Column(DateTime)  # When goal was achieved
    
    # Relationships
    user = relationship("User", back_populates="career_goals")
    
    def __repr__(self):
        return f"<CareerGoal(user_id={self.user_id}, type={self.goal_type}, status={self.status})>"
    
    def update_progress(self):
        """Calculate progress based on completed actions"""
        if self.action_items:
            self.progress = int((len(self.completed_actions) / len(self.action_items)) * 100)
            if self.progress >= 100:
                self.status = "achieved"
                self.achieved_at = datetime.utcnow()
            return self.progress
        return 0
    
    def is_overdue(self):
        """Check if goal is past deadline"""
        if self.target_date and self.status == "active":
            return datetime.utcnow().date() > self.target_date
        return False
