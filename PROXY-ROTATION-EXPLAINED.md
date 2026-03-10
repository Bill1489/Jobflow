# 🌐 How Proxies Work in JobScale Automation

## The Short Answer

**NO - users don't need individual proxies.**

We use a **shared proxy pool** that rotates across ALL users' applications.

---

## 🔄 How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  JobScale Backend (Railway)                            │
│  ─────────────────────────────────────────────────     │
│                                                         │
│  User 1: Apply to 10 jobs ──┐                          │
│  User 2: Apply to 5 jobs  ──┼──→ Proxy Pool ──→ Job Sites
│  User 3: Apply to 15 jobs ──┘     (Rotation)           │
│                                                         │
│  Proxy Pool: 100 residential IPs                       │
│  - Each application uses different IP                  │
│  - Rotate every 3-5 applications                       │
│  - Auto-replace blocked IPs                            │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Proxy Usage Model

### Per-Application Rotation

```python
# Each job application uses a different proxy

Application 1 (User 1, Indeed Job A) → Proxy IP #1
Application 2 (User 1, Indeed Job B) → Proxy IP #2
Application 3 (User 2, LinkedIn Job) → Proxy IP #3
Application 4 (User 3, Greenhouse)   → Proxy IP #4
Application 5 (User 1, Lever Job)    → Proxy IP #5
# Then cycle back or get new IPs
```

### Why This Works

| Reason | Explanation |
|--------|-------------|
| **Different targets** | Each app goes to different job URL |
| **Different times** | Apps spread across minutes/hours |
| **Different sessions** | Each has unique browser fingerprint |
| **Low volume per IP** | 3-5 apps per IP before rotation |

---

## 💰 Proxy Cost Model

### Residential Proxy Pricing

**Most providers charge per GB, not per IP:**

| Provider | Price | What You Get |
|----------|-------|--------------|
| **BrightData** | $15/GB | Unlimited IPs, pay for data |
| **Smartproxy** | $12/GB | Unlimited IPs, pay for data |
| **Oxylabs** | $15/GB | Unlimited IPs, pay for data |
| **IPRoyal** | $7/GB | Budget option |

---

### Estimated Usage

```
Per job application:
- Page load: ~2-5 MB
- CV upload: ~1-3 MB
- Form submission: ~500 KB
- Total: ~5-10 MB per application

Per user (10 applications):
- 10 apps × 10 MB = 100 MB = 0.1 GB

Per 100 users (10 apps each):
- 1000 apps × 10 MB = 10 GB

Monthly cost (at $15/GB):
- 10 GB × $15 = $150/month
```

---

### Cost Per User

| Users/Month | Apps/Month | Data Usage | Proxy Cost | Cost/User |
|-------------|------------|------------|------------|-----------|
| 10 | 100 | 1 GB | $15 | $1.50 |
| 100 | 1,000 | 10 GB | $150 | $1.50 |
| 500 | 5,000 | 50 GB | $750 | $1.50 |
| 1,000 | 10,000 | 100 GB | $1,500 | $1.50 |

**Marginal cost: ~$1.50 per user/month**

---

## 🔧 How Crawlee Handles Proxy Rotation

### Setup

```python
from crawlee.crawlers import PlaywrightCrawler
from crawlee.proxy_configuration import ProxyConfiguration

# Configure proxy pool
proxy_config = ProxyConfiguration(
    proxy_urls=[
        'http://user1:pass1@proxy1.brightdata.com:8080',
        'http://user2:pass2@proxy2.brightdata.com:8080',
        'http://user3:pass3@proxy3.brightdata.com:8080',
        # Add 50-100 IPs for good rotation
    ],
    
    # Auto-rotate on failure
    tiered_proxy_urls=[
        # Tier 1: Premium residential (use first)
        ['http://premium1.com:8080', 'http://premium2.com:8080'],
        # Tier 2: Standard residential (fallback)
        ['http://standard1.com:8080', 'http://standard2.com:8080'],
    ]
)

# Create crawler with proxy config
crawler = PlaywrightCrawler(
    proxy_configuration=proxy_config,
    max_request_retries=3,  # Retry with different proxy on failure
    max_session_rotations=10,  # Try up to 10 different sessions
)
```

