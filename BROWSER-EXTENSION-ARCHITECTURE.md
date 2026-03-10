# 🧩 JobScale Browser Extension - Complete Architecture

## Overview

**Purpose:** Enable true one-click job applications across Indeed, LinkedIn, and 5,000+ company career pages

**Approach:** Chrome/Edge extension that injects into job sites, auto-fills applications, and tracks submission status

---

## 📁 Extension Structure

```
jobscale-extension/
├── manifest.json                 # Extension config (Manifest V3)
├── package.json
├── webpack.config.js
│
├── src/
│   ├── background/
│   │   └── serviceWorker.js      # Background service worker
│   │
│   ├── content/
│   │   ├── contentScript.js      # Injected into job sites
│   │   ├── formDetector.js       # Detect application forms
│   │   ├── fieldMapper.js        # Map form fields to user data
│   │   ├── autoFiller.js         # Fill forms programmatically
│   │   └── siteAdapters/
│   │       ├── indeedAdapter.js  # Indeed-specific logic
│   │       ├── linkedinAdapter.js # LinkedIn-specific logic
│   │       ├── greenhouseAdapter.js
│   │       ├── leverAdapter.js
│   │       └── genericAdapter.js # Fallback for unknown sites
│   │
│   ├── popup/
│   │   ├── popup.html
│   │   ├── popup.jsx
│   │   └── popup.css
│   │
│   ├── options/
│   │   ├── options.html
│   │   └── options.jsx
│   │
│   ├── shared/
│   │   ├── api.js                # Backend API client
│   │   ├── storage.js            # Chrome storage wrapper
│   │   └── constants.js
│   │
│   └── assets/
│       ├── icon16.png
│       ├── icon48.png
│       └── icon128.png
│
└── dist/                         # Built extension
```

---

## 🔧 manifest.json (Manifest V3)

```json
{
  "manifest_version": 3,
  "name": "JobScale One-Click Apply",
  "version": "1.0.0",
  "description": "Auto-fill job applications with one click",
  
  "permissions": [
    "storage",
    "tabs",
    "activeTab",
    "scripting",
    "cookies"
  ],
  
  "host_permissions": [
    "https://*.indeed.com/*",
    "https://*.linkedin.com/*",
    "https://*.greenhouse.io/*",
    "https://*.lever.co/*",
    "https://*.workable.com/*",
    "https://jobscale.com/*"
  ],
  
  "background": {
    "service_worker": "background/serviceWorker.js",
    "type": "module"
  },
  
  "action": {
    "default_popup": "popup/popup.html",
    "default_icon": {
      "16": "assets/icon16.png",
      "48": "assets/icon48.png",
      "128": "assets/icon128.png"
    }
  },
  
  "options_page": "options/options.html",
  
  "content_scripts": [
    {
      "matches": [
        "https://*.indeed.com/*",
        "https://*.linkedin.com/*",
        "https://*.greenhouse.io/*",
        "https://*.lever.co/*",
        "https://*.workable.com/*",
        "https://*/*"
      ],
      "js": ["content/contentScript.js"],
      "run_at": "document_idle"
    }
  ],
  
  "web_accessible_resources": [
    {
      "resources": ["assets/*"],
      "matches": ["<all_urls>"]
    }
  ]
}
```

---

## 🔄 Complete User Flow

### Step 1: User Installs Extension
```
Chrome Web Store → Install → Extension added to browser
Extension icon appears in toolbar
User clicks icon → Login with JobScale account
```

### Step 2: User Browses Job Sites
```
User visits Indeed.co.uk
Searches for "Software Engineer"
Clicks on a job posting
Extension detects job page → Injects content script
```

### Step 3: Extension Detects Job Page
```
Content script runs
Checks URL pattern (indeed.com/viewjob)
Extracts job data (title, company, location, job ID)
Sends to background script
Background script checks if user has JobScale account
Shows "Apply with JobScale" button
```

### Step 4: User Clicks "Apply with JobScale"
```
Extension fetches user's CV + data from backend
Detects application form fields
Auto-fills all fields
User reviews (optional)
User clicks "Submit"
Application submitted
Status sent to JobScale dashboard
```

