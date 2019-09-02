api_version = '0.1';

$( document ).ready(function() {
    poll_update();
    show_code_list()
});

function handle_form_test(){

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
            console.log("calling handle_form_test")
            handle_form_test();
            show_code_list();
            enable_email();
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
    });
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
        document.getElementById("email_button").disabled = true;
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
        })
    }
};

function show_email_address(){

    console.log("running show_email_address");

    $.getJSON('/api/' + api_version + '/timeslice/email_address', function(response) {
        var email_displayer = response.email_address;
        console.log(email_displayer);
        $('#email').html(email_displayer);
    });
}

function send_email_test(){

    console.log("sending test email");

    $.ajax({
        type: "PUT",
        url: '/api/' + api_version + '/timeslice',
        contentType: "application/json",
        data: JSON.stringify({'send_email_new': true}) 
    });
}
function enable_email(){
    document.getElementById("email_button").disabled = false;
}
