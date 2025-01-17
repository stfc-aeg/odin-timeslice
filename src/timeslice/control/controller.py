import glob
import logging
import os
import random
import shlex
import shutil
import string
import subprocess
import time

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from tornado.ioloop import PeriodicCallback

from timeslice.base_controller import BaseController

from . import TimesliceError
from .camera_config import CameraConfig
from .camera_response_parser import CameraResponseParser
from .camera_server import CameraServer
from .capture_config import CaptureConfig
from .multicast_client import MulticastClient
from .preview_config import PreviewConfig
from .states import (
    CameraState,
    CaptureState,
    ConfigureState,
    CountdownState,
    RenderState,
    RetrieveState,
    SystemState,
)
from .utils import rw_param
from .._version import version

class TimesliceController(BaseController):

    MAX_CAMERAS = 48

    def __init__(self, options):

        # Parse options from argument
        self.ctrl_port = int(options.get("ctrl_port", 8008))
        self.ctrl_addr = options.get("ctrl_addr", "127.0.0.1")
        self.mcast_group = options.get("mcast_group", "224.1.1.1")
        self.mcast_port = int(options.get("mcast_port", 5007))
        self.output_path = options.get("output_path", "/tmp/timeslice")
        self.num_cameras = int(options.get("num_cameras", self.MAX_CAMERAS))
        self.resource_path = str(options.get("resource_path",
            os.path.join(os.path.dirname(__file__), "../../../test/static/control/")
        ))
        self.default_preview_file = str(options.get("default_preview_file", "img/testcard.jpg"))
        self.trigger_audio_file = str(options.get("trigger_audio_file", "audio/shutter.wav"))
        self.audio_player= str(options.get("audio_player", "/usr/bin/aplay -N"))
        self.capture_countdown_count = int(
            options.get("countdown_count", CountdownState.INITIAL_COUNT)
        )
        self.countdown_capture_delay = float(options.get("countdown_capture_delay", 0.30))

        self.eventloop_period = 0.1
        self.monitor_period = 1.0
        self.capture_countdown_period = 1.0

        self.camera_max_ping_age = 4.0
        self.configure_timeout = 5.0
        self.capture_timeout = 5.0
        self.capture_timeout_staggered = self.capture_timeout
        self.retrieve_timeout = 5.0
        self.render_timeout = 20.0

        self.monitor_enable = True

        self.camera_version_info   = [('Unknown', '0')] * self.num_cameras

        self.configure_time = 0.0
        self.capture_time = 0.0
        self.retrieve_time = 0.0
        self.render_time = 0.0
        self.preview_time = 0.0

        # Set up paths for images, renders and saved videos
        self.image_path = os.path.join(self.output_path, "temp_image_files")
        self.render_path = os.path.join(self.output_path, "renders")
        self.saved_video_path = os.path.join(self.output_path, "saved_videos")
        self.current_image_path = self.image_path

        self.render_file = "None"
        self.render_framerate = 24
        self.render_format = 'mp4'
        self.render_format_codec = {
            'mp4' : 'libx264',
            'mkv' : 'copy',
            'avi' : 'copy',
        }
        self.render_timestamp = ""
        self.render_process = None

        self.preview_id = 0
        self.preview_image = b''
        preview_file_path = os.path.abspath(
            os.path.join(self.resource_path, self.default_preview_file)
        )
        try:
            with open(preview_file_path, 'rb') as preview_file:
                self.preview_image = preview_file.read()
        except FileNotFoundError:
            logging.error(f"Default preview file {preview_file_path} not found")
        self.preview_video = b''

        self.trigger_audio_file_path = os.path.abspath(
            os.path.join(self.resource_path, self.trigger_audio_file)
        )
        if not os.path.exists(self.trigger_audio_file_path):
            logging.error(f"Trigger audio file {self.trigger_audio_file_path} not found")
            self.trigger_audio_file_path = ""

        self.camera_config = CameraConfig(self)
        self.capture_config = CaptureConfig()
        self.preview_config = PreviewConfig()

        self.system_state = SystemState(countdown_initial_count=self.capture_countdown_count)
        self.camera_state = CameraState(num_cameras=self.num_cameras)

        self.param_tree = ParameterTree({
            "camera_config": self.camera_config.as_tree(),
            "capture_config": self.capture_config.as_tree(),
            "preview_config": self.preview_config.as_tree(),
            "system_state": self.system_state.as_tree(),
            "camera_state": self.camera_state.as_tree(),
            "version_info": (self.get_version_info, None),
            "monitor": rw_param(self, "monitor_enable"),
            "command": {
                "configure": (lambda: True, self.do_configure),
                "capture": (lambda: True, self.do_capture),
                "countdown": (lambda: True, self.do_countdown),
                "reset": (lambda: True, self.do_reset),
                "save": (lambda: True, self.do_save),
                "version": (lambda: True, self.request_camera_version_info),
            },
        })

        self.camera_server = CameraServer(self, self.ctrl_port, self.ctrl_addr)
        self.mcast_client = MulticastClient(self.mcast_group, self.mcast_port)
        self.camera_response_parser = CameraResponseParser(self)

        self.event_loop = PeriodicCallback(
            self.event_loop_callback, int(self.eventloop_period * 1000)
        )

        self.camera_monitor = PeriodicCallback(
            self.camera_monitor_callback, int(self.monitor_period * 1000)
        )

        self.capture_countdown = PeriodicCallback(
            self.capture_countdown_callback, int(self.capture_countdown_period * 1000)
        )

    def initialize(self, adapters):

        self.adapters = adapters
        self.camera_server.listen()
        self.event_loop.start()
        self.camera_monitor.start()

    def cleanup(self):

        self.capture_countdown.stop()
        self.camera_monitor.stop()
        self.event_loop.stop()

