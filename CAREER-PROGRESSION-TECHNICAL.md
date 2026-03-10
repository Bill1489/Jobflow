# 🔧 CAREER PROGRESSION - TECHNICAL IMPLEMENTATION

**Date:** 2026-03-09  
**Status:** Technical Specification

---

## 📊 HOW IT ACTUALLY WORKS (TECHNICAL FLOW)

---

## PHASE 1: USER GETS JOB (Month 0)

### Step 1: User Applies Through JobScale

```
User action:
- Applies to "Software Engineer @ Stripe" via extension
- Application status: "submitted"

Database:
applications {
  id: 1,
  user_id: 1,
  job_id: 123,
  status: "submitted",
  submitted_at: "2026-03-09",
  ...
}
```

---

### Step 2: User Updates Application Status

```
User action (2 weeks later):
- Goes to /applications
- Clicks on Stripe application
- Changes status: "submitted" → "offer_received"

Frontend:
PATCH /api/v1/applications/1
{
  "status": "offer_received",
  "offer_details": {
    "salary": 80000,
    "currency": "GBP",
    "start_date": "2026-04-01",
    "title": "Software Engineer",
    "seniority": "mid"
  }
}

Backend:
@applications_router.patch("/{application_id}")
async def update_application(application_id, update_data, current_user):
    application = db.query(Application).get(application_id)
    
    if update_data.status == "offer_received":
        # Trigger career tracking setup
        await setup_career_tracking(
            user=current_user,
            offer=update_data.offer_details
        )
    
    application.status = update_data.status
    db.commit()
```

---

### Step 3: User Accepts Offer

```
User action:
- Clicks "I Accept" on offer
- Confirms start date

Frontend:
POST /api/v1/career/start-role
{
  "application_id": 1,
  "company": "Stripe",
  "title": "Software Engineer",
  "seniority_level": "mid",
  "salary": 80000,
  "currency": "GBP",
  "start_date": "2026-04-01",
  "location": "London, UK"
}

Backend:
@career_router.post("/start-role")
async def start_new_role(role_data, current_user):
    # 1. Create career record
    career = CareerProgress(
        user_id=current_user.id,
        current_company=role_data.company,
        current_title=role_data.title,
        seniority_level=role_data.seniority_level,
        salary=role_data.salary,
        currency=role_data.currency,
        started_at=role_data.start_date,
        location=role_data.location
    )
    db.add(career)
    
    # 2. Update user profile
    user_profile = db.query(UserProfile).filter(
        UserProfile.user_id == current_user.id
    ).first()
    user_profile.current_company = role_data.company
    user_profile.current_title = role_data.title
    user_profile.employment_status = "employed"
    
    # 3. Suggest downgrade to CAREER tier
    if current_user.subscription_plan == "pro":
        send_downgrade_suggestion_email(current_user)
    
    # 4. Schedule first salary review (3 months from start)
    first_review_date = role_data.start_date + timedelta(days=90)
    schedule_salary_review(current_user.id, first_review_date)
    
    db.commit()
    
    return {"message": "Career tracking started!", "next_review": first_review_date}
```

---

### Step 4: Downgrade from PRO to CAREER

```
Email sent to user:
From: JobScale
Subject: Congrats on the new role! 🎉 + Special offer

Content:
┌─────────────────────────────────────────────┐
│  🎉 Congratulations on Your New Role!      │
│                                             │
│  We're thrilled you got the job!           │
│                                             │
│  Special Offer:                            │
│  Downgrade to CAREER tier for just         │
│  $149/year (save 57% vs monthly)           │
│                                             │
│  What you get:                             │
│  ✅ Quarterly salary reviews               │
│  ✅ Promotion readiness alerts             │
│  ✅ Passive job alerts (quality > qty)    │
│  ✅ Annual career report                   │
│  ✅ Negotiation coaching                   │
│                                             │
│  [Downgrade to CAREER - $149/year]        │
│  [Keep PRO - $29/month]                   │
│  [Cancel Subscription]                     │
└─────────────────────────────────────────────┘

User clicks: "Downgrade to CAREER - $149/year"

Frontend:
POST /api/v1/billing/downgrade
{
  "from_plan": "pro",
  "to_plan": "career_annual",
  "effective_date": "2026-04-09"  # End of current billing cycle
}

Backend (Stripe integration):
@billing_router.post("/downgrade")
async def downgrade_plan(downgrade_data, current_user):
    # 1. Cancel current PRO subscription at period end
    stripe.Subscription.modify(
        current_user.stripe_subscription_id,
        cancel_at_period_end=True
    )
    
    # 2. Create new CAREER annual subscription
    career_price_id = "price_career_annual_149"
    new_subscription = stripe.Subscription.create(
        customer=current_user.stripe_customer_id,
        items=[{"price": career_price_id}],
        trial_period_days=0  # Start immediately after PRO ends
    )
    
    # 3. Update user record
    current_user.subscription_plan = "career"
    current_user.subscription_cycle = "annual"
    current_user.career_started_at = datetime.now()
    
    db.commit()
    
    # 4. Send confirmation
    send_career_tier_welcome_email(current_user)
    
    return {"new_plan": "career_annual", "next_billing": new_subscription.current_period_end}
```

