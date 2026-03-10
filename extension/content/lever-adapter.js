/**
 * JobScale Auto-Apply - Lever Adapter
 * 
 * Handles auto-filling and submitting Lever job applications.
 * Only runs when triggered by background script (pre-approved jobs only).
 */

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'START_APPLICATION') {
    startLeverApplication(message.job, message.userData)
      .then((result) => sendResponse(result))
      .catch((error) => sendResponse({ success: false, error: error.message }));
    
    return true;
  }
});

async function startLeverApplication(job, userData) {
  console.log('[JobScale Lever] Starting application for:', job.title);
  
  try {
    // Find the application form
    const form = await waitForSelector('form[enzyme="applicationForm"], form[name="application_form"]', 10000);
    
    if (!form) {
      throw new Error('Application form not found');
    }
    
    // Fill personal information
    await safeFill('input[name="name"]', `${userData.firstName} ${userData.lastName}`);
    await safeFill('input[placeholder*="first name"]', userData.firstName);
    await safeFill('input[placeholder*="last name"]', userData.lastName);
    await safeFill('input[type="email"]', userData.email);
    await safeFill('input[type="tel"]', userData.phone);
    
    // Upload CV
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
      console.log('[JobScale Lever] Uploading CV...');
      await uploadFile(fileInput, userData.cvBlob, 'resume.pdf');
      await sleep(2000);
    }
    
    // Fill additional fields
    await fillAdditionalFields(userData);
    
    // Submit
    const submitButton = document.querySelector('button[type="submit"], input[type="submit"]');
    if (submitButton) {
      console.log('[JobScale Lever] Submitting application...');
      submitButton.click();
      
      // Wait for confirmation
      const success = await waitForConfirmation();
      
      if (success) {
        console.log('[JobScale Lever] Application submitted successfully!');
        return { success: true, jobId: job.id };
      } else {
        throw new Error('No confirmation received');
      }
    } else {
      throw new Error('Submit button not found');
    }
    
  } catch (error) {
    console.error('[JobScale Lever] Application failed:', error);
    return { success: false, error: error.message };
  }
}

async function fillAdditionalFields(userData) {
  const inputs = document.querySelectorAll('input[type="text"]:not([readonly]), textarea:not([readonly])');
  
  for (const input of inputs) {
    if (!input.value) {
      const label = input.closest('label')?.textContent.toLowerCase() || 
                    input.getAttribute('placeholder')?.toLowerCase() || '';
      
      if (label.includes('website') || label.includes('portfolio')) {
        input.value = userData.portfolioUrl || 'N/A';
      } else if (label.includes('linkedin')) {
        input.value = userData.linkedinUrl || 'N/A';
      } else if (label.includes('salary')) {
        input.value = userData.expectedSalary || 'Negotiable';
      } else if (label.includes('notice')) {
        input.value = '2 weeks';
      } else if (label.includes('summary') || label.includes('about')) {
        input.value = userData.summary || 'Please see my CV for details';
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
    await waitForSelector('.application-success, .success-message, :contains("successfully"), :contains("thank you")', 15000);
    return true;
  } catch (error) {
    const formStillOpen = document.querySelector('form[enzyme="applicationForm"]');
    return !formStillOpen;
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

console.log('[JobScale Lever] Adapter loaded');
