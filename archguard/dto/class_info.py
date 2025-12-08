from dataclasses import dataclass, field


@dataclass()
class ClassInfo:
    name: str
    qualname: str  # "myapp.infrastructure.repositories.order.OrderRepository"
    decorators: list[str]  # ["@dataclass", "@service"]
    base_classes: list[str] = field(default_factory=list)
    module: str
    lineno: int
