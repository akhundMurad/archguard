from dataclasses import dataclass


@dataclass()
class FunctionInfo:
    name: str
    qualname: str
    decorators: list[str]
    module: str
