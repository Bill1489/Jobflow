/**
 * JobScale Auto-Apply - Popup Script
 * 
 * Handles popup UI interactions and communicates with background script.
 */

// DOM Elements
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const statsContainer = document.getElementById('statsContainer');
const successCount = document.getElementById('successCount');
const failedCount = document.getElementById('failedCount');
const pendingCount = document.getElementById('pendingCount');
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const dashboardBtn = document.getElementById('dashboardBtn');
const jobList = document.getElementById('jobList');
const emptyState = document.getElementById('emptyState');

// State
let isProcessing = false;
let jobs = [];

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  console.log('[JobScale Popup] Initialized');
  
  // Load saved state
  await loadState();
  
  // Set up event listeners
  startBtn.addEventListener('click', startAutoApply);
  stopBtn.addEventListener('click', stopAutoApply);
  dashboardBtn.addEventListener('click', openDashboard);
  
  // Listen for messages from background
  chrome.runtime.onMessage.addListener((message) => {
    if (message.type === 'STATUS_UPDATE') {
      updateUI(message);
    }
  });
  
  // Get current status
  getStatus();
});

/**
 * Load saved state from storage
 */
async function loadState() {
  try {
    const result = await chrome.storage.local.get(['applyQueue', 'isProcessing', 'currentJobIndex', 'results']);
    
    if (result.applyQueue && result.applyQueue.length > 0) {
      jobs = result.applyQueue;
      isProcessing = result.isProcessing || false;
      
      if (isProcessing) {
        updateUI({
          isProcessing: true,
          queueLength: jobs.length,
          currentIndex: result.currentJobIndex || 0,
          results: result.results || []
        });
      } else {
        showJobList(jobs, result.results || []);
      }
    }
  } catch (error) {
    console.error('[JobScale Popup] Error loading state:', error);
  }
}

/**
 * Get current status from background
 */
function getStatus() {
  chrome.runtime.sendMessage({ type: 'GET_STATUS' }, (response) => {
    if (response) {
      updateUI(response);
    }
  });
}

/**
 * Start auto-apply process
 */