#
# Parameter getter/setter methods
#
    def get(self, path, with_metadata=False):

        try:
            return self.param_tree.get(path, with_metadata)
        except ParameterTreeError as e:
            raise TimesliceError(e)

    def set(self, path, value):

        try:
            self.param_tree.set(path, value)
        except ParameterTreeError as e:
            raise TimesliceError(e)

    def get_version_info(self):

        return {
            'server': version,
            'camera': {
                'commit': [elems[0] for elems in self.camera_version_info],
                'time': [elems[1] for elems in self.camera_version_info]
            }
        }

    def request_camera_version_info(self, _):

        self.mcast_client.send("version id=0")

    def get_preview_image(self):
        return self.preview_image

    def get_preview_video(self):
        return self.preview_video

#
# Periodic callback methods
#

    def event_loop_callback(self):

        self.handle_configure_state()
        self.handle_capture_state()
        self.handle_retrieve_state()
        self.handle_render_state()
        self.handle_preview_update()

    def camera_monitor_callback(self):

        if self.monitor_enable and self.system_state.capture_state != CaptureState.CAPTURING:
            self.mcast_client.send(f"ping id=0 host={self.ctrl_addr} port={self.ctrl_port}")

            now = time.time()
            for camera in range(self.num_cameras):
                if (now - self.camera_state.last_ping_time[camera]) < self.camera_max_ping_age:
                    self.camera_state.state[camera] = self.camera_state.ALIVE
                else:
                    self.camera_state.state[camera] = self.camera_state.DEAD

            num_enabled_cameras = sum(self.camera_state.enable)
            num_enabled_cameras_alive = self.num_enabled_in_state(
                self.camera_state.ALIVE, self.camera_state.state
            )

            if num_enabled_cameras == num_enabled_cameras_alive:
                self.system_state.state = SystemState.READY
                status_flag = "Ready"
            else:
                self.system_state.state = SystemState.NOT_READY
                status_flag = "NOT ready"

            self.system_state.status = "{}, {}/{} cameras alive".format(
                status_flag, num_enabled_cameras_alive, num_enabled_cameras)

    def capture_countdown_callback(self):

        self.system_state.countdown_count -= 1
        logging.info(f"Capture countdown, count = {self.system_state.countdown_count}")

        if self.system_state.countdown_count == 0:
            logging.info("Capture countdown triggering capture")
            self.system_state.stop_countdown()
            self.capture_countdown.stop()
            self.do_capture(with_delay=True)