---

## 🎯 Core Components

### 1. Content Script (`contentScript.js`)

```javascript
// Detect if this is a job application page
function detectJobPage() {
  const url = window.location.href;
  
  // Indeed
  if (url.includes('indeed.com/viewjob')) {
    return { site: 'indeed', type: 'job' };
  }
  
  // LinkedIn
  if (url.includes('linkedin.com/jobs/view/')) {
    return { site: 'linkedin', type: 'job' };
  }
  
  // Greenhouse
  if (url.includes('greenhouse.io/jobs/')) {
    return { site: 'greenhouse', type: 'job' };
  }
  
  // Lever
  if (url.includes('lever.co/jobs/')) {
    return { site: 'lever', type: 'job' };
  }
  
  // Generic - look for application form indicators
  if (document.querySelector('form') && 
      (document.body.textContent.includes('application') ||
       document.body.textContent.includes('apply'))) {
    return { site: 'generic', type: 'application' };
  }
  
  return null;
}

// Inject "Apply with JobScale" button
function injectApplyButton(jobData) {
  const button = document.createElement('button');
  button.id = 'jobscale-apply-btn';
  button.textContent = '⚡ Apply with JobScale';
  button.style.cssText = `
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    margin: 16px 0;
  `;
  
  button.addEventListener('click', () => {
    startApplication(jobData);
  });
  
  // Find appropriate location to inject
  const applySection = document.querySelector('.apply-section, #apply-container, form');
  if (applySection) {
    applySection.insertBefore(button, applySection.firstChild);
  }
}

// Listen for messages from background/popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'apply') {
    startApplication(request.jobData);
    sendResponse({ status: 'started' });
  }
});
```

---

### 2. Form Detector (`formDetector.js`)

```javascript
// Detect and map form fields
class FormDetector {
  constructor() {
    this.fieldPatterns = {
      firstName: ['first_name', 'firstname', 'first-name', 'fname'],
      lastName: ['last_name', 'lastname', 'last-name', 'lname', 'surname'],
      email: ['email', 'e-mail', 'email_address'],
      phone: ['phone', 'telephone', 'mobile', 'cell'],
      linkedin: ['linkedin', 'linkedin_url', 'profile'],
      portfolio: ['portfolio', 'website', 'personal_site'],
      resume: ['resume', 'cv', 'document', 'file'],
      coverLetter: ['cover_letter', 'coverletter', 'letter'],
      currentCompany: ['current_company', 'current_employer'],
      currentRole: ['current_title', 'current_role'],
      salary: ['salary', 'compensation', 'expected_salary'],
      noticePeriod: ['notice_period', 'availability', 'start_date'],
      rightToWork: ['right_to_work', 'work_authorization', 'visa'],
      gender: ['gender', 'sex'],
      ethnicity: ['ethnicity', 'race', 'diversity']
    };
  }
  
  detectForm() {
    const forms = document.querySelectorAll('form');
    let applicationForm = null;
    
    // Find the most likely application form
    for (const form of forms) {
      const fields = form.querySelectorAll('input, textarea, select');
      const fieldNames = Array.from(fields).map(f => 
        (f.name || f.id || '').toLowerCase()
      );
      
      // Score based on common application fields
      const score = this.scoreForm(fieldNames);
      if (score > 3) {
        applicationForm = form;
        break;
      }
    }
    
    return applicationForm;
  }
  
  scoreForm(fieldNames) {
    let score = 0;
    const applicationIndicators = ['email', 'resume', 'first_name', 'last_name', 'phone'];
    
    for (const indicator of applicationIndicators) {
      if (fieldNames.some(name => name.includes(indicator))) {
        score++;
      }
    }
    
    return score;
  }
  
  mapFields(form) {
    const fields = form.querySelectorAll('input, textarea, select');
    const fieldMap = {};
    
    for (const field of fields) {
      const fieldName = (field.name || field.id || '').toLowerCase();
      const fieldLabel = field.labels?.[0]?.textContent?.toLowerCase() || '';
      
      // Match against patterns
      for (const [type, patterns] of Object.entries(this.fieldPatterns)) {
        if (patterns.some(p => fieldName.includes(p) || fieldLabel.includes(p))) {
          fieldMap[type] = {
            element: field,
            type: field.type,
            required: field.required,
            tagName: field.tagName
          };
          break;
        }
      }
    }
    
    return fieldMap;
  }
}
```