async function startAutoApply() {
  try {
    // Get auth token
    const tokenResult = await chrome.runtime.sendMessage({ type: 'GET_AUTH_TOKEN' });
    const authToken = tokenResult.token;
    
    if (!authToken) {
      alert('Please log in to JobScale first');
      openDashboard();
      return;
    }
    
    // Fetch pre-approved jobs from backend
    const response = await fetch('https://api.jobscale.com/api/v1/applications/pending', {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch pending applications');
    }
    
    const data = await response.json();
    
    if (!data.applications || data.applications.length === 0) {
      alert('No pending applications found. Please select jobs from your dashboard first.');
      openDashboard();
      return;
    }
    
    jobs = data.applications;
    
    // Get user data (CV, profile info)
    const userData = await fetchUserData(authToken);
    
    // Send to background script
    chrome.runtime.sendMessage({
      type: 'START_AUTO_APPLY',
      jobs: jobs,
      userData: userData
    });
    
    // Update UI
    isProcessing = true;
    updateUI({
      isProcessing: true,
      queueLength: jobs.length,
      currentIndex: 0,
      results: []
    });
    
  } catch (error) {
    console.error('[JobScale Popup] Error starting auto-apply:', error);
    alert('Error: ' + error.message);
  }
}

/**
 * Stop auto-apply process
 */
function stopAutoApply() {
  chrome.runtime.sendMessage({ type: 'STOP_AUTO_APPLY' });
  isProcessing = false;
  updateUI({
    isProcessing: false,
    queueLength: 0,
    currentIndex: 0,
    results: []
  });
}

/**
 * Open JobScale dashboard
 */
function openDashboard() {
  chrome.tabs.create({ url: 'https://app.jobscale.com/dashboard' });
}

/**
 * Fetch user data (CV, profile info)
 */
async function fetchUserData(authToken) {
  try {
    // Get user profile
    const profileResponse = await fetch('https://api.jobscale.com/api/v1/users/me', {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!profileResponse.ok) {
      throw new Error('Failed to fetch user profile');
    }
    
    const profile = await profileResponse.json();
    
    // Get default CV
    const cvsResponse = await fetch('https://api.jobscale.com/api/v1/cvs/default', {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    let cvBlob = null;
    if (cvsResponse.ok) {
      const cvData = await cvsResponse.json();
      const cvDownloadResponse = await fetch(cvData.download_url);
      cvBlob = await cvDownloadResponse.blob();
    }
    
    return {
      firstName: profile.first_name || '',
      lastName: profile.last_name || '',
      email: profile.email || '',
      phone: profile.phone || '',
      city: profile.city || '',
      state: profile.state || '',
      zipcode: profile.zipcode || '',
      currentCompany: profile.current_company || '',
      currentTitle: profile.current_title || '',
      expectedSalary: profile.expected_salary || '',
      linkedinUrl: profile.linkedin_url || '',
      portfolioUrl: profile.portfolio_url || '',
      summary: profile.summary || '',
      cvBlob: cvBlob
    };
    
  } catch (error) {
    console.error('[JobScale Popup] Error fetching user data:', error);
    throw error;
  }
}

/**
 * Update UI with current status
 */
function updateUI(status) {
  const { isProcessing, queueLength, currentIndex, results } = status;
  
  // Update status indicator
  if (isProcessing) {
    statusDot.className = 'status-dot active';
    statusText.textContent = `Applying to jobs... (${currentIndex}/${queueLength})`;
    startBtn.style.display = 'none';
    stopBtn.style.display = 'block';
    stopBtn.disabled = false;
  } else if (results && results.length > 0) {
    statusDot.className = 'status-dot complete';
    statusText.textContent = 'Auto-apply complete!';
    startBtn.style.display = 'block';
    startBtn.disabled = false;
    stopBtn.style.display = 'none';
  } else {
    statusDot.className = 'status-dot';
    statusText.textContent = 'Ready to start';
    startBtn.style.display = 'block';
    startBtn.disabled = false;
    stopBtn.style.display = 'none';
  }
  
  // Update progress bar
  const progress = queueLength > 0 ? (currentIndex / queueLength) * 100 : 0;
  progressFill.style.width = `${progress}%`;
  progressText.textContent = `${currentIndex} / ${queueLength} jobs`;
  
  // Update stats
  if (results && results.length > 0) {
    statsContainer.style.display = 'grid';
    const successful = results.filter(r => r.success).length;
    const failed = results.filter(r => !r.success && !r.skipped).length;
    const pending = queueLength - currentIndex;
    
    successCount.textContent = successful;
    failedCount.textContent = failed;
    pendingCount.textContent = pending;
    
    // Show job list
    showJobList(jobs, results);
  } else {
    statsContainer.style.display = 'none';
    jobList.style.display = 'none';
  }
  
  // Show/hide empty state
  if (!isProcessing && (!jobs || jobs.length === 0)) {
    emptyState.style.display = 'block';
  } else {
    emptyState.style.display = 'none';
  }
}

/**
 * Show job list with results
 */
function showJobList(jobs, results) {
  jobList.innerHTML = '';
  jobList.style.display = 'block';
  
  jobs.forEach((job, index) => {
    const result = results.find(r => r.jobId === job.id);
    const status = result 
      ? (result.success ? 'success' : 'failed')
      : (index < results.length ? 'failed' : 'pending');
    
    const statusText = result
      ? (result.success ? '✅ Applied' : `❌ ${result.error}`)
      : '⏳ Pending';
    
    const jobItem = document.createElement('div');
    jobItem.className = `job-item ${status}`;
    jobItem.innerHTML = `
      <div class="job-title">
        <strong>${job.title}</strong><br>
        <span style="color: #94a3b8;">${job.company}</span>
      </div>
      <div class="job-status">${statusText}</div>
    `;
    
    jobList.appendChild(jobItem);
  });
}
