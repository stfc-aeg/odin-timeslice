/*
    The user interface "views" are displayed by removing the 'd-none' class from their div, 
    and are hidden by adding the 'd-none' class to their div. With jQuery, it is possible 
    to add and remove a class from a div using the '.addClass' and '.removeClass' methods.
*/

var system_state = 0;
var capture_state = 0;
var retrieve_state = 0;
var render_state = 0;
var capture_countdown_count = null;
var process_status = null;
var access_code = null;
var countdown_active = false

document.getElementById("capture-message").textContent = "Capturing"

pollCameraState();

function pollCameraState() {
    /* 
        Loads data from the server by sending a getJSON request to the '/camera_state' URL,
        and assigns it to different variables before calling itself again in 0.2 seconds.
    */

	$.getJSON("/camera_state", function(response) {
        system_state = response.system_state;
        capture_state = response.capture_state;
        retrieve_state = response.retrieve_state;
        render_state = response.render_state;
        capture_countdown_count = response.capture_countdown_count;
        process_status = response.process_status;
        access_code = response.access_code;
    });

    setTimeout(pollCameraState, 200);
}

// Calls the 'displayIndexView' function once the page is fully loaded
$(document).ready(displayIndexView);

function capture() {
    // Sends a post request to the '/capture_countdown' URL and calls the 'displayCountdownView' function. 

    if (countdown_active) {
        displayCountdownView();
        $.post('/capture_countdown')
    }
    else {
        awaitCaptureCapturing();
        $.post('/capture_trigger');
        $('#index-view').addClass('d-none');
        $('#capture-view').removeClass('d-none')
    }
}

function resetStates() {
    // Sends a post request to the '/reset_states' URL and calls the 'displayIndexView' function.

    $.post('/reset_states');
    displayIndexView();
}

function saveVideo() {
    // Sends a post request to the '/save_video' URL and calls the 'displayAccessCodeView' function. 

    $.post('/save_video');
    displayAccessCodeView();
}

/* 
    The '.click' method binds event handlers (functions) to click events. Keep '.click' methods 
    outside of any functions to prevent event handlers from being bound multiple times.
*/

$('#capture-button').click(capture);
$('#start-again-button, #retake-button').click(resetStates);
$('#save-button').click(saveVideo);
$('#done-button').click(displayFinalView);
$('#finish-button').click(displayIndexView);
$('#countdown-active').click(changeCountdown)

function displayIndexView() {
    // Displays the Index view and checks the value of 'system_state' to decide which function(s) to call.
 
    $('#step-progress-bar, #error-view, #loading-element, #retake-save-view, #final-view').addClass('d-none');
    $('#index-view').removeClass('d-none');

    /*
        Calls the 'updateViewToNotReady' and 'awaitSystemReady' functions if the value of 'system_state' 
        is 0 (not ready), othewrise it calls the 'updateViewToReady' and 'awaitSystemNotReady' functions.
    */

    if(system_state == 0) {
        updateViewToNotReady();
        awaitSystemReady();
        
    } else {
        updateViewToReady();
        awaitSystemNotReady();
    }

    function awaitSystemNotReady() {
        /*
            Calls the 'updateViewToNotReady' and 'awaitSystemReady' functions if the value of 
            'system_state' is 0 (not ready), othewrise it calls itself again in 0.1 seconds.
        */

         if(system_state == 0) {
            updateViewToNotReady();
            awaitSystemReady();
        } else {
            setTimeout(awaitSystemNotReady, 100);
        }
    }

    function updateViewToNotReady() {
        /*  
            Updates the look of the Index view to make the user aware that the system 
            is not ready, and disables the Capture button so that is not clickable.
        */

        $('#system-state').removeClass('alert-success').addClass('alert-danger');
        $('#system-state').css({"border":"3px solid darkred"});
        $('#system-state').html('<h3>System not ready</h3>');
        $('#capture-button').prop("disabled", true);
        $('#index-view-message').html('<h4>Please wait until the system is ready, to be able to capture a video!</h4>');
    }
    
    function awaitSystemReady() {
        /*  
            Calls the 'updateViewToReady' and 'awaitSystemNotReady' functions if the value 
            of 'system_state' is 1 (ready), otherwise it calls itself again in 0.1 seconds.
        */

        if(system_state == 1) {
            updateViewToReady();
            awaitSystemNotReady();
        } else {
            setTimeout(awaitSystemReady, 100);
        }
    }

    function updateViewToReady() {
        /*
            Updates the look of the Index view to make the user aware that the system 
            is ready, and enables the Capture button so that it is clickable.
        */

        $('#system-state').removeClass('alert-danger').addClass('alert-success');
        $('#system-state').css({"border":"3px solid darkgreen"});
        $('#system-state').html('<h3>System ready</h3>');
        $('#capture-button').prop("disabled", false);
        $('#index-view-message').html('<h4>Tap Capture to start capturing a video.</h4>');
    }
}

function displayCountdownView() {
    // Displays the Countdown view and calls the 'updateCountdown' and 'awaitCaptureCapturing' functions.

    $('#index-view').addClass('d-none');
    $('#countdown-view').removeClass('d-none');
    updateCountdown();
    awaitCaptureCapturing();

    function updateCountdown() {
        /* 
            Takes the value of 'capture_countdown_count' and adds it to the '#countdown' element. It 
            calls itself again in 0.1 seconds if the value of 'capture_countdown_count' is not 0.
        */
        $('#countdown').html(capture_countdown_count);
        if (capture_countdown_count != 0) {
            setTimeout(updateCountdown, 100);
        }
    }
} 