#
# State handler methods
#

    def handle_configure_state(self):

        if self.system_state.configure_state == ConfigureState.CONFIGURING:

            num_cameras_configuring = self.num_enabled_in_state(
                ConfigureState.CONFIGURING, self.camera_state.configure_state
            )
            num_cameras_not_ready = self.num_enabled_in_state(
                ConfigureState.NOT_READY, self.camera_state.configure_state
            )
            configure_elapsed_time = time.time() - self.configure_time

            if num_cameras_configuring > 0:
                if configure_elapsed_time > self.configure_timeout:
                    self.system_state.configure_state = ConfigureState.NOT_READY
                    self.system_state.configure_status = (
                        f"Configure timed out with {num_cameras_configuring} cameras "
                        "in configuring state"
                    )
                    logging.error(self.system_state.configure_status)
            elif num_cameras_not_ready > 0:
                if configure_elapsed_time > self.configure_timeout:
                    self.system_state.configure_state = ConfigureState.NOT_READY
                    self.system_state.configure_status = (
                        f"Configure timed out with {num_cameras_not_ready} cameras not ready"
                    )
                    logging.error(self.system_state.configure_status)
            else:
                self.system_state.configure_state = ConfigureState.READY
                self.system_state.configure_status = (
                    f"Configuration completed OK after {configure_elapsed_time:.3f} secs"
                )
                logging.info(self.system_state.configure_status)

    def handle_capture_state(self):

        if self.system_state.capture_state == CaptureState.CAPTURING:

            num_cameras_capturing = self.num_enabled_in_state(
                CaptureState.CAPTURING, self.camera_state.capture_state
            )
            capture_elapsed_time = time.time() - self.capture_time

            if num_cameras_capturing > 0:

                self.system_state.capture_status = (
                    f"Capture in progress on {num_cameras_capturing} cameras"
                )
                self.system_state.process_status = "The cameras are now capturing"

                if capture_elapsed_time > self.capture_timeout_staggered:
                    self.system_state.capture_status = (
                        f"Capture timed out on {num_cameras_capturing} cameras"
                    )
                    self.system_state.process_status = (
                        "An error occurred while the cameras were capturing, "
                        "please try capturing a video again"
                    )
                    self.system_state.capture_state = CaptureState.CAPTURING_FAILED
            else:
                self.system_state.capture_status = (
                    f"Camera capture completed OK after {capture_elapsed_time:.3f} secs"
                )
                logging.info(self.system_state.capture_status)
                self.system_state.capture_state = CaptureState.CAPTURING_COMPLETED
                self.do_retrieve(None)

    def handle_retrieve_state(self):

        if self.system_state.retrieve_state == RetrieveState.RETRIEVING:

            num_cameras_retrieving = self.num_enabled_in_state(
                RetrieveState.RETRIEVING, self.camera_state.retrieve_state
            )
            retrieve_elapsed_time = time.time() - self.retrieve_time

            if num_cameras_retrieving > 0:
                if retrieve_elapsed_time > self.retrieve_timeout:
                    self.system_state.retrieve_status = (
                        f"Retrieve timed out on {num_cameras_retrieving} cameras"
                    )
                    logging.error(self.system_state.retrieve_status)
                    self.system_state.process_status = (
                        "An error occurred while retrieving the images, "
                        "please try capturing a video again"
                    )
                    self.system_state.retrieve_state = RetrieveState.RETRIEVING_FAILED
            else:
                self.system_state.retrieve_status = (
                    f"Image retrieve completed OK after {retrieve_elapsed_time:.3f} secs"
                )
                logging.info(self.system_state.retrieve_status)
                self.system_state.retrieve_state = RetrieveState.RETRIEVING_COMPLETED
                self.do_render(None)

    def handle_render_state(self):

        if self.system_state.render_state == RenderState.RENDERING:

            render_state_poll = self.render_process.poll()
            render_elapsed_time = time.time() - self.render_time

            if render_state_poll is None:
                if render_elapsed_time > (self.render_timeout * self.capture_config.render_loop):
                    self.system_state.render_status = "Timeslice render timed out"
                    self.system_state.process_status = (
                        "An error occurred while creating your video, "
                        "please try capturing a video again"
                    )
                    self.system_state.render_state = RenderState.RENDERING_FAILED
            else:
                (render_stdout, render_stderr) = self.render_process.communicate()
                if render_state_poll == 0:
                    self.system_state.last_render_file = self.render_file
                    self.system_state.render_status = (
                        f"Timeslice render completed OK after {render_elapsed_time:.3f} secs"
                    )
                    logging.info(self.system_state.render_status)
                    self.system_state.render_state = RenderState.RENDERING_COMPLETED
                    self.update_preview_video()
                else:
                    self.system_state.render_status = (
                        f"Timeslice render failed with return code {render_state_poll}"
                    )
                    logging.error(self.system_state.render_status)
                    logging.error("Render output:\n{}\n{}".format(render_stdout, render_stderr))
                    self.system_state.render_state = RenderState.RENDERING_FAILED

    def handle_preview_update(self):

        if self.preview_config.enable:

            if (time.time() - self.preview_time) > self.preview_config.update:
                logging.debug("Preview update fired")

                self.mcast_client.send("preview id={}".format(self.preview_config.camera))
                self.preview_time = time.time()

