# 🤖 JobScale - Fully Automated Application System

## Goal

**User selects jobs → Everything else is automatic**

No manual visiting, no manual form filling, no manual submitting.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  User Dashboard                                         │
│  ─────────────────────────────────────────────────     │
│  [ ] Software Engineer @ Stripe  ✅ 85%  [Select]      │
│  [ ] Senior Dev @ GitLab        ✅ 78%  [Select]      │
│  [ ] Backend @ Monzo            ✅ 72%  [Select]      │
│                                                         │
│  Selected: 3 jobs                                       │
│  [ 🚀 Apply to All Selected ]                          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Backend Automation Service                             │
│  ─────────────────────────────────────────────────      │
│  • Gets selected jobs from queue                        │
│  • Launches headless browsers                           │
│  • Visits each job URL                                  │
│  • Auto-fills forms                                     │
│  • Uploads CV                                           │
│  • Submits application                                  │
│  • Tracks status                                        │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  Job Sites (Indeed, LinkedIn, Company Sites)           │
│  ─────────────────────────────────────────────────      │
│  • Receive applications                                 │
│  • Send confirmation emails                             │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Technical Implementation

### 1. Job Queue System

```python
# backend/app/services/application_queue.py

from celery import Celery
from playwright.async_api import async_playwright

celery_app = Celery('jobscale', broker='redis://localhost:6379/0')

@celery_app.task(bind=True, max_retries=3)
def apply_to_job(self, application_id: str):
    """Apply to a single job"""
    
    try:
        # Get application + job details
        application = db.applications.find_one({"_id": application_id})
        job = db.jobs.find_one({"_id": application.job_id})
        user = db.users.find_one({"_id": application.user_id})
        
        # Get CV
        cv = db.cvs.find_one({"_id": application.resume_id})
        cv_path = download_cv(cv)
        
        # Launch browser
        import asyncio
        result = asyncio.run(automate_application(job, user, cv_path))
        
        # Update status
        if result["success"]:
            db.applications.update_one(
                {"_id": application_id},
                {"$set": {"status": "applied", "applied_at": datetime.now()}}
            )
            
            # Send email to user
            send_email(
                to=user.email,
                subject=f"✅ Applied to {job.title} at {job.company}",
                body=f"Successfully applied to {job.title} at {job.company}!"
            )
        else:
            db.applications.update_one(
                {"_id": application_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": result["error"]
                    }
                }
            )
            
        return result
        
    except Exception as e:
        # Retry logic
        raise self.retry(exc=e, countdown=300)  # Retry in 5 minutes
```

---

### 2. Browser Automation

```python
# backend/app/services/automation/browser.py

from playwright.async_api import async_playwright

async def automate_application(job, user, cv_path):
    """Automate job application"""
    
    async with async_playwright() as p:
        # Launch browser with anti-detection
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        # Create context with realistic fingerprint
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            locale='en-GB',
            timezone_id='Europe/London'
        )
        
        page = await context.new_page()
        
        try:
            # Navigate to job
            await page.goto(job.url, wait_until='networkidle', timeout=30000)
            
            # Detect site and use appropriate adapter
            if 'indeed.com' in job.url:
                result = await apply_indeed(page, job, user, cv_path)
            elif 'linkedin.com' in job.url:
                result = await apply_linkedin(page, job, user, cv_path)
            elif 'greenhouse.io' in job.url:
                result = await apply_greenhouse(page, job, user, cv_path)
            elif 'lever.co' in job.url:
                result = await apply_lever(page, job, user, cv_path)
            else:
                result = await apply_generic(page, job, user, cv_path)
            
            return result
            
        except Exception as e:
            # Take screenshot for debugging
            await page.screenshot(path=f'/tmp/error_{job.id}.png')
            return {'success': False, 'error': str(e)}
            
        finally:
            await browser.close()
```

---

### 3. Indeed Adapter (Fully Automated)