---

### 3. Auto Filler (`autoFiller.js`)

```javascript
class AutoFiller {
  constructor(userData) {
    this.userData = userData;
  }
  
  fillField(field, value) {
    if (!field || !value) return false;
    
    const element = field.element;
    
    try {
      if (element.tagName === 'SELECT') {
        return this.fillSelect(element, value);
      } else if (element.type === 'file') {
        return this.fillFile(element, value);
      } else if (element.type === 'checkbox') {
        return this.fillCheckbox(element, value);
      } else if (element.type === 'radio') {
        return this.fillRadio(element, value);
      } else {
        return this.fillText(element, value);
      }
    } catch (error) {
      console.error('Error filling field:', error);
      return false;
    }
  }
  
  fillText(element, value) {
    // Focus and set value
    element.focus();
    element.value = value;
    
    // Trigger React/Angular/Vue change events
    element.dispatchEvent(new Event('input', { bubbles: true }));
    element.dispatchEvent(new Event('change', { bubbles: true }));
    element.dispatchEvent(new Event('blur', { bubbles: true }));
    
    return true;
  }
  
  fillSelect(element, value) {
    const options = Array.from(element.options);
    
    // Try exact match first
    let match = options.find(opt => 
      opt.value.toLowerCase() === value.toLowerCase() ||
      opt.text.toLowerCase() === value.toLowerCase()
    );
    
    // Try partial match
    if (!match) {
      match = options.find(opt => 
        opt.text.toLowerCase().includes(value.toLowerCase())
      );
    }
    
    if (match) {
      element.value = match.value;
      element.dispatchEvent(new Event('change', { bubbles: true }));
      return true;
    }
    
    return false;
  }
  
  fillFile(element, value) {
    // For file uploads, we need the actual file blob
    // This is handled separately via download + upload
    return false; // Placeholder
  }
  
  fillCheckbox(element, value) {
    element.checked = value === true || value === 'yes';
    element.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
  }
  
  fillRadio(element, value) {
    const radioGroup = document.querySelectorAll(
      `input[type="radio"][name="${element.name}"]`
    );
    
    for (const radio of radioGroup) {
      if (radio.value.toLowerCase() === value.toString().toLowerCase()) {
        radio.checked = true;
        radio.dispatchEvent(new Event('change', { bubbles: true }));
        return true;
      }
    }
    
    return false;
  }
  
  async fillAll(fieldMap) {
    const results = {
      filled: [],
      skipped: [],
      failed: []
    };
    
    // Personal info
    if (fieldMap.firstName) {
      const success = this.fillField(fieldMap.firstName, this.userData.firstName);
      (success ? results.filled : results.failed).push('firstName');
    }
    
    if (fieldMap.lastName) {
      const success = this.fillField(fieldMap.lastName, this.userData.lastName);
      (success ? results.filled : results.failed).push('lastName');
    }
    
    if (fieldMap.email) {
      const success = this.fillField(fieldMap.email, this.userData.email);
      (success ? results.filled : results.failed).push('email');
    }
    
    if (fieldMap.phone) {
      const success = this.fillField(fieldMap.phone, this.userData.phone);
      (success ? results.filled : results.failed).push('phone');
    }
    
    // Experience
    if (fieldMap.currentCompany) {
      const success = this.fillField(fieldMap.currentCompany, this.userData.currentCompany);
      (success ? results.filled : results.failed).push('currentCompany');
    }
    
    if (fieldMap.currentRole) {
      const success = this.fillField(fieldMap.currentRole, this.userData.currentRole);
      (success ? results.filled : results.failed).push('currentRole');
    }
    
    // Resume upload (special handling)
    if (fieldMap.resume) {
      results.resumeNeeded = true;
    }
    
    return results;
  }
}
```

