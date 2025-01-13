//$('#captureButton').button();

const adapter_path = "/api/0.1/timeslice/";

var max_cameras = 48
var cameras_per_group = 8;
var max_groups = max_cameras / cameras_per_group;
var camera_enable = [];
var camera_state = [];
var icam = 0;

var capture_stagger_enable = 0;

var preview_config = {};
preview_config.enable = true;
preview_config.camera = 1;
preview_config.update = 1;

config_capture_pane();
config_camera_pane();
config_system_pane();
config_preview_pane();
config_version_modal();
resize_panels();

function config_capture_pane()
{

    $("[name='stagger-enable-checkbox']").bootstrapSwitch();

    update_capture_config();

	function update_capture_config()
	{
		$.getJSON("/capture_config", function(response)
		{
			capture_stagger_enable = parseInt(response.stagger_enable);
            $("[name='stagger-enable-checkbox']").bootstrapSwitch('state', capture_stagger_enable, true);
			$('#stagger-offset-input').val(parseInt(response.stagger_offset));
            $(function() {
                $('#render-loop-select option').filter(function() {
                    return ($(this).text() == response.render_loop);
                }).prop('selected', true);
            });

		});
	}


	$('#captureButton').click(function() {

	    $(this).button('loading');

	    $.post('/capture', function(data) {
	        $('#captureButton').button('reset');
	    });
	});

	$('#render-loop-select').change(function() {
		post_capture_config_change();
	});

	$('input[name="stagger-enable-checkbox"]').on('switchChange.bootstrapSwitch', function(event,state) {
	    post_capture_config_change();
	});

	$('#stagger-offset-input').change(function() {
		// TODO validate input value as integer
		post_capture_config_change();
	});

	function post_capture_config_change()
	{
        capture_stagger_enable = $("[name='stagger-enable-checkbox']").bootstrapSwitch('state');
        render_loop = parseInt($('#render-loop-select').val());
        stagger_offset = parseInt($('#stagger-offset-input').val());
		$.post("/capture_config?render_loop=" + render_loop + "&stagger_enable=" + (capture_stagger_enable == true ? 1 : 0)
            + "&stagger_offset=" + stagger_offset);
	}
}

function config_camera_pane()
{
	update_camera_config();

	function update_camera_config()
	{
	    $.getJSON('/camera_config', function(response)
	    {
	        $(function() {
	            $('#config-resolution-select option').filter(function() {
	                return ($(this).text() == response.resolution);
	            }).prop('selected', true);
	        });
	        $(function() {
	            $('#config-iso-select option').filter(function() {
	                return ($(this).text() == response.iso);
	            }).prop('selected', true);
	        });
	        $(function() {
	            $('#config-shutter-select option').filter(function() {
	                return ($(this).text() == response.shutter_speed);
	            }).prop('selected', true);
	        });
	    });
	}

	$('#config-resolution-select').change(function() {
	    post_camera_config_change(false); //"resolution", $(this).val());
	});

	$('#config-iso-select').change(function() {
	    post_camera_config_change(false); //"iso", $(this).val());
	});

	$('#config-shutter-select').change(function() {
	    post_camera_config_change(false); //"shutter_speed", $(this).val());
	});

	$('#camera-config-button').click(function() {
	    post_camera_config_change(true);
	});


	function post_camera_config_change(do_config)
	{
	    resolution = $('#config-resolution-select').val();
	    iso = $('#config-iso-select').val();
	    shutter_speed = $('#config-shutter-select').val();
	    
	    configure = (do_config == true) ? '1' : '0';
	    
	    $.post("/camera_config?resolution=" + resolution + "&iso=" + iso + "&shutter_speed=" + shutter_speed + "&configure=" + configure, function(data) {

	    });
	}
}

