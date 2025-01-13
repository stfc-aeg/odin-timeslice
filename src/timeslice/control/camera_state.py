from dataclasses import dataclass, field, fields
from typing import List

from odin.adapters.parameter_tree import ParameterTree

from utils import rw_param, ro_param


MAX_CAMERAS = 48

SYSTEM_STATE_NOT_READY = 0
SYSTEM_STATE_READY     = 1

CAMERA_STATE_DEAD  = 0
CAMERA_STATE_ALIVE = 1

@dataclass
class CameraState:

    num_cameras: int = 48
    state: List[int] = field(default_factory=list)
    last_ping_time: List[float] = field(default_factory=list)
    enable: List[bool] = field(default_factory=list)
    system_state: int = SYSTEM_STATE_NOT_READY
    system_status: str = "Not ready"

    def __post_init__(self) -> None:
      self.state = [CAMERA_STATE_DEAD] * self.num_cameras
      self.last_ping_time = [0] * self.num_cameras
      self.enable = [True] * self.num_cameras

    def as_tree(self):
        return ParameterTree({
            field.name: rw_param(self, field.name) if field.name == 'enable'
                else ro_param(self, field.name) for field in fields(self)
        })

if __name__ == '__main__':

    camera_state = CameraState(num_cameras=48)
    print(camera_state.num_cameras)
    print(camera_state.state)
    print(camera_state.last_ping_time)

    camera_state_tree = camera_state.as_tree()
    print(camera_state_tree.get('', with_metadata=True))
    print('Done')