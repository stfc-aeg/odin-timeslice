import logging
import os
import time

from odin.adapters.parameter_tree import ParameterTree, ParameterTreeError
from tornado.ioloop import PeriodicCallback

from timeslice.base_controller import BaseController

from . import TimesliceError
from .camera_response_parser import CameraResponseParser
from .camera_config import CameraConfig
from .camera_server import CameraServer
from .multicast_client import MulticastClient
from .utils import rw_param

class TimesliceController(BaseController):

    MAX_CAMERAS = 48

    SYSTEM_STATE_NOT_READY = 0
    SYSTEM_STATE_READY     = 1

    CAMERA_STATE_DEAD  = 0
    CAMERA_STATE_ALIVE = 1

    CONFIGURE_STATE_NOT_READY   = 0
    CONFIGURE_STATE_CONFIGURING = 1
    CONFIGURE_STATE_READY       = 2

    CAPTURE_STATE_IDLE                  = 0
    CAPTURE_STATE_CAPTURING             = 1
    CAPTURE_STATE_CAPTURING_FAILED      = 2
    CAPTURE_STATE_CAPTURING_COMPLETED   = 3

    RETRIEVE_STATE_IDLE                 = 0
    RETRIEVE_STATE_RETRIEVING           = 1
    RETRIEVE_STATE_RETRIEVING_FAILED    = 2
    RETRIEVE_STATE_RETRIEVING_COMPLETED = 3

    RENDER_STATE_IDLE                  = 0
    RENDER_STATE_RENDERING             = 1
    RENDER_STATE_RENDERING_FAILED      = 2
    RENDER_STATE_RENDERING_COMPLETED   = 3

    RENDER_STATUS_IDLE = 0
    RENDER_STATUS_RENDERING = 1
    RENDER_STATUS_RENDERING_FAILED = 2
    RENDER_STATUS_RENDERING_COMPLETED = 3

    def __init__(self, options):

        self.ctrl_port = int(options.get("ctrl_port", 8008))
        self.ctrl_addr = options.get("ctrl_addr", "127.0.0.1")
        self.mcast_group = options.get("mcast_group", "224.1.1.1")
        self.mcast_port = int(options.get("mcast_port", 5007))
        self.output_path = options.get("output_path", "/data/timeslice")
        self.num_cameras = int(options.get("num_cameras", self.MAX_CAMERAS))

        self.eventloop_period = 0.1

        self.camera_max_ping_age = 4.0
        self.configure_timeout = 5.0
        self.capture_timeout = 5.0
        self.retrieve_timeout = 5.0
        self.render_timeout = 20.0

        self.monitor_enable = True
        self.monitor_period = 1.0

        self.system_state = self.SYSTEM_STATE_NOT_READY
        self.system_status = "Not ready"

        self.camera_state = [self.CAMERA_STATE_DEAD] * self.num_cameras
        self.camera_last_ping_time = [0.0] * self.num_cameras
        self.camera_version_info   = [('Unknown', '0')] * self.num_cameras
        self.camera_enable = [1] * self.num_cameras

        self.camera_configure_state = [self.CONFIGURE_STATE_NOT_READY] * self.num_cameras
        self.configure_state = self.CONFIGURE_STATE_NOT_READY
        self.configure_status = "Not ready"

        self.camera_capture_state = [self.CAPTURE_STATE_IDLE] * self.num_cameras
        self.capture_state = self.CAPTURE_STATE_IDLE
        self.capture_status = "Capture state idle"

        self.camera_retrieve_state = [self.RETRIEVE_STATE_IDLE] * self.num_cameras
        self.retrieve_state = self.RETRIEVE_STATE_IDLE
        self.retrieve_status = "Retrieve state idle"

        self.render_state = self.RENDER_STATE_IDLE
        self.render_status = "Render state idle"

        self.process_status = ""

        self.configure_time = 0.0
        self.capture_time = 0.0
        self.retrieve_time = 0.0
        self.render_time = 0.0

        self.preview_enable = False
        self.preview_camera = 1
        self.preview_update = 1
        self.preview_time = 0.0

        self.preview_id = 0
        self.preview_image = ''

        self.camera_config = CameraConfig()
        self.camera_config_tree = self.camera_config.as_tree()

        default_preview_file = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../../test/static/control/img/testcard.jpg"))
        with open(default_preview_file, 'rb') as preview_file:
            self.preview_image = preview_file.read()

        self.camera_state_tree = ParameterTree({
            "camera_state": (lambda: self.camera_state, None),
            "camera_enable": rw_param(self, "camera_enable"),
            "camera_last_ping_time": (lambda: self.camera_last_ping_time, None),
            "system_state": (lambda: self.system_state, None),
            "system_status": (lambda: self.system_status, None),
        })

        self.preview_config_tree = ParameterTree({
            "enable": rw_param(self, "preview_enable"),
            "camera": rw_param(self, "preview_camera"),
            "update": rw_param(self, "preview_update"),
        })

        self.param_tree = ParameterTree({
            "camera_state": self.camera_state_tree,
            "camera_version": (self.get_camera_version_info, self.request_camera_version_info),
            "monitor": rw_param(self, "monitor_enable"),
            "preview_config": self.preview_config_tree,
            "camera_config": self.camera_config_tree,
        })

        self.camera_server = CameraServer(self, self.ctrl_port, self.ctrl_addr)
        self.mcast_client = MulticastClient(self.mcast_group, self.mcast_port)
        self.camera_response_parser = CameraResponseParser(self)

        self.eventloop_callback = PeriodicCallback(
            self.event_loop, int(self.eventloop_period * 1000)
        )

        self.monitor_callback = PeriodicCallback(
            self.monitor_camera_state, int(self.monitor_period * 1000)
        )

    def initialize(self, adapters):

        self.adapters = adapters
        self.camera_server.listen()
        self.eventloop_callback.start()
        self.monitor_callback.start()

    def cleanup(self):

        self.monitor_callback.stop()
        self.eventloop_callback.stop()

    def get(self, path, with_metadata=False):

        try:
            return self.param_tree.get(path)
        except ParameterTreeError as e:
            raise TimesliceError(e)

    def set(self, path, value):

        try:
            self.param_tree.set(path, value)
        except ParameterTreeError as e:
            raise TimesliceError(e)

    def event_loop(self):

        self.do_preview_update()

    def do_preview_update(self):

        if self.preview_enable:

            if (time.time() - self.preview_time) > self.preview_update:
                logging.debug("Preview update fired")

                self.mcast_client.send("preview id={}".format(self.preview_camera))
                self.preview_time = time.time()

    def monitor_camera_state(self):

        if self.monitor_enable and self.capture_state != self.CAPTURE_STATE_CAPTURING:
            self.mcast_client.send(f"ping id=0 host={self.ctrl_addr} port={self.ctrl_port}")

            now = time.time()
            for camera in range(self.num_cameras):
                if (now - self.camera_last_ping_time[camera]) < self.camera_max_ping_age:
                    self.camera_state[camera] = self.CAMERA_STATE_ALIVE
                else:
                    self.camera_state[camera] = self.CAMERA_STATE_DEAD

            num_enabled_cameras = sum(self.camera_enable)
            num_enabled_cameras_alive = sum([
                (enabled and (state == self.CAMERA_STATE_ALIVE)) for (enabled, state) in
                    zip(self.camera_enable, self.camera_state)
            ])

            if num_enabled_cameras == num_enabled_cameras_alive:
                self.system_state = self.SYSTEM_STATE_READY
                status_flag = "Ready"
            else:
                self.system_state = self.SYSTEM_STATE_NOT_READY
                status_flag = "NOT ready"

            self.system_status = "{}, {}/{} cameras alive".format(
                status_flag, num_enabled_cameras_alive, num_enabled_cameras)

    def get_camera_version_info(self):

        return {
            'camera_version_commit': [elems[0] for elems in self.camera_version_info],
            'camera_version_time': [elems[1] for elems in self.camera_version_info]
        }

    def process_camera_response(self, response):

        self.camera_response_parser.parse_response(response)

    def request_camera_version_info(self, _):

        self.mcast_client.send("version id=0")

    def update_camera_last_ping_time(self, id):

        if id < 1 or id > self.num_cameras:
            logging.warning("Got camera ping response for illegal ID: {}".format(id))
        else:
            self.camera_last_ping_time[id-1] = time.time()

    def update_camera_version_info(self, id, commit, time):

        if id < 1 or id > self.num_cameras:
            logging.warning("Got version response for illegal ID: {}".format(id))
        else:
            self.camera_version_info[id-1] = (commit, time)

    def get_preview_image(self):
        return self.preview_image

    def update_preview_image(self, id, image_data):

        self.preview_image = image_data


