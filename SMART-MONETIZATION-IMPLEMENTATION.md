# 🚀 SMART MONETIZATION - IMPLEMENTATION PLAN

**Date:** 2026-03-09  
**Status:** Ready to Build  
**Timeline:** 4-5 weeks

---

## 📋 OVERVIEW

**Goal:** Implement pure subscription monetization with smart upgrade triggers

**Key Features:**
- 3-tier pricing (FREE, PRO $29/mo, CAREER $19/mo or $149/yr)
- Blurred data for FREE users (teaser strategy)
- Smart email triggers (FOMO, curiosity, timing)
- Career tracking dashboard
- Quarterly salary reviews (automated)
- Promotion readiness alerts
- Annual career reports

---

## 🗄️ PHASE 1: DATABASE MODELS (Week 1)

### New Models (4 files)

**1. `backend/app/models/career.py`**
```python
- CareerProgress (current role tracking)
- CareerHistory (archived roles)
- SalaryBenchmark (market data)
- CareerGoal (user goals)
```

**2. `backend/app/models/__init__.py`**
```python
- Import new models
- Update model registry
```

**3. Database Migration**
```bash
alembic revision --autogenerate -m "Add career tracking models"
alembic upgrade head
```

**4. Update User Model**
```python
- subscription_plan: str (free/pro/career)
- subscription_cycle: str (monthly/annual)
- employment_status: str (unemployed/employed)
- career_started_at: datetime
- next_salary_review_date: datetime
```

**Deliverables:**
- ✅ 4 new database tables
- ✅ User model updated
- ✅ Migration scripts
- ✅ Model tests

---

## 🔌 PHASE 2: API ENDPOINTS (Week 2)

### Career Management API

**File: `backend/app/api/career.py`**

**Endpoints:**
```python
POST   /api/v1/career/start-role          # Start tracking new role
POST   /api/v1/career/update-role         # Update after promotion
GET    /api/v1/career/dashboard           # Get career dashboard
GET    /api/v1/career/salary-check        # Get salary vs market (blurred for FREE)
GET    /api/v1/career/progression         # Get promotion readiness
GET    /api/v1/career/annual-report       # Get annual report PDF
POST   /api/v1/career/set-goals          # Set career goals
GET    /api/v1/career/goals              # Get user goals
```

**Key Logic:**
```python
# Blurred data for FREE users
@career_router.get("/salary-check")
async def get_salary_check(current_user):
    if current_user.subscription_plan == "free":
        return teaser_data()  # Blurred
    else:
        return full_data()    # Complete
```

### Billing Updates

**File: `backend/app/api/billing.py`**

**New Endpoints:**
```python
POST   /api/v1/billing/upgrade            # Handle plan upgrades
GET    /api/v1/billing/upgrade/success    # Success callback
POST   /api/v1/billing/downgrade          # PRO → CAREER
```

**Stripe Integration:**
```python
- Create price IDs for CAREER tier
- Handle upgrade/downgrade flows
- Webhook for subscription changes
```

**Deliverables:**
- ✅ 8 career endpoints
- ✅ 3 billing endpoints
- ✅ Blurred data logic
- ✅ API tests

---

## 📧 PHASE 3: EMAIL SYSTEM (Week 3)

### Email Templates (6 templates)

**1. `salary_check_teaser.html`** (FREE users)
```
Shows: Current salary
Blurs: Market avg, top 25%, similar roles
CTA: Unlock Full Report - $149/year
```

**2. `salary_check_full.html`** (PRO/CAREER users)
```
Shows: Everything
CTA: None (value reinforcement)
```

**3. `promotion_readiness_teaser.html`** (PRO users)
```
Shows: Readiness score, months, opportunity count
Blurs: Salary data
CTA: Get Salary Data - CAREER $149/yr
```

**4. `promotion_readiness_full.html`** (CAREER users)
```
Shows: Everything including salary benchmarks
CTA: See Senior Roles
```

**5. `network_fomo.html`** (FREE users)
```
Shows: Promotion stats, average increase
Blurs: Company names, specific salaries
CTA: See What They Did - Upgrade
```