function config_system_pane()
{
	
	// Set up monitor enable checkbox and sync state with server
	$("[name='monitor-enable-checkbox']").bootstrapSwitch();
	$.getJSON(adapter_path + 'monitor', function(response) {
	    monitor_state = response.monitor;
	    $("[name='monitor-enable-checkbox']").bootstrapSwitch('state', monitor_state, true);
	});

	$('input[name="monitor-enable-checkbox"]').on('switchChange.bootstrapSwitch', function(event, state) {
		$.ajax({
			type: 'PUT',
			url: adapter_path,
			data: JSON.stringify({ 'monitor': state }),
			contentType: 'application/json',
			dataType: 'json',
		});
	});


	for ( var group = 0; group < max_groups; group++)
	{
	    var offset = group * cameras_per_group;
	    $('<div class="btn-group" role="group">'+
	      '<button id="camera-state-'+(++offset)+'" type="button" class="btn btn-danger btn-fixed-size">'+(offset)+'</button>'+
	      '<button id="camera-state-'+(++offset)+'" type="button" class="btn btn-danger btn-fixed-size">'+(offset)+'</button>'+
	      '<button id="camera-state-'+(++offset)+'" type="button" class="btn btn-danger btn-fixed-size">'+(offset)+'</button>'+
	      '<button id="camera-state-'+(++offset)+'" type="button" class="btn btn-danger btn-fixed-size">'+(offset)+'</button>'+
	      '<button id="camera-state-'+(++offset)+'" type="button" class="btn btn-danger btn-fixed-size">'+(offset)+'</button>'+
	      '<button id="camera-state-'+(++offset)+'" type="button" class="btn btn-danger btn-fixed-size">'+(offset)+'</button>'+
	      '<button id="camera-state-'+(++offset)+'" type="button" class="btn btn-danger btn-fixed-size">'+(offset)+'</button>'+
	      '<button id="camera-state-'+(++offset)+'" type="button" class="btn btn-danger btn-fixed-size">'+(offset)+'</button>'+
	      '</div><br>').appendTo('#camera-state');
	}
	$('</div>').appendTo('#camera-state');

	for (var icam = 1; icam <= max_cameras; icam++)
	{
	    $('#camera-state-'+(icam)).click(function() {
	        //console.log($(this).html());
	        var camera_id = parseInt($(this).html())
	        camera_enable[camera_id-1] = 1 - camera_enable[camera_id-1];
	        $(this).toggleClass('active');
	        set_camera_enable();
	    });
	}

	function set_camera_enable()
	{
	    var enable_var = { 'camera_enable' : camera_enable};
	    $.ajax({
	        type: 'PUT',
	        url: adapter_path + 'camera_state',
	        data: JSON.stringify(enable_var),
	        contentType: 'application/json',
	        dataType: 'json'
	     });

	}

	$('#camera-enable-all').click(function() {
	    for (var icam = 1; icam <= max_cameras; icam++)
	    {
	        camera_enable[icam-1] = 1;
	        $('#camera-state-'+icam).addClass('active');
	    }
	    set_camera_enable();
	});

	$('#camera-enable-none').click(function() {
	    for (var icam = 1; icam <= max_cameras; icam++)
	    {
	        camera_enable[icam-1] = 0
	        $('#camera-state-'+icam).removeClass('active');
	    }
	    set_camera_enable();
	});

	$('#camera-enable-alive').click(function() {
		for (var icam = 1; icam <= max_cameras; icam++)
		{
			camera_enable[icam-1] = (camera_state[icam-1] == 1 ? 1 : 0);
			if (camera_enable[icam-1] == 1) {
				$('#camera-state-'+icam).addClass('active');
			} else {
				$('#camera-state-'+icam).removeClass('active');
			}
		}
		set_camera_enable();
	});

	poll_camera_state();

	function poll_camera_state()
	{
	    $.getJSON(adapter_path + "camera_state", function(response)
		{
			var state = response.camera_state;
	        var loop_len = (state.camera_state.length > max_cameras) ? max_cameras : state.camera_state.length;
	        for (var icam = 0; icam < loop_len; icam++)
	        {
	            var btn_id = '#camera-state-'+(icam+1);
	            if (state.camera_state[icam] == 1) {
	                $(btn_id).removeClass('btn-danger').addClass('btn-success');
	            } else {
	                $(btn_id).removeClass('btn-success').addClass('btn-danger');
	            }
	            if (state.camera_enable[icam] == 1) {
	                 $(btn_id).addClass('active');
	             } else {
	                 $(btn_id).removeClass('active');
	             }
	        }
	        camera_enable = state.camera_enable;
	        camera_state = state.camera_state;

	        $('#system-state').html(state.system_status);
	        if (state.system_state == 0) {
	            $('#system-state').removeClass('label-success').addClass('label-danger');
	        }
	        else {
	            $('#system-state').removeClass('label-danger').addClass('label-success');
	        }
	        $('#capture-state').html(state.capture_status);

	        $('#configure-state').html(state.configure_status);
	        if (state.configure_state == 0) {
	            $('#configure-state').removeClass('label-success').addClass('label-danger');
	        }
	        else {
	            $('#configure-state').removeClass('label-danger').addClass('label-success');
	        }

	        $('#last-render-file').html(state.last_render_file);
	    });
	    setTimeout(poll_camera_state, 1000);
	}

}

