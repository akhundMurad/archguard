from dataclasses import dataclass


@dataclass()
class ClassInfo:
    name: str
    qualname: str           # "myapp.infrastructure.repositories.order.OrderRepository"
    decorators: list[str]   # ["@dataclass", "@service"]
    bases: list[str]        # ["Base", "ABC"]
    module: str