**6. `annual_report_teaser.html`** (FREE users)
```
Shows: Basic summary (company, salary, apps sent)
Blurs: Growth analysis, projections, PDF
CTA: Unlock Full Report - CAREER
```

### Email Scheduler

**File: `backend/app/services/email_scheduler.py`**

```python
class EmailScheduler:
    def schedule_for_user(self, user):
        if user.plan == "free":
            schedule_monthly("salary_check_teaser")
            schedule_monthly("network_fomo")
            schedule_quarterly("career_review_teaser")
            schedule_yearly("annual_report_teaser")
        
        elif user.plan == "pro":
            schedule_monthly("promotion_readiness_teaser")
            schedule_quarterly("salary_check_full")
        
        elif user.plan == "career":
            schedule_monthly("passive_job_alerts")
            schedule_quarterly("salary_check_full")
            schedule_yearly("annual_report_full")
```

### Upgrade Trigger Service

**File: `backend/app/services/upgrade_triggers.py`**

```python
class UpgradeTriggerService:
    def send_salary_check_teaser(self, user)
    def send_promotion_readiness_teaser(self, user)
    def send_network_fomo(self, user)
    def send_passive_alert_teaser(self, user)
```

**Deliverables:**
- ✅ 6 email templates
- ✅ Email scheduler
- ✅ Upgrade trigger service
- ✅ Email tests

---

## ⚙️ PHASE 4: BACKGROUND TASKS (Week 4)

### Celery Tasks

**File: `backend/app/tasks/career_tasks.py`**

**Tasks:**
```python
@celery.task
def run_quarterly_salary_reviews():
    """Send salary review emails to all due users"""
    
@celery.task
def check_promotion_readiness():
    """Alert users ready for promotion (18+ months)"""

@celery.task
def send_passive_job_alerts():
    """Send 3 quality opportunities to CAREER users"""

@celery.task
def generate_annual_career_reports():
    """Generate PDF reports for career anniversaries"""

@celery.task
def update_salary_benchmarks():
    """Aggregate user data + external APIs weekly"""

@celery.task
def schedule_user_emails():
    """Schedule monthly/quarterly/yearly emails"""
```

### Scheduler Configuration

**File: `backend/app/core/scheduler.py`**

```python
CELERY_BEAT_SCHEDULE = {
    "quarterly-reviews": {
        "task": "run_quarterly_salary_reviews",
        "schedule": crontab(minute=0, hour=9, day_of_month="1/3"),  # Every 3 months
    },
    "promotion-checks": {
        "task": "check_promotion_readiness",
        "schedule": crontab(minute=0, hour=10, day_of_month=1),  # Monthly
    },
    "passive-alerts": {
        "task": "send_passive_job_alerts",
        "schedule": crontab(minute=0, hour=11, day_of_week=1),  # Weekly
    },
    "annual-reports": {
        "task": "generate_annual_career_reports",
        "schedule": crontab(minute=0, hour=9, day_of_month=1, month_of_year=1),  # Yearly
    },
    "benchmark-updates": {
        "task": "update_salary_benchmarks",
        "schedule": crontab(minute=0, hour=2, day_of_week=0),  # Weekly
    },
}
```

**Deliverables:**
- ✅ 6 Celery tasks
- ✅ Scheduler configuration
- ✅ Task tests

---

## 🎨 PHASE 5: FRONTEND (Week 5)

### Career Dashboard

**File: `frontend/src/app/career/page.tsx`**

**Components:**
```tsx
- CareerOverview (current role, tenure, salary)
- SalaryBenchmark (market comparison - blurred for FREE)
- PromotionReadiness (score, timeline)
- CareerGoals (set and track goals)
- AnnualReports (download PDFs)
```

**Features:**
```tsx
- Blurred data for FREE users
- Upgrade prompts inline
- Progress visualizations
- Goal tracking
```

### Upgrade Flow

**File: `frontend/src/app/billing/upgrade/page.tsx`**

**Components:**
```tsx
- PlanComparison (FREE vs PRO vs CAREER)
- UpgradeForm (Stripe checkout)
- SuccessMessage (post-upgrade)
```

