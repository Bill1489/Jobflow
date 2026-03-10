"""
Career Schemas

Pydantic models for career tracking API requests and responses.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, date


# Request Schemas

class CareerProgressCreate(BaseModel):
    """Schema for starting a new career role"""
    company: str = Field(..., min_length=1, max_length=255)
    title: str = Field(..., min_length=1, max_length=255)
    salary: int = Field(..., gt=0)
    currency: str = Field(default="GBP", max_length=3)
    seniority_level: str = Field(..., description="junior, mid, senior, staff, principal, lead")
    start_date: date
    location: str = Field(..., max_length=255)
    next_seniority_level: Optional[str] = Field(None, max_length=50)


class CareerProgressUpdate(BaseModel):
    """Schema for updating career progress"""
    company: Optional[str] = Field(None, max_length=255)
    title: Optional[str] = Field(None, max_length=255)
    salary: Optional[int] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    seniority_level: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    skills_gained: Optional[List[str]] = None
    leadership_projects: Optional[int] = Field(None, ge=0)


class CareerGoalCreate(BaseModel):
    """Schema for creating a career goal"""
    goal_type: str = Field(..., description="promotion, salary, skills, company, work_life_balance")
    target_title: Optional[str] = Field(None, max_length=255)
    target_salary: Optional[int] = Field(None, gt=0)
    target_company: Optional[str] = Field(None, max_length=255)
    target_location: Optional[str] = Field(None, max_length=255)
    target_date: Optional[date] = None
    action_items: Optional[List[str]] = None


class CareerGoalUpdate(BaseModel):
    """Schema for updating a career goal"""
    goal_type: Optional[str] = None
    target_title: Optional[str] = None
    target_salary: Optional[int] = None
    target_company: Optional[str] = None
    target_location: Optional[str] = None
    target_date: Optional[date] = None
    status: Optional[str] = Field(None, description="active, achieved, abandoned, paused")
    action_items: Optional[List[str]] = None
    completed_actions: Optional[List[str]] = None


# Response Schemas

class CareerProgressResponse(BaseModel):
    """Schema for career progress response"""
    id: int
    user_id: int
    current_company: str
    current_title: str
    current_salary: int
    currency: str
    seniority_level: str
    started_at: date
    location: str
    next_seniority_level: Optional[str]
    months_in_role: int
    promotions_count: int
    skills_gained: List[str]
    leadership_projects: int
    next_salary_review_date: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class CareerHistoryResponse(BaseModel):
    """Schema for career history response"""
    id: int
    user_id: int
    company: str
    title: str
    salary: int
    currency: str
    seniority_level: str
    location: str
    started_at: date
    ended_at: date
    achievements: List[str]
    skills_gained: List[str]
    leadership_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class SalaryBenchmarkResponse(BaseModel):
    """Schema for salary benchmark response"""
    id: int
    role: str
    location: str
    experience_level: str
    min_salary: int
    avg_salary: int
    max_salary: int
    top_25_salary: Optional[int]
    top_10_salary: Optional[int]
    median_salary: Optional[int]
    sample_size: int
    last_updated: datetime
    
    class Config:
        from_attributes = True


class CareerGoalResponse(BaseModel):
    """Schema for career goal response"""
    id: int
    user_id: int
    goal_type: str
    target_title: Optional[str]
    target_salary: Optional[int]
    target_company: Optional[str]
    target_location: Optional[str]
    target_date: Optional[date]
    progress: int
    status: str
    action_items: List[str]
    completed_actions: List[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SalaryPosition(BaseModel):
    """Schema for salary position within market"""
    percentile: Optional[int]
    is_below_market: Optional[bool]
    underpaid_percentage: Optional[float]
    market_avg: Optional[int]
    market_top_25: Optional[int]


class SimilarRole(BaseModel):
    """Schema for similar higher-paying role"""
    role: str
    avg_salary: int
    difference: int


class SalaryCheckResponse(BaseModel):
    """
    Schema for salary check response.
    Returns blurred data for FREE users, full data for paid tiers.
    """
    current_salary: int
    currency: str
    market_avg: Optional[int] = None
    market_top_25: Optional[int] = None
    market_top_10: Optional[int] = None
    percentile: Optional[int] = None
    is_below_market: Optional[bool] = None
    underpaid_percentage: Optional[float] = None
    similar_roles: Optional[List[SimilarRole]] = None
    upgrade_required: bool = False
    upgrade_plan: Optional[str] = None
    upgrade_price: Optional[str] = None
    message: Optional[str] = None


class PromotionReadinessResponse(BaseModel):
    """
    Schema for promotion readiness response.
    PRO users see score but not salary opportunity.
    CAREER users see everything.
    """
    score: int
    months_in_role: int
    skills_gained: int
    leadership_count: int
    ready: bool
    next_level: Optional[str]
    market_salary: Optional[int] = None
    roles_available: Optional[int] = None
    upgrade_required: bool = False
    upgrade_plan: Optional[str] = None
    message: Optional[str] = None


class CareerDashboardResponse(BaseModel):
    """Schema for career dashboard response"""
    has_career_tracking: bool
    message: Optional[str] = None
    career: Optional[CareerProgressResponse] = None
    history: List[CareerHistoryResponse] = []
    goals: List[CareerGoalResponse] = []
    salary_position: Optional[dict] = None
    promotion_ready: Optional[bool] = None
    total_growth: Optional[dict] = None


class AnnualReportResponse(BaseModel):
    """Schema for annual career report response"""
    year: int
    summary: dict
    pdf_url: Optional[str] = None
    upgrade_required: bool = False
    upgrade_plan: Optional[str] = None
    upgrade_price: Optional[str] = None
    message: Optional[str] = None