---

## PHASE 2: CAREER TRACKING (Months 1-12)

### Step 5: Quarterly Salary Review (Automated)

```
Background Task (Celery):
@celery.task
def run_quarterly_salary_reviews():
    # Find all users due for review
    due_users = db.query(User).filter(
        User.career_started_at != None,
        User.next_salary_review_date <= datetime.now()
    ).all()
    
    for user in due_users:
        generate_salary_review(user)

def generate_salary_review(user):
    # 1. Get current role info
    career = db.query(CareerProgress).filter(
        CareerProgress.user_id == user.id
    ).first()
    
    # 2. Query salary benchmarks
    benchmarks = db.query(SalaryBenchmark).filter(
        SalaryBenchmark.role == career.current_title,
        SalaryBenchmark.location == career.location,
        SalaryBenchmark.experience_level == career.seniority_level
    ).first()
    
    # 3. Calculate position
    if benchmarks:
        percentile = calculate_percentile(career.salary, benchmarks)
        market_avg = benchmarks.avg_salary
        underpaid_by = ((market_avg - career.salary) / market_avg) * 100
        
        # 4. Generate email
        if underpaid_by > 10:
            urgency = "high"
            subject = f"⚠️ You're {underpaid_by:.0f}% below market!"
        elif underpaid_by > 0:
            urgency = "medium"
            subject = f"💰 Salary Check: {underpaid_by:.0f}% below average"
        else:
            urgency = "low"
            subject = "✅ Your salary is competitive!"
        
        # 5. Send email
        send_salary_review_email(
            to=user.email,
            subject=subject,
            data={
                "current_salary": career.salary,
                "market_avg": market_avg,
                "market_top_25": benchmarks.top_25_salary,
                "percentile": percentile,
                "underpaid_by": underpaid_by,
                "similar_roles": get_similar_roles(career)
            }
        )
        
        # 6. Schedule next review (3 months)
        user.next_salary_review_date = datetime.now() + timedelta(days=90)
        db.commit()
```

**Email User Receives:**

```
From: JobScale <career@jobscale.com>
Subject: ⚠️ You're 13% below market!

Content:
┌─────────────────────────────────────────────┐
│  💰 Your Q2 2026 Salary Review             │
│  ─────────────────────────────────────────  │
│                                             │
│  Your Salary: £80,000                      │
│  Market Average: £92,000                   │
│  Top 25%: £105,000                         │
│                                             │
│  ⚠️ You're 13% below market average!       │
│                                             │
│  Similar Roles (Mid-Level, London):        │
│  - Senior SWE @ GitLab: £95,000           │
│  - Senior SWE @ Monzo: £98,000            │
│  - Senior SWE @ Revolut: £102,000         │
│                                             │
│  Action:                                   │
│  [See 10 Companies Paying More]           │
│  [Download Negotiation Script]            │
│  [Book Salary Coaching - £99]             │
│                                             │
│  Next review: September 2026               │
└─────────────────────────────────────────────┘
```

---

### Step 6: Promotion Readiness Check (Automated)