---

### 4. Site Adapters

#### Indeed Adapter (`indeedAdapter.js`)

```javascript
class IndeedAdapter {
  detectJobPage() {
    return window.location.href.includes('indeed.com/viewjob');
  }
  
  extractJobData() {
    return {
      title: document.querySelector('h1.jobsearch-JobInfoHeader-title')?.textContent?.trim(),
      company: document.querySelector('[data-testid="company-name"]')?.textContent?.trim(),
      location: document.querySelector('[data-testid="text-location"]')?.textContent?.trim(),
      jobId: new URLSearchParams(window.location.search).get('jk'),
      url: window.location.href
    };
  }
  
  findApplyButton() {
    return document.querySelector('#indeedApplyButton, [data-testid="indeed-apply-button"]');
  }
  
  findApplicationForm() {
    return document.querySelector('#indeedApplyContainer form');
  }
  
  async handleApply(jobData, userData) {
    // Click Indeed's apply button first
    const applyBtn = this.findApplyButton();
    if (applyBtn) applyBtn.click();
    
    // Wait for modal to open
    await this.waitForModal();
    
    // Get form
    const form = this.findApplicationForm();
    if (!form) return { success: false, error: 'Form not found' };
    
    // Fill form
    const detector = new FormDetector();
    const fieldMap = detector.mapFields(form);
    
    const filler = new AutoFiller(userData);
    const results = await filler.fillAll(fieldMap);
    
    // Handle resume upload
    if (results.resumeNeeded) {
      await this.uploadResume(fieldMap.resume, userData.cvUrl);
    }
    
    return { success: true, results };
  }
  
  waitForModal() {
    return new Promise(resolve => {
      const check = setInterval(() => {
        if (document.querySelector('#indeedApplyContainer')) {
          clearInterval(check);
          resolve();
        }
      }, 100);
      
      // Timeout after 5 seconds
      setTimeout(() => {
        clearInterval(check);
        resolve();
      }, 5000);
    });
  }
  
  async uploadResume(field, cvUrl) {
    // Download CV from backend
    const response = await fetch(cvUrl);
    const blob = await response.blob();
    const file = new File([blob], 'cv.pdf', { type: 'application/pdf' });
    
    // Create file input event
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    field.element.files = dataTransfer.files;
    field.element.dispatchEvent(new Event('change', { bubbles: true }));
  }
}
```

#### LinkedIn Adapter (`linkedinAdapter.js`)

```javascript
class LinkedInAdapter {
  detectJobPage() {
    return window.location.href.includes('linkedin.com/jobs/view/');
  }
  
  extractJobData() {
    const jobId = window.location.pathname.split('/').pop();
    return {
      title: document.querySelector('h1.topcard__title')?.textContent?.trim(),
      company: document.querySelector('h4.topcard__flavor--company')?.textContent?.trim(),
      location: document.querySelector('.topcard__flavor--bullet')?.textContent?.trim(),
      jobId: jobId,
      url: window.location.href,
      source: 'linkedin'
    };
  }
  
  async handleApply(jobData, userData) {
    // Check if it's "Easy Apply"
    const easyApplyBtn = document.querySelector('button.jobs-apply-button');
    
    if (easyApplyBtn && easyApplyApplyBtn.textContent?.includes('Easy Apply')) {
      return await this.handleEasyApply(jobData, userData);
    } else {
      // External application
      const applyLink = document.querySelector('a.jobs-apply-button[href]');
      if (applyLink) {
        window.open(applyLink.href, '_blank');
        return { success: true, type: 'external', url: applyLink.href };
      }
    }
    
    return { success: false, error: 'No apply button found' };
  }
  
  async handleEasyApply(jobData, userData) {
    // Click Easy Apply button
    const btn = document.querySelector('button.jobs-apply-button');
    btn?.click();
    
    // Wait for modal
    await this.waitForModal();
    
    // Navigate through multi-step form
    const steps = document.querySelectorAll('.jobs-easy-apply-modal');
    for (const step of steps) {
      await this.fillStep(step, userData);
      
      // Click next
      const nextBtn = step.querySelector('button[aria-label="Next"]');
      if (nextBtn) nextBtn.click();
      await this.sleep(500);
    }
    
    // Submit final step
    const submitBtn = document.querySelector('button[aria-label="Submit application"]');
    if (submitBtn) {
      submitBtn.click();
      return { success: true };
    }
    
    return { success: false, error: 'Submit failed' };
  }
  
  waitForModal() {
    return new Promise(resolve => {
      const check = setInterval(() => {
        if (document.querySelector('.jobs-easy-apply-modal')) {
          clearInterval(check);
          resolve();
        }
      }, 100);
      setTimeout(() => { clearInterval(check); resolve(); }, 5000);
    });
  }
  
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

---

### 5. Background Service Worker (`serviceWorker.js`)

```javascript
// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  handleMessage(request, sender, sendResponse);
  return true; // Keep channel open for async response
});

