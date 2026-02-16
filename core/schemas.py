from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ObjectDesc:
    name: str
    count: Optional[int] = None
    location: Optional[str] = None
    attributes: List[str] = field(default_factory=list)
    contents: List[str] = field(default_factory=list)


@dataclass
class VQAResponse:
    ambiguity: bool = False
    objects: List[ObjectDesc] = field(default_factory=list)
    response: str = ""
    raw_text: str = ""