```
Background Task (Monthly):
@celery.task
def check_promotion_readiness():
    # Find users approaching promotion timeline
    users = db.query(User).join(CareerProgress).filter(
        CareerProgress.months_in_role >= 18,  # 18+ months
        CareerProgress.promotion_alert_sent == False
    ).all()
    
    for user in users:
        readiness = calculate_promotion_readiness(user)
        
        if readiness.score >= 70:
            send_promotion_alert(user, readiness)

def calculate_promotion_readiness(user):
    career = user.career_progress
    profile = user.profile
    
    # Scoring algorithm
    score = 0
    
    # Tenure (30%)
    months = career.months_in_role
    score += min(months / 24, 1.0) * 30
    
    # Skills gained (40%)
    current_level_skills = get_skills_for_level(career.seniority_level)
    next_level_skills = get_skills_for_level(career.next_seniority_level)
    skills_gained = count_matching_skills(profile.skills, next_level_skills)
    score += (skills_gained / len(next_level_skills)) * 40
    
    # Leadership experience (30%)
    leadership_count = count_leadership_projects(user)
    score += min(leadership_count / 3, 1.0) * 30
    
    return PromotionReadiness(
        score=score,
        months_in_role=months,
        skills_gained=skills_gained,
        leadership_count=leadership_count,
        next_level=career.next_seniority_level
    )
```

**Email User Receives:**

```
From: JobScale <career@jobscale.com>
Subject: 🎯 You're Ready for Senior Role!

Content:
┌─────────────────────────────────────────────┐
│  🎉 Promotion Ready!                       │
│  ─────────────────────────────────────────  │
│                                             │
│  Based on your profile:                    │
│  ✅ 20 months at Stripe                    │
│  ✅ Led 3 major projects                   │
│  ✅ Mentored 2 junior engineers            │
│  ✅ System design experience               │
│                                             │
│  Promotion Score: 85/100                   │
│  ████████████████████░░  85%              │
│                                             │
│  Market Opportunity:                       │
│  📈 847 Senior SWE roles (was 423)        │
│  💰 Avg salary: £105,000 (+31%)           │
│                                             │
│  Next Steps:                               │
│  1. Update CV with leadership experience  │
│  2. Apply to 5-10 senior roles            │
│  3. Prepare for system design interviews  │
│                                             │
│  [See Senior Roles] [Get Interview Prep]  │
│  [Book Mock Interview - £99]              │
└─────────────────────────────────────────────┘
```

---

### Step 7: Passive Job Alerts (Weekly)

```
Background Task (Weekly):
@celery.task
def send_passive_job_alerts():
    # Only for CAREER tier users
    career_users = db.query(User).filter(
        User.subscription_plan == "career",
        User.employment_status == "employed"
    ).all()
    
    for user in career_users:
        # Find EXCEPTIONAL opportunities (20%+ better)
        better_jobs = find_quality_opportunities(user)
        
        if better_jobs:
            send_passive_alert(user, better_jobs[:3])  # Max 3 jobs

def find_quality_opportunities(user):
    career = user.career_progress
    
    # Query for roles that are 20%+ better
    min_salary = career.salary * 1.20  # 20% increase
    
    jobs = db.query(Job).filter(
        Job.salary_min >= min_salary,
        Job.seniority_level == career.next_seniority_level,
        Job.posted_date >= datetime.now() - timedelta(days=7)
    ).all()
    
    # Rank by match score
    ranked = []
    for job in jobs:
        match_score = calculate_match_score(user, job)
        if match_score >= 80:  # Only high matches
            ranked.append((job, match_score))
    
    ranked.sort(key=lambda x: x[1], reverse=True)
    return [job for job, score in ranked[:10]]
```

**Email User Receives:**

```
From: JobScale <career@jobscale.com>
Subject: 3 Exceptional Opportunities This Week

Content:
┌─────────────────────────────────────────────┐
│  🎯 Curated for You (This Week)           │
│  ─────────────────────────────────────────  │
│                                             │
│  Only showing roles 20%+ better than      │
│  your current £80k salary:                 │
│                                             │
│  ⭐ Staff Engineer @ Stripe               │
│     £130,000 (+62%)                        │
│     Your network: 3 connections            │
│     Match: 94%                             │
│     [Apply] [Research]                     │
│                                             │
│  ⭐ Senior SWE @ Airbnb (Remote)          │
│     $150,000 (+87%)                        │
│     Relocation support                     │
│     Match: 91%                             │
│     [Apply] [Research]                     │
│                                             │
│  ⭐ Tech Lead @ Startup (Equity)          │
│     £110,000 + 0.5% equity                 │
│     First engineering hire                 │
│     Match: 87%                             │
│     [Apply] [Research]                     │
│                                             │
│  Want more? [Adjust Criteria]             │
└─────────────────────────────────────────────┘
```

