# 🎯 JobScale - Job URL Storage & Application Automation

## Core Concept

**Store job URLs → User selects → Automation applies**

Simple as that.

---

## 🗄️ Database Schema

### Jobs Table

```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(50) NOT NULL, -- 'indeed', 'linkedin', 'greenhouse', 'lever'
    source_job_id VARCHAR(255) NOT NULL, -- External job ID
    url TEXT NOT NULL, -- Full job URL
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    country VARCHAR(2), -- 'UK', 'US', etc.
    salary_min INTEGER,
    salary_max INTEGER,
    salary_currency VARCHAR(3),
    employment_type VARCHAR(50), -- 'fulltime', 'parttime', 'contract'
    remote BOOLEAN DEFAULT FALSE,
    description TEXT,
    requirements TEXT[],
    posted_date DATE,
    
    -- Metadata
    scraped_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE, -- Jobs expire after 30 days
    
    -- Indexes
    UNIQUE(source, source_job_id)
);

CREATE INDEX idx_jobs_source ON jobs(source);
CREATE INDEX idx_jobs_posted ON jobs(posted_date DESC);
CREATE INDEX idx_jobs_country ON jobs(country);
```

### Applications Table

```sql
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    job_id UUID NOT NULL REFERENCES jobs(id),
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- 'pending' = User hasn't selected yet
    -- 'selected' = User wants to apply
    -- 'applying' = Automation in progress
    -- 'applied' = Successfully submitted
    -- 'failed' = Application failed
    
    -- User's CV/Resume for this application
    resume_id UUID REFERENCES cvs(id),
    cover_letter_id UUID REFERENCES cover_letters(id),
    
    -- Tracking
    match_score DECIMAL(5,2),
    selected_at TIMESTAMP WITH TIME ZONE,
    applied_at TIMESTAMP WITH TIME ZONE,
    
    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    UNIQUE(user_id, job_id)
);

CREATE INDEX idx_applications_user ON applications(user_id);
CREATE INDEX idx_applications_status ON applications(user_id, status);
```

---

## 🔄 Complete Flow

### Step 1: Scrape/Import Jobs

```python
# backend/app/services/job_scraper.py

async def scrape_indeed_jobs(query, location, country):
    """Scrape jobs from Indeed"""
    jobs = []
    
    # Call Apify Indeed scraper
    run_input = {
        "query": query,
        "location": location,
        "country": country,
        "max_jobs": 50
    }
    
    # Run scraper
    run = await apify_client.actor("indeed-scraper").call(run_input=run_input)
    
    # Get results
    for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
        job = Job(
            source="indeed",
            source_job_id=item["job_id"],
            url=item["url"],  # ✅ STORE THIS URL
            title=item["job_title"],
            company=item["company_name"],
            location=item["location"],
            country=country.upper(),
            salary_min=item.get("salary_min"),
            salary_max=item.get("salary_max"),
            description=item.get("description"),
            posted_date=item.get("posted_date")
        )
        jobs.append(job)
    
    # Save to database
    await db.jobs.insert_many(jobs)
    
    return jobs
```

---

### Step 2: Show Jobs to User (Dashboard)

```python
# backend/app/api/jobs.py

@router.get("/jobs/matched")
async def get_matched_jobs(
    user: User = Depends(get_current_user),
    limit: int = 100,
    offset: int = 0
):
    """Get jobs matching user preferences"""
    
    # Get user preferences
    prefs = await db.preferences.find_one({"user_id": user.id})
    
    # Query jobs matching preferences
    query = {
        "country": {"$in": prefs.countries},
        "posted_date": {"$gte": datetime.now() - timedelta(days=14)}
    }
    
    # Add location filter
    if prefs.locations:
        query["location"] = {"$regex": "|".join(prefs.locations), "$options": "i"}
    
    # Get jobs
    jobs = await db.jobs.find(query).limit(limit).skip(offset).to_list()
    
    # Calculate match scores
    matched_jobs = []
    for job in jobs:
        score = calculate_match_score(job, prefs)
        if score >= 50:  # At least 50% match
            # Check if user already applied
            existing_app = await db.applications.find_one({
                "user_id": user.id,
                "job_id": job.id
            })
            
            matched_jobs.append({
                **job.dict(),
                "match_score": score,
                "application_status": existing_app["status"] if existing_app else None
            })
    
    return matched_jobs
```

---

### Step 3: User Selects Jobs to Apply

