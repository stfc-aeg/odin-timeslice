import dataclasses

from odin.adapters.parameter_tree import ParameterTree

from .utils import rw_param

@dataclasses.dataclass
class CameraConfig:

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

    def as_tree(self):
        return ParameterTree({
            field.name: rw_param(self, field.name) for field in dataclasses.fields(self)
        })