---

## PHASE 3: PROMOTION/JOB CHANGE (Month 12-18)

### Step 8: User Gets New Role

```
User action:
- Applies to 2-3 roles via CAREER alerts
- Gets offer: Senior SWE @ GitLab, £100k

User updates in JobScale:
POST /api/v1/career/update-role
{
  "new_company": "GitLab",
  "new_title": "Senior Software Engineer",
  "new_salary": 100000,
  "start_date": "2027-09-01"
}

Backend:
@career_router.post("/update-role")
async def update_role(role_data, current_user):
    career = db.query(CareerProgress).filter(
        CareerProgress.user_id == current_user.id
    ).first()
    
    # 1. Archive old role
    old_role = CareerHistory(
        user_id=current_user.id,
        company=career.current_company,
        title=career.current_title,
        salary=career.current_salary,
        started_at=career.started_at,
        ended_at=datetime.now()
    )
    db.add(old_role)
    
    # 2. Update current role
    career.current_company = role_data.new_company
    career.current_title = role_data.new_title
    career.current_salary = role_data.new_salary
    career.started_at = role_data.start_date
    career.promotions_count += 1
    
    # 3. Calculate career growth
    salary_increase = role_data.new_salary - old_role.salary
    salary_increase_pct = (salary_increase / old_role.salary) * 100
    
    # 4. Success fee check (if JobScale helped)
    if career.used_success_service:
        fee_percentage = 0.05  # 5%
        success_fee = salary_increase * fee_percentage
        
        if success_fee > 0:
            send_success_fee_invoice(current_user, success_fee)
    
    # 5. Send achievement email
    send_career_milestone_email(
        user=current_user,
        milestone="promotion",
        data={
            "old_role": old_role,
            "new_role": career,
            "salary_increase": salary_increase,
            "salary_increase_pct": salary_increase_pct
        }
    )
    
    # 6. Reset review cycle
    career.next_salary_review_date = datetime.now() + timedelta(days=90)
    
    db.commit()
    
    return {
        "message": "Career updated!",
        "salary_increase": salary_increase,
        "total_growth": calculate_total_growth(current_user)
    }
```

---

### Step 9: Annual Career Report (Automated)

```
Background Task (Yearly, on career anniversary):
@celery.task
def generate_annual_career_reports():
    users = db.query(User).filter(
        User.career_started_at != None
    ).all()
    
    for user in users:
        # Check if anniversary month
        if is_career_anniversary(user):
            report = generate_career_report(user)
            send_annual_report_email(user, report)

def generate_career_report(user):
    career = user.career_progress
    history = db.query(CareerHistory).filter(
        CareerHistory.user_id == user.id
    ).all()
    
    # Calculate metrics
    total_growth = calculate_total_salary_growth(user)
    promotions = len(history)
    skills_gained = count_new_skills_this_year(user)
    market_percentile = get_market_percentile(user)
    
    # Generate PDF
    pdf = generate_pdf_report(
        template="annual_career_report",
        data={
            "user": user,
            "year": datetime.now().year,
            "current_role": career,
            "career_history": history,
            "total_growth": total_growth,
            "promotions": promotions,
            "skills_gained": skills_gained,
            "market_percentile": market_percentile,
            "next_year_goals": get_suggested_goals(user)
        }
    )
    
    return {
        "pdf_url": save_pdf(pdf),
        "summary": {
            "salary_growth": total_growth,
            "promotions": promotions,
            "market_position": market_percentile
        }
    }
```

**Email User Receives:**

```
From: JobScale <career@jobscale.com>
Subject: Your 2026 Annual Career Report 📊

Content:
┌─────────────────────────────────────────────┐
│  📊 Your 2026 Career Report                │
│  ─────────────────────────────────────────  │
│                                             │
│  This Year's Achievements:                 │
│  ✅ Promoted: SWE → Senior SWE            │
│  ✅ Salary: £80k → £100k (+25%)           │
│  ✅ Led 3 major projects                   │
│  ✅ Mentored 2 junior engineers            │
│  ✅ Skills gained: 6                       │
│                                             │
│  Market Position:                          │
│  📈 You're now in top 40% for your level  │
│  💰 Salary is at market average            │
│  🎯 Ready for Staff level in 12-18 months │
│                                             │
│  Career Trajectory:                        │
│  2024: Junior SWE · £60k                  │
│  2025: SWE · £80k                         │
│  2026: Senior SWE · £100k                 │
│  2027: Staff SWE · £130k (projected)      │
│                                             │
│  [Download PDF Report]                     │
│  [Share on LinkedIn]                       │
│  [Set 2027 Goals]                          │
└─────────────────────────────────────────────┘
```

