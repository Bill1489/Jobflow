# 🚀 JobScale Extension - Installation & Testing Guide

## Quick Start (15 minutes)

### Step 1: Load Extension in Chrome (5 minutes)

```
1. Open Chrome
2. Go to: chrome://extensions/
3. Enable "Developer mode" (toggle in top-right)
4. Click "Load unpacked"
5. Select folder: /home/admin/.openclaw/workspace/extension/
6. Extension icon appears in toolbar
```

---

### Step 2: Pin Extension (1 minute)

```
1. Click puzzle piece icon (extensions)
2. Find "JobScale Auto-Apply"
3. Click pin icon
4. Extension icon now always visible
```

---

### Step 3: Test on Dashboard (5 minutes)

```
1. Go to: https://app.jobscale.com/dashboard
2. Browse matched jobs
3. Click "Apply" on 3-5 jobs (marks as pending)
4. Click extension icon
5. Click "Start Auto-Apply"
6. Watch it work!
```

---

### Step 4: Verify Applications (2 minutes)

```
1. Go to: https://app.jobscale.com/applications
2. Check status shows "Applied"
3. Check email for Indeed confirmations
```

---

## 📁 Extension Structure

```
extension/
├── manifest.json              # Extension configuration
├── background/
│   └── background.js          # Service worker (queue management)
├── content/
│   ├── indeed-adapter.js      # Indeed automation
│   ├── linkedin-adapter.js    # LinkedIn Easy Apply
│   ├── greenhouse-adapter.js  # Greenhouse forms
│   └── lever-adapter.js       # Lever forms
├── popup/
│   ├── popup.html             # Extension popup UI
│   └── popup.js               # Popup logic
└── icons/
    ├── icon-16.png
    ├── icon-32.png
    ├── icon-48.png
    └── icon-128.png
```

---

## 🔧 Backend Requirements

### API Endpoints Needed

```python
# backend/app/api/applications.py

@router.get("/applications/pending")
async def get_pending_applications(user: User = Depends(get_current_user)):
    """Get jobs user has pre-approved for application"""
    
    applications = await db.applications.find({
        "user_id": user.id,
        "status": "pending_application"
    }).to_list()
    
    jobs = []
    for app in applications:
        job = await db.jobs.find_one({"_id": app["job_id"]})
        jobs.append({
            "id": str(app["_id"]),
            "job_id": str(job["_id"]),
            "url": job["url"],
            "title": job["title"],
            "company": job["company"],
            "source": job["source"]
        })
    
    return {"applications": jobs}


@router.post("/applications/{application_id}/submit")
async def submit_application(
    application_id: str,
    status: str,
    error_message: str = None,
    submitted_at: datetime = None,
    user: User = Depends(get_current_user)
):
    """Update application status after submission"""
    
    await db.applications.update_one(
        {"_id": ObjectId(application_id)},
        {
            "$set": {
                "status": "applied" if status == "applied" else "failed",
                "error_message": error_message,
                "applied_at": submitted_at or datetime.now(),
                "source": "extension"
            }
        }
    )
    
    return {"success": True}


@router.get("/cvs/default")
async def get_default_cv(user: User = Depends(get_current_user)):
    """Get user's default CV"""
    
    cv = await db.cvs.find_one({
        "user_id": user.id,
        "is_default": True
    })
    
    if not cv:
        # Fall back to most recent
        cv = await db.cvs.find_one({"user_id": user.id})
    
    if not cv:
        raise HTTPException(404, "No CV found")
    
    return {
        "id": str(cv["_id"]),
        "download_url": f"/api/v1/cvs/{cv['_id']}/download"
    }
```

---

## 🧪 Testing Checklist

### Test 1: Indeed Application

```
✅ Job: Software Engineer at Stripe
✅ URL: indeed.com/viewjob?jk=xxx
✅ Expected: Auto-fills form, uploads CV, submits
✅ Verify: Indeed confirmation email received
```

---

### Test 2: LinkedIn Easy Apply

```
✅ Job: Senior Developer at GitLab
✅ URL: linkedin.com/jobs/view/xxx
✅ Expected: Detects Easy Apply, fills steps, submits
✅ Verify: LinkedIn application shows in "My Jobs"
```

---

### Test 3: Greenhouse Application

```
✅ Job: Backend Engineer at Startup
✅ URL: greenhouse.io/company/jobs/xxx
✅ Expected: Fills form, uploads CV, submits
✅ Verify: Greenhouse confirmation email
```