### Email Landing Pages

**Files:**
```tsx
- frontend/src/app/career/salary-check/page.tsx
- frontend/src/app/career/promotion/page.tsx
- frontend/src/app/career/annual-report/page.tsx
```

**Purpose:** When users click email CTAs, land on dedicated pages with upgrade prompts

**Deliverables:**
- ✅ Career dashboard page
- ✅ Upgrade flow
- ✅ Email landing pages
- ✅ Frontend tests

---

## 💳 PHASE 6: STRIPE CONFIGURATION (Week 5)

### Price IDs

**Create in Stripe Dashboard:**
```
price_pro_monthly_29       - PRO $29/month
price_career_monthly_19    - CAREER $19/month
price_career_annual_149    - CAREER $149/year
```

### Webhook Handler

**File: `backend/app/api/billing_webhooks.py`**

```python
@router.post("/webhooks/stripe")
async def handle_stripe_webhook(event: stripe.Event):
    if event.type == "customer.subscription.updated":
        update_user_subscription(event.data.object)
    elif event.type == "checkout.session.completed":
        handle_successful_upgrade(event.data.object)
```

**Deliverables:**
- ✅ 3 Stripe price IDs
- ✅ Webhook handler
- ✅ Integration tests

---

## 📊 PHASE 7: SALARY BENCHMARK DATA (Ongoing)

### Data Sources

**1. User-Reported (Opt-in)**
```python
# When users update role, ask to share salary
if user.opt_in_data_sharing:
    aggregate_salary_data(user)
```

**2. External APIs**
```python
- Levels.fyi API (tech salaries)
- Glassdoor API
- LinkedIn Salary Insights
```

**3. Job Postings**
```python
# Extract salary ranges from scraped jobs
def extract_salary_from_job(job):
    if job.salary_min and job.salary_max:
        return (job.salary_min + job.salary_max) / 2
```

### Benchmark Aggregation

**File: `backend/app/services/benchmark_service.py`**

```python
class BenchmarkService:
    def get_benchmark(self, role, location, level):
        benchmark = db.query(SalaryBenchmark).filter(
            role=role, location=location, experience_level=level
        ).first()
        
        if not benchmark:
            # Fetch from external APIs
            benchmark = self.fetch_from_apis(role, location, level)
        
        return benchmark
```

**Deliverables:**
- ✅ Benchmark service
- ✅ External API integrations
- ✅ Data aggregation pipeline

---

## ✅ DELIVERABLES CHECKLIST

### Phase 1: Database (Week 1)
- [ ] `backend/app/models/career.py` (4 models)
- [ ] `backend/app/models/__init__.py` (updated imports)
- [ ] User model updated (subscription fields)
- [ ] Alembic migration created
- [ ] Migration tested

### Phase 2: API (Week 2)
- [ ] `backend/app/api/career.py` (8 endpoints)
- [ ] `backend/app/api/billing.py` (3 endpoints)
- [ ] Blurred data logic implemented
- [ ] API tests written
- [ ] API documented

### Phase 3: Email (Week 3)
- [ ] 6 email templates created
- [ ] `backend/app/services/email_scheduler.py`
- [ ] `backend/app/services/upgrade_triggers.py`
- [ ] Email tests written
- [ ] Email sending tested

### Phase 4: Background Tasks (Week 4)
- [ ] `backend/app/tasks/career_tasks.py` (6 tasks)
- [ ] `backend/app/core/scheduler.py` (Celery Beat config)
- [ ] Task tests written
- [ ] Tasks tested manually

### Phase 5: Frontend (Week 5)
- [ ] `frontend/src/app/career/page.tsx` (dashboard)
- [ ] `frontend/src/app/billing/upgrade/page.tsx`
- [ ] 3 email landing pages
- [ ] Blurred data UI components
- [ ] Frontend tests written

### Phase 6: Stripe (Week 5)
- [ ] 3 price IDs created
- [ ] `backend/app/api/billing_webhooks.py`
- [ ] Upgrade flow tested end-to-end
- [ ] Webhook tested

