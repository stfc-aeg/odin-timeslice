from dataclasses import dataclass, field, fields, InitVar
from enum import IntEnum
from typing import List

from odin.adapters.parameter_tree import ParameterTree

from .utils import ro_param, rw_param

class ConfigureState(IntEnum):
    NOT_READY = 0
    CONFIGURING = 1
    READY = 2

class CaptureState(IntEnum):
    IDLE = 0
    CAPTURING = 1
    CAPTURING_FAILED = 2
    CAPTURING_COMPLETED = 3

class RetrieveState(IntEnum):
    IDLE = 0
    RETRIEVING = 1
    RETRIEVING_FAILED = 2
    RETRIEVING_COMPLETED = 3

class RenderState(IntEnum):
    IDLE = 0
    RENDERING = 1
    RENDERING_FAILED = 2
    RENDERING_COMPLETED = 3

class CountdownState(IntEnum):
    IDLE = 0
    RUNNING = 1
    INITIAL_COUNT = 3

@dataclass
class SystemState:

    NOT_READY = 0
    READY = 1

    state: int = NOT_READY
    status: str = "Not ready"

    configure_state: ConfigureState = ConfigureState.NOT_READY
    configure_status: str = "Not ready"

    capture_state: CaptureState = CaptureState.IDLE
    capture_status: str = "Capture state idle"

    retrieve_state: RetrieveState = RetrieveState.IDLE
    retrieve_status: str = "Retrieve state idle"

    render_state: RenderState = RenderState.IDLE
    render_status: str = "Render state idle"

    countdown_initial_count: int = CountdownState.INITIAL_COUNT
    countdown_count: int = 0
    countdown_state: CountdownState = CountdownState.IDLE

    last_render_file: str = "none"
    access_code: str = ""
    process_status: str = ""

    def start_countdown(self):

        self.countdown_count = self.countdown_initial_count
        self.countdown_state = CountdownState.RUNNING

    def stop_countdown(self):

        self.countdown_count = self.countdown_initial_count
        self.countdown_state = CountdownState.IDLE

    def as_tree(self):
        return ParameterTree({
            field.name: ro_param(self, field.name) for field in fields(self)
        })


@dataclass
class CameraState:

    MAX_CAMERAS = 48
    DEAD = 0
    ALIVE = 1

    num_cameras: int = MAX_CAMERAS
    state: List[int] = field(default_factory=list)
    last_ping_time: List[float] = field(default_factory=list)
    enable: List[int] = field(default_factory=list)
    configure_state: List[int] = field(default_factory=list)
    capture_state: List[int] = field(default_factory=list)
    retrieve_state: List[int] = field(default_factory=list)

    def __post_init__(self) -> None:

      self.state = [self.DEAD] * self.num_cameras
      self.last_ping_time = [0.0] * self.num_cameras
      self.enable = [1] * self.num_cameras
      self.configure_state = [ConfigureState.NOT_READY] * self.num_cameras
      self.capture_state = [CaptureState.IDLE] * self.num_cameras
      self.retrieve_state = [RetrieveState.IDLE] * self.num_cameras

    def as_tree(self):

        return ParameterTree({
            field.name: rw_param(self, field.name) if field.name == 'enable'
                else ro_param(self, field.name) for field in fields(self)
        })
