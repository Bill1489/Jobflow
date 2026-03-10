# 🎯 JobScale Extension - Job Qualification & Control System

## Problem Statement

**How do we ensure the extension only applies to jobs the user actually wants?**

We don't want users accidentally applying to:
- ❌ Wrong locations
- ❌ Wrong seniority levels
- ❌ Below their salary expectations
- ❌ Jobs they already applied to
- ❌ Exceeding their monthly application limit (free tier: 5/month)

---

## ✅ Solution: Multi-Layer Qualification System

```
User visits job page
       ↓
Extension extracts job data
       ↓
Check 1: Is user authenticated?
       ↓
Check 2: Job matches user preferences?
       ↓
Check 3: Within monthly application limit?
       ↓
Check 4: Not a duplicate application?
       ↓
Check 5: User confirms application?
       ↓
Submit application
       ↓
Track in dashboard
```

---

## 🔍 Check 1: Authentication

```javascript
async function checkAuthentication() {
  const stored = await chrome.storage.local.get(['token', 'userId']);
  
  if (!stored.token) {
    return {
      authenticated: false,
      reason: 'Please login to JobScale',
      action: 'redirect_to_login'
    };
  }
  
  // Verify token is still valid
  try {
    const response = await fetch('https://api.jobscale.com/api/v1/auth/me', {
      headers: { 'Authorization': `Bearer ${stored.token}` }
    });
    
    if (!response.ok) {
      return {
        authenticated: false,
        reason: 'Session expired',
        action: 'refresh_token'
      };
    }
    
    return { authenticated: true, user: await response.json() };
  } catch (error) {
    return { authenticated: false, reason: 'Network error' };
  }
}
```

---

## 🎯 Check 2: Job Matches User Preferences

### User Preferences Schema

```javascript
// From backend: /api/v1/users/me/preferences
{
  "target_roles": ["Software Engineer", "Senior Software Engineer"],
  "seniority_levels": ["mid", "senior"],
  "countries": ["uk"],
  "locations": ["London, UK", "Remote"],
  "remote_preference": "hybrid_ok",
  "employment_types": ["fulltime"],
  "min_salary": 60000,
  "target_companies": ["Stripe", "GitLab"]
}
```

### Job Qualification Logic

