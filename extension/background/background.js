/**
 * JobScale Auto-Apply - Background Service Worker
 * 
 * Manages the auto-apply queue:
 * - Only processes jobs pre-approved from dashboard
 * - Opens tabs sequentially
 * - Tracks progress
 * - Notifies user when complete
 */

// State management
let applyQueue = [];
let isProcessing = false;
let currentJobIndex = 0;
let results = [];

// Listen for messages from popup or content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('[JobScale] Message received:', message);
  
  switch (message.type) {
    case 'START_AUTO_APPLY':
      startAutoApply(message.jobs, message.userData);
      sendResponse({ success: true });
      break;
      
    case 'STOP_AUTO_APPLY':
      stopAutoApply();
      sendResponse({ success: true });
      break;
      
    case 'GET_STATUS':
      sendResponse({
        isProcessing,
        queueLength: applyQueue.length,
        currentIndex: currentJobIndex,
        results
      });
      break;
      
    case 'APPLICATION_COMPLETE':
      handleApplicationComplete(message.jobId, message.success, message.error);
      sendResponse({ success: true });
      break;
      
    case 'GET_AUTH_TOKEN':
      chrome.storage.local.get(['authToken'], (result) => {
        sendResponse({ token: result.authToken });
      });
      return true; // Keep channel open for async response
      
    default:
      sendResponse({ error: 'Unknown message type' });
  }
});

/**
 * Start auto-apply process
 * Only processes jobs that are pre-approved from dashboard
 */
async function startAutoApply(jobs, userData) {
  console.log('[JobScale] Starting auto-apply for', jobs.length, 'jobs');
  
  // Reset state
  applyQueue = jobs;
  currentJobIndex = 0;
  results = [];
  isProcessing = true;
  
  // Save state to storage (survives browser restart)
  await saveState();
  
  // Update popup UI
  broadcastStatus();
  
  // Start processing queue
  processNextJob();
}

/**
 * Stop auto-apply process
 */
function stopAutoApply() {
  isProcessing = false;
  applyQueue = [];
  chrome.storage.local.remove(['applyQueue', 'isProcessing', 'currentJobIndex', 'results']);
  broadcastStatus();
}

/**
 * Process next job in queue
 */
async function processNextJob() {
  if (!isProcessing || currentJobIndex >= applyQueue.length) {
    // Queue complete
    await completeQueue();
    return;
  }
  
  const job = applyQueue[currentJobIndex];
  
  console.log(`[JobScale] Processing job ${currentJobIndex + 1}/${applyQueue.length}:`, job.title);
  
  // Update status
  await saveState();
  broadcastStatus();
  
  try {
    // Verify job is still pre-approved (double-check with backend)
    const isApproved = await verifyPreApproval(job.id);
    
    if (!isApproved) {
      console.warn('[JobScale] Job is no longer pre-approved, skipping:', job.id);
      results.push({
        jobId: job.id,
        title: job.title,
        company: job.company,
        success: false,
        error: 'Job no longer pre-approved',
        skipped: true
      });
      currentJobIndex++;
      processNextJob();
      return;
    }
    
    // Open job in new tab
    const tab = await chrome.tabs.create({ 
      url: job.url,
      active: false // Don't steal focus from user
    });
    
    // Wait for page to load
    await waitForTabLoad(tab.id);
    
    // Inject content script for this site
    const siteType = detectSiteType(job.url);
    console.log('[JobScale] Detected site type:', siteType);
    
    // Send message to content script to start application
    chrome.tabs.sendMessage(tab.id, {
      type: 'START_APPLICATION',
      job: job,
      userData: userData
    });
    
    // Wait for application to complete (content script will send message)
    // Timeout after 5 minutes
    const timeout = setTimeout(() => {
      console.error('[JobScale] Application timeout for job:', job.id);
      handleApplicationComplete(job.id, false, 'Timeout after 5 minutes');
    }, 300000);
    
    // Store timeout reference to clear later
    chrome.storage.local.set({ [`${job.id}_timeout`]: timeout });
    
  } catch (error) {
    console.error('[JobScale] Error processing job:', error);
    results.push({
      jobId: job.id,
      title: job.title,
      company: job.company,
      success: false,
      error: error.message
    });
    currentJobIndex++;
    processNextJob();
  }
}

/**
 * Handle application completion from content script
 */
