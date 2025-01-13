/*
    The user interface "views" are displayed by removing the 'd-none' class from their div, 
    and are hidden by adding the 'd-none' class to their div. With jQuery, it is possible 
    to add and remove a class from a div using the '.addClass' and '.removeClass' methods.
*/

var system_state = 0;
var capture_state = 0;
var retrieve_state = 0;
var render_state = 0;

pollCameraState();

function pollCameraState() {
    /* 
        Loads data from the server by sending a getJSON request to the '/camera_state' URL,
        and assigns it to different variables before calling itself again in 1 second.
    */

	$.getJSON("/camera_state", function(response) {	     
        system_state = response.system_state;
        capture_state = response.capture_state;
        retrieve_state = response.retrieve_state;
        render_state = response.render_state;
    });

    setTimeout(pollCameraState, 1000);
}

// Calls the 'awaitCaptureIdle' function once the page is fully loaded
$(document).ready(awaitCaptureIdle);

function awaitCaptureIdle() {
    /*
        Calls the 'displayImageView' and 'awaitRenderCompleted' functions if the value of 
        'capture_state' is 0 (Idle), othewrise it calls itself again in 1 second.
    */

    if(capture_state != 0) {
        setTimeout(awaitCaptureIdle, 1000);
    } else {
        displayImageView();
        awaitRenderCompleted();

        function displayImageView() {
            // Displays the Image view and calls the 'poll_preview_image' function.

            $('#image-view').removeClass('d-none');
            $('#video-view').addClass('d-none');
            poll_preview_image();
        }

        function poll_preview_image() {
            /* 
                Adds a timestamp at the end of the image 'src' URL and calls itself again in 1 second if
                the value of 'capture_state' is 0 (Idle). This is done to stop the browser from 
                caching and displaying the same image.
            */

            d = new Date();
            $('#preview-image').attr('src', $('#preview-image').attr('data-src') + '?' + d.getTime());

            if(capture_state == 0) {
                setTimeout(poll_preview_image, 1000);
            }
        }
    }
}

function awaitRenderCompleted() {
    /*
        Calls the 'loadVideo' and 'awaitCaptureIdle' functions if the value of 'render_state' 
        is 3 (Render completed), othewrise it calls itself again in 1 second.
    */

    if(render_state != 3) {
        setTimeout(awaitRenderCompleted, 200);
    } else {
        loadVideo();
        awaitCaptureIdle();
    }

    function loadVideo() {
        /*
            To prevent the browser from caching and displaying the same video, this function adds 
            the video source and loads the video, every time it is called. It also calls the 
            'displayVideoView' function after 1 second.
        */

        $('#preview-video').html('<source id="video-previewer" src="/preview_video" data-src="/preview_video" type="video/mp4"></source>')
        $('#preview-video')[0].load();
        setTimeout(displayVideoView, 1000);
    }

    function displayVideoView() {
        // Displays the Video view.
        $('#image-view').addClass('d-none');
        $('#video-view').removeClass('d-none');
    } 
}