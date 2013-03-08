<!--
//WARNING - EVIL browser-sniffing ahead
var Safari = (document.childNodes) && (!document.all) && (!navigator.taintEnabled) && (!navigator.accentColorName);

// -----------------------
// FUNCTION: fAllowTabbing
// DESCRIPTION: Prevents onkey events firing when the tab key is pressed, thus allowing users to tab past them
// ARGUMENTS: 1: the event - always described as: event, 2: a function name to call without parenthesis "()", 3 variable names to pass to a function. Multiple variable names must be seperated by a "~", i.e. 'variable one~variable two~variable three~etc...'
// RETURNS: n/a
// N.B: onKey.... events should be followed with "return:true;" NOT "return:false" as for onClick events.
// -----------------------
function fAllowTabbing(e, sFunctionName, sVariable) {
	var e = e || window.event;
	var sKeyPressed = e.keyCode || e.charCode;

	if (sKeyPressed != 9) {
		if (sVariable) {
			if (sVariable.match("~")) {
				var aVariables = sVariable.split('~');
				window[sFunctionName].apply(this, aVariables);
			} else {
				window[sFunctionName](sVariable);
			}
		} else {
		window[sFunctionName]();
		}
	}
}

// -----------------------
// FUNCTION: fHeaderSetup
// DESCRIPTION: Code brought in from header.js to allow tabbing of dropdown menus
// ARGUMENTS: none
// RETURNS: n/a
// -----------------------

function fHeaderSetup()	{
	//to make the dropdown menu appear in full in FF when tabbing
	//this is done by giving a class 'menufocus' to the <a> tags that sit within the
	//menu <div>s, and not to the other ones
	var aDDLinks = document.getElementById('main-navigation').getElementsByTagName('a');
	var nDDLinksCount = aDDLinks.length;		
	for (nCount = 0; nCount < nDDLinksCount ; nCount++ ) {
		var oParentDiv=aDDLinks[nCount].parentNode.parentNode.parentNode;
		//ensure that the <a>s are only sub-links, not main menu links, which have the parent 'nav-bar'
		if (oParentDiv.id!='nav-bar')	{
			fAddEvent(aDDLinks[nCount], 'focus', fMenuGainFocus);
			fAddEvent(aDDLinks[nCount], 'blur', fMenuLoseFocus);
		}		
	}

	function fMenuGainFocus(e,oParentDiv)	{	//enables smooth non-IE menu tabbing
		var e = e || window.event;
		var oTargetElement = e.target || e.srcElement;
		oTargetElement.className += ' menufocus';
		oTargetElement.parentNode.parentNode.parentNode.className += ' menufocus';
	}
	function fMenuLoseFocus(e)	{	//see previous
		var e = e || window.event;
		var oTargetElement = e.target || e.srcElement;
		oTargetElement.className = oTargetElement.className.replace(/\bmenufocus\b/,'');
		oTargetElement.parentNode.parentNode.parentNode.className = oTargetElement.parentNode.parentNode.parentNode.className.replace(/\bmenufocus\b/,'');
	}
	
	//Service search dropdown has different markup from others, so dropdown on focus needs to be triggered differently
	$('li#find-services-topnav').children('div').children('ul').children('.topnav-first').children('p.topnav-link').children('a').each(function() {
        $(this).focus(function() {
            $(this).parent('p.topnav-link').parent('.topnav-first').parent('ul').parent('div').addClass('menufocus');
        });
        $(this).blur(function() {
            $(this).parent('p.topnav-link').parent('.topnav-first').parent('ul').parent('div').removeClass('menufocus');
        });
    });

}


// -----------------------
// FUNCTION: addEvent
// DESCRIPTION: Attaches an event to the requested object
// ARGUMENTS: 1: The object type, 2: The event type 3: The function to be called
// -----------------------
function fAddEvent(sObject, sEventType, sFunction){ 
 if (sObject.addEventListener){ 
	 if (Safari && (sEventType == 'DOMContentLoaded'))	{	//safari
		sEventType = 'load';
	 } 
	 sObject.addEventListener(sEventType, sFunction, false); 
	 return true; 
 } else if (sObject.attachEvent){
	if (sEventType == 'DOMContentLoaded') {
		sEventType = 'load';
	}
	var sReturn = sObject.attachEvent("on" + sEventType, sFunction); 
	return sReturn; 
 } else { 
   return false; 
 } 
}
//-----------------
// Function: fRemoveEvent
// DESCRIPTION: Removes an event from the object
// ARGUMENTS: 1: The object 2: The event type 3: Associated function
// ----------------
function fRemoveEvent(sObject, sEventType, sFunction){
  if (sObject && sObject.removeEventListener){
    sObject.removeEventListener(sEventType, sFunction, false);
    return true;
  } else if (sObject.detachEvent){
    var oRemove = sObject.detachEvent("on" + sEventType, sFunction);
    return oRemove;
  } else {
    return false;
  }
}

