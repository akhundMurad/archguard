import ast

from archguard import dto


class _ClassVisitor(ast.NodeVisitor):
    def __init__(self, module: str):
        self.module = module
        self.stack: list[str] = []
        self.classes: list[dto.ClassInfo] = []

    def visit_ClassDef(self, node: ast.ClassDef):
        self.stack.append(node.name)

        # qualname = module + nested path
        if self.module:
            qualname = f"{self.module}." + ".".join(self.stack)
        else:
            qualname = ".".join(self.stack)

        base_classes = [_expr_to_dotted_name(b) for b in node.bases]
        decorators = [_decorator_to_string(d) for d in node.decorator_list]

        self.classes.append(
            dto.ClassInfo(
                name=node.name,
                qualname=qualname,
                decorators=decorators,
                base_classes=base_classes,
                module=self.module,
                lineno=node.lineno,
            )
        )

        # Continue into nested classes
        self.generic_visit(node)

        self.stack.pop()



def _expr_to_dotted_name(node: ast.AST) -> str:
    """
    Best-effort conversion of an expression to a dotted name string.
    Handles:
      - Name:      A        -> "A"
      - Attribute: mod.A    -> "mod.A"
      - Other/complex:      -> ast.unparse(node) or "<expr>"
    """
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parts = []
        cur = node
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))

    try:
        return ast.unparse(node)  # Python 3.9+
    except AttributeError:
        return "<expr>"


def _decorator_to_string(node: ast.AST) -> str:
    """
    Convert decorator AST node to a readable decorator string.
    Examples:
      @dataclass            -> "@dataclass"
      @service()            -> "@service"
      @pkg.decorator(x, y)  -> "@pkg.decorator"
    """
    # @something
    if isinstance(node, (ast.Name, ast.Attribute)):
        return "@" + _expr_to_dotted_name(node)

    # @something(...)
    if isinstance(node, ast.Call):
        return "@" + _expr_to_dotted_name(node.func)

    try:
        return "@" + ast.unparse(node)
    except AttributeError:
        return "@<expr>"
