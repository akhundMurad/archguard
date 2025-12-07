from dataclasses import dataclass


@dataclass()
class ImportInfo:
    from_module: str
    to_module: str
    line_no: int