#
# State action methods
#

    def do_configure(self, _):

        self.configure_time = time.time()
        self.system_state.configure_state = ConfigureState.CONFIGURING
        self.system_state.configure_status = "Configuring cameras"

        for camera in range(self.num_cameras):
            if self.camera_state.enable[camera]:
                self.camera_state.configure_state[camera] = ConfigureState.CONFIGURING

        param_str = " ".join([
            f"{key}={value}" for key, value in self.camera_config.as_dict().items()
        ])
        self.mcast_client.send(f"configure id=0 {param_str}")

    def do_capture(self, _=None, with_delay=False):

        if with_delay:
            time.sleep(self.countdown_capture_delay)

        self.system_state.access_code = ''
        self.render_timestamp = time.strftime("%Y%m%d-%H%M%S")
        self.current_image_path = os.path.join(
            self.image_path, f"timeslice_{self.render_timestamp}"
        )
        logging.info("Writing image files to path {}".format(self.current_image_path))

        try:
            os.makedirs(self.current_image_path)
        except OSError as e:
            if not os.path.isdir(self.current_image_path):
                self.system_state.capture_status = (
                    f"Failed to create image file path {self.current_image_path} : {e}"
                )
                logging.error(self.system_state.capture_status)

        # Set the capture state to capturing, set the capture time
        self.capture_time = time.time()
        self.system_state.capture_state = CaptureState.CAPTURING
        self.system_state.capture_status = "Capture in progress"

        # Set state of enabled cameras to capturing
        for camera in range(self.num_cameras):
            if self.camera_state.enable[camera]:
                self.camera_state.capture_state[camera] = CaptureState.CAPTURING

        # Calculate timeout dependent on whether staggered capture is enabled or not
        if self.capture_config.stagger_enable:
            self.capture_timeout_staggered = self.capture_timeout + (
                self.num_cameras * ((1.0 * self.stagger_offset) / 1000.0)
            )
        else:
            self.capture_timeout_staggered = self.capture_timeout

        # Send capture command to all cameras
        self.mcast_client.send(
            f"capture id=0 stagger_enable={self.capture_config.stagger_enable:d} "
            f"stagger_offset={self.capture_config.stagger_offset}"
        )

        self.play_trigger_audio()
        logging.info(f"Capture {self.render_timestamp} started")

    def do_retrieve(self, _):

        # Set the capture state to retrieving, set the capture time
        self.retrieve_time = time.time()
        self.system_state.retrieve_state = RetrieveState.RETRIEVING
        self.system_state.retrieve_status = "Image retrieve in progress"
        self.system_state.process_status = (
            "Please wait while I am retrieving the images from the cameras"
        )

        # Set state of enabled cameras to retrieving
        for camera in range(self.num_cameras):
            if self.camera_state.enable[camera]:
                self.camera_state.retrieve_state[camera] = RetrieveState.RETRIEVING

        self.mcast_client.send("retrieve id=0")

    def do_render(self, _):

        self.render_time = time.time()
        self.system_state.render_state = RenderState.RENDERING
        self.system_state.render_status = "Timeslice render in progress"
        self.system_state.process_status = (
            "Images retrieved successfully, I am now creating your video"
        )

        # Squash file list to ensure files are contiguously numbered
        src_files = sorted(glob.glob(os.path.join(self.current_image_path, "image_*.jpg")))
        num_src_files = len(src_files)
        squashed_files = []
        num_squashed = 0
        dst_idx = 1

        for src_file in src_files:
            dst_file = (os.path.join(self.current_image_path, "image_{:03d}.jpg".format(dst_idx)))
            if src_file != dst_file:
                num_squashed += 1
                os.rename(src_file, dst_file)
            squashed_files.append(dst_file)
            dst_idx += 1

        logging.info(
            f"Squashed {num_squashed} image files out of {num_src_files} "
            f"in render path {self.current_image_path}"
        )

        # Copy image files in order to generate the correct number of loops for rendering
        dst_idx = len(squashed_files) + 1

        for loop in range(self.capture_config.render_loop - 1):
            for src_file in squashed_files:
                dst_file = os.path.join(self.current_image_path, "image_{:03d}.jpg".format(dst_idx))
                shutil.copy2(src_file, dst_file)
                dst_idx += 1

        logging.info(
            f"Created a total of {dst_idx-1} image files from {num_src_files} "
            f"for {self.capture_config.render_loop} render loops at path {self.current_image_path}"
        )

        input_file_pattern = os.path.join(self.current_image_path, "image_%03d.jpg")
        self.render_file = os.path.join(
            self.render_path, f"timeslice_{self.render_timestamp}.{self.render_format}"
        )

        render_cmd = (
            f"ffmpeg -framerate {self.render_framerate} -i \'{input_file_pattern}\' "
            f"-codec {self.render_format_codec[self.render_format]} -y {self.render_file}"
        )
        logging.info("Launching render process with command: {}".format(render_cmd))
        self.render_process = subprocess.Popen(
            shlex.split(render_cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

    def do_save(self, _):

        self.reset_state_values()

        access_code_length = 7
        chars = string.ascii_uppercase + string.digits
        chars = ''.join(sorted(set(chars) - set('0O')))

        self.system_state.access_code = ''.join(
            random.choice(chars) for _ in range(access_code_length)
        )
        save_render_file_name = os.path.join(
            self.saved_video_path, f"{self.system_state.access_code}.mp4"
        )
        shutil.copy2(self.render_file, save_render_file_name)
        logging.info(
            f"Saved render file as {self.system_state.access_code}.mp4 "
            f"in saved render path {self.saved_video_path}"
        )
        self.system_state.process_status = (
            f"Your video is saved with the access code {self.system_state.access_code}"
        )

    def do_countdown(self, _):

        if self.system_state.countdown_state == CountdownState.IDLE:
            self.system_state.start_countdown()
            self.capture_countdown.start()
            logging.info(f"Capture countdown, count = {self.system_state.countdown_count}")
        else:
            pass

    def do_reset(self, _):
        self.reset_state_values()

#
# Camera response processing methods
#

    def process_camera_response(self, response):

        self.camera_response_parser.parse_response(response)

    def update_camera_last_ping_time(self, id):

        if id < 1 or id > self.num_cameras:
            logging.warning(f"Got camera ping response for illegal ID: {id}")
        else:
            self.camera_state.last_ping_time[id-1] = time.time()

    def update_camera_version_info(self, id, commit, time):

        if id < 1 or id > self.num_cameras:
            logging.warning(f"Got version response for illegal ID: {id}")
        else:
            self.camera_version_info[id-1] = (commit, time)

    def update_preview_image(self, id, image_data):

        self.preview_image = image_data

    def update_camera_configure_state(self, id, did_ack):

        if id < 1 or id > self.num_cameras:
            logging.warning(f"Got configure response for illegal ID: {id}")
        else:
            if self.camera_state.configure_state[id-1] != ConfigureState.CONFIGURING:
                logging.warning(
                    f"Got configure response for camera ID {id} when not in configuring state"
                )
            elif not did_ack:
                logging.warning(
                    f"Camera ID {id} responded with no-acknowledge for configure command"
                )
            else:
                self.camera_state.configure_state[id-1] = ConfigureState.READY

    def update_camera_capture_state(self, id, did_ack):

        if id < 1 or id > self.num_cameras:
            logging.warning(f"Got camera capture response for illegal ID: {id}")
        else:
            if self.camera_state.capture_state[id-1] != CaptureState.CAPTURING:
                logging.warning(
                    f"Got capture response for camera ID {id} when not in capturing state"
                )
            elif not did_ack:
                logging.warning(
                    f"Camera ID {id} responded with no-acknowledge for capture command"
                )
            else:
                self.camera_state.capture_state[id-1] =CaptureState.CAPTURING_COMPLETED

    def update_camera_retrieve_state(self, id, did_ack, image_data):

        if id < 0 or id > self.num_cameras:
            logging.warning(f"Got camera retrieve response for illegal ID: {id}")
        else:
            if self.camera_state.retrieve_state[id-1] != RetrieveState.RETRIEVING:
                logging.warning(
                    f"Got retrieve response for camera ID {id} when not in retrieving state"
                )
            elif not did_ack:
                logging.warning(
                    f"Camera ID {id} responded with no-acknowledge for retrieve command"
                )
            else:
                self.camera_state.retrieve_state[id-1] = RetrieveState.RETRIEVING_COMPLETED

                if image_data is not None and len(image_data) > 0:
                    image_file_name = os.path.join(self.current_image_path, f"image_{id:03d}.jpg")
                    try:
                        with open(image_file_name, 'wb') as image_file:
                            image_file.write(image_data)
                        logging.info(f"Wrote image data for camera {id} to file {image_file_name}")
                    except (OSError, FileNotFoundError) as e:
                        logging.error(
                            f"Failed to write image data for camera {id} "
                            f"to file {image_file_name}: {e}"
                    )

    def update_preview_video(self):
        """ Open the rendered file in binary mode and assign its data to 'self.preview_video'. """

        logging.info(f"Updating preview video from file = {self.render_file}")
        try:
            with open(self.render_file, 'rb') as preview_video_file:
                self.preview_video = preview_video_file.read()
        except FileNotFoundError:
            logging.error(f"Rendered file {self.render_file} not found, not updating preview video")
            self.preview_video = b''
#
# Utility methods
#

    def camera_config_changed(self):

        self.system_state.configure_state = ConfigureState.NOT_READY
        self.system_state.configure_status = "Configuration changed"

    def num_enabled_in_state(self, desired_state, object_state):

        return sum([(enabled and (state == desired_state))
            for (enabled, state) in zip(self.camera_state.enable, object_state)])

    def play_trigger_audio(self):

        if self.trigger_audio_file_path:
            subprocess.Popen(shlex.split(f"{self.audio_player} {self.trigger_audio_file_path}"))
        else:
            logging.error(f"Trigger audio file {self.trigger_audio_file_path} not found")

    def reset_state_values(self):

        """ Set capture, retrieve and render state to idle (0), and countdown count to 5 """

        self.system_state.capture_state = CaptureState.IDLE
        self.system_state.retrieve_state = RetrieveState.IDLE
        self.system_state.render_state = RenderState.IDLE
        self.capture_countdown_count = 3
        self.preview_video = ''