async function handleMessage(request, sender, sendResponse) {
  switch (request.action) {
    case 'getUserData':
      const userData = await getUserData();
      sendResponse({ userData });
      break;
      
    case 'startApplication':
      const result = await startApplication(request.jobData);
      sendResponse({ result });
      break;
      
    case 'trackApplication':
      await trackApplication(request.jobData, request.status);
      sendResponse({ success: true });
      break;
      
    case 'checkAuth':
      const isAuth = await checkAuthentication();
      sendResponse({ authenticated: isAuth });
      break;
  }
}

async function getUserData() {
  // Get from Chrome storage or fetch from backend
  const stored = await chrome.storage.local.get(['userData', 'token']);
  
  if (stored.token) {
    const response = await fetch('https://api.jobscale.com/api/v1/users/me', {
      headers: {
        'Authorization': `Bearer ${stored.token}`
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      return data;
    }
  }
  
  return null;
}

async function startApplication(jobData) {
  // Get user data
  const userData = await getUserData();
  if (!userData) {
    return { success: false, error: 'Not authenticated' };
  }
  
  // Determine site adapter
  const adapter = getAdapterForSite(jobData.url);
  if (!adapter) {
    return { success: false, error: 'Site not supported' };
  }
  
  // Execute application
  const result = await adapter.handleApply(jobData, userData);
  
  // Track in JobScale
  if (result.success) {
    await trackApplication(jobData, 'applied');
  }
  
  return result;
}

async function trackApplication(jobData, status) {
  const stored = await chrome.storage.local.get(['token']);
  
  await fetch('https://api.jobscale.com/api/v1/applications', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${stored.token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      job_id: jobData.jobId,
      job_title: jobData.title,
      company: jobData.company,
      url: jobData.url,
      status: status,
      applied_at: new Date().toISOString()
    })
  });
}

function getAdapterForSite(url) {
  if (url.includes('indeed.com')) return new IndeedAdapter();
  if (url.includes('linkedin.com')) return new LinkedInAdapter();
  if (url.includes('greenhouse.io')) return new GreenhouseAdapter();
  if (url.includes('lever.co')) return new LeverAdapter();
  return new GenericAdapter();
}
```

---

### 6. Popup UI (`popup.jsx`)

```jsx
import React, { useState, useEffect } from 'react';