```python
# backend/app/api/applications.py

@router.post("/applications/select")
async def select_job_for_application(
    job_id: UUID,
    resume_id: UUID = None,
    cover_letter_id: UUID = None,
    user: User = Depends(get_current_user)
):
    """User selects a job they want to apply to"""
    
    # Get job
    job = await db.jobs.find_one({"_id": job_id})
    if not job:
        raise HTTPException(404, "Job not found")
    
    # Create or update application
    application = await db.applications.find_one_and_update(
        {"user_id": user.id, "job_id": job_id},
        {
            "$set": {
                "status": "selected",
                "selected_at": datetime.now(),
                "resume_id": resume_id or user.default_resume_id,
                "cover_letter_id": cover_letter_id or user.default_cover_letter_id
            }
        },
        upsert=True
    )
    
    return {
        "application_id": application["_id"],
        "job_url": job.url,  # ✅ Return the URL
        "status": "selected",
        "message": "Job added to application queue"
    }
```

---

### Step 4: Automation Applies to Selected Jobs

```python
# backend/app/services/application_automation.py

class ApplicationAutomation:
    """Automates job applications"""
    
    def __init__(self, user: User):
        self.user = user
        self.browser = None
    
    async def apply_to_job(self, application: Application):
        """Apply to a specific job"""
        
        # Get job details
        job = await db.jobs.find_one({"_id": application.job_id})
        
        # Get user's CV
        cv = await db.cvs.find_one({"_id": application.resume_id})
        cv_url = cv.download_url
        
        # Launch browser (Playwright)
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to job URL
            await page.goto(job.url, wait_until="networkidle")
            
            # Detect job site and use appropriate adapter
            if "indeed.com" in job.url:
                result = await self._apply_indeed(page, job, cv_url)
            elif "linkedin.com" in job.url:
                result = await self._apply_linkedin(page, job, cv_url)
            elif "greenhouse.io" in job.url:
                result = await self._apply_greenhouse(page, job, cv_url)
            elif "lever.co" in job.url:
                result = await self._apply_lever(page, job, cv_url)
            else:
                result = await self._apply_generic(page, job, cv_url)
            
            # Update application status
            if result["success"]:
                await db.applications.update_one(
                    {"_id": application.id},
                    {"$set": {"status": "applied", "applied_at": datetime.now()}}
                )
            else:
                await db.applications.update_one(
                    {"_id": application.id},
                    {
                        "$set": {
                            "status": "failed",
                            "error_message": result["error"]
                        }
                    }
                )
            
            return result
            
        finally:
            await browser.close()
```

---

### Step 5: Indeed Adapter Example

```python
# backend/app/services/adapters/indeed_adapter.py

class IndeedAdapter:
    """Indeed-specific application logic"""
    
    async def apply(self, page, job, cv_url):
        """Apply to Indeed job"""
        
        try:
            # Click "Apply Now" button
            await page.click('#indeedApplyButton', timeout=5000)
            
            # Wait for modal
            await page.wait_for_selector('#indeedApplyContainer', timeout=10000)
            
            # Fill form fields
            await self._fill_form(page)
            
            # Upload CV
            await self._upload_cv(page, cv_url)
            
            # Submit
            await page.click('[data-testid="submit-application"]')
            
            # Wait for confirmation
            await page.wait_for_selector('.application-success', timeout=10000)
            
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _fill_form(self, page):
        """Auto-fill Indeed form with user data"""
        
        # Get user data from database
        user = self.user
        
        # Fill fields
        await page.fill('input[name="firstName"]', user.first_name)
        await page.fill('input[name="lastName"]', user.last_name)
        await page.fill('input[name="email"]', user.email)
        await page.fill('input[name="phone"]', user.phone)
        
        # Fill experience if asked
        if await page.is_visible('input[name="currentEmployer"]'):
            await page.fill('input[name="currentEmployer"]', user.current_company)
            await page.fill('input[name="currentTitle"]', user.current_title)
    
    async def _upload_cv(self, page, cv_url):
        """Upload CV to Indeed"""
        
        # Download CV
        async with aiohttp.ClientSession() as session:
            async with session.get(cv_url) as response:
                cv_content = await response.read()
        
        # Save temporarily
        cv_path = f"/tmp/cv_{self.user.id}.pdf"
        with open(cv_path, "wb") as f:
            f.write(cv_content)
        
        # Upload
        file_input = await page.query_selector('input[type="file"]')
        await file_input.set_input_files(cv_path)
        
        # Clean up
        os.remove(cv_path)
```