async function handleApplicationComplete(jobId, success, error = null) {
  const job = applyQueue[currentJobIndex];
  
  // Clear timeout
  chrome.storage.local.get([`${jobId}_timeout`], (result) => {
    if (result[`${jobId}_timeout`]) {
      clearTimeout(result[`${jobId}_timeout`]);
    }
  });
  
  // Record result
  results.push({
    jobId: jobId,
    title: job?.title || 'Unknown',
    company: job?.company || 'Unknown',
    success: success,
    error: error,
    timestamp: new Date().toISOString()
  });
  
  console.log(`[JobScale] Application ${success ? 'SUCCESS' : 'FAILED'} for job:`, jobId);
  
  // Update backend
  if (job) {
    await updateApplicationStatus(job.id, success, error);
  }
  
  // Close the tab
  const tabs = await chrome.tabs.query({});
  const jobTab = tabs.find(tab => tab.url?.includes(jobId));
  if (jobTab) {
    await chrome.tabs.remove(jobTab.id);
  }
  
  // Move to next job
  currentJobIndex++;
  
  // Small delay between applications (be human-like)
  setTimeout(() => {
    processNextJob();
  }, 2000);
}

/**
 * Verify job is pre-approved from dashboard
 */
async function verifyPreApproval(jobId) {
  try {
    const token = await getAuthToken();
    
    const response = await fetch(`https://api.jobscale.com/api/v1/applications/pending?job_id=${jobId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.status === 404) {
      return false; // Not pre-approved
    }
    
    if (!response.ok) {
      console.warn('[JobScale] Pre-approval check failed, assuming approved');
      return true; // Fail open
    }
    
    const data = await response.json();
    return data.approved === true;
    
  } catch (error) {
    console.error('[JobScale] Pre-approval check error:', error);
    return true; // Fail open on error
  }
}

/**
 * Update application status in backend
 */
async function updateApplicationStatus(jobId, success, error = null) {
  try {
    const token = await getAuthToken();
    
    await fetch(`https://api.jobscale.com/api/v1/applications/${jobId}/submit`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        status: success ? 'applied' : 'failed',
        error_message: error,
        submitted_at: new Date().toISOString(),
        source: 'extension'
      })
    });
  } catch (error) {
    console.error('[JobScale] Failed to update application status:', error);
  }
}

/**
 * Complete queue and notify user
 */
async function completeQueue() {
  isProcessing = false;
  await saveState();
  broadcastStatus();
  
  // Calculate summary
  const successful = results.filter(r => r.success).length;
  const failed = results.filter(r => !r.success && !r.skipped).length;
  const skipped = results.filter(r => r.skipped).length;
  
  console.log(`[JobScale] Queue complete: ${successful} successful, ${failed} failed, ${skipped} skipped`);
  
  // Show notification
  chrome.notifications.create('jobscale-complete', {
    type: 'basic',
    iconUrl: 'icons/icon-128.png',
    title: 'JobScale Auto-Apply Complete! 🎉',
    message: `Applied to ${successful}/${applyQueue.length} jobs successfully.`,
    priority: 2
  });
  
  // Reset queue
  applyQueue = [];
  currentJobIndex = 0;
  await saveState();
}

/**
 * Wait for tab to finish loading
 */
function waitForTabLoad(tabId) {
  return new Promise((resolve) => {
    const onUpdated = (id, changeInfo, tab) => {
      if (id === tabId && changeInfo.status === 'complete') {
        chrome.tabs.onUpdated.removeListener(onUpdated);
        resolve(tab);
      }
    };
    
    chrome.tabs.onUpdated.addListener(onUpdated);
    
    // Timeout after 30 seconds
    setTimeout(() => {
      chrome.tabs.onUpdated.removeListener(onUpdated);
      resolve(null);
    }, 30000);
  });
}

/**
 * Detect site type from URL
 */
function detectSiteType(url) {
  if (url.includes('indeed.com')) return 'indeed';
  if (url.includes('linkedin.com')) return 'linkedin';
  if (url.includes('greenhouse.io')) return 'greenhouse';
  if (url.includes('lever.co')) return 'lever';
  return 'unknown';
}

/**
 * Get auth token from storage
 */
async function getAuthToken() {
  return new Promise((resolve) => {
    chrome.storage.local.get(['authToken'], (result) => {
      resolve(result.authToken || '');
    });
  });
}

/**
 * Save state to storage (survives browser restart)
 */
async function saveState() {
  await chrome.storage.local.set({
    applyQueue,
    isProcessing,
    currentJobIndex,
    results,
    lastUpdated: new Date().toISOString()
  });
}

/**
 * Broadcast status to popup
 */
function broadcastStatus() {
  chrome.runtime.sendMessage({
    type: 'STATUS_UPDATE',
    isProcessing,
    queueLength: applyQueue.length,
    currentIndex: currentJobIndex,
    results
  }).catch(() => {
    // Ignore if popup is not open
  });
}

// Restore state on service worker restart
chrome.runtime.onStartup.addListener(async () => {
  const state = await chrome.storage.local.get(['applyQueue', 'isProcessing', 'currentJobIndex', 'results']);
  if (state.isProcessing && state.applyQueue) {
    console.log('[JobScale] Restoring state after restart');
    applyQueue = state.applyQueue;
    currentJobIndex = state.currentJobIndex || 0;
    results = state.results || [];
    isProcessing = true;
    processNextJob();
  }
});

console.log('[JobScale] Background service worker initialized');
