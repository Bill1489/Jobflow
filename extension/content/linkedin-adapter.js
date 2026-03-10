/**
 * JobScale Auto-Apply - LinkedIn Adapter
 * 
 * Handles auto-filling and submitting LinkedIn Easy Apply applications.
 * Only works for Easy Apply jobs (not external applications).
 * Only runs when triggered by background script (pre-approved jobs only).
 */

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('[JobScale LinkedIn] Message received:', message);
  
  if (message.type === 'START_APPLICATION') {
    startLinkedInApplication(message.job, message.userData)
      .then((result) => {
        sendResponse(result);
      })
      .catch((error) => {
        console.error('[JobScale LinkedIn] Error:', error);
        sendResponse({ success: false, error: error.message });
      });
    
    return true; // Keep channel open for async response
  }
});

/**
 * Start LinkedIn Easy Apply application process
 */
async function startLinkedInApplication(job, userData) {
  console.log('[JobScale LinkedIn] Starting application for:', job.title);
  
  try {
    // Check if this is an Easy Apply job
    console.log('[JobScale LinkedIn] Checking for Easy Apply...');
    const easyApplyButton = document.querySelector(
      'button.jobs-apply-button:contains("Easy Apply"), button:contains("Easy Apply")'
    );
    
    if (!easyApplyButton) {
      throw new Error('Not an Easy Apply job - requires external application');
    }
    
    // Click Easy Apply button
    console.log('[JobScale LinkedIn] Clicking Easy Apply button...');
    easyApplyButton.click();
    
    // Wait for modal to appear
    console.log('[JobScale LinkedIn] Waiting for application modal...');
    const modal = await waitForSelector('.jobs-easy-apply-modal', 10000);
    
    if (!modal) {
      throw new Error('Application modal did not appear');
    }
    
    // Wait for modal to fully render
    await sleep(1000);
    
    // Navigate through application steps
    console.log('[JobScale LinkedIn] Processing application steps...');
    let stepCount = 0;
    const maxSteps = 10; // Safety limit
    
    while (stepCount < maxSteps) {
      stepCount++;
      console.log('[JobScale LinkedIn] Processing step', stepCount);
      
      // Check if we're on the final review step
      const submitButton = document.querySelector(
        'button[aria-label="Submit application"], button:contains("Submit application")'
      );
      
      if (submitButton) {
        // Final step - review and submit
        console.log('[JobScale LinkedIn] On final review step, submitting...');
        await sleep(1000); // Review for a moment (human-like)
        submitButton.click();
        
        // Wait for confirmation
        const success = await waitForConfirmation();
        
        if (success) {
          console.log('[JobScale LinkedIn] Application submitted successfully!');
          return { success: true, jobId: job.id };
        } else {
          throw new Error('No confirmation received');
        }
      }
      
      // Process current step
      await processApplicationStep(userData);
      
      // Click Next button
      const nextButton = document.querySelector(
        'button[aria-label="Next"], button:contains("Next"), button[aria-label="Continue"], button:contains("Continue")'
      );
      
      if (nextButton) {
        nextButton.click();
        await sleep(1000); // Wait for next step to load
      } else {
        // No next button and no submit button - something's wrong
        throw new Error('Could not navigate application steps');
      }
    }
    
    throw new Error('Too many application steps - possible loop detected');
    
  } catch (error) {
    console.error('[JobScale LinkedIn] Application failed:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Process a single application step
 */
async function processApplicationStep(userData) {
  // Look for form fields in current step
  const activeStep = document.querySelector('.jobs-easy-apply-modal [role="dialog"]');
  
  if (!activeStep) {
    console.log('[JobScale LinkedIn] No active step found');
    return;
  }
  
  // File uploads (CV/Resume)
  const fileInputs = activeStep.querySelectorAll('input[type="file"]');
  for (const fileInput of fileInputs) {
    const label = fileInput.closest('label')?.textContent.toLowerCase() || '';
    if (label.includes('resume') || label.includes('cv') || label.includes('profile')) {
      console.log('[JobScale LinkedIn] Uploading CV...');
      await uploadFile(fileInput, userData.cvBlob, 'resume.pdf');
    }
  }
  
  // Phone number fields
  const phoneFields = activeStep.querySelectorAll('input[type="tel"], input[aria-label*="phone"]');
  for (const field of phoneFields) {
    if (!field.value) {
      field.value = userData.phone;
      field.dispatchEvent(new Event('input', { bubbles: true }));
    }
  }
  
  // Text fields
  const textFields = activeStep.querySelectorAll('input[type="text"]:not([readonly]), textarea:not([readonly])');
  for (const field of textFields) {
    if (!field.value) {
      const label = field.closest('label')?.textContent.toLowerCase() || 
                    field.getAttribute('aria-label')?.toLowerCase() || '';
      
      if (label.includes('name')) {
        continue; // Skip name fields (should be pre-filled)
      }
      
      field.value = getDefaultValueForField(label, userData);
      field.dispatchEvent(new Event('input', { bubbles: true }));
    }
  }
  
  // Dropdown selects
  const selects = activeStep.querySelectorAll('select');
  for (const select of selects) {
    if (select.value === '' || select.value === '0') {
      // Select first non-empty option
      for (let i = 1; i < select.options.length; i++) {
        if (select.options[i].value && select.options[i].value !== '0') {
          select.selectedIndex = i;
          select.dispatchEvent(new Event('change', { bubbles: true }));
          break;
        }
      }
    }
  }
  
  // Radio buttons (select first option for most questions)
  const radioGroups = {};
  const radioButtons = activeStep.querySelectorAll('input[type="radio"]');
  for (const radio of radioButtons) {
    const name = radio.name;
    if (name && !radioGroups[name]) {
      radioGroups[name] = radio;
    }
  }
  
  for (const radio of Object.values(radioGroups)) {
    if (!radio.checked) {
      radio.click();
      await sleep(300);
    }
  }
  
  // Checkboxes (auto-check reasonable ones)
  const checkboxes = activeStep.querySelectorAll('input[type="checkbox"]');
  for (const checkbox of checkboxes) {
    const label = checkbox.closest('label')?.textContent.toLowerCase() || '';
    
    // Auto-check if it's about receiving communications or reasonable terms
    if (label.includes('receive') || label.includes('agree') || label.includes('terms')) {
      if (!checkbox.checked) {
        checkbox.click();
        await sleep(300);
      }
    }
  }
  
  await sleep(500);
}

/**
 * Get default value for a field based on label
 */
function getDefaultValueForField(label, userData) {
  label = label.toLowerCase();
  
  if (label.includes('notice')) return '2 weeks';
  if (label.includes('salary') || label.includes('compensation')) return userData.expectedSalary || 'Negotiable';
  if (label.includes('start') || label.includes('availability')) return 'Immediately';
  if (label.includes('linkedin')) return userData.linkedinUrl || 'N/A';
  if (label.includes('website') || label.includes('portfolio')) return userData.portfolioUrl || 'N/A';
  if (label.includes('summary') || label.includes('about')) return userData.summary || 'Please see my CV for details';
  if (label.includes('reason')) return 'Looking for new opportunities';
  if (label.includes('current')) return userData.currentCompany || 'N/A';
  if (label.includes('title')) return userData.currentTitle || 'N/A';
  
  return 'Please see my CV for details';
}

/**
 * Upload file (CV/Resume)
 */
async function uploadFile(fileInput, fileBlob, fileName) {
  try {
    const file = new File([fileBlob], fileName, { type: 'application/pdf' });
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(file);
    fileInput.files = dataTransfer.files;
    fileInput.dispatchEvent(new Event('change', { bubbles: true }));
    await sleep(2000); // Wait for upload
  } catch (error) {
    console.error('[JobScale LinkedIn] File upload failed:', error);
  }
}

/**
 * Wait for application confirmation
 */
async function waitForConfirmation() {
  try {
    // Wait for success message
    await waitForSelector(
      '.jobs-easy-apply-success, [data-test-application-success], :contains("successfully"), :contains("application sent")',
      15000
    );
    return true;
  } catch (error) {
    // Check if there's an error message
    const errorMessage = document.querySelector('.error-message, [data-test-application-error]');
    if (errorMessage) {
      throw new Error(errorMessage.textContent);
    }
    
    // Check if modal closed (often means success on LinkedIn)
    const modalStillOpen = document.querySelector('.jobs-easy-apply-modal');
    if (!modalStillOpen) {
      return true;
    }
    
    return false;
  }
}

/**
 * Wait for selector to appear
 */
function waitForSelector(selector, timeout = 5000) {
  return new Promise((resolve) => {
    // Try to find immediately
    let element = document.querySelector(selector);
    if (element) {
      resolve(element);
      return;
    }
    
    // Create observer
    const observer = new MutationObserver(() => {
      element = document.querySelector(selector);
      if (element) {
        observer.disconnect();
        resolve(element);
      }
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
    
    // Timeout
    setTimeout(() => {
      observer.disconnect();
      resolve(null);
    }, timeout);
  });
}

/**
 * Sleep for specified milliseconds
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

console.log('[JobScale LinkedIn] Adapter loaded');
