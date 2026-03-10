from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from passlib.context import CryptContext

from app.models.base import Base, TimestampMixin

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Subscription & Monetization
    subscription_plan = Column(String(20), default="free")  # free, pro, career
    subscription_cycle = Column(String(20), default="monthly")  # monthly, annual
    subscription_status = Column(String(20), default="active")  # active, canceled, past_due
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))
    
    # Career Tracking
    employment_status = Column(String(20), default="unemployed")  # unemployed, employed, self_employed
    career_started_at = Column(Date)  # When career tracking started
    next_salary_review_date = Column(DateTime)  # Next scheduled salary review
    
    # Data Sharing (for salary benchmarks)
    opt_in_data_sharing = Column(Boolean, default=True)  # Allow anonymized salary data sharing
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    cvs = relationship("CV", back_populates="user", cascade="all, delete-orphan")
    career_progress = relationship("CareerProgress", back_populates="user", uselist=False, cascade="all, delete-orphan")
    career_history = relationship("CareerHistory", back_populates="user", cascade="all, delete-orphan")
    career_goals = relationship("CareerGoal", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def password(self):
        return self.hashed_password
    
    @password.setter
    def password(self, plaintext: str):
        self.hashed_password = pwd_context.hash(plaintext)
    
    def verify_password(self, plaintext: str) -> bool:
        return pwd_context.verify(plaintext, self.hashed_password)
    
    # Subscription helpers
    @property
    def is_free(self):
        return self.subscription_plan == "free"
    
    @property
    def is_pro(self):
        return self.subscription_plan == "pro"
    
    @property
    def is_career(self):
        return self.subscription_plan == "career"
    
    def has_feature(self, feature: str) -> bool:
        """Check if user has access to a feature based on subscription tier"""
        if self.subscription_plan == "free":
            return feature in ["basic_matching", "application_tracking", "basic_dashboard"]
        elif self.subscription_plan == "pro":
            return feature in ["basic_matching", "application_tracking", "basic_dashboard", 
                              "unlimited_applications", "ai_cv", "ai_cover_letter", "auto_apply",
                              "salary_benchmarking", "quarterly_reviews"]
        elif self.subscription_plan == "career":
            return True  # Career has all features
        return False
