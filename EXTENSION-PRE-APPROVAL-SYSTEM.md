# 🎯 JobScale Extension - Pre-Approved Job Application System

## Core Principle

**The extension does NOT decide which jobs to apply to.**

**Only jobs the user explicitly selects from their JobScale dashboard can be applied to via the extension.**

---

## 🔄 Correct User Flow

### Step 1: User Browses JobScale Dashboard
```
User logs into JobScale.com/dashboard
Dashboard shows 150 matched jobs (based on preferences)
User reviews jobs, reads descriptions
User clicks "Apply" on 10 specific jobs they want
```

### Step 2: JobScale Marks Jobs as "Pending Application"
```
Backend creates application records:
{
  user_id: "user_123",
  job_id: "indeed_456",
  status: "pending_application",
  approved_at: "2026-03-09T00:30:00Z"
}
```

### Step 3: User Visits Job Page
```
User clicks "Go to Job" from dashboard
Opens Indeed.com in new tab
Extension detects job page
Extension checks: "Is this job pre-approved for this user?"
```

### Step 4: Extension Verifies Pre-Approval
```
Extension queries backend:
GET /api/v1/applications/pending?job_id=indeed_456&url=https://indeed.com/...

Backend responds:
{
  approved: true,
  application_id: "app_789",
  status: "pending_application"
}
```

### Step 5: Extension Shows Apply Button
```
✅ This job is pre-approved!
[ Submit Application ]
```

### Step 6: User Confirms & Applies
```
User clicks "Submit Application"
Extension auto-fills form
Extension uploads CV
Extension submits
Extension updates status to "applied"
```

---

## 🗄️ Database Schema

### Applications Table

```sql
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    job_id VARCHAR(255) NOT NULL,
    job_source VARCHAR(50) NOT NULL, -- indeed, linkedin, greenhouse, etc.
    job_url TEXT NOT NULL,
    job_title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    salary_amount INTEGER,
    salary_currency VARCHAR(3),
    
    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending_application',
    -- pending_application: User selected from dashboard, not yet applied
    -- applying: Extension is currently submitting
    -- applied: Successfully submitted
    -- failed: Application failed
    -- withdrawn: User withdrew application
    
    -- Timestamps
    approved_at TIMESTAMP WITH TIME ZONE, -- When user clicked "Apply" in dashboard
    applied_at TIMESTAMP WITH TIME ZONE,  -- When extension submitted
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    resume_version_id UUID REFERENCES cvs(id),
    cover_letter_version_id UUID REFERENCES cover_letters(id),
    match_score DECIMAL(5,2),
    
    -- Error tracking
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    UNIQUE(user_id, job_id, job_source)
);

CREATE INDEX idx_applications_user_status ON applications(user_id, status);
CREATE INDEX idx_applications_pending ON applications(user_id, status) WHERE status = 'pending_application';
```

---

## 🔌 Backend API Endpoints

### 1. User Selects Job from Dashboard

```javascript
// POST /api/v1/applications/select
// User clicks "Apply" on a job in their dashboard

Request:
{
  "job_id": "indeed_456",
  "job_source": "indeed",
  "job_url": "https://indeed.com/viewjob?jk=456",
  "job_title": "Software Engineer",
  "company": "Stripe",
  "location": "London, UK",
  "salary": 80000,
  "resume_id": "cv_123",
  "cover_letter_id": "cl_456"
}

Response (201 Created):
{
  "application_id": "app_789",
  "status": "pending_application",
  "approved_at": "2026-03-09T00:30:00Z",
  "message": "Job added to your application queue. Visit the job page to submit."
}
```

### 2. Extension Checks Pre-Approval

```javascript
// GET /api/v1/applications/pending?job_id={job_id}&job_source={source}&url={url}
// Extension checks if this job is pre-approved

Response (200 OK):
{
  "approved": true,
  "application_id": "app_789",
  "status": "pending_application",
  "job_title": "Software Engineer",
  "company": "Stripe",
  "resume_url": "https://api.jobscale.com/api/v1/cvs/cv_123/download",
  "cover_letter_url": "https://api.jobscale.com/api/v1/cover-letters/cl_456/download"
}

Response (404 Not Found):
{
  "approved": false,
  "message": "This job has not been pre-approved for application"
}
```

