from dataclasses import dataclass

from archguard.dto.module_info import ModuleInfo


@dataclass()
class ProjectRoot:
    modules: dict[str, ModuleInfo]
