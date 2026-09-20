"""GUI example registry entry — points to a core scene builder."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List

from lmgc90_core.project import Project


@dataclass(frozen=True)
class ExampleSpec:
    id: str
    title: str
    category: str
    description: str
    dimension: int
    difficulty: str
    # pure core: Callable[[Project], None]
    scene: Callable[[Project], None]
    tags: List[str] = field(default_factory=list)