```python
# backend/app/services/automation/indeed_adapter.py

async def apply_indeed(page, job, user, cv_path):
    """Fully automated Indeed application"""
    
    try:
        # Step 1: Click "Apply Now"
        apply_button = await page.wait_for_selector(
            '#indeedApplyButton, [data-testid="indeed-apply-button"]',
            timeout=5000
        )
        await apply_button.click()
        
        # Step 2: Wait for modal
        await page.wait_for_selector('#indeedApplyContainer', timeout=10000)
        
        # Step 3: Fill personal info
        await safe_fill(page, 'input[name="firstName"]', user.first_name)
        await safe_fill(page, 'input[name="lastName"]', user.last_name)
        await safe_fill(page, 'input[name="email"]', user.email)
        await safe_fill(page, 'input[name="phone"]', user.phone)
        
        # Step 4: Fill experience (if asked)
        if await page.is_visible('input[name="currentEmployer"]', timeout=2000):
            await safe_fill(page, 'input[name="currentEmployer"]', user.current_company)
            await safe_fill(page, 'input[name="currentTitle"]', user.current_title)
        
        # Step 5: Upload CV
        file_input = await page.query_selector('input[type="file"]')
        if file_input:
            await file_input.set_input_files(cv_path)
            await page.wait_for_timeout(2000)  # Wait for upload
        
        # Step 6: Answer screening questions (if any)
        await handle_screening_questions(page)
        
        # Step 7: Submit
        submit_button = await page.wait_for_selector(
            'button[type="submit"], [data-testid="submit-application"]',
            timeout=5000
        )
        await submit_button.click()
        
        # Step 8: Wait for confirmation
        try:
            await page.wait_for_selector(
                '.application-success, [data-testid="application-success"]',
                timeout=10000
            )
            return {'success': True, 'external_id': extract_application_id(page)}
        except:
            # Some sites don't show success page but still submit
            return {'success': True, 'note': 'No confirmation page but no errors'}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def safe_fill(page, selector, value):
    """Safely fill a field"""
    try:
        element = await page.wait_for_selector(selector, timeout=3000)
        await element.fill(value)
    except:
        pass  # Field not found, skip

async def handle_screening_questions(page):
    """Handle Indeed screening questions"""
    
    # Check for screening questions
    questions = await page.query_selector_all('.screening-question')
    
    for question in questions:
        # Auto-select positive answers
        yes_button = await question.query_selector('text="Yes"')
        if yes_button:
            await yes_button.click()
        
        # Or select first option for dropdowns
        dropdown = await question.query_selector('select')
        if dropdown:
            await dropdown.select_option(index=1)
        
        # Or fill text fields with reasonable answers
        text_field = await question.query_selector('input[type="text"]')
        if text_field:
            await text_field.fill('Available immediately')
```

---

### 4. LinkedIn Adapter (Easy Apply)

```python
# backend/app/services/automation/linkedin_adapter.py

async def apply_linkedin(page, job, user, cv_path):
    """Automated LinkedIn Easy Apply"""
    
    try:
        # Step 1: Check if Easy Apply available
        easy_apply_btn = await page.query_selector(
            'button.jobs-apply-button:has-text("Easy Apply")'
        )
        
        if not easy_apply_btn:
            return {'success': False, 'error': 'Not an Easy Apply job'}
        
        await easy_apply_btn.click()
        
        # Step 2: Wait for modal
        await page.wait_for_selector('.jobs-easy-apply-modal', timeout=10000)
        
        # Step 3: Navigate through steps
        while True:
            # Check if on review step
            submit_btn = await page.query_selector(
                'button[aria-label="Submit application"]'
            )
            
            if submit_btn:
                # Final step - submit
                await submit_btn.click()
                await page.wait_for_timeout(3000)
                return {'success': True}
            
            # Fill current step
            await fill_linkedin_step(page, user, cv_path)
            
            # Click next
            next_btn = await page.query_selector('button[aria-label="Next"]')
            if next_btn:
                await next_btn.click()
                await page.wait_for_timeout(1000)
            else:
                break
        
        return {'success': False, 'error': 'Could not complete application'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def fill_linkedin_step(page, user, cv_path):
    """Fill LinkedIn Easy Apply step"""
    
    # Check for file upload
    file_input = await page.query_selector('input[type="file"]')
    if file_input:
        await file_input.set_input_files(cv_path)
        await page.wait_for_timeout(2000)
    
    # Check for phone field
    phone_field = await page.query_selector('input[aria-label*="phone"]')
    if phone_field:
        await phone_field.fill(user.phone)
    
    # Check for text fields (auto-fill with reasonable defaults)
    text_fields = await page.query_selector_all('input[type="text"]')
    for field in text_fields:
        label = await field.get_attribute('aria-label')
        if label and 'resume' in label.lower():
            continue  # Skip, already handled
        await field.fill('Please see my CV for details')
    
    # Check for dropdowns (select first option)
    selects = await page.query_selector_all('select')
    for select in selects:
        await select.select_option(index=1)
```

---

### 5. Greenhouse/Lever Adapters

```python
# backend/app/services/automation/greenhouse_adapter.py

async def apply_greenhouse(page, job, user, cv_path):
    """Greenhouse applications are usually straightforward"""
    
    try:
        # Find form
        form = await page.wait_for_selector('form#application_form', timeout=10000)
        
        # Fill personal info
        await safe_fill(page, 'input[name="name"]', f"{user.first_name} {user.last_name}")
        await safe_fill(page, 'input[name="email"]', user.email)
        await safe_fill(page, 'input[name="phone"]', user.phone)
        
        # Upload CV
        file_input = await page.query_selector('input[type="file"]')
        if file_input:
            await file_input.set_input_files(cv_path)
            await page.wait_for_timeout(2000)
        
        # Fill optional fields
        await safe_fill(page, 'textarea[name="note"]', 
            f"I'm very interested in this {job.title} position at {job.company}. "
            f"Please see my attached CV for details.")
        
        # Submit
        submit_btn = await page.wait_for_selector(
            'input[type="submit"], button[type="submit"]',
            timeout=5000
        )
        await submit_btn.click()
        
        # Wait for confirmation
        await page.wait_for_selector('.application_success', timeout=10000)
        
        return {'success': True}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

---

### 6. Anti-Detection Measures

```python
# backend/app/services/automation/stealth.py

