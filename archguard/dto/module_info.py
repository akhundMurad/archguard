from dataclasses import dataclass
from pathlib import Path

from archguard.dto.import_info import ImportInfo
from archguard.dto.class_info import ClassInfo


@dataclass()
class ModuleInfo:
    name: str
    file_path: Path
    imports: list[ImportInfo]
    classes: list[ClassInfo]
