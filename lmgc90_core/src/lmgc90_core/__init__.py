"""lmgc90_core — headless scientific core for LMGC90 scene preparation.

    from lmgc90_core import Project, pre

    p = Project(name="box", dimension=2)
    p.add(pre.material(name="STEEL", materialType="RIGID", density=7800))
    p.add(pre.model(name="rigid", physics="MECAx", element="Rxx2D", dimension=2))
    p.add(pre.rigidDisk(r=0.1, center=[0, 0], model="rigid", material="STEEL"))
    print(p.to_pre_script())
    p.save("box.lmgc90")

No PyQt6. No pylmgc90. numpy is the only runtime dependency.
The GUI (LMGC90_GUI) is a client of this package, not the other way around.
"""

from . import pre
from .chipy_script import emit_chipy
from .compute_script import ComputeScriptGenerator, generate_command_script, write_command_script
from .commands import CommandHistory
from .entities import (
    Avatar, ContactLaw, DOFOperation, ForLoop, GranuloConfig, Loop, Material, Model,
    PostProCommand, VisibilityRule,
)
from .errors import HistoryError, LMGC90Error, UnknownReferenceError, ValidationError
from .ids import new_avatar_id, new_population_id
from .pipeline import Pipeline, render_sbatch
from .masonry import MasonryConfig, expand_masonry
from .population import ParticlePopulation
from .pre_script import emit_equivalent, emit_pre
from .project import Project
from .types import AvatarOrigin, AvatarType, ContactLawType, MaterialType, UnitSystem
from .validate import compatible_contactors, is_shape_compatible

__version__ = "0.1.1"
__all__ = [
    "Project", "pre",
    "Material", "Model", "Avatar", "ParticlePopulation",
    "ContactLaw", "VisibilityRule", "DOFOperation", "PostProCommand",
    "Loop", "ForLoop", "GranuloConfig", "MasonryConfig", "expand_masonry",
    "MaterialType", "AvatarType", "AvatarOrigin", "ContactLawType", "UnitSystem",
    "CommandHistory", "Pipeline", "render_sbatch",
    "emit_pre", "emit_chipy", "emit_equivalent",
    "ComputeScriptGenerator", "generate_command_script", "write_command_script",
    "ValidationError", "UnknownReferenceError", "HistoryError", "LMGC90Error",
    "new_avatar_id", "new_population_id",
    "compatible_contactors", "is_shape_compatible",
    "__version__",
]
