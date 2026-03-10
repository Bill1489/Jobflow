/**
 * JobScale Auto-Apply - Indeed Adapter
 * 
 * Handles auto-filling and submitting Indeed job applications.
 * Only runs when triggered by background script (pre-approved jobs only).
 */

// Listen for messages from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('[JobScale Indeed] Message received:', message);
  
  if (message.type === 'START_APPLICATION') {
    startIndeedApplication(message.job, message.userData)
      .then((result) => {
        sendResponse(result);
      })
      .catch((error) => {
        console.error('[JobScale Indeed] Error:', error);
        sendResponse({ success: false, error: error.message });
      });
    
    return true; // Keep channel open for async response
  }
});

/**
 * Start Indeed application process
 */
async function startIndeedApplication(job, userData) {
  console.log('[JobScale Indeed] Starting application for:', job.title);
  
  try {
    // Wait for Indeed Apply button to appear
    console.log('[JobScale Indeed] Waiting for Apply button...');
    const applyButton = await waitForSelector('#indeedApplyButton, [data-testid="indeed-apply-button"]', 10000);
    
    if (!applyButton) {
      // Check if already applied
      if (await isAlreadyApplied()) {
        throw new Error('Already applied to this job');
      }
      
      // Check if external application
      if (await isExternalApplication()) {
        throw new Error('External application (not Indeed Apply)');
      }
      
      throw new Error('Apply button not found');
    }
    
    // Click Apply button
    console.log('[JobScale Indeed] Clicking Apply button...');
    applyButton.click();
    
    // Wait for application modal
    console.log('[JobScale Indeed] Waiting for application modal...');
    const modal = await waitForSelector('#indeedApplyContainer, [data-testid="indeed-apply-modal"]', 10000);
    
    if (!modal) {
      throw new Error('Application modal did not appear');
    }
    
    // Wait a moment for modal to fully render
    await sleep(1000);
    
    // Fill out the application form
    console.log('[JobScale Indeed] Filling application form...');
    await fillApplicationForm(userData);
    
    // Handle screening questions if present
    console.log('[JobScale Indeed] Checking for screening questions...');
    await handleScreeningQuestions(userData);
    
    // Review and submit
    console.log('[JobScale Indeed] Submitting application...');
    await submitApplication();
    
    // Wait for confirmation
    console.log('[JobScale Indeed] Waiting for confirmation...');
    const success = await waitForConfirmation();
    
    if (success) {
      console.log('[JobScale Indeed] Application submitted successfully!');
      return { success: true, jobId: job.id };
    } else {
      throw new Error('No confirmation received');
    }
    
  } catch (error) {
    console.error('[JobScale Indeed] Application failed:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Fill out the Indeed application form
 */
async function fillApplicationForm(userData) {
  // Personal information
  await safeFill('input[name="firstName"]', userData.firstName);
  await safeFill('input[name="lastName"]', userData.lastName);
  await safeFill('input[name="email"]', userData.email);
  await safeFill('input[name="phone"]', userData.phone);
  
  // Location (if asked)
  await safeFill('input[name="city"]', userData.city);
  await safeFill('input[name="state"]', userData.state);
  await safeFill('input[name="zipcode"]', userData.zipcode);
  
  // Experience information (if asked)
  await safeFill('input[name="currentEmployer"]', userData.currentCompany);
  await safeFill('input[name="currentTitle"]', userData.currentTitle);
  
  // Upload CV/Resume
  const fileInput = document.querySelector('input[type="file"]');
  if (fileInput) {
    console.log('[JobScale Indeed] Uploading CV...');
    await uploadCV(fileInput, userData.cvBlob);
  }
  
  // Additional fields (auto-fill with reasonable defaults)
  await autoFillAdditionalFields();
}

/**
 * Handle Indeed screening questions
 */
async function handleScreeningQuestions(userData) {
  const questions = document.querySelectorAll('.screening-question, [data-testid="screening-question"]');
  
  if (questions.length === 0) {
    console.log('[JobScale Indeed] No screening questions found');
    return;
  }
  
  console.log('[JobScale Indeed] Found', questions.length, 'screening questions');
  
  for (const question of questions) {
    await handleSingleQuestion(question, userData);
  }
}

/**
 * Handle a single screening question
 */
async function handleSingleQuestion(question, userData) {
  const questionText = question.textContent.toLowerCase();
  
  // Yes/No questions - default to positive answers
  const yesButton = question.querySelector('button:contains("Yes"), [value="Yes"], [data-testid="yes-button"]');
  const noButton = question.querySelector('button:contains("No"), [value="No"], [data-testid="no-button"]');
  
  if (yesButton && noButton) {
    // Determine best answer based on question
    const shouldSayYes = !questionText.includes('convicted') && 
                         !questionText.includes('arrested') && 
                         !questionText.includes('legal right');
    
    if (shouldSayYes) {
      yesButton.click();
    } else {
      noButton.click();
    }
    await sleep(500);
    return;
  }
  
  // Multiple choice - select first reasonable option
  const selects = question.querySelectorAll('select');
  for (const select of selects) {
    if (select.options.length > 1) {
      select.selectedIndex = 1; // Select second option (usually not "Select...")
      select.dispatchEvent(new Event('change'));
    }
  }
  
  // Text fields - fill with reasonable defaults
  const textFields = question.querySelectorAll('input[type="text"], textarea');
  for (const field of textFields) {
    const label = field.closest('label')?.textContent.toLowerCase() || '';
    
    if (label.includes('notice')) {
      field.value = '2 weeks';
    } else if (label.includes('salary')) {
      field.value = userData.expectedSalary || 'Negotiable';
    } else if (label.includes('start')) {
      field.value = 'Immediately';
    } else {
      field.value = 'Please see my CV for details';
    }
    
    field.dispatchEvent(new Event('input', { bubbles: true }));
  }
  
  await sleep(500);
}

/**
 * Auto-fill additional fields
 */
async function autoFillAdditionalFields() {
  // Find all unfilled text inputs
  const inputs = document.querySelectorAll('input[type="text"]:not([readonly]), textarea:not([readonly])');
  
  for (const input of inputs) {
    if (!input.value) {
      const label = input.closest('label')?.textContent.toLowerCase() || 
                    input.getAttribute('aria-label')?.toLowerCase() || '';
      
      // Skip if already handled
      if (label.includes('name') || label.includes('email') || label.includes('phone')) {
        continue;
      }
      
      // Fill with reasonable default
      input.value = 'Please see my CV for details';
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }
  }
  
  await sleep(500);
}

/**
 * Upload CV/Resume
 */
async function uploadCV(fileInput, cvBlob) {
  // Create a File object from the blob
  const file = new File([cvBlob], 'resume.pdf', { type: 'application/pdf' });
  
  // Create a DataTransfer object to set the file
  const dataTransfer = new DataTransfer();
  dataTransfer.items.add(file);
  
  // Set the file input
  fileInput.files = dataTransfer.files;
  fileInput.dispatchEvent(new Event('change', { bubbles: true }));
  
  // Wait for upload to complete
  await sleep(2000);
}

/**
 * Submit the application
 */
async function submitApplication() {
  // Find submit button
  const submitButton = document.querySelector(
    'button[type="submit"], [data-testid="submit-application"], button:contains("Submit Application")'
  );
  
  if (!submitButton) {
    throw new Error('Submit button not found');
  }
  
  // Click submit
  submitButton.click();
}

/**
 * Wait for application confirmation
 */
async function waitForConfirmation() {
  try {
    // Wait for success message
    await waitForSelector(
      '.application-success, [data-testid="application-success"], .thank-you, :contains("successfully")',
      15000
    );
    return true;
  } catch (error) {
    // Check if there's an error message
    const errorMessage = document.querySelector('.error-message, [data-testid="error-message"]');
    if (errorMessage) {
      throw new Error(errorMessage.textContent);
    }
    
    // Some sites don't show confirmation but also no error
    // Check if we're still on the application page
    const stillOnApplication = document.querySelector('#indeedApplyContainer');
    if (!stillOnApplication) {
      // We've been redirected, likely successful
      return true;
    }
    
    return false;
  }
}

/**
 * Check if already applied to this job
 */
async function isAlreadyApplied() {
  const appliedMessage = document.querySelector(
    ':contains("already applied"), :contains("You\'ve applied"), [data-testid="already-applied"]'
  );
  return !!appliedMessage;
}

/**
 * Check if this is an external application (redirects to company site)
 */
async function isExternalApplication() {
  const externalButton = document.querySelector(
    'a:contains("Apply on company site"), a:contains("Apply externally"), [data-testid="external-apply"]'
  );
  return !!externalButton;
}

/**
 * Safely fill a field (doesn't throw if not found)
 */
async function safeFill(selector, value) {
  try {
    const element = await waitForSelector(selector, 2000);
    if (element) {
      element.value = value;
      element.dispatchEvent(new Event('input', { bubbles: true }));
      element.dispatchEvent(new Event('change', { bubbles: true }));
      await sleep(100); // Human-like typing delay
    }
  } catch (error) {
    // Field not found, skip
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

console.log('[JobScale Indeed] Adapter loaded');
