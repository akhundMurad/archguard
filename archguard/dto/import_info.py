from dataclasses import dataclass, field


@dataclass()
class ImportInfo:
    import_module: str
    line_no: int
    level: int
    from_module: str | None = field(default=None)