---

## 🗄️ DATABASE SCHEMA

### New Models Required

```python
# backend/app/models/career.py

class CareerProgress(Base, TimestampMixin):
    """Tracks user's current career progression"""
    __tablename__ = "career_progress"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Current role
    current_company = Column(String)
    current_title = Column(String)
    current_salary = Column(Integer)
    currency = Column(String, default="GBP")
    seniority_level = Column(String)  # junior, mid, senior, staff, principal
    started_at = Column(DateTime)
    location = Column(String)
    
    # Progress tracking
    next_seniority_level = Column(String)
    months_in_role = Column(Integer, default=0)
    promotions_count = Column(Integer, default=0)
    skills_gained = Column(JSON)  # List of skills gained this role
    leadership_projects = Column(Integer, default=0)
    
    # Review cycle
    next_salary_review_date = Column(DateTime)
    last_anniversary_date = Column(DateTime)
    
    # Success fee tracking
    used_success_service = Column(Boolean, default=False)
    success_fee_owed = Column(Integer)
    
    # Relationships
    user = relationship("User", back_populates="career_progress")
    history = relationship("CareerHistory", back_populates="user")


class CareerHistory(Base, TimestampMixin):
    """Archived career history"""
    __tablename__ = "career_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    company = Column(String)
    title = Column(String)
    salary = Column(Integer)
    currency = Column(String)
    seniority_level = Column(String)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    
    achievements = Column(JSON)  # List of achievements in role
    skills_gained = Column(JSON)
    
    user = relationship("User", back_populates="career_history")


class SalaryBenchmark(Base):
    """Market salary data by role/location/level"""
    __tablename__ = "salary_benchmarks"
    
    id = Column(Integer, primary_key=True)
    role = Column(String, index=True)
    location = Column(String, index=True)
    experience_level = Column(String, index=True)
    
    min_salary = Column(Integer)
    avg_salary = Column(Integer)
    max_salary = Column(Integer)
    top_25_salary = Column(Integer)
    top_10_salary = Column(Integer)
    
    sample_size = Column(Integer)  # Number of data points
    last_updated = Column(DateTime)
    
    source = Column(String)  # "user_data", "public_api", "partner"


class CareerGoal(Base, TimestampMixin):
    """User's career goals"""
    __tablename__ = "career_goals"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    goal_type = Column(String)  # "promotion", "salary", "skills", "company"
    target_title = Column(String)
    target_salary = Column(Integer)
    target_company = Column(String)
    target_date = Column(DateTime)
    
    progress = Column(Integer, default=0)  # 0-100%
    status = Column(String, default="active")  # active, achieved, abandoned
    
    action_items = Column(JSON)  # List of actions to achieve goal
```

---

## 🔌 API ENDPOINTS

### Career Management

```python
# backend/app/api/career.py

@router.post("/start-role")
async def start_new_role(role_data, current_user):
    """Start tracking new career role"""

@router.post("/update-role")
async def update_role(role_data, current_user):
    """Update current role (promotion/job change)"""

@router.get("/dashboard")
async def get_career_dashboard(current_user):
    """Get career dashboard data"""

@router.get("/salary-check")
async def get_salary_check(current_user):
    """Get current salary vs market benchmark"""

@router.get("/progression")
async def get_career_progression(current_user):
    """Get promotion readiness and timeline"""

@router.get("/annual-report")
async def get_annual_report(current_user, year: int):
    """Get annual career report PDF"""

@router.post("/set-goals")
async def set_career_goals(goals_data, current_user):
    """Set career goals for tracking"""

@router.get("/goals")
async def get_career_goals(current_user):
    """Get user's career goals"""
```

---

## 📊 SALARY BENCHMARK DATA

### How We Get Salary Data

