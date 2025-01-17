from dataclasses import dataclass, fields

from odin.adapters.parameter_tree import ParameterTree

from .utils import rw_param

@dataclass
class CaptureConfig:

    render_loop: int = 1
    stagger_enable: bool = False
    stagger_offset: int = 0

    def as_tree(self):
        return ParameterTree({
            field.name: rw_param(self, field.name) for field in fields(self)
        })
