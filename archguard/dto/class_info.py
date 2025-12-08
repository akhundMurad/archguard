from dataclasses import dataclass, field


@dataclass()
class ClassInfo:
    name: str
    qualname: str  # "myapp.infrastructure.repositories.order.OrderRepository"
    decorators: list[str]  # ["@dataclass", "@service"]
    module: str
    lineno: int
    base_classes: list[str] = field(default_factory=list)
