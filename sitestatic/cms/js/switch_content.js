/**
 * Created by ekivemark on 8/10/15.
 * From switch code demo:
 * http://www.sitepoint.com/content-switching-component-built-three-ways/
 * Using the JS and CSS Version from the page
 */

var selectInput = document.getElementById('choose'),
    panels = document.querySelectorAll('.options'),
    currentSelect,
    i;


$(function() {
  $('.jqueryOptions').hide();

  $('#choose').change(function() {
    $('.jqueryOptions').slideUp();
    $('.jqueryOptions').removeClass('current-opt');
    $("." + $(this).val()).slideDown();
    $("." + $(this).val()).addClass('current-opt');
  });
});


/**
 * The clearShow() function is doing a couple of things.
 * First, it’s taking our panels variable
 * (which is a list of all nodes on the page with a class of “options”)
 * and it iterates over each (three in this case)
 * and removes the class of “show” from all of them.

* The “show” class is what makes the content visible on our page.

* */
function clearShow() {
  for ( i = 0; i < panels.length; i++ ) {
    panels[i].classList.remove('show');
  }
}

/**
 * The addShow() function receives an argument called showThis and adds
 * the “show” class to the panel node that has a class that matches the
 * current value of the select input. Now we still need one more piece
 * to pass the showThis value to addShow().
* */
function addShow(showThis) {
  var el = document.getElementsByClassName(showThis);
  for ( i = 0; i < el.length; i++ ) {
     el[i].classList.add('show');
   }
}

/**
 * The vUpdate() function executes whenever the select input is updated
 * (detected via the change event).
 * So when vUpdate() runs, it does the following:

 * - Grabs the current value of selectInput and
 * stores it in the currentSelect variable.
 * - Executes the clearShow function to remove any traces of
 * .show from the panels.
 * - Executes the addShow() function, passing in currentSelect to
 * complete the missing piece of that function
 * - Assigns .show to the panel with the class that matches the
 * current value of the select input.

* */
function vUpdate() {
  currentSelect = selectInput.value;

  clearShow();
  addShow(currentSelect);
}

selectInput.addEventListener('change', vUpdate);


/**
 * This if construct will check to see if the selectInput value is
 * something other than nul. If that’s the case, it will pass in the
 * value of the current selection to the addShow() function,
 * firing that on page reload. Handy to fix the rare case where the
 * page was refreshed and the select element displayed a value,
 * but the appropriate content wasn't shown.
* */
if (selectInput.value !== 'nul') {
  currentSelect = selectInput.value;
  addShow(currentSelect);
}

function addClass(elm, newClass) {
    elm.className += ' ' + newClass;
}

/**
 * finally, in the instance that you need to support Internet Explorer 9
 * or lower, we can’t use classList(). To work around this,
 * here are functions to add and remove classes from an element.
 * The CodePen demos are using these functions:

* */
function removeClass(elm, deleteClass) {
  elm.className = elm.className.replace(new RegExp("\\b" + deleteClass + "\\b", 'g'), '').trim();
  /* the RegExp here makes sure that only
     the class we want to delete, and not
     any other potentially matching strings
     get deleted.
  */
}