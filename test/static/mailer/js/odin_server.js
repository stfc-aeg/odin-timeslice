api_version = '0.1';

$(document).ready(function() {
    show_code_list();
    start_page();
    clear_list();
    clear_email();
});

function good_code_response(){

    var task_access_code = $('#input_test').val();
    $('#displayer').html(task_access_code);
    $('#displayer').css('color', 'green');
    $('#validity').html("your code is valid");

}

function bad_code_response(err_msg){
    var input_code = $('#input_test').val();
    $('#displayer').html(input_code).val();
    $('#displayer').css('color', 'red');
    $('#validity').html(err_msg);
}

function check_code_validation() {
    var input_code = $('#input_test').val();
    if (/^([A-N)]|[P-Z]|[1-9]){7}$/.test(input_code))
    {
        $.ajax({
            type: "PUT",
            url: '/api/' + api_version + '/timeslice',
            contentType: "application/json",
            data: JSON.stringify({'add_access_code': input_code})
        })
        .done(function(json){
            console.log("calling good_code_response")
            good_code_response();
            show_code_list();
            document.getElementById("email_button").disabled = false;
            document.getElementById("codes_next").disabled = false;
            document.getElementById('input_test').value = "";
        })
        .fail(function( status, errorThrown ) {
            console.log(status.responseJSON.error);
            bad_code_response(status.responseJSON.error)
        })
        .always(
            console.log("Access code check has been completed"))
    } else {
    alert("The code you have entered is invalid");
    }
}

function show_code_list(){
    $.getJSON('/api/' + api_version + '/timeslice/access_codes', function(response) {
        var access_code_list = response.access_codes
        var code_list = access_code_list.toString();
        $('#codes').html(code_list)
        $('#final_codes').html(code_list)

    });
}

function clear_email(){
    $.ajax({
        type: "PUT",
        url: '/api/' + api_version + '/timeslice',
        contentType: "application/json",
        data: JSON.stringify({'clear_email': true})
    })

    .done( function(){
        show_email_address();
        console.log("Email address has been cleared")
    })
}

function clear_list(){
    $.ajax({
        type: "PUT",
        url: '/api/' + api_version + '/timeslice',
        contentType: "application/json",
        data: JSON.stringify({'clear_access_codes': true})
    })

    .done( function(){
        show_code_list();
        console.log("List has been cleared")
        $('#displayer').html("");
        $('#validity').html("");
        document.getElementById("email_button").disabled = true;
        document.getElementById("codes_next").disabled = true;

    })
}

function check_email_validation(){
    var email_input = $('#email_input').val();
    if (/^(\S+@\S+\.\S+)$/.test(email_input))
    {
        console.log("valid email address entered");

        $.ajax({
            type: "PUT",
            url: '/api/' + api_version + '/timeslice',
            contentType: "application/json",
            data: JSON.stringify({'add_email_address': email_input}) 
        })

        .done(function(json){
            console.log("calling show_email_address");
            show_email_address();
            document.getElementById("email_next").disabled = false;
            $('#email_validity').css('color', 'green');
            $('#email_validity').html("Email address is valid");

        })
    }

    else
    {
        $('#email_validity').css('color', 'red');
        $('#email_validity').html("Please enter a valid email address");
        document.getElementById("email_next").disabled = true;

 
    }
};

function show_email_address(){

    console.log("running show_email_address");

    $.getJSON('/api/' + api_version + '/timeslice/email_address', function(response) {
        var email_displayer = response.email_address;
        console.log(email_displayer);
        $('#email').html(email_displayer);
        $('#final_email').html(email_displayer);

    });
}

function send_email_test(){

    console.log("sending test email");

    $.ajax({
        type: "PUT",
        url: '/api/' + api_version + '/timeslice',
        contentType: "application/json",
        data: JSON.stringify({'send_email_new': true}) 
    })

    .done(function(){
        console.log("clearing page");
        final_page();
    })
}

function refresh_page(timeoutPeriod){
	setTimeout("location.reload(true);",timeoutPeriod);
}

function start_page(){

    $('#email-view').addClass('d-none');
    $('#send-email').addClass('d-none');
    $('#codes-view').removeClass('d-none');

}

function email_page(){

    $('#email-view').removeClass('d-none');
    $('#codes-view').addClass('d-none');
    $('#send-email').addClass('d-none');

}

function send_page(){

    $('#email-view').addClass('d-none');
    $('#send-email').removeClass('d-none');

}

function final_page(){

    $('#email-view').addClass('d-none');
    $('#send-email').addClass('d-none');
    $('#codes-view').addClass('d-none');
    $('#final-view').removeClass('d-none');
    countdown();
    refresh_page(5000);

}

function countdown(){

    var counter = 5;

  setInterval(function() {
    counter--;
    if (counter >= 0) {
      span = document.getElementById("count");
      $('#count').html(counter);
    }

    if (counter === 0) {
        clearInterval(counter);
    }
  }, 1000);

}
