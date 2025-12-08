import ast

from pathlib import Path

from archguard import dto, protocols
from archguard.analyzer._class_visitor import _ClassVisitor


class ModuleParser(protocols.ModuleParserProtocol):
    def parse_project_root(self, root_path: Path) -> dto.ProjectRoot:
        project_root = dto.ProjectRoot(modules={})

        for item in root_path.iterdir():
            if item.is_file() and item.suffix == ".py":
                module_info = self._parse_module(item)
                project_root.modules[module_info.name] = module_info
            elif item.is_dir() and (item / "__init__.py").exists():
                self.parse_project_root(item)

        return project_root

    def _parse_module(self, module_path: Path) -> dto.ModuleInfo:
        source = module_path.read_text(encoding="utf-8")

        tree = ast.parse(source, filename=str(module_path))

        imports: list[dto.ImportInfo] = []
        classes: list[dto.ClassInfo] = []

        for node in ast.walk(tree):
            imports.extend(_find_imports(node))

            classes.extend(_find_classes(node))

        return dto.ModuleInfo(
            name=module_path.name,
            file_path=module_path,
            imports=imports,
            classes=classes,
        )


def _find_imports(node: ast.AST) -> list[dto.ImportInfo]:
    imports: list[dto.ImportInfo] = []
    # Case 1: import x, y.z as t
    if isinstance(node, ast.Import):
        for alias in node.names:
            imports.append(dto.ImportInfo(import_module=alias.name, line_no=node.lineno, from_module=None))

    # Case 2: from x.y import a, b as c
    elif isinstance(node, ast.ImportFrom):
        module = node.module
        for alias in node.names:
            imports.append(
                dto.ImportInfo(
                    import_module=alias.name,  # imported name (e.g., "path", "sin")
                    line_no=node.lineno,
                    from_module=module,
                )
            )


def _find_classes(node: ast.AST, module: str = "") -> list[dto.ClassInfo]:
    visitor = _ClassVisitor(module=module)
    visitor.visit(node)
    return visitor.classes