### 3. Extension Submits Application

```javascript
// POST /api/v1/applications/{application_id}/submit
// Extension confirms application was submitted

Request:
{
  "status": "applied",
  "submitted_at": "2026-03-09T00:35:00Z",
  "external_application_id": "indeed_application_123" // If provided by job site
}

Response (200 OK):
{
  "application_id": "app_789",
  "status": "applied",
  "applied_at": "2026-03-09T00:35:00Z",
  "message": "Application tracked successfully"
}
```

### 4. Extension Reports Failure

```javascript
// POST /api/v1/applications/{application_id}/fail
// Extension reports application failed

Request:
{
  "status": "failed",
  "error_message": "Form submission timeout after 30 seconds",
  "error_code": "TIMEOUT",
  "retry_count": 1
}

Response (200 OK):
{
  "application_id": "app_789",
  "status": "failed",
  "can_retry": true,
  "message": "You can retry this application from your dashboard"
}
```

---

## 📱 Frontend Dashboard Flow

### Dashboard Job Card

```jsx
// Dashboard Job Card Component
function JobCard({ job }) {
  const [applicationStatus, setApplicationStatus] = useState(job.application?.status || null);
  
  const handleApply = async () => {
    // Mark job as pending application
    const response = await fetch('/api/v1/applications/select', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: JSON.stringify({
        job_id: job.id,
        job_source: job.source,
        job_url: job.url,
        job_title: job.title,
        company: job.company,
        location: job.location,
        salary: job.salary,
        resume_id: user.defaultResumeId,
        cover_letter_id: user.defaultCoverLetterId
      })
    });
    
    const data = await response.json();
    setApplicationStatus('pending_application');
    
    // Open job in new tab
    window.open(job.url, '_blank');
  };
  
  return (
    <div className="job-card">
      <h3>{job.title}</h3>
      <p>{job.company}</p>
      <p>{job.location}</p>
      <p>💰 {job.salary || 'Not disclosed'}</p>
      <p>✅ {job.matchScore}% match</p>
      
      {applicationStatus === 'pending_application' && (
        <div className="pending-badge">
          ⏳ Ready to apply - Visit job page
        </div>
      )}
      
      {applicationStatus === 'applied' && (
        <div className="applied-badge">
          ✅ Applied on {formatDate(job.application.applied_at)}
        </div>
      )}
      
      {!applicationStatus && (
        <button onClick={handleApply} className="apply-btn">
          ⚡ Apply with JobScale
        </button>
      )}
      
      <a href={job.url} target="_blank" className="view-job-link">
        View on {job.source} →
      </a>
    </div>
  );
}
```

### Application Queue Sidebar

```jsx
// Sidebar showing pending applications
function ApplicationQueue({ pendingApplications }) {
  return (
    <div className="application-queue">
      <h3>📋 Ready to Apply ({pendingApplications.length})</h3>
      
      {pendingApplications.length === 0 ? (
        <p className="empty">No pending applications</p>
      ) : (
        <ul>
          {pendingApplications.map(app => (
            <li key={app.id} className="pending-item">
              <div className="job-info">
                <strong>{app.job_title}</strong>
                <span>{app.company}</span>
              </div>
              <div className="status">
                ⏳ Pending
              </div>
              <button 
                onClick={() => window.open(app.job_url, '_blank')}
                className="visit-btn"
              >
                Visit Job →
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
```

---

## 🔌 Extension Logic

### Content Script - Pre-Approval Check

