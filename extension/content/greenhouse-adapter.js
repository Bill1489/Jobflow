/**
 * JobScale Auto-Apply - Greenhouse Adapter
 * 
 * Handles auto-filling and submitting Greenhouse job applications.
 * Only runs when triggered by background script (pre-approved jobs only).
 */

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'START_APPLICATION') {
    startGreenhouseApplication(message.job, message.userData)
      .then((result) => sendResponse(result))
      .catch((error) => sendResponse({ success: false, error: error.message }));
    
    return true;
  }
});

async function startGreenhouseApplication(job, userData) {
  console.log('[JobScale Greenhouse] Starting application for:', job.title);
  
  try {
    // Find the application form
    const form = await waitForSelector('form#application_form, form[name="application_form"]', 10000);
    
    if (!form) {
      throw new Error('Application form not found');
    }
    
    // Fill personal information
    await safeFill('input[name="name"]', `${userData.firstName} ${userData.lastName}`);
    await safeFill('input[name="first_name"]', userData.firstName);
    await safeFill('input[name="last_name"]', userData.lastName);
    await safeFill('input[name="email"]', userData.email);
    await safeFill('input[name="phone"]', userData.phone);
    
    // Fill location
    await safeFill('input[name="location"]', userData.location);
    
    // Upload CV
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
      console.log('[JobScale Greenhouse] Uploading CV...');
      await uploadFile(fileInput, userData.cvBlob, 'resume.pdf');
      await sleep(2000);
    }
    
    // Fill optional note/cover letter
    const noteField = document.querySelector('textarea[name="note"], textarea[name="cover_letter"]');
    if (noteField && !noteField.value) {
      noteField.value = `I'm very interested in this ${job.title} position at ${job.company}. Please see my attached CV for details.`;
      noteField.dispatchEvent(new Event('input', { bubbles: true }));
    }
    
    // Fill any additional fields
    await fillAdditionalFields(userData);
    
    // Submit
    const submitButton = document.querySelector('input[type="submit"], button[type="submit"]');
    if (submitButton) {
      console.log('[JobScale Greenhouse] Submitting application...');
      submitButton.click();
      
      // Wait for confirmation
      const success = await waitForConfirmation();
      
      if (success) {
        console.log('[JobScale Greenhouse] Application submitted successfully!');
        return { success: true, jobId: job.id };
      } else {
        throw new Error('No confirmation received');
      }
    } else {
      throw new Error('Submit button not found');
    }
    
  } catch (error) {
    console.error('[JobScale Greenhouse] Application failed:', error);
    return { success: false, error: error.message };
  }
}

async function fillAdditionalFields(userData) {
  const inputs = document.querySelectorAll('input[type="text"]:not([readonly]), textarea:not([readonly])');
  
  for (const input of inputs) {
    if (!input.value) {
      const label = input.closest('label')?.textContent.toLowerCase() || '';
      
      if (label.includes('website') || label.includes('portfolio')) {
        input.value = userData.portfolioUrl || 'N/A';
      } else if (label.includes('linkedin')) {
        input.value = userData.linkedinUrl || 'N/A';
      } else if (label.includes('salary')) {
        input.value = userData.expectedSalary || 'Negotiable';
      } else if (label.includes('notice')) {
        input.value = '2 weeks';
      } else {
        input.value = 'Please see my CV for details';
      }
      
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }
  }
}

async function uploadFile(fileInput, fileBlob, fileName) {
  const file = new File([fileBlob], fileName, { type: 'application/pdf' });
  const dataTransfer = new DataTransfer();
  dataTransfer.items.add(file);
  fileInput.files = dataTransfer.files;
  fileInput.dispatchEvent(new Event('change', { bubbles: true }));
}

async function waitForConfirmation() {
  try {
    await waitForSelector('.application_success, .success-message, :contains("successfully")', 15000);
    return true;
  } catch (error) {
    const modalStillOpen = document.querySelector('form#application_form');
    return !modalStillOpen;
  }
}

async function safeFill(selector, value) {
  try {
    const element = await waitForSelector(selector, 2000);
    if (element) {
      element.value = value;
      element.dispatchEvent(new Event('input', { bubbles: true }));
      await sleep(100);
    }
  } catch (error) {}
}

function waitForSelector(selector, timeout = 5000) {
  return new Promise((resolve) => {
    let element = document.querySelector(selector);
    if (element) {
      resolve(element);
      return;
    }
    
    const observer = new MutationObserver(() => {
      element = document.querySelector(selector);
      if (element) {
        observer.disconnect();
        resolve(element);
      }
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
    
    setTimeout(() => {
      observer.disconnect();
      resolve(null);
    }, timeout);
  });
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

console.log('[JobScale Greenhouse] Adapter loaded');