function config_preview_pane()
{
	$("[name='preview-enable-checkbox']").bootstrapSwitch();
	
	update_preview_config();
	
	function update_preview_config() 
	{
		$.getJSON(adapter_path + "preview_config", function(response)
		{
			preview_config = response.preview_config;
			$("[name='preview-enable-checkbox']").bootstrapSwitch('state', preview_config.enable, true);
			$(function() {
				$('#preview-camera-select option').filter(function() {
					return ($(this).text() == preview_config.camera);
				}).prop('selected', true)
			});
			$(function() {
				$('#preview-update-select option').filter(function() {
					return ($(this).text() == preview_config.update);
				}).prop('selected', true)
			});
		});
	}
	

	for (var icam = 1; icam <= max_cameras; icam++)
	{
	    $('<option>'+icam+'</option>').appendTo('#preview-camera-select');
	}

	$('input[name="preview-enable-checkbox"]').on('switchChange.bootstrapSwitch', function(event,state) {
	    set_preview_config();
	});

	$('#preview-camera-select').change(function() {
	    set_preview_config();
	});

	$('#preview-update-select').change(function() {
	    set_preview_config();
	});

	function set_preview_config()
	{
	    preview_config.enable = $("[name='preview-enable-checkbox']").bootstrapSwitch('state');
	    preview_config.camera = parseInt($('#preview-camera-select').val());
	    preview_config.update = parseInt($('#preview-update-select').val());

		$.ajax({
			type: 'PUT',
			url: adapter_path + 'preview_config',
			data: JSON.stringify(preview_config),
			contentType: 'application/json',
			dataType: 'json'
		});

	    // #$.post("/preview_config?enable=" + (preview_enable == true ? 1 : 0) + "&camera=" + preview_camera_select + "&update=" + preview_update_time);
	}

	poll_preview_image();

	function poll_preview_image()
	{
	    if (preview_config.enable) {
	        d = new Date();
	        $("#preview-image").attr("src", $('#preview-image').attr('data-src') + '?' + d.getTime());

	    }
	    setTimeout(poll_preview_image, preview_config.update * 1000);
	}

}

function config_version_modal()
{

	$('#version-info-link').click(function() {
	    $.post('/camera_version', function(data) {
	        // Do nothing
	    });
	});

	$('#version-modal').on('shown.bs.modal', function (e) {

	    $('#version-modal-content tbody').html('');

	    for (var icam = 0; icam < max_cameras/2; icam++)
	    {
	        $('<tr>'+
	            '<td><b>' + (icam+1)  + '</b></td>'+
	            '<td id="camera-commit-' + (icam+1)  + '"> &nbsp; </td>'+
	            '<td id="camera-time-'   + (icam+1)  + '"> &nbsp; </td>'+
	            '<td><b>' + (icam+25) + '</b></td>'+
	            '<td id="camera-commit-' + (icam+25) +'"> &nbsp; </td>'+
	            '<td id="camera-time-'   + (icam+25) +'"> &nbsp; </td>'+
	          '</tr>').appendTo('#version-modal-content tbody');
	    }
	    update_camera_version_info();
	});

	$('#version-modal-refresh').click(function() {
	    $.post('/camera_version', function(data)
	    {
	        setTimeout(update_camera_version_info, 1000);
	    });
	});

	function update_camera_version_info()
	{
	    $.getJSON('/camera_version', function(response)
	    {
	        var loop_len = response.camera_version_time.length;
	        for (var icam = 0; icam < loop_len; icam++)
	        {
	            $('#camera-commit-'+(icam+1)).html(response.camera_version_commit[icam]);
	            $('#camera-time-'+(icam+1)).html(date_from_unix_time(response.camera_version_time[icam]));
	        }
	    });
	}

}

function date_from_unix_time(unix_time)
{
    var date_str;
    if (unix_time == 0) {
        date_str = '-';
    } else {
        the_date = new Date(parseInt(unix_time) * 1000);
        date_str = the_date.toLocaleString();
    }
    return date_str;
}

function resize_panels(){
    var h1 = Math.max($("#config").height(), $("#capture").height())
    $("#capture").height(h1);
    $("#config").height(h1);
    var h2 = Math.max($("#system").height(), $("#preview").height())
    $("#system").height(h2);
    $("#preview").height(h2);
}