// -----------------------
// FUNCTION: fGetTarget
// DESCRIPTION: Returns the object of an event
// ARGUMENTS: The Event
// RETURNS: The object
// -----------------------
function fGetTarget(e) {
	e = e || window.event;
	if (e.target) {
		var sTarget = e.target;
	}
	if (e.srcElement) {
		var sTarget = e.srcElement;
	}
	return sTarget;
}

// Removes the default value of an input
function fRemoveValue(e) {
	var oTarget = fGetTarget(e);
	
    if (oTarget.value == oTarget.defaultValue) {
		oTarget.value = '';
	}
}

// Adds the default value to an input if no entry present
function fAddValue(e) {
	var oTarget = fGetTarget(e);
	if (oTarget.value == '') {
		oTarget.value = oTarget.defaultValue;
	}
}
// -----------------------
// FUNCTION: fInputClear
// DESCRIPTION: clears and repopulates inputs unless listed in aPresetFormElements array
// -----------------------
function fInputClear() {
	// Add clearing to Inputs
	aInputs = document.getElementsByTagName('input');
	nInputLength = aInputs.length;
	for (nInputCount = 0; nInputCount < nInputLength; nInputCount++) {		
		 if (aInputs[nInputCount].type == 'text') {
		    if (aInputs[nInputCount].readOnly) {
		        var sReadOnlyId = aInputs[nInputCount].id;
		        fAddEvent(aInputs[nInputCount], 'focus', function() {document.getElementById(sReadOnlyId).select();});   
		    } else {
			    fAddEvent(aInputs[nInputCount], 'focus', fRemoveValue);
			    fAddEvent(aInputs[nInputCount], 'blur', fAddValue);
			}
		 }
	}
	// Add clearing to Text areas
	aTextAreas = document.getElementsByTagName('textarea');
	nTextAreaLength = aTextAreas.length;
	for (nTextAreaCount = 0; nTextAreaCount < nTextAreaLength; nTextAreaCount++) {
		fAddEvent(aTextAreas[nTextAreaCount], 'focus', fRemoveValue);
		fAddEvent(aTextAreas[nTextAreaCount], 'blur', fAddValue);
	}
	// Check for excluded form elements.
	// NB: This will clear any elements with their ID listed in the array 'aPresetFormElements' - this array should be declared on the page from the back end.
	if (typeof aPresetFormElements != 'undefined') {
		var nPresetLength = aPresetFormElements.length;
		for (nPresetCount = 0; nPresetCount < nPresetLength; nPresetCount++) {
			fRemoveEvent(document.getElementById(aPresetFormElements[nPresetCount]), 'focus', fRemoveValue);
			fRemoveEvent(document.getElementById(aPresetFormElements[nPresetCount]), 'blur', fAddValue);
		}
	}
}

// Create and return a DOM element.
function fCreateElement(hElement) {
	if (hElement.type) {
		var oElement = document.createElement(hElement.type);
		if (hElement.className) {
			oElement.className = hElement.className;
		}		
		if (hElement.id) {
			oElement.id = hElement.id;
		}
		if (hElement.forTag) {
			oElement.htmlFor = hElement.forAttribute;
		}
		if (hElement.inputType) {
		    oElement.type = hElement.inputType;
		}
		if (hElement.inputValue) {
		    oElement.defaultValue = hElement.inputValue;
		    oElement.value = hElement.inputValue;
		}
		if (hElement.elementName) {
			oElement.name = hElement.elementName;
		}
		if (hElement.href) {
			oElement.href = hElement.href;
		}
		if (hElement.title) {
			oElement.title = hElement.title;
		}
		if (hElement.tabindex) {
			oElement.tabIndex = hElement.tabindex;
		}			
		return oElement;
	}	
}


