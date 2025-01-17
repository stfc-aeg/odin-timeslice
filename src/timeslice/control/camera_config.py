from dataclasses import dataclass, fields, InitVar
from functools import partial

from odin.adapters.parameter_tree import ParameterTree

from .utils import rw_param

@dataclass
class CameraConfig:

    controller: InitVar[object]

    resolution: str = '1024x768'
    framerate: str = '30'
    shutter_speed: str = '300000'
    iso: str = '100'
    exposure_mode: str = 'fixedfps'
    color_effects: str = 'None'
    contrast: str = '0'
    drc_strength: str = 'off'
    awb_mode: str = 'off'
    awb_gains: str = '1.5,1.5'
    brightness: str = '50'

    def __post_init__(self, controller):
        self.controller = controller

    def as_tree(self):
        return ParameterTree({
            field.name: (
                getattr(self, field.name),
                partial(self.set_param, field.name)
            ) for field in fields(self)
        })

    def as_dict(self):
        return {field.name: getattr(self, field.name) for field in fields(self)}

    def set_param(self, param, value):
        if value != getattr(self, param):
            self.controller.camera_config_changed()
            setattr(self, param, value)
            print(f'CameraConfig: {param} changed to {value}')