---

### Automatic Rotation

```python
# Crawlee automatically:
# 1. Picks a random proxy from the pool for each request
# 2. Marks proxy as "bad" if it fails
# 3. Retries with a different proxy
# 4. Tracks proxy success rate

@crawler.router.default_handler
async def request_handler(context: PlaywrightCrawlingContext):
    # Context includes which proxy was used
    context.log.info(f'Using proxy: {context.proxy_info}')
    
    # If blocked, mark proxy as bad
    if await is_blocked(context.page):
        context.session.retire()  # Mark this proxy as bad
        raise context.retry()  # Retry with different proxy
```

---

## 🎯 Proxy Strategy

### How Many Proxies Do We Need?

| Scale | Proxies Needed | Cost/Month |
|-------|----------------|------------|
| **MVP (10 users)** | 10-20 IPs | $15-30 |
| **Beta (100 users)** | 30-50 IPs | $150-200 |
| **Launch (500 users)** | 50-100 IPs | $500-800 |
| **Scale (2000 users)** | 100-200 IPs | $1,500-2,500 |

---

### Proxy Types

| Type | Speed | Reliability | Cost | Use Case |
|------|-------|-------------|------|----------|
| **Datacenter** | Fast | Poor (blocked) | $5/GB | ❌ Don't use |
| **Residential** | Medium | Good | $15/GB | ✅ Primary |
| **Mobile (4G/5G)** | Slow | Excellent | $50/GB | ⚠️ For LinkedIn only |
| **ISP (Static)** | Fast | Good | $30/GB | ⚠️ For Indeed only |

---

### Recommended Mix

```
For MVP (100 users, 1000 apps/month):

Residential proxies: 90% of traffic
- 45 IPs from BrightData
- 45 IPs from Smartproxy
- Cost: ~$150/month

Mobile proxies: 10% of traffic (LinkedIn only)
- 5 IPs from BrightData mobile
- Cost: ~$50/month

Total: ~$200/month
```

---

## 📋 Implementation with Crawlee

### Proxy Configuration

```python
# backend/app/services/proxy_manager.py

import os
from crawlee.proxy_configuration import ProxyConfiguration

class JobScaleProxyManager:
    """Manage proxy pool for job applications"""
    
    def __init__(self):
        # Load proxies from environment
        self.residential_proxies = os.getenv('RESIDENTIAL_PROXIES', '').split(',')
        self.mobile_proxies = os.getenv('MOBILE_PROXIES', '').split(',')
        
        # Create proxy configuration
        self.config = ProxyConfiguration(
            proxy_urls=self.residential_proxies,
            tiered_proxy_urls=[
                self.mobile_proxies,  # Tier 1: Mobile (best)
                self.residential_proxies,  # Tier 2: Residential
            ]
        )
    
    def get_crawler_config(self, site: str):
        """Get proxy config optimized for specific site"""
        
        if 'linkedin' in site.lower():
            # LinkedIn needs mobile proxies
            return ProxyConfiguration(
                proxy_urls=self.mobile_proxies,
                tiered_proxy_urls=[
                    self.mobile_proxies,
                    self.residential_proxies,
                ]
            )
        else:
            # Other sites work with residential
            return self.config
    
    def track_success(self, proxy: str, success: bool):
        """Track proxy success rate for optimization"""
        # Store in database
        # Remove proxies with <50% success rate
        pass
```

---

### Crawler Integration