```javascript
// contentScript.js

async function initialize() {
  const jobData = extractJobDataFromPage();
  if (!jobData) return;
  
  // Check if this job is pre-approved
  const approval = await checkPreApproval(jobData);
  
  if (approval.approved) {
    // Show apply button
    injectApplyButton(jobData, approval);
  } else {
    // Job not pre-approved - stay hidden or show info message
    console.log('JobScale: This job is not pre-approved for application');
  }
}

async function checkPreApproval(jobData) {
  const token = await getAuthToken();
  
  try {
    const response = await fetch(
      `https://api.jobscale.com/api/v1/applications/pending?` +
      `job_id=${encodeURIComponent(jobData.jobId)}&` +
      `job_source=${encodeURIComponent(jobData.source)}&` +
      `url=${encodeURIComponent(jobData.url)}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      }
    );
    
    if (response.status === 404) {
      return { approved: false };
    }
    
    if (!response.ok) {
      throw new Error('Failed to check pre-approval');
    }
    
    const data = await response.json();
    return {
      approved: true,
      applicationId: data.application_id,
      status: data.status,
      resumeUrl: data.resume_url,
      coverLetterUrl: data.cover_letter_url
    };
  } catch (error) {
    console.error('JobScale: Pre-approval check failed:', error);
    return { approved: false, error: error.message };
  }
}

function injectApplyButton(jobData, approval) {
  const button = document.createElement('button');
  button.id = 'jobscale-apply-btn';
  button.innerHTML = '⚡ Submit Application with JobScale';
  button.style.cssText = `
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 14px 28px;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    margin: 20px 0;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  `;
  
  button.addEventListener('click', () => {
    showConfirmationDialog(jobData, approval);
  });
  
  // Inject near the apply section
  const applySection = document.querySelector('.apply-section, #apply-container, form');
  if (applySection) {
    applySection.insertBefore(button, applySection.firstChild);
  }
}

function showConfirmationDialog(jobData, approval) {
  // Create modal
  const modal = document.createElement('div');
  modal.className = 'jobscale-modal';
  modal.innerHTML = `
    <div class="jobscale-modal-content">
      <h3>✅ Ready to Apply</h3>
      <p>This job was pre-approved from your JobScale dashboard.</p>
      
      <div class="job-summary">
        <strong>${jobData.title}</strong>
        <p>${jobData.company}</p>
        <p>${jobData.location}</p>
      </div>
      
      <div class="checklist">
        <label>
          <input type="checkbox" checked />
          I've reviewed the job description
        </label>
        <label>
          <input type="checkbox" checked />
          My CV is up to date
        </label>
      </div>
      
      <div class="actions">
        <button class="cancel-btn">Cancel</button>
        <button class="submit-btn">✅ Submit Application</button>
      </div>
      
      <p class="disclaimer">
        This will submit your application. You can track the status in your JobScale dashboard.
      </p>
    </div>
  `;
  
  // Handle actions
  modal.querySelector('.cancel-btn').addEventListener('click', () => {
    modal.remove();
  });
  
  modal.querySelector('.submit-btn').addEventListener('click', async () => {
    modal.querySelector('.submit-btn').disabled = true;
    modal.querySelector('.submit-btn').textContent = 'Submitting...';
    
    // Start application process
    await submitApplication(jobData, approval);
  });
  
  document.body.appendChild(modal);
}

async function submitApplication(jobData, approval) {
  // Get user data + CV
  const userData = await getUserData();
  const cvBlob = await downloadFile(approval.resumeUrl);
  
  // Fill form
  const formDetector = new FormDetector();
  const form = formDetector.detectForm();
  const fieldMap = formDetector.mapFields(form);
  
  const autoFiller = new AutoFiller(userData);
  const results = await autoFiller.fillAll(fieldMap);
  
  // Upload CV
  if (fieldMap.resume) {
    await uploadCV(fieldMap.resume, cvBlob);
  }
  
  // Submit form (or guide user to submit)
  const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
  if (submitBtn) {
    submitBtn.click();
  }
  
  // Track application
  await trackApplication(approval.applicationId, 'applied');
  
  // Show success
  showSuccessMessage();
}

async function trackApplication(applicationId, status) {
  const token = await getAuthToken();
  
  await fetch(`https://api.jobscale.com/api/v1/applications/${applicationId}/submit`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      status: status,
      submitted_at: new Date().toISOString()
    })
  });
}
```

---

## 🎨 UI States

### State 1: Job Pre-Approved ✅

```
┌─────────────────────────────────────┐
│  ✅ Ready to Apply                  │
│                                     │
│  This job was selected from your    │
│  JobScale dashboard.                │
│                                     │
│  Software Engineer @ Stripe         │
│  London, UK · £80,000               │
│                                     │
│  [ ⚡ Submit Application ]          │
│                                     │
│  This will auto-fill and submit     │
│  your application.                  │
└─────────────────────────────────────┘
```

### State 2: Job NOT Pre-Approved ❌

```
┌─────────────────────────────────────┐
│  ℹ️ JobScale                        │
│                                     │
│  This job hasn't been pre-approved  │
│  for application.                   │
│                                     │
│  To apply with JobScale:            │
│  1. Visit JobScale dashboard        │
│  2. Select jobs you want to apply   │
│  3. Return here to submit           │
│                                     │
│  [ Go to Dashboard ]                │
└─────────────────────────────────────┘
```

### State 3: Already Applied ✅

```
┌─────────────────────────────────────┐
│  ✅ Already Applied                 │
│                                     │
│  You applied to this job on         │
│  9th March 2026 at 00:35            │
│                                     │
│  Status: Submitted                  │
│                                     │
│  [ View in Dashboard ]              │
└─────────────────────────────────────┘
```

---

## 📊 Dashboard Status Flow

```
┌─────────────────────────────────────────────┐
│  📊 Application Status                      │
│  ─────────────────────────────────────────  │
│                                             │
│  Job              Status        Actions     │
│  ─────────────────────────────────────────  │
│  Stripe           ⏳ Pending    [Visit]     │
│  GitLab           ✅ Applied    [Track]     │
│  Monzo            ❌ Failed     [Retry]     │
│  Revolut          🟡 Interview  [Prepare]   │
│                                             │
│  Legend:                                    │
│  ⏳ Pending = Selected, not yet applied     │
│  ✅ Applied = Submitted successfully        │
│  ❌ Failed = Error during submission        │
│  🟡 Interview = Employer responded          │
└─────────────────────────────────────────────┘
```

---

## 🔐 Security Considerations

### What We Verify

| Check | Purpose |
|-------|---------|
| **JWT Token** | User is authenticated |
| **Application ID** | Job was pre-approved |
| **User ID Match** | Application belongs to this user |
| **Status = pending** | Not already applied |
| **URL Match** | Prevents applying to wrong job |

### What We DON'T Allow

- ❌ Applying to jobs not in user's dashboard
- ❌ Applying to jobs already submitted
- ❌ Applying without explicit user confirmation
- ❌ Applying on behalf of other users
- ❌ Bulk applying without user review

---

## 📈 Analytics

### Track These Metrics

```javascript
const metrics = {
  // Funnel
  jobsViewedInDashboard: 0,
  jobsMarkedAsPending: 0,
  jobsVisitedOnExternalSite: 0,
  applicationsSubmitted: 0,
  applicationsSuccessful: 0,
  
  // Conversion rates
  dashboardToPending: 0, // pending / viewed
  pendingToSubmitted: 0, // submitted / pending
  submissionSuccessRate: 0, // successful / submitted
  
  // Errors
  preApprovalCheckFailures: 0,
  formFillFailures: 0,
  submissionFailures: 0,
  
  // User behavior
  averageJobsSelectedPerSession: 0,
  averageTimeFromSelectToApply: 0, // ms
  retryRate: 0 // failed applications retried
};
```

---

## ✅ Summary

### The Correct Flow:

```
1. User browses JobScale dashboard
2. User clicks "Apply" on specific jobs
3. Backend marks jobs as "pending_application"
4. User visits job page (Indeed, LinkedIn, etc.)
5. Extension checks: "Is this job pre-approved?"
6. If YES → Show "Submit Application" button
7. If NO → Stay hidden
8. User clicks "Submit" → Auto-fill + submit
9. Track status in dashboard
```

### Key Principle:

**Extension NEVER decides which jobs to apply to.**

**Only user-selected jobs from dashboard can be applied to.**

---

*This gives users full control while automating the tedious form-filling.* 🎯