// Creates a hidden input '___JSSniffer' and inserts into each <form> element on the page
// Used for JS detection on search result with maps. (i.e. if no JS - no map tab will be rendered).
function fCreateSniffer() {
	var aTheForm = document.body.getElementsByTagName('form');
	var nFormCount = (aTheForm.length);
	for (nCount = 0; nCount < nFormCount; nCount++) {
	    var oInput = document.createElement('input');
	    oInput.setAttribute('type', 'hidden');
	    oInput.setAttribute('name', '___JSSniffer');
	    oInput.id = '___JSSniffer';
	    oInput.value = 'true';  
	    aTheForm[nCount].insertBefore(oInput, aTheForm[nCount].firstChild);
	}
}

// Hides all elements of a given type within a container element using the CSS class 'hidden'
// recieves the container ID and element type
function fHideElements(sContainerId, sElementType) {
	var sElementId;
	var sContainer = document.getElementById(sContainerId);
	var aElements = sContainer.getElementsByTagName(sElementType);
	var nArrayLength = aElements.length;
	for (nCount = 0; nCount < nArrayLength ; nCount++) {
		sElementId = aElements[nCount].id;
		fSwitchClass(sElementId, 'hidden');
	}
}

var oMSGlobals; // Global variable for Main Search.

// Object instance to hold global variables for main search switching.
function fMainSearchGlobals() {
	this.sSearchContainer = 'search-options';
	this.sActiveId = 'search-1';
	this.sActiveClassName = 'active';
}

// ----------------------
// FUNCTION: fSearchOptionsSetUp
// DESCRIPTION: Re-styling and event allocation for main search.
// ARGUMENTS: none
// ----------------------
function fSearchOptionsSetUp() {
	fHideElements('search-options','input');
	oMSGlobals = new fMainSearchGlobals();
	var aLabels = document.getElementById(oMSGlobals.sSearchContainer).getElementsByTagName('label');
	var nLabelCount = aLabels.length;
	for (nCount = 0; nCount < nLabelCount; nCount++ ) {
		fAddEvent(document.getElementById(aLabels[nCount].id), 'click', fSearchOptionsSwitch);
		fAddEvent(document.getElementById(aLabels[nCount].id), 'keydown', fSearchOptionsSwitch);
	}
}

// Checks for requirement of and adds common site wide events.
function fAddChoicesEvents() {
	fInputClear();
	fCreateSniffer();
}
fAddEvent(window, 'load', fAddChoicesEvents);

// ----------------------
// FUNCTION: fAddPersonalisationEvents
// DESCRIPTION: A function that adds personalisation events where appropriate
// ARGUMENTS: None
// ----------------------
function fAddPersonalisationEvents() {
	if (document.getElementById('height') && document.getElementById('weight')) {
		fAddBMIListeners('height');
		fAddBMIListeners('weight');
	}
	if (document.getElementById('rss-feed-link')) {
		fAddEvent(document.getElementById('rss-feed-link'), 'click', fSelectText);
		fAddEvent(document.getElementById('rss-feed-link'), 'keypress', fSelectText);
	}
	if (document.getElementById('update-password')) {
		fRenderPasswordStrength();
	}
}
function fInsertAfter(newElement,targetElement) 
{
	var parent = targetElement.parentNode;
	if(parent.lastchild == targetElement) 
	{
		parent.appendChild(newElement);
	} else 
	{
		parent.insertBefore(newElement, targetElement.nextSibling);
	}
}

fAddEvent(window, 'load', fAddPersonalisationEvents);
fAddEvent(window, 'load', fHeaderSetup); //to run all header scripts

function fHappyBobby() {
}
//-->

// -----------------------------------------------------------------------------
/* Footer tabs */
// ----------------------------------------------------------------------------- 
jQuery(document).ready(function($) {
  if ($(".footer").length) {
    $(".footer").tabs();
  }
});

//-------------------------------------
// Adding an event handler for clearing the site search box before the page controls load
//-------------------------------------
    jQuery(document).ready(function($) {
    fAddEvent(document.getElementById('q'), 'focus', fRemoveValue);
    fAddEvent(document.getElementById('q'), 'blur', fAddValue);
});