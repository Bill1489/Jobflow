"""
Career Management API

Endpoints for career tracking, salary benchmarks, and promotion readiness.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta, date
from typing import List, Optional

from backend.app.database import get_db
from backend.app.models.user import User
from backend.app.models.career import CareerProgress, CareerHistory, SalaryBenchmark, CareerGoal
from backend.app.core.security import get_current_user
from backend.app.schemas.career import (
    CareerProgressCreate,
    CareerProgressUpdate,
    CareerProgressResponse,
    CareerHistoryResponse,
    SalaryBenchmarkResponse,
    CareerGoalCreate,
    CareerGoalUpdate,
    CareerGoalResponse,
    CareerDashboardResponse,
    PromotionReadinessResponse,
    SalaryCheckResponse
)

router = APIRouter(prefix="/api/v1/career", tags=["Career"])


@router.post("/start-role", response_model=CareerProgressResponse, status_code=status.HTTP_201_CREATED)
async def start_new_role(
    role_data: CareerProgressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start tracking a new career role.
    Called when user accepts a job offer.
    """
    # Check if user already has career progress
    existing = db.query(CareerProgress).filter(
        CareerProgress.user_id == current_user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Career tracking already active. Use update-role to change roles."
        )
    
    # Create career progress record
    career = CareerProgress(
        user_id=current_user.id,
        current_company=role_data.company,
        current_title=role_data.title,
        current_salary=role_data.salary,
        currency=role_data.currency,
        seniority_level=role_data.seniority_level,
        started_at=role_data.start_date,
        location=role_data.location,
        next_seniority_level=role_data.next_seniority_level,
        next_salary_review_date=datetime.utcnow() + timedelta(days=90)  # First review in 3 months
    )
    
    # Update user employment status
    current_user.employment_status = "employed"
    current_user.career_started_at = role_data.start_date
    current_user.next_salary_review_date = career.next_salary_review_date
    
    db.add(career)
    db.commit()
    db.refresh(career)
    
    return career