```javascript
class JobQualifier {
  constructor(userPreferences) {
    this.preferences = userPreferences;
  }
  
  async qualifyJob(jobData) {
    const checks = {
      role: this.checkRole(jobData.title),
      location: this.checkLocation(jobData.location),
      salary: this.checkSalary(jobData.salary),
      seniority: this.checkSeniority(jobData.title, jobData.description),
      employmentType: this.checkEmploymentType(jobData.type),
      company: this.checkCompany(jobData.company),
      remote: this.checkRemote(jobData.remote)
    };
    
    const score = Object.values(checks).filter(c => c.passed).length;
    const total = Object.values(checks).length;
    const matchPercentage = (score / total) * 100;
    
    return {
      qualified: matchPercentage >= 60, // At least 60% match
      matchPercentage,
      checks,
      warnings: this.getWarnings(checks)
    };
  }
  
  checkRole(jobTitle) {
    const { target_roles } = this.preferences;
    const titleLower = jobTitle.toLowerCase();
    
    // Check if any target role matches
    const match = target_roles.some(role => 
      titleLower.includes(role.toLowerCase())
    );
    
    // Also check for related titles
    const relatedTitles = this.getRelatedTitles(target_roles);
    const relatedMatch = relatedTitles.some(title =>
      titleLower.includes(title)
    );
    
    return {
      passed: match || relatedMatch,
      label: 'Role Match',
      message: match ? '✅ Matches your target roles' : '⚠️ Different from your target roles'
    };
  }
  
  checkLocation(jobLocation) {
    const { locations, countries } = this.preferences;
    const locationLower = jobLocation.toLowerCase();
    
    // Check country
    const countryMatch = countries.some(country =>
      locationLower.includes(country.toLowerCase())
    );
    
    // Check specific location
    const locationMatch = locations.some(loc =>
      locationLower.includes(loc.toLowerCase().split(',')[0])
    );
    
    // Check if remote
    const isRemote = locationLower.includes('remote');
    const remoteOk = this.preferences.remote_preference !== 'onsite_only';
    
    return {
      passed: countryMatch || locationMatch || (isRemote && remoteOk),
      label: 'Location',
      message: countryMatch ? '✅ In your target country' : '⚠️ Different location'
    };
  }
  
  checkSalary(jobSalary) {
    const { min_salary } = this.preferences;
    
    if (!jobSalary || !jobSalary.amount) {
      return {
        passed: true, // Can't disqualify if unknown
        label: 'Salary',
        message: '⚠️ Salary not disclosed'
      };
    }
    
    const matches = jobSalary.amount >= min_salary;
    
    return {
      passed: matches,
      label: 'Salary',
      message: matches 
        ? `✅ £${jobSalary.amount.toLocaleString()} (above your £${min_salary.toLocaleString()} min)`
        : `❌ £${jobSalary.amount.toLocaleString()} (below your £${min_salary.toLocaleString()} min)`
    };
  }
  
  checkSeniority(jobTitle, jobDescription) {
    const { seniority_levels } = this.preferences;
    const text = `${jobTitle} ${jobDescription}`.toLowerCase();
    
    const seniorityKeywords = {
      entry: ['entry', 'junior', 'graduate', 'trainee', 'associate'],
      mid: ['mid', 'middle', 'experienced'],
      senior: ['senior', 'sr', 'lead'],
      lead: ['lead', 'principal', 'staff'],
      executive: ['head', 'director', 'vp', 'chief', 'cto', 'ceo']
    };
    
    const detectedLevels = [];
    for (const [level, keywords] of Object.entries(seniorityKeywords)) {
      if (keywords.some(k => text.includes(k))) {
        detectedLevels.push(level);
      }
    }
    
    const match = detectedLevels.some(level => 
      seniority_levels.includes(level)
    );
    
    return {
      passed: match || detectedLevels.length === 0, // Pass if can't detect
      label: 'Seniority',
      message: match ? '✅ Matches your seniority level' : '⚠️ Different seniority level'
    };
  }
  
  checkEmploymentType(jobType) {
    const { employment_types } = this.preferences;
    
    const typeMap = {
      'full-time': 'fulltime',
      'fulltime': 'fulltime',
      'part-time': 'parttime',
      'parttime': 'parttime',
      'contract': 'contract',
      'temporary': 'contract',
      'internship': 'internship'
    };
    
    const normalizedType = typeMap[jobType?.toLowerCase()] || 'unknown';
    const match = employment_types.includes(normalizedType);
    
    return {
      passed: match || normalizedType === 'unknown',
      label: 'Employment Type',
      message: match ? '✅ Matches your preference' : '⚠️ Different employment type'
    };
  }
  
  checkCompany(companyName) {
    const { target_companies, blacklisted_companies } = this.preferences;
    
    if (blacklisted_companies?.some(c => companyName.toLowerCase().includes(c.toLowerCase()))) {
      return {
        passed: false,
        label: 'Company',
        message: '❌ You\'ve blocked this company',
        critical: true
      };
    }
    
    if (target_companies?.some(c => companyName.toLowerCase().includes(c.toLowerCase()))) {
      return {
        passed: true,
        label: 'Company',
        message: '✅ One of your target companies!',
        bonus: true
      };
    }
    
    return {
      passed: true, // Neutral
      label: 'Company',
      message: '✅ Company'
    };
  }
  
  checkRemote(isRemote) {
    const { remote_preference } = this.preferences;
    
    if (!isRemote) {
      return {
        passed: remote_preference !== 'remote_only',
        label: 'Remote',
        message: remote_preference !== 'remote_only' ? '✅ On-site role' : '❌ You want remote only'
      };
    }
    
    return {
      passed: remote_preference !== 'onsite_only',
      label: 'Remote',
      message: remote_preference !== 'onsite_only' ? '✅ Remote role' : '❌ You want on-site only'
    };
  }
  
  getWarnings(checks) {
    const warnings = [];
    
    if (checks.salary.passed && !checks.salary.message.includes('above')) {
      warnings.push('Salary not disclosed');
    }
    
    if (!checks.role.passed) {
      warnings.push('Role differs from your targets');
    }
    
    if (!checks.location.passed) {
      warnings.push('Location outside your preferences');
    }
    
    return warnings;
  }
  
  getRelatedTitles(targetRoles) {
    // Expand target roles with related titles
    const expansions = {
      'software engineer': ['developer', 'software developer', 'engineer', 'programmer'],
      'senior software engineer': ['senior developer', 'lead engineer', 'staff engineer'],
      'data scientist': ['data analyst', 'ml engineer', 'ai engineer'],
      'product manager': ['product owner', 'pm', 'head of product']
    };
    
    const related = [];
    for (const role of targetRoles) {
      const roleLower = role.toLowerCase();
      if (expansions[roleLower]) {
        related.push(...expansions[roleLower]);
      }
    }
    
    return related;
  }
}
```

