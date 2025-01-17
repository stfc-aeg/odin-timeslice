from dataclasses import dataclass, fields

from odin.adapters.parameter_tree import ParameterTree

from .utils import rw_param

@dataclass
class PreviewConfig:

    enable: bool = True
    camera: int = 1
    update: float = 1.0

    def as_tree(self):
        return ParameterTree({
            field.name: rw_param(self, field.name) for field in fields(self)
        })