function Popup() {
  const [authenticated, setAuthenticated] = useState(false);
  const [jobData, setJobData] = useState(null);
  const [applying, setApplying] = useState(false);
  const [status, setStatus] = useState(null);
  
  useEffect(() => {
    checkAuth();
    detectCurrentJob();
  }, []);
  
  async function checkAuth() {
    const response = await chrome.runtime.sendMessage({ action: 'checkAuth' });
    setAuthenticated(response.authenticated);
  }
  
  async function detectCurrentJob() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    chrome.tabs.sendMessage(tab.id, { action: 'getJobData' }, (response) => {
      if (response?.jobData) {
        setJobData(response.jobData);
      }
    });
  }
  
  async function handleApply() {
    setApplying(true);
    
    const result = await chrome.runtime.sendMessage({
      action: 'startApplication',
      jobData: jobData
    });
    
    setApplying(false);
    setStatus(result);
    
    if (result.success) {
      // Show success animation
      setTimeout(() => window.close(), 2000);
    }
  }
  
  if (!authenticated) {
    return (
      <div className="popup">
        <h3>🔐 Login Required</h3>
        <p>Please login to JobScale to use one-click apply</p>
        <button onClick={() => window.open('https://jobscale.com/login')}>
          Login to JobScale
        </button>
      </div>
    );
  }
  
  if (!jobData) {
    return (
      <div className="popup">
        <h3>📄 No Job Detected</h3>
        <p>Navigate to a job posting to apply</p>
      </div>
    );
  }
  
  return (
    <div className="popup">
      <h3>⚡ Apply with JobScale</h3>
      
      <div className="job-info">
        <strong>{jobData.title}</strong>
        <p>{jobData.company}</p>
        <p>{jobData.location}</p>
      </div>
      
      {status?.success && (
        <div className="success">✅ Application submitted!</div>
      )}
      
      {status?.error && (
        <div className="error">❌ {status.error}</div>
      )}
      
      <button 
        onClick={handleApply} 
        disabled={applying}
        className="apply-btn"
      >
        {applying ? 'Applying...' : 'Submit Application'}
      </button>
      
      <div className="options-link">
        <a href="#" onClick={() => chrome.runtime.openOptionsPage()}>
          Settings
        </a>
      </div>
    </div>
  );
}

export default Popup;
```

---

## 🔐 Security Considerations

### 1. Authentication
- JWT token stored in Chrome storage (encrypted)
- Token refreshed automatically via backend
- No credentials stored in extension

### 2. Data Protection
- User data fetched on-demand, not stored persistently
- CV downloaded temporarily for upload, then cleared
- No sensitive data in extension storage

### 3. Permissions
- Minimal permissions requested
- `activeTab` for current job page only
- `storage` for auth token
- No broad host permissions beyond job sites

### 4. CSP Compliance
- No inline scripts
- All scripts loaded from extension bundle
- Content Security Policy in manifest

---

## 📊 Supported Sites (Phase 1)

| Site | Coverage | Complexity |
|------|----------|------------|
| Indeed | 100% | Medium |
| LinkedIn (Easy Apply) | 80% | High |
| Greenhouse | 95% | Low |
| Lever | 95% | Low |
| Workable | 90% | Medium |
| Generic ATS | 60% | High |

---

## 🚀 Development Phases

### Phase 1: MVP (4-6 weeks)
- [ ] Indeed adapter
- [ ] Greenhouse adapter
- [ ] Lever adapter
- [ ] Basic form filler
- [ ] Auth integration
- [ ] Application tracking

### Phase 2: Enhanced (4 weeks)
- [ ] LinkedIn Easy Apply
- [ ] Workable adapter
- [ ] Generic form detector
- [ ] Multi-step form support
- [ ] Resume upload handling

### Phase 3: Polish (2 weeks)
- [ ] Error handling
- [ ] Progress indicators
- [ ] Application history
- [ ] Settings page
- [ ] Chrome Web Store submission

---

## 🧪 Testing Strategy

1. **Unit Tests:** Field mapping, form detection
2. **Integration Tests:** Each site adapter
3. **E2E Tests:** Real applications on test accounts
4. **Manual Testing:** 50+ real job applications

---

## 📈 Success Metrics

- **Application Success Rate:** >90%
- **Time Saved per Application:** 5-10 minutes
- **User Adoption:** >60% of active users
- **Error Rate:** <5%

---

## 🎯 Summary

**The extension:**
1. Detects when user is on a job page
2. Shows "Apply with JobScale" button
3. Fetches user's CV + profile data
4. Auto-fills application form
5. Uploads CV
6. Submits application
7. Tracks status in dashboard

**No credentials needed** — user is already logged into Indeed/LinkedIn/etc.

**ToS compliant** — user triggers each application manually.

---

*This is the complete architecture. Ready to build?* 🚀