@router.post("/update-role", response_model=CareerProgressResponse)
async def update_role(
    role_data: CareerProgressCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current role (promotion or job change).
    Archives old role and creates new career progress.
    """
    # Get current career progress
    career = db.query(CareerProgress).filter(
        CareerProgress.user_id == current_user.id
    ).first()
    
    if not career:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active career tracking found. Use start-role first."
        )
    
    # Archive current role
    old_role = CareerHistory(
        user_id=current_user.id,
        company=career.current_company,
        title=career.current_title,
        salary=career.current_salary,
        currency=career.currency,
        seniority_level=career.seniority_level,
        location=career.location,
        started_at=career.started_at,
        ended_at=date.today(),
        skills_gained=career.skills_gained,
        leadership_count=career.leadership_projects
    )
    
    db.add(old_role)
    
    # Update career progress with new role
    career.current_company = role_data.company
    career.current_title = role_data.title
    career.current_salary = role_data.salary
    career.currency = role_data.currency
    career.seniority_level = role_data.seniority_level
    career.location = role_data.location
    career.started_at = role_data.start_date
    career.promotions_count += 1
    career.skills_gained = []  # Reset for new role
    career.leadership_projects = 0  # Reset for new role
    career.next_salary_review_date = datetime.utcnow() + timedelta(days=90)
    
    # Update next seniority level if provided
    if role_data.next_seniority_level:
        career.next_seniority_level = role_data.next_seniority_level
    
    db.commit()
    db.refresh(career)
    
    return career


@router.get("/dashboard", response_model=CareerDashboardResponse)
async def get_career_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive career dashboard data.
    Includes current role, history, goals, and benchmarks.
    """
    # Get current career progress
    career = db.query(CareerProgress).filter(
        CareerProgress.user_id == current_user.id
    ).first()
    
    if not career:
        return CareerDashboardResponse(
            has_career_tracking=False,
            message="Start career tracking to see your dashboard"
        )
    
    # Calculate months in role
    career.calculate_months_in_role()
    
    # Get career history
    history = db.query(CareerHistory).filter(
        CareerHistory.user_id == current_user.id
    ).order_by(CareerHistory.ended_at.desc()).all()
    
    # Get career goals
    goals = db.query(CareerGoal).filter(
        CareerGoal.user_id == current_user.id,
        CareerGoal.status == "active"
    ).all()
    
    # Get salary benchmark for current role
    benchmark = db.query(SalaryBenchmark).filter(
        SalaryBenchmark.role == career.current_title,
        SalaryBenchmark.location == career.location,
        SalaryBenchmark.experience_level == career.seniority_level
    ).first()
    
    # Calculate salary position
    salary_position = None
    if benchmark:
        salary_position = {
            "percentile": benchmark.get_percentile(career.current_salary),
            "is_below_market": benchmark.is_below_market(career.current_salary),
            "underpaid_percentage": benchmark.get_underpaid_percentage(career.current_salary),
            "market_avg": benchmark.avg_salary,
            "market_top_25": benchmark.top_25_salary
        }
    
    # Calculate promotion readiness
    promotion_ready = career.is_promotion_ready()
    
    # Calculate total career growth
    total_growth = None
    if history:
        oldest = history[-1]
        total_growth = {
            "absolute": career.current_salary - oldest.salary,
            "percentage": round(((career.current_salary - oldest.salary) / oldest.salary) * 100, 1)
        }
    
    return CareerDashboardResponse(
        has_career_tracking=True,
        career=career,
        history=history,
        goals=goals,
        salary_position=salary_position,
        promotion_ready=promotion_ready,
        total_growth=total_growth
    )


@router.get("/salary-check", response_model=SalaryCheckResponse)
async def get_salary_check(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get salary benchmark comparison.
    Returns blurred data for FREE users, full data for paid tiers.
    """
    # Get current career progress
    career = db.query(CareerProgress).filter(
        CareerProgress.user_id == current_user.id
    ).first()
    
    if not career:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No career tracking found. Start tracking your career first."
        )
    
    # Get salary benchmark
    benchmark = db.query(SalaryBenchmark).filter(
        SalaryBenchmark.role == career.current_title,
        SalaryBenchmark.location == career.location,
        SalaryBenchmark.experience_level == career.seniority_level
    ).first()
    
    # FREE users get blurred data
    if current_user.subscription_plan == "free":
        return SalaryCheckResponse(
            current_salary=career.current_salary,
            currency=career.currency,
            market_avg=None,
            market_top_25=None,
            market_top_10=None,
            percentile=None,
            is_below_market=None,
            underpaid_percentage=None,
            similar_roles=None,
            upgrade_required=True,
            upgrade_plan="career",
            upgrade_price="$149/year",
            message="Upgrade to CAREER to unlock full salary benchmarking"
        )
    
    # Paid users get full data
    if not benchmark:
        return SalaryCheckResponse(
            current_salary=career.current_salary,
            currency=career.currency,
            market_avg=None,
            message="No benchmark data available for your role yet"
        )
    
    # Get similar roles (higher paying)
    similar_roles = db.query(SalaryBenchmark).filter(
        and_(
            SalaryBenchmark.location == career.location,
            SalaryBenchmark.experience_level == career.seniority_level,
            SalaryBenchmark.avg_salary > benchmark.avg_salary
        )
    ).order_by(SalaryBenchmark.avg_salary.desc()).limit(5).all()
    
    similar_roles_data = [
        {
            "role": r.role,
            "avg_salary": r.avg_salary,
            "difference": r.avg_salary - benchmark.avg_salary
        }
        for r in similar_roles
    ]
    
    return SalaryCheckResponse(
        current_salary=career.current_salary,
        currency=career.currency,
        market_avg=benchmark.avg_salary,
        market_top_25=benchmark.top_25_salary,
        market_top_10=benchmark.top_10_salary,
        percentile=benchmark.get_percentile(career.current_salary),
        is_below_market=benchmark.is_below_market(career.current_salary),
        underpaid_percentage=benchmark.get_underpaid_percentage(career.current_salary),
        similar_roles=similar_roles_data,
        upgrade_required=False
    )


@router.get("/progression", response_model=PromotionReadinessResponse)
async def get_promotion_readiness(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get promotion readiness assessment.
    PRO users see readiness score but not salary opportunity.
    CAREER users see everything.
    """
    # Get current career progress
    career = db.query(CareerProgress).filter(
        CareerProgress.user_id == current_user.id
    ).first()
    
    if not career:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No career tracking found"
        )
    
    # Calculate months in role
    months = career.calculate_months_in_role()
    
    # Calculate readiness score
    # Tenure: 30% (max at 24 months)
    tenure_score = min(months / 24, 1.0) * 30
    
    # Skills: 40% (based on skills gained)
    skills_score = min(len(career.skills_gained) / 5, 1.0) * 40
    
    # Leadership: 30% (based on leadership projects)
    leadership_score = min(career.leadership_projects / 3, 1.0) * 30
    
    total_score = int(tenure_score + skills_score + leadership_score)
    
    # Get market salary for next level (CAREER users only)
    market_salary = None
    roles_available = None
    
    if current_user.subscription_plan == "career" and career.next_seniority_level:
        benchmark = db.query(SalaryBenchmark).filter(
            SalaryBenchmark.role == career.current_title,
            SalaryBenchmark.location == career.location,
            SalaryBenchmark.experience_level == career.next_seniority_level
        ).first()
        
        if benchmark:
            market_salary = benchmark.avg_salary
        
        # Count available roles at next level
        # This would integrate with job search in production
        roles_available = 0  # Placeholder
    
    # PRO users get limited data
    if current_user.subscription_plan == "pro":
        return PromotionReadinessResponse(
            score=total_score,
            months_in_role=months,
            skills_gained=len(career.skills_gained),
            leadership_count=career.leadership_projects,
            ready=total_score >= 70,
            next_level=career.next_seniority_level,
            market_salary=None,
            roles_available=None,
            upgrade_required=True,
            upgrade_plan="career",
            message="Upgrade to CAREER to see salary opportunities"
        )
    
    # CAREER users get full data
    return PromotionReadinessResponse(
        score=total_score,
        months_in_role=months,
        skills_gained=len(career.skills_gained),
        leadership_count=career.leadership_projects,
        ready=total_score >= 70,
        next_level=career.next_seniority_level,
        market_salary=market_salary,
        roles_available=roles_available,
        upgrade_required=False
    )


@router.get("/annual-report")
async def get_annual_report(
    year: int = Query(..., description="Report year"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get annual career report.
    FREE users get teaser, CAREER users get full PDF.
    """
    # Get career history for the year
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)
    
    history = db.query(CareerHistory).filter(
        CareerHistory.user_id == current_user.id,
        CareerHistory.ended_at >= start_date,
        CareerHistory.ended_at <= end_date
    ).all()
    
    # Get current career
    career = db.query(CareerProgress).filter(
        CareerProgress.user_id == current_user.id
    ).first()
    
    # FREE users get teaser
    if current_user.subscription_plan == "free":
        return {
            "year": year,
            "summary": {
                "roles_held": len(history),
                "current_company": career.current_company if career else None,
                "current_salary": career.current_salary if career else None
            },
            "upgrade_required": True,
            "upgrade_plan="career",
            "upgrade_price": "$149/year",
            "message": "Upgrade to CAREER for full annual report with growth analysis and PDF"
        }
    
    # CAREER users get full report
    # In production, this would generate a PDF
    return {
        "year": year,
        "summary": {
            "roles_held": len(history),
            "promotions": len([h for h in history if h.seniority_level != (history[history.index(h)-1].seniority_level if history.index(h) > 0 else None)]),
            "salary_growth": calculate_salary_growth(history, career),
            "skills_gained": sum(len(h.skills_gained) for h in history)
        },
        "pdf_url": f"/api/v1/career/annual-report/{year}/pdf",  # Would generate PDF
        "upgrade_required": False
    }


@router.post("/goals", response_model=CareerGoalResponse, status_code=status.HTTP_201_CREATED)
async def set_career_goals(
    goal_data: CareerGoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set career goals for tracking.
    """
    goal = CareerGoal(
        user_id=current_user.id,
        goal_type=goal_data.goal_type,
        target_title=goal_data.target_title,
        target_salary=goal_data.target_salary,
        target_company=goal_data.target_company,
        target_location=goal_data.target_location,
        target_date=goal_data.target_date,
        action_items=goal_data.action_items or []
    )
    
    db.add(goal)
    db.commit()
    db.refresh(goal)
    
    return goal


@router.get("/goals", response_model=List[CareerGoalResponse])
async def get_career_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's career goals.
    """
    goals = db.query(CareerGoal).filter(
        CareerGoal.user_id == current_user.id
    ).order_by(CareerGoal.created_at.desc()).all()
    
    return goals


@router.put("/goals/{goal_id}", response_model=CareerGoalResponse)
async def update_career_goal(
    goal_id: int,
    goal_data: CareerGoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a career goal.
    """
    goal = db.query(CareerGoal).filter(
        CareerGoal.id == goal_id,
        CareerGoal.user_id == current_user.id
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    # Update fields
    if goal_data.goal_type is not None:
        goal.goal_type = goal_data.goal_type
    if goal_data.target_title is not None:
        goal.target_title = goal_data.target_title
    if goal_data.target_salary is not None:
        goal.target_salary = goal_data.target_salary
    if goal_data.target_company is not None:
        goal.target_company = goal_data.target_company
    if goal_data.target_date is not None:
        goal.target_date = goal_data.target_date
    if goal_data.status is not None:
        goal.status = goal_data.status
    if goal_data.action_items is not None:
        goal.action_items = goal_data.action_items
    if goal_data.completed_actions is not None:
        goal.completed_actions = goal_data.completed_actions
    
    # Update progress
    goal.update_progress()
    
    db.commit()
    db.refresh(goal)
    
    return goal


# Helper functions

def calculate_salary_growth(history: List[CareerHistory], current: Optional[CareerProgress]) -> dict:
    """Calculate salary growth over career"""
    if not history:
        return {"absolute": 0, "percentage": 0}
    
    oldest = history[-1]
    latest = current if current else history[0]
    
    growth = latest.current_salary - oldest.salary
    pct = ((growth / oldest.salary) * 100) if oldest.salary else 0
    
    return {
        "absolute": growth,
        "percentage": round(pct, 1)
    }