function awaitCaptureCapturing() {
    /* 
        Calls the 'displayLoadingView' function if the value of 'capture_state' is 
        greater than or equal to 1, otherwise it calls itself again in 0.1 seconds.
    */

    if (capture_state >= 1) {
        displayLoadingView()
    } else {
        setTimeout(awaitCaptureCapturing, 100);
    }

    function displayLoadingView() {
        // Displays the Loading view and calls the 'resetStepProgressBar' and 'updateCaptureCircle' functions.
        if (countdown_active) {
            $('#countdown-view').addClass('d-none');
        } else {
            $('capture-view').addClass('d-none')
        }
        $('#loading-element, #step-progress-bar').removeClass('d-none');
        resetStepProgressBar();
        updateCaptureCircle();

        function resetStepProgressBar() {
            // Sets the Step Progress Bar circles to 'inactive' and removes their icons (if any).
            $('#circle-capture, #circle-retrieve, #circle-render').empty().removeClass().addClass('circle-inactive');
        }

        function updateCaptureCircle() {
            /* 
                Calls the 'setProgressIcon' function and passes the '#circle-capture' element and the value 
                of 'capture_state' as arguments. It also calls the 'updateRetrieveCircle' if the value of
                'capture_state is 3 (Capturing completed), otherwise it calls itself again in 0.2 seconds.
            */

            setProgressIcon("#circle-capture", capture_state);
            if(capture_state != 3) {
                setTimeout(updateCaptureCircle, 200);
            } else {
                updateRetrieveCircle();
            }
        }

        function updateRetrieveCircle() {
            /* 
                Calls the 'setProgressIcon' function and passes the '#circle-retrieve' element and the value of 
                'retrieve_state' as arguments. It also calls the 'updateRenderCircle' function if the value 
                of 'retrieve_state is 3 (Retrieving completed), otherwise it calls itself again in 0.2 seconds.
            */

            setProgressIcon("#circle-retrieve", retrieve_state);
            if(retrieve_state != 3) {
                setTimeout(updateRetrieveCircle, 200);
            } else {
                updateRenderCircle();
            }
        }

        function updateRenderCircle() {
            /* 
                Calls the 'setProgressIcon' function and passes the '#circle-render' element and the value of 
                'render_state' as arguments. It also calls the 'awaitRenderCompleted' function if the value 
                of 'render_state is 3 (Rendering completed), otherwise it calls itself again in 0.2 seconds.
            */

            setProgressIcon("#circle-render", render_state);
            if(render_state != 3) {
                setTimeout(updateRenderCircle, 200);
            } else {
                awaitRenderCompleted();
            }
        }

        function setProgressIcon(element, state) {
            /* 
                It uses the passed arguments to determine which element (circle) to manipulate and which if 
                statement to execute. Each if statement has its own if statement to stop the code from 
                repeatedly being executed if it has already being executed once.
            */

            if(state == 1) {
                if(!$(element).hasClass('circle-in-progress')) {
                    $(element).removeClass().addClass('circle-in-progress');
                }
            } else if(state == 2) {
                if(!$(element).hasClass('circle-failed')) {
                    $(element).removeClass().addClass('circle-failed');
                    $(element).html('<i class="fa fa-times bar-icons"></i>');
                    displayErrorView();
                }
            } else if(state == 3) {
                if(!$(element).hasClass('circle-completed')) {
                    $(element).removeClass().addClass('circle-completed');
                    $(element).html('<i class="fa fa-check bar-icons"></i>');
                }
            }
        }

        function displayErrorView() {
            // Displays the Error view and calls the 'displayErrorMessage' function.
            $('#loading-element').addClass('d-none');
            $('#error-view').removeClass('d-none');
            displayErrorMessage();

            function displayErrorMessage() {
                // Takes the message stored in 'process_status' and adds it to the '#error-message' element.
                $('#error-message').html('<h4>'+process_status+'</h4>');
            }
        }
    }
}

function awaitRenderCompleted() {
    /* 
        Calls the 'displayRetakeSaveView' function if the value of 'render_state' 
        is 3, otherwise it calls itself again in 0.1 seconds.
    */

    if (render_state != 3) {
        setTimeout(awaitRenderCompleted, 100);
    } else {
        displayRetakeSaveView();
    }

    function displayRetakeSaveView() {
        // Displays the Retake & Save view.
        $('#loading-element').addClass('d-none');
        $('#retake-save-view').removeClass('d-none');
    }
}

function displayAccessCodeView() {
    /* 
        Displays the Access Code view and calls the 'emptyAccessCodeElement' 
        and 'displayAccessCode' functions.
    */

    $('#step-progress-bar, #retake-save-view').addClass('d-none');
    $('#access-code-view').removeClass('d-none');
    emptyAccessCodeElement();
    displayAccessCode();

    function emptyAccessCodeElement() {
        // Empties the content in the '#access-code' element so that users cannot see previous access codes.
        $('#access-code').html('<h3>&nbsp;</h3>');
    }

    function displayAccessCode() {
        /* 
            Calls itself every 0.2 seconds if the 'access_code' variable is emtpy, otherwise it 
            takes the string stored in 'access_code' and adds it to the '#access-code' element.
        */

        if(access_code == "") {
            setTimeout(displayAccessCode, 200);
        } else {
            $('#access-code').html('<h3>'+access_code+'</h3>');
        }
    }
}

function displayFinalView() {
    // Displays the Final view.
    $('#access-code-view').addClass('d-none');
    $('#final-view').removeClass('d-none');
}

function changeCountdown() {
    countdown_active = !countdown_active
}