async def setup_stealth_browser(playwright):
    """Setup browser with anti-detection"""
    
    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-web-security',
            '--disable-features=ImprovedCookieControls'
        ]
    )
    
    context = await browser.new_context(
        # Realistic user agent
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        
        # Realistic viewport
        viewport={'width': 1920, 'height': 1080},
        
        # Locale/timezone
        locale='en-GB',
        timezone_id='Europe/London',
        
        # Extra headers
        extra_http_headers={
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
    )
    
    # Inject JavaScript to hide automation
    await context.add_init_script("""
        // Hide webdriver
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Mock plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5]
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-GB', 'en']
        });
    """)
    
    return browser, context
```

---

### 7. Proxy Rotation (Critical for Scale)

```python
# backend/app/services/automation/proxy_manager.py

class ProxyManager:
    """Manage proxy rotation to avoid IP bans"""
    
    def __init__(self):
        self.proxies = [
            'http://user:pass@proxy1.com:8080',
            'http://user:pass@proxy2.com:8080',
            'http://user:pass@proxy3.com:8080',
            # Use residential proxies for best results
        ]
        self.current_index = 0
    
    def get_next_proxy(self):
        """Get next proxy in rotation"""
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
    
    async def get_proxy_context(self, playwright):
        """Get browser context with proxy"""
        proxy = self.get_next_proxy()
        
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir='/tmp/browser_profile',
            proxy={'server': proxy},
            headless=True
        )
        
        return context
```

---

### 8. Rate Limiting & Delays

```python
# backend/app/services/automation/rate_limiter.py

import asyncio
from datetime import datetime, timedelta

class RateLimiter:
    """Prevent applying too fast (looks suspicious)"""
    
    def __init__(self, max_per_minute=5, max_per_hour=50):
        self.max_per_minute = max_per_minute
        self.max_per_hour = max_per_hour
        self.applications = []
    
    async def wait_if_needed(self):
        """Wait if rate limit reached"""
        
        now = datetime.now()
        
        # Clean old entries
        self.applications = [
            t for t in self.applications 
            if now - t < timedelta(hours=1)
        ]
        
        # Check hourly limit
        if len(self.applications) >= self.max_per_hour:
            wait_time = 3600  # Wait 1 hour
            await asyncio.sleep(wait_time)
            return
        
        # Check minute limit
        recent = [t for t in self.applications if now - t < timedelta(minutes=1)]
        if len(recent) >= self.max_per_minute:
            wait_time = 60  # Wait 1 minute
            await asyncio.sleep(wait_time)
            return
        
        # Random delay between applications (2-5 seconds)
        import random
        await asyncio.sleep(random.uniform(2, 5))
        
        # Record this application
        self.applications.append(now)
```

---

### 9. Error Handling & Retry Logic

```python
# backend/app/services/automation/error_handler.py

class ApplicationErrorHandler:
    """Handle application failures"""
    
    RETRIABLE_ERRORS = [
        'timeout',
        'network error',
        'connection reset',
        'server error'
    ]
    
    NON_RETRIABLE_ERRORS = [
        'not found',
        'expired job',
        'already applied'
    ]
    
    async def handle_error(self, application, error):
        """Handle application error"""
        
        error_lower = error.lower()
        
        # Check if retriable
        is_retriable = any(e in error_lower for e in self.RETRIABLE_ERRORS)
        
        if is_retriable:
            # Increment retry count
            retry_count = application.get('retry_count', 0)
            
            if retry_count < 3:
                # Schedule retry with exponential backoff
                delay = 300 * (2 ** retry_count)  # 5min, 10min, 20min
                
                db.applications.update_one(
                    {"_id": application["_id"]},
                    {
                        "$set": {
                            "status": "pending",
                            "retry_count": retry_count + 1,
                            "next_retry_at": datetime.now() + timedelta(seconds=delay)
                        }
                    }
                )
                
                # Re-queue
                apply_to_job.apply_async(
                    args=[str(application["_id"])],
                    countdown=delay
                )
            else:
                # Max retries reached
                db.applications.update_one(
                    {"_id": application["_id"]},
                    {
                        "$set": {
                            "status": "failed",
                            "error_message": f"Max retries reached: {error}"
                        }
                    }
                )
        else:
            # Non-retriable error
            db.applications.update_one(
                {"_id": application["_id"]},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": error
                    }
                }
            )