---

## 📊 Check 3: Monthly Application Limit

```javascript
class ApplicationLimitChecker {
  async checkLimit(userId, token) {
    // Get user's subscription tier
    const response = await fetch('https://api.jobscale.com/api/v1/billing/subscription', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    const subscription = await response.json();
    
    // Get applications this month
    const appsResponse = await fetch(
      `https://api.jobscale.com/api/v1/applications?month=${this.getCurrentMonth()}`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    
    const applications = await appsResponse.json();
    const count = applications.length;
    
    const limits = {
      free: 5,
      pro: Infinity,
      premium: Infinity
    };
    
    const limit = limits[subscription.tier] || limits.free;
    const remaining = limit - count;
    
    return {
      withinLimit: remaining > 0,
      used: count,
      limit: limit === Infinity ? 'Unlimited' : limit,
      remaining: remaining === Infinity ? 'Unlimited' : remaining,
      tier: subscription.tier,
      upgradeNeeded: remaining <= 0
    };
  }
  
  getCurrentMonth() {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  }
}
```

---

## 🔄 Check 4: Duplicate Prevention

```javascript
class DuplicateChecker {
  async isDuplicate(jobData, token) {
    // Check if user already applied to this job
    const response = await fetch(
      `https://api.jobscale.com/api/v1/applications?job_id=${jobData.jobId}`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    
    const applications = await response.json();
    
    if (applications.length > 0) {
      return {
        isDuplicate: true,
        appliedAt: applications[0].applied_at,
        status: applications[0].status
      };
    }
    
    // Also check by URL (for jobs without consistent IDs)
    const urlResponse = await fetch(
      `https://api.jobscale.com/api/v1/applications?url=${encodeURIComponent(jobData.url)}`,
      { headers: { 'Authorization': `Bearer ${token}` } }
    );
    
    const urlApplications = await urlResponse.json();
    
    return {
      isDuplicate: urlApplications.length > 0,
      appliedAt: urlApplications[0]?.applied_at,
      status: urlApplications[0]?.status
    };
  }
}
```

---

## ✅ Check 5: User Confirmation

```javascript
// popup/ConfirmationDialog.jsx
function ConfirmationDialog({ jobData, qualification, onConfirm, onCancel }) {
  return (
    <div className="confirmation-dialog">
      <h3>⚡ Confirm Application</h3>
      
      <div className="job-summary">
        <strong>{jobData.title}</strong>
        <p>{jobData.company}</p>
        <p>{jobData.location}</p>
        {jobData.salary && <p>💰 {jobData.salary}</p>}
      </div>
      
      <div className="match-score">
        <div className="score-circle" style={{
          borderColor: getScoreColor(qualification.matchPercentage)
        }}>
          {qualification.matchPercentage}%
        </div>
        <span>Match with your preferences</span>
      </div>
      
      {qualification.warnings.length > 0 && (
        <div className="warnings">
          <h4>⚠️ Things to note:</h4>
          <ul>
            {qualification.warnings.map((warning, i) => (
              <li key={i}>{warning}</li>
            ))}
          </ul>
        </div>
      )}
      
      <div className="checklist">
        <div className="check-item">
          <input type="checkbox" id="confirm-role" defaultChecked />
          <label htmlFor="confirm-role">I want to apply for this role</label>
        </div>
        <div className="check-item">
          <input type="checkbox" id="confirm-cv" defaultChecked />
          <label htmlFor="confirm-cv">My CV is up to date</label>
        </div>
      </div>
      
      <div className="actions">
        <button onClick={onCancel} className="btn-secondary">Cancel</button>
        <button onClick={onConfirm} className="btn-primary">
          ✅ Submit Application
        </button>
      </div>
      
      <p className="disclaimer">
        This will submit your application to {jobData.company}. 
        You can track the status in your JobScale dashboard.
      </p>
    </div>
  );
}
```

---

## 🎯 Complete Qualification Flow

```javascript
// contentScript.js - Main qualification logic
async function handleApplyClick(jobData) {
  // Show loading state
  showLoading('Checking eligibility...');
  
  // CHECK 1: Authentication
  const auth = await checkAuthentication();
  if (!auth.authenticated) {
    showLoginPrompt(auth.reason);
    return;
  }
  
  // CHECK 2: Job preferences match
  const preferences = await getUserPreferences(auth.token);
  const qualifier = new JobQualifier(preferences);
  const qualification = await qualifier.qualifyJob(jobData);
  
  if (!qualification.qualified) {
    showMismatchWarning(qualification);
    return; // Don't proceed if job doesn't match
  }
  
  // CHECK 3: Application limit
  const limitChecker = new ApplicationLimitChecker();
  const limitStatus = await limitChecker.checkLimit(auth.user.id, auth.token);
  
  if (!limitStatus.withinLimit) {
    showUpgradePrompt(limitStatus);
    return; // Don't proceed if over limit
  }
  
  // CHECK 4: Duplicate check
  const duplicateChecker = new DuplicateChecker();
  const duplicate = await duplicateChecker.isDuplicate(jobData, auth.token);
  
  if (duplicate.isDuplicate) {
    showAlreadyApplied(duplicate);
    return; // Don't apply twice
  }
  
  // CHECK 5: User confirmation
  showConfirmationDialog({
    jobData,
    qualification,
    limitStatus,
    onConfirm: () => submitApplication(jobData, auth.token),
    onCancel: () => closeDialog()
  });
}
```

---

## 🎨 UI States

### State 1: Job Matches ✅

```
┌─────────────────────────────────────┐
│  ⚡ Apply with JobScale             │
│                                     │
│  Software Engineer @ Stripe         │
│  London, UK · £80,000               │
│                                     │
│  ✅ 85% match with preferences      │
│  ✅ Within application limit        │
│  ✅ Not applied before              │
│                                     │
│  [ Submit Application ]             │
└─────────────────────────────────────┘
```

### State 2: Partial Match ⚠️

```
┌─────────────────────────────────────┐
│  ⚡ Apply with JobScale             │
│                                     │
│  Developer @ Startup                │
│  Manchester, UK · Salary unknown    │
│                                     │
│  ⚠️ 60% match with preferences      │
│                                     │
│  ✅ Role matches                    │
│  ⚠️ Location outside preferences    │
│  ⚠️ Salary not disclosed            │
│                                     │
│  [ Review Details ] [ Apply Anyway ]│
└─────────────────────────────────────┘
```

### State 3: Poor Match ❌

```
┌─────────────────────────────────────┐
│  ⚠️ Job Doesn't Match               │
│                                     │
│  Junior Developer @ Agency          │
│  Remote · £35,000                   │
│                                     │
│  ❌ 25% match with preferences      │
│                                     │
│  ❌ Seniority: Entry (you want Mid+)│
│  ❌ Salary: £35k (you want £60k+)   │
│                                     │
│  This doesn't match your criteria.  │
│  [ Dismiss ]                        │
└─────────────────────────────────────┘
```

### State 4: Over Limit 💎

```
┌─────────────────────────────────────┐
│  💎 Application Limit Reached       │
│                                     │
│  You've used all 5 free applications│
│  this month.                        │
│                                     │
│  Upgrade to Pro for unlimited:      │
│  • Unlimited applications           │
│  • AI CV tailoring                  │
│  • Interview prep                   │
│                                     │
│  [ Upgrade to Pro £29/mo ]          │
│  [ Maybe Later ]                    │
└─────────────────────────────────────┘
```

### State 5: Already Applied ✅

```
┌─────────────────────────────────────┐
│  ✅ Already Applied                 │
│                                     │
│  You applied to this job on         │
│  15th February 2026                 │
│                                     │
│  Current status: Under Review       │
│                                     │
│  [ View in Dashboard ]              │
│  [ Dismiss ]                        │
└─────────────────────────────────────┘
```

---

## 📊 Dashboard Integration

### Application Tracking

```javascript
// When application is submitted
async function trackApplication(jobData, status) {
  await fetch('https://api.jobscale.com/api/v1/applications', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      job_id: jobData.jobId,
      job_title: jobData.title,
      company: jobData.company,
      location: jobData.location,
      salary: jobData.salary,
      url: jobData.url,
      source: jobData.source, // indeed, linkedin, etc.
      status: 'applied',
      applied_at: new Date().toISOString(),
      match_score: jobData.matchScore,
      resume_version: jobData.resumeId,
      cover_letter_version: jobData.coverLetterId
    })
  });
  
  // Update extension badge
  updateApplicationCount();
}
```

### Dashboard Shows

```
┌─────────────────────────────────────────────┐
│  📊 Applications This Month: 3/5 (Free)     │
│  ─────────────────────────────────────────  │
│                                             │
│  Company          Role            Status    │
│  ─────────────────────────────────────────  │
│  Stripe           SWE             🟡 Review │
│  GitLab           Senior SWE      🟢 Interview
│  Monzo            Backend         ⚪ Applied│
│                                             │
│  [Upgrade to Pro for Unlimited]             │
└─────────────────────────────────────────────┘
```

---

## 🔐 Security & Privacy

### What We Store

| Data | Where | Retention |
|------|-------|-----------|
| JWT Token | Chrome storage (encrypted) | Until logout |
| User preferences | Fetched on-demand | Not stored |
| Application history | Backend only | Permanent |
| CV/Resume | Downloaded temporarily | Cleared after upload |

### What We DON'T Store

- ❌ User credentials (password)
- ❌ Full job descriptions
- ❌ Application answers
- ❌ Third-party site cookies

---

## 📈 Analytics

### Track These Metrics

```javascript
const metrics = {
  // Qualification funnel
  jobsViewed: 0,
  jobsQualified: 0,
  jobsApplied: 0,
  
  // Qualification breakdown
  qualificationReasons: {
    roleMismatch: 0,
    locationMismatch: 0,
    salaryMismatch: 0,
    overLimit: 0,
    duplicate: 0
  },
  
  // Conversion
  applyButtonClicks: 0,
  applicationsConfirmed: 0,
  applicationsSubmitted: 0,
  
  // Success
  applicationSuccessRate: 0,
  averageMatchScore: 0
};
```

---

## ✅ Summary

**5-Layer Qualification System:**

1. **Authentication** - User logged in?
2. **Job Match** - Matches preferences (60%+ threshold)?
3. **Application Limit** - Within monthly quota?
4. **Duplicate Check** - Already applied?
5. **User Confirmation** - User explicitly confirms?

**Only if ALL 5 checks pass → Application submitted**

---

*This ensures users only apply to relevant jobs, within their limits, with full control.* 🎯