---

## 📱 Dashboard UI

### Job Card Component

```jsx
function JobCard({ job }) {
  const [status, setStatus] = useState(job.application_status);
  
  const handleSelect = async () => {
    // User clicks "Apply" - selects this job
    const response = await fetch('/api/v1/applications/select', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({
        job_id: job.id,
        resume_id: user.defaultResumeId
      })
    });
    
    const data = await response.json();
    setStatus('selected');
    
    // Option 1: Automation applies immediately
    // await applyAutomatically(data.application_id);
    
    // Option 2: User visits and applies manually
    // window.open(job.url, '_blank');
  };
  
  return (
    <div className="job-card">
      <h3>{job.title}</h3>
      <p>{job.company}</p>
      <p>{job.location}</p>
      <p>💰 {formatSalary(job.salary)}</p>
      <p>✅ {job.match_score}% match</p>
      
      {status === 'applied' ? (
        <div className="applied-badge">✅ Applied</div>
      ) : status === 'selected' ? (
        <div className="selected-badge">
          ⏳ Ready to apply
          <button onClick={() => window.open(job.url)}>
            Visit Job →
          </button>
        </div>
      ) : (
        <button onClick={handleSelect} className="apply-btn">
          ⚡ Apply to This Job
        </button>
      )}
    </div>
  );
}
```

---

## 🤖 Two Automation Modes

### Mode 1: Fully Automated (Background)

```python
# backend/app/tasks/apply_to_jobs.py

@celery.task
def apply_to_selected_jobs(user_id):
    """Automatically apply to all selected jobs"""
    
    user = db.users.find_one({"_id": user_id})
    applications = db.applications.find({
        "user_id": user_id,
        "status": "selected"
    })
    
    automation = ApplicationAutomation(user)
    
    for app in applications:
        result = automation.apply_to_job(app)
        
        if result["success"]:
            logger.info(f"Applied to {app.job_id}")
        else:
            logger.error(f"Failed: {result['error']}")
```

**User Flow:**
1. User selects 10 jobs in dashboard
2. Clicks "Apply to All Selected"
3. Backend automation applies to all 10
4. User gets email: "Applied to 10 jobs!"

---

### Mode 2: Extension-Assisted (User Visits)

```javascript
// Extension checks if job is selected

async function checkIfSelected(jobUrl) {
  const response = await fetch(
    `https://api.jobscale.com/api/v1/applications/check?url=${encodeURIComponent(jobUrl)}`
  );
  
  const data = await response.json();
  
  return {
    selected: data.status === 'selected',
    applicationId: data.application_id
  };
}
```

**User Flow:**
1. User selects 10 jobs in dashboard
2. Clicks "Visit Job" on each
3. Extension detects pre-selected job
4. Shows "⚡ Submit Application" button
5. User clicks → Auto-fills → Submits

---

## 📊 Queue Management

```python
# backend/app/services/application_queue.py

class ApplicationQueue:
    """Manages application queue"""
    
    async def get_pending_applications(self, user_id):
        """Get jobs user selected but haven't applied to"""
        
        return await db.applications.find({
            "user_id": user_id,
            "status": "selected"
        }).to_list()
    
    async def add_to_queue(self, user_id, job_id):
        """Add job to application queue"""
        
        await db.applications.update_one(
            {"user_id": user_id, "job_id": job_id},
            {
                "$set": {
                    "status": "selected",
                    "selected_at": datetime.now()
                }
            },
            upsert=True
        )
    
    async def process_queue(self, user_id):
        """Process all pending applications"""
        
        pending = await self.get_pending_applications(user_id)
        
        for app in pending:
            await self.apply(app)
```

---

## ✅ Summary

### The Complete Flow:

```
1. Scrape jobs → Store URLs in database
2. Show jobs to user (dashboard)
3. User clicks "Apply" on specific jobs
4. Backend marks as "selected"
5. Automation applies to those jobs:
   - Mode 1: Fully automated (background)
   - Mode 2: Extension-assisted (user visits)
6. Track status in dashboard
```

### Key Points:

✅ **Store job URLs** in database when scraping  
✅ **User selects** which jobs to apply to  
✅ **Automation only applies** to selected jobs  
✅ **Two modes**: Fully automated OR extension-assisted  
✅ **Track everything** in applications table

---

*Simple, clean, user-controlled.* 🎯
