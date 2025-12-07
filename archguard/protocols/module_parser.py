from pathlib import Path
from typing import Protocol

from archguard import dto


class ModuleParserProtocol(Protocol):
    def parse_project_root(self, root_path: Path) -> dto.ProjectRoot:
        raise NotImplementedError()