---

### Test 4: Lever Application

```
✅ Job: Full Stack at Tech Company
✅ URL: lever.co/company/jobs/xxx
✅ Expected: Fills form, uploads CV, submits
✅ Verify: Lever confirmation email
```

---

### Test 5: Pre-Approval Check

```
✅ Select 3 jobs from dashboard
✅ Click "Start Auto-Apply"
✅ Extension should only apply to those 3
✅ Visit random job page → Extension stays hidden
```

---

### Test 6: Error Handling

```
✅ Already applied job → Shows error, skips
✅ External application (not Easy Apply) → Shows error, skips
✅ Timeout (>5 min) → Shows error, moves to next
✅ Network error → Retries, then shows error
```

---

### Test 7: Progress Tracking

```
✅ Popup shows real-time progress
✅ Stats update (success/failed/pending)
✅ Job list shows individual status
✅ Notification when complete
```

---

### Test 8: Resume After Restart

```
✅ Start auto-apply (5 jobs)
✅ Close Chrome after 2 jobs
✅ Reopen Chrome
✅ Extension should resume from job 3
```

---

## 🐛 Common Issues & Fixes

### Issue 1: "No pending applications found"

**Cause:** Jobs not marked as pending in dashboard

**Fix:**
```
1. Go to dashboard
2. Click "Apply" on jobs (not just "View")
3. Check backend: status = "pending_application"
```

---

### Issue 2: "Apply button not found" (Indeed)

**Cause:** Indeed changed HTML or job is external

**Fix:**
```
1. Check if job has "Apply on company site" button
2. If external, skip (can't automate)
3. Update selector in indeed-adapter.js
```

---

### Issue 3: "Not an Easy Apply job" (LinkedIn)

**Cause:** Job requires external application

**Fix:**
```
This is expected - LinkedIn has two types:
- Easy Apply (we can automate)
- External apply (user must apply manually)

Skip these jobs or apply manually.
```

---

### Issue 4: CV upload fails

**Cause:** File upload API changed

**Fix:**
```javascript
// Try alternative upload method
const fileInput = document.querySelector('input[type="file"]');
await fileInput.click();
await sleep(1000);
// Use keyboard to type file path (advanced)
```

---

### Issue 5: Extension not loading

**Cause:** Manifest error or missing files

**Fix:**
```
1. Check chrome://extensions/ for errors
2. Click "Reload" on extension card
3. Check console for specific errors
4. Verify all files exist in extension/
```

---

## 📊 Success Metrics

### Target Success Rates

| Site | Target | Minimum |
|------|--------|---------|
| Indeed | 90%+ | 80%+ |
| LinkedIn Easy Apply | 85%+ | 75%+ |
| Greenhouse | 95%+ | 90%+ |
| Lever | 95%+ | 90%+ |
| **Overall** | **90%+** | **85%+** |

---

### Track These Metrics

```python
# backend/app/services/analytics.py

metrics = {
    "total_applications": 0,
    "successful_applications": 0,
    "failed_applications": 0,
    "success_rate": 0,
    
    "by_site": {
        "indeed": {"success": 0, "failed": 0},
        "linkedin": {"success": 0, "failed": 0},
        "greenhouse": {"success": 0, "failed": 0},
        "lever": {"success": 0, "failed": 0}
    },
    
    "average_time_per_application": 0,  # seconds
    "common_errors": {}
}
```

---

## 🚀 Deployment

### For Beta Testing (Sideload)

```
1. Zip extension folder
2. Send to beta testers
3. They load unpacked (as above)
4. Collect feedback
5. Iterate quickly
```

---

### For Public Release (Chrome Store)

```
1. Create developer account ($5 one-time)
2. Prepare assets:
   - Screenshots (1280x800, 640x400)
   - Promotional images (440x280, 920x380)
   - Icon (128x128)
   - Description
3. Submit for review
4. Wait 3-7 days
5. Address any feedback
6. Publish!
```

---

## 📝 Next Steps

1. ✅ Create icon files (16, 32, 48, 128 px)
2. ✅ Add backend endpoints (pending applications)
3. ✅ Test on 10 real jobs
4. ✅ Fix any bugs found
5. ✅ Beta test with 5 users
6. ✅ Iterate based on feedback
7. ✅ Submit to Chrome Store (optional)

---

*Extension is ready to build and test!* 🎯