```python
# Sources:

1. User-reported data (anonymized, aggregated)
   - When users update their role, they opt-in to share salary
   - Aggregated by role, location, level

2. Public APIs
   - Levels.fyi API (tech salaries)
   - Glassdoor API
   - LinkedIn Salary Insights

3. Job postings
   - Scrape salary ranges from job postings
   - Normalize by role, location, level

4. Partner data
   - Recruiting partners share anonymized offer data
   - Company partnerships
```

**Data Pipeline:**

```python
@celery.task
def update_salary_benchmarks():
    """Update salary benchmarks weekly"""
    
    # 1. Aggregate user data
    user_data = db.query(
        CareerProgress.title,
        CareerProgress.location,
        CareerProgress.seniority_level,
        func.avg(CareerProgress.salary),
        func.min(CareerProgress.salary),
        func.max(CareerProgress.salary),
        func.count(CareerProgress.id)
    ).group_by(
        CareerProgress.title,
        CareerProgress.location,
        CareerProgress.seniority_level
    ).all()
    
    # 2. Fetch from external APIs
    levels_fyi_data = fetch_levels_fyi_data()
    glassdoor_data = fetch_glassdoor_data()
    
    # 3. Merge and update benchmarks
    for role, location, level, avg, min, max, count in user_data:
        benchmark = db.query(SalaryBenchmark).filter(
            SalaryBenchmark.role == role,
            SalaryBenchmark.location == location,
            SalaryBenchmark.experience_level == level
        ).first()
        
        if benchmark:
            # Update with weighted average
            benchmark.avg_salary = (benchmark.avg_salary * benchmark.sample_size + avg * count) / (benchmark.sample_size + count)
            benchmark.sample_size += count
            benchmark.last_updated = datetime.now()
        else:
            # Create new benchmark
            benchmark = SalaryBenchmark(
                role=role,
                location=location,
                experience_level=level,
                avg_salary=avg,
                min_salary=min,
                max_salary=max,
                sample_size=count
            )
            db.add(benchmark)
    
    db.commit()
```

---

## 💰 SUCCESS FEE IMPLEMENTATION

```python
# backend/app/api/career_success.py

@router.post("/engage-success-service")
async def engage_success_service(service_data, current_user):
    """User opts in to success fee service"""
    
    career = current_user.career_progress
    career.used_success_service = True
    career.success_fee_percentage = 0.05  # 5%
    career.success_fee_baseline_salary = career.current_salary
    
    db.commit()
    
    # Send contract
    send_success_fee_contract(current_user)
    
    return {"message": "Success service engaged!"}


@router.post("/report-new-offer")
async def report_new_offer(offer_data, current_user):
    """User reports new job offer"""
    
    career = current_user.career_progress
    
    if career.used_success_service:
        salary_increase = offer_data.salary - career.success_fee_baseline_salary
        
        if salary_increase > 0:
            success_fee = salary_increase * career.success_fee_percentage
            
            # Check if fee applies (20%+ increase)
            increase_pct = (salary_increase / career.success_fee_baseline_salary) * 100
            
            if increase_pct >= 20:
                send_success_fee_invoice(current_user, success_fee)
                
                return {
                    "success_fee_applicable": True,
                    "fee_amount": success_fee,
                    "salary_increase": salary_increase,
                    "increase_percentage": increase_pct
                }
            else:
                return {
                    "success_fee_applicable": False,
                    "reason": "Increase less than 20%"
                }
    
    return {"success_fee_applicable": False}
```

---

## ✅ SUMMARY

### Technical Flow

```
1. User gets job → Updates application status → Career tracking starts
2. PRO → CAREER downgrade → Annual subscription
3. Quarterly: Automated salary review emails
4. Monthly: Promotion readiness checks
5. Weekly: Passive job alerts (quality > quantity)
6. Yearly: Annual career report PDF
7. Job change: Update role, track growth, success fee if applicable
```

### Database Changes

- 4 new models: CareerProgress, CareerHistory, SalaryBenchmark, CareerGoal
- User model: Add subscription_plan, employment_status, career_started_at
- Application model: Add offer_details JSON field

### API Endpoints

- 8 new career endpoints
- 1 billing downgrade endpoint
- 1 success fee endpoint

### Background Tasks

- Quarterly salary reviews (Celery)
- Monthly promotion checks (Celery)
- Weekly passive alerts (Celery)
- Yearly annual reports (Celery)
- Weekly salary benchmark updates (Celery)

---

*This is how it actually works, technically.* 🚀