### Phase 7: Benchmarks (Ongoing)
- [ ] `backend/app/services/benchmark_service.py`
- [ ] External API integrations
- [ ] Initial data populated
- [ ] Weekly update task working

---

## 🎯 TESTING STRATEGY

### Unit Tests
```bash
# Models
pytest tests/models/test_career.py

# API
pytest tests/api/test_career.py
pytest tests/api/test_billing.py

# Services
pytest tests/services/test_upgrade_triggers.py
pytest tests/services/test_email_scheduler.py

# Tasks
pytest tests/tasks/test_career_tasks.py
```

### Integration Tests
```bash
# Full flow: FREE user → Salary check teaser → Upgrade → Full data
pytest tests/integration/test_upgrade_flow.py

# Email scheduling
pytest tests/integration/test_email_scheduling.py

# Background tasks
pytest tests/integration/test_celery_tasks.py
```

### Manual Testing
```
1. Create FREE user account
2. Start career tracking
3. Receive salary check teaser email
4. Click upgrade CTA
5. Complete Stripe checkout
6. Verify full data unlocked
7. Verify CAREER features accessible
```

---

## 📈 SUCCESS METRICS

### Technical
- [ ] All API endpoints return 200 OK
- [ ] Email delivery rate > 95%
- [ ] Celery tasks complete without errors
- [ ] Blurred data logic working correctly
- [ ] Stripe webhooks processed successfully

### Business
- [ ] FREE → Paid conversion: 25%+
- [ ] PRO → CAREER conversion: 50%+
- [ ] CAREER annual retention: 70%+
- [ ] Email open rate: 40%+
- [ ] Email CTR: 10%+

---

## 🚀 DEPLOYMENT

### Environment Variables
```bash
# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email
RESEND_API_KEY=re_...

# Career Features
CAREER_ENABLED=true
SALARY_BENCHMARK_ENABLED=true
```

### Deployment Steps
```bash
# 1. Run migrations
alembic upgrade head

# 2. Seed initial benchmark data
python -m backend.app.services.seed_benchmarks

# 3. Start Celery Beat
celery -A backend.app.core.celery beat --loglevel=info

# 4. Start Celery Worker
celery -A backend.app.core.celery worker --loglevel=info

# 5. Deploy frontend
cd frontend && npm run build && vercel deploy

# 6. Deploy backend
railway up
```

---

## ⚠️ RISKS & MITIGATIONS

### Risk 1: Insufficient Benchmark Data
**Mitigation:** Start with Levels.fyi API, aggregate user data over time

### Risk 2: Email Spam Complaints
**Mitigation:** Limit to 1-2 emails/month, clear unsubscribe option

### Risk 3: Low Conversion Rate
**Mitigation:** A/B test email copy, optimize teaser blur strategy

### Risk 4: Stripe Integration Issues
**Mitigation:** Test thoroughly in Stripe test mode, monitor webhooks

### Risk 5: Celery Task Failures
**Mitigation:** Add retry logic, monitoring, alerting

---

## 📝 DOCUMENTATION

### Files to Create
- [ ] `CAREER-API.md` - API documentation
- [ ] `EMAIL-TEMPLATES.md` - Email template guide
- [ ] `CELERY-TASKS.md` - Background task documentation
- [ ] `STRIPE-SETUP.md` - Stripe configuration guide
- [ ] `UPGRADE-FLOW.md` - User upgrade journey

### Files to Update
- [ ] `README.md` - Add career features
- [ ] `COMPLETE-USER-FLOW-2026.md` - Add monetization flow
- [ ] `PRODUCTION-DEPLOYMENT-GUIDE.md` - Add career deployment

---

## 🎉 SUMMARY

**Timeline:** 4-5 weeks  
**Phases:** 7 (Database, API, Email, Tasks, Frontend, Stripe, Benchmarks)  
**Deliverables:** 20+ files, 15+ endpoints, 6 email templates, 6 Celery tasks

**Start Date:** 2026-03-09  
**Target Completion:** 2026-04-13

---

*Let's build this.* 🚀