```

---

### 10. Dashboard API

```python
# backend/app/api/applications.py

@router.post("/applications/bulk-apply")
async def bulk_apply(
    job_ids: List[UUID],
    resume_id: UUID = None,
    user: User = Depends(get_current_user)
):
    """Apply to multiple jobs at once"""
    
    applications = []
    
    for job_id in job_ids:
        # Create application record
        app = await db.applications.insert_one({
            "user_id": user.id,
            "job_id": job_id,
            "status": "pending",
            "resume_id": resume_id or user.default_resume_id,
            "selected_at": datetime.now()
        })
        
        # Queue for automation
        apply_to_job.delay(str(app.inserted_id))
        
        applications.append(str(app.inserted_id))
    
    return {
        "queued": len(applications),
        "application_ids": applications,
        "message": f"Queued {len(applications)} applications for automation"
    }


@router.get("/applications/status")
async def get_application_status(user: User = Depends(get_current_user)):
    """Get status of all applications"""
    
    apps = await db.applications.find({"user_id": user.id}).to_list()
    
    # Group by status
    status_counts = {}
    for app in apps:
        status = app["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    
    return {
        "total": len(apps),
        "by_status": status_counts,
        "applications": apps
    }
```

---

## 📊 Dashboard UI

```jsx
function ApplicationDashboard() {
  const [selectedJobs, setSelectedJobs] = useState([]);
  const [applying, setApplying] = useState(false);
  const [status, setStatus] = useState(null);
  
  const handleBulkApply = async () => {
    setApplying(true);
    
    const response = await fetch('/api/v1/applications/bulk-apply', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({
        job_ids: selectedJobs,
        resume_id: user.defaultResumeId
      })
    });
    
    const data = await response.json();
    setStatus(data);
    setApplying(false);
  };
  
  return (
    <div>
      <h1>Job Applications</h1>
      
      <div className="job-list">
        {jobs.map(job => (
          <div key={job.id} className="job-card">
            <input 
              type="checkbox" 
              onChange={() => toggleJob(job.id)}
              checked={selectedJobs.includes(job.id)}
            />
            <h3>{job.title}</h3>
            <p>{job.company}</p>
            <p>✅ {job.match_score}% match</p>
          </div>
        ))}
      </div>
      
      <div className="actions">
        <p>Selected: {selectedJobs.length} jobs</p>
        <button 
          onClick={handleBulkApply}
          disabled={applying || selectedJobs.length === 0}
        >
          {applying ? '🤖 Applying...' : '🚀 Apply to All Selected'}
        </button>
      </div>
      
      {status && (
        <div className="status">
          ✅ Queued {status.queued} applications!
          <p>You'll receive email confirmations as they're submitted.</p>
        </div>
      )}
    </div>
  );
}
```

---

## ⚠️ Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| **CAPTCHA** | Use residential proxies, rotate IPs, add delays |
| **Login Required** | Store user cookies, use session tokens |
| **Multi-step Forms** | Handle each step programmatically |
| **File Uploads** | Download CV, upload via Playwright |
| **Screening Questions** | Auto-select positive answers |
| **Rate Limiting** | Implement delays, proxy rotation |
| **Job Expired** | Check before applying, skip if expired |
| **Already Applied** | Check database, skip duplicates |

---

## 📈 Success Metrics

```python
# Track these metrics
metrics = {
    'total_applications': 0,
    'successful_applications': 0,
    'failed_applications': 0,
    'success_rate': 0,  # successful / total
    
    'by_site': {
        'indeed': {'success': 0, 'failed': 0},
        'linkedin': {'success': 0, 'failed': 0},
        'greenhouse': {'success': 0, 'failed': 0},
        'lever': {'success': 0, 'failed': 0}
    },
    
    'average_time_per_application': 0,  # seconds
    'retry_rate': 0,  # applications that needed retry
}
```

---

## ✅ Summary

### Fully Automated Flow:

```
1. User logs into dashboard
2. Browses 100-200 matched jobs
3. Selects 10-20 jobs to apply to
4. Clicks "🚀 Apply to All Selected"
5. Backend queues applications
6. Automation applies to each job:
   - Visits URL
   - Auto-fills forms
   - Uploads CV
   - Submits
7. User gets email confirmations
8. Dashboard shows status
```

### Key Requirements:

✅ **Store job URLs** in database  
✅ **Playwright automation** for each site  
✅ **Proxy rotation** to avoid bans  
✅ **Rate limiting** (5/min, 50/hour)  
✅ **Error handling** with retries  
✅ **Status tracking** in dashboard  
✅ **Email notifications** on success  

---

*This is how we achieve FULL automation.* 🚀