```python
# backend/app/services/application_crawler.py

from crawlee.crawlers import PlaywrightCrawler
from .proxy_manager import JobScaleProxyManager

class ApplicationCrawler:
    def __init__(self):
        self.proxy_manager = JobScaleProxyManager()
    
    async def apply_to_jobs(self, jobs: list, user_data: dict):
        """Apply to multiple jobs with proxy rotation"""
        
        # Group jobs by site (for proxy optimization)
        indeed_jobs = [j for j in jobs if 'indeed' in j['url']]
        linkedin_jobs = [j for j in jobs if 'linkedin' in j['url']]
        other_jobs = [j for j in jobs if j not in indeed_jobs + linkedin_jobs]
        
        results = []
        
        # Apply to Indeed jobs (residential proxies)
        if indeed_jobs:
            crawler = PlaywrightCrawler(
                proxy_configuration=self.proxy_manager.config,
                max_requests_per_crawl=len(indeed_jobs),
            )
            result = await self._run_crawler(crawler, indeed_jobs, user_data)
            results.extend(result)
        
        # Apply to LinkedIn jobs (mobile proxies)
        if linkedin_jobs:
            crawler = PlaywrightCrawler(
                proxy_configuration=self.proxy_manager.get_crawler_config('linkedin'),
                max_requests_per_crawl=len(linkedin_jobs),
            )
            result = await self._run_crawler(crawler, linkedin_jobs, user_data)
            results.extend(result)
        
        # Apply to other jobs (residential proxies)
        if other_jobs:
            crawler = PlaywrightCrawler(
                proxy_configuration=self.proxy_manager.config,
                max_requests_per_crawl=len(other_jobs),
            )
            result = await self._run_crawler(crawler, other_jobs, user_data)
            results.extend(result)
        
        return results
```

---

## 🔐 Security & Privacy

### What We Store

```python
# We store in database:
{
    "proxy_id": "brightdata_residential_001",
    "proxy_url": "http://***:***@proxy.brightdata.com:8080",  # Encrypted
    "success_rate": 0.85,
    "last_used": "2026-03-09T15:00:00Z",
    "total_requests": 150,
    "failed_requests": 22,
}

# We DO NOT store:
- User ↔ Proxy mapping (no need to track which user used which proxy)
- Proxy credentials in plain text (encrypt in database)
```

---

### Multi-Tenant Considerations

```
Question: Can User A's applications affect User B's?

Answer: Minimal risk, because:
1. Proxies rotate every 3-5 applications
2. Each application has unique browser fingerprint
3. Different job URLs, different sessions
4. Rate limiting per proxy (5 apps/hour max)

Risk mitigation:
- Monitor proxy success rates
- Remove bad proxies automatically
- Use multiple proxy providers
- Don't put all users on same proxy batch
```

---

## 📈 Scaling Strategy

### Phase 1: MVP (0-100 users)

```
Proxies: 50 residential IPs
Provider: BrightData or Smartproxy
Cost: $150-200/month
Management: Manual (add/remove proxies as needed)
```

---

### Phase 2: Growth (100-500 users)

```
Proxies: 100 residential + 20 mobile IPs
Providers: BrightData + Smartproxy (redundancy)
Cost: $500-800/month
Management: Semi-automated (track success rates)
```

---

### Phase 3: Scale (500-2000 users)

```
Proxies: 200 residential + 50 mobile IPs
Providers: 3+ providers (BrightData, Smartproxy, Oxylabs)
Cost: $1,500-2,500/month
Management: Automated (auto-add/remove based on performance)
```

---

## ✅ Summary

| Question | Answer |
|----------|--------|
| **Does each user need a proxy?** | ❌ No, shared pool |
| **How many proxies needed?** | 50-100 for MVP |
| **How does rotation work?** | Every 3-5 applications |
| **Cost per user?** | ~$1.50/month |
| **Which providers?** | BrightData, Smartproxy, Oxylabs |
| **Residential or mobile?** | Residential (90%), Mobile for LinkedIn (10%) |
| **How does Crawlee help?** | Built-in proxy rotation + retry logic |

---

## 🚀 Next Steps

1. **Sign up for proxy provider** (BrightData recommended)
2. **Get 50 residential proxy IPs** (~$150/month)
3. **Configure in Crawlee** (as shown above)
4. **Test on 10 jobs** (verify rotation works)
5. **Monitor success rates** (track per-proxy performance)

---

*Shared proxy pool = lower costs, simpler management.* 🎯
