// Global JS for the Sandbox Environment
// -------------------------------------

// Mobile Navigation Logic
// -----------------------

// Get all nav items from desktop menu to append to the mobile nav
const mobileNavContent = document.querySelector('.desktop-nav-items').innerHTML;

// Define the Mobile Nav Container - this is where we will append the mobileNavContent
const mobileNavContainer = document.querySelector('.mobile-nav-items');

// Apend nav items to mobile nav container
mobileNavContainer.innerHTML += mobileNavContent;

// Define the mobile nav trigger button - this opens and closes the mobile nav
const mobileNavTriggerButton = document.querySelector('.mobile-nav-trigger-button');

// Define the text for the mobile nav trigger button
const mobileNavTriggerText = document.querySelector('.mobile-nav-trigger-text');

const mobileNavIcon = mobileNavTriggerButton.querySelector('.mobile-nav-icon');

// Define the resize event listener to close the mobile nav on window resize
const closeNavOnResize = function(e) {
  if (mobileNavContainer.classList.contains('is-visible') === false) { return }
  // Close and reset the nav
  mobileNavTriggerText.innerHTML = 'Menu'
  mobileNavIcon.innerHTML = feather.icons['menu'].toSvg();
  mobileNavContainer.classList.remove('is-visible');
  mobileNavTriggerButton.classList.remove('trigger-active');
  console.log('Resize Call Active');
};

// Add an event listenter to close the nav if the window is resized
window.addEventListener('resize', closeNavOnResize);

// Add the click ation to the mobile nav trigger
mobileNavTriggerButton.addEventListener('click', function () {
  mobileNavContainer.classList.toggle('is-visible');
  mobileNavTriggerButton.classList.toggle('trigger-active');
  // Set up toggle for the menu icon and text
  if (mobileNavContainer.classList.contains('is-visible') === true) {
    mobileNavTriggerText.innerHTML = 'Close';
    mobileNavIcon.innerHTML = feather.icons['x'].toSvg();
  } else {
    mobileNavTriggerText.innerHTML = 'Menu'
    mobileNavIcon.innerHTML = feather.icons['menu'].toSvg();
  }
});

// Sanbox Dashboard UI Application List Interactions
// -------------------------------------------------

// Dashboard App Credential Toggle
// This shows/hides the client ID and secret for each application
const appCredentialToggleLinks = document.querySelectorAll('.app-credentials-toggle');

// Toggle on Mouse Click
appCredentialToggleLinks.forEach((appCredentialToggleLink) => {
  appCredentialToggleLink.addEventListener('click', function() {
    let appID = document.querySelector('#id-' + this.id);
    let appSecret = document.querySelector('#secret-' + this.id);
    if (appID.type == 'password') {
      appID.type = 'text';
      appSecret.type = 'text';
    } else {
      appID.type = 'password';
      appSecret.type = 'password';
    }
  });
});

// Toggle for Keyboard Naviagation
appCredentialToggleLinks.forEach((appCredentialToggleLink) => {
  appCredentialToggleLink.addEventListener('keypress', function (e) {
    var key = e.which || e.keyCode;
    if (key === 13) { // 13 is enter
      let appID = document.querySelector('#id-' + this.id);
      let appSecret = document.querySelector('#secret-' + this.id);
      if (appID.type == 'password') {
        appID.type = 'text';
        appSecret.type = 'text';
      } else {
        appID.type = 'password';
        appSecret.type = 'password';
      }
    }
  });
});

// Copy Credentials to Clipboard
function copyCredential(copyID) {
  // Determine if a user is copying a client id or secret
  if (copyID.includes('secret') === true) {
    // Get the element we want to copy
    let secretToCopy = document.querySelector('#' + copyID);
    // If it is hidden, change to text, copy, and then hide again
    if (secretToCopy.type == 'password') {
      secretToCopy.type = 'text';
      secretToCopy.select();
      document.execCommand('copy');
      secretToCopy.type = 'password';
    } else {
      // Else, if it is shown, just copy!
      secretToCopy.select();
      document.execCommand('copy');
    }
    // Fade In / Out Copy Confirmation Message
    let copyConfirmation = document.querySelector('#confirm-' + copyID);
    $( copyConfirmation ).fadeIn( 300 ).delay( 1500 ).fadeOut( 400 );
  } else {
    // Get the element we want to copy
    let IDToCopy = document.querySelector('#' + copyID);
    // If it is hidden, change to text, copy, and then hide again
    if (IDToCopy.type == 'password') {
      IDToCopy.type = 'text';
      IDToCopy.select();
      document.execCommand('copy');
      IDToCopy.type = 'password';
  } else {
      // Else, if it is shown, just copy!
      IDToCopy.select();
      document.execCommand("copy");
   }
   // Fade In / Out Copy Confirmation Message
   let copyConfirmation = document.querySelector('#confirm-' + copyID);
   $( copyConfirmation ).fadeIn( 300 ).delay( 1500 ).fadeOut( 400 );
  }
};
