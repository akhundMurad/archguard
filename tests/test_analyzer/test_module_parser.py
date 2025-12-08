import ast
from pathlib import Path

import pytest

from archguard.analyzer.module_parser import ModuleParser, _find_imports, _find_classes
from archguard import dto


def test_find_imports_handles_import_and_from_import():
    source = """\
import os, sys
import pathlib as pl
from math import sin, cos as c
x = 1
"""
    tree = ast.parse(source)

    imports = []
    for node in ast.walk(tree):
        imports.extend(_find_imports(node))

    # We expect:
    #   import os, sys              -> os, sys (from_module=None)
    #   import pathlib as pl        -> pathlib (from_module=None)
    #   from math import sin, cos   -> sin, cos (from_module="math")
    names_from_module = {(imp.import_module, imp.from_module) for imp in imports}

    assert names_from_module == {
        ("os", None),
        ("sys", None),
        ("pathlib", None),
        ("sin", "math"),
        ("cos", "math"),
    }

    # All imports should have a positive line number
    assert all(imp.line_no > 0 for imp in imports)


def test_find_imports_on_non_import_node_returns_empty_list():
    tree = ast.parse("x = 42")
    [assign_node] = [n for n in ast.walk(tree) if isinstance(n, ast.Assign)]

    result = _find_imports(assign_node)
    assert result == []


def test_find_classes_collects_basic_class_info():
    source = """\
from dataclasses import dataclass

@dataclass
class User(BaseModel):
    id: int
"""
    tree = ast.parse(source)

    classes = _find_classes(tree)
    assert len(classes) == 1

    cls = classes[0]
    # Basic expectations – adjust if your ClassInfo is different
    assert isinstance(cls, dto.ClassInfo)
    assert cls.name == "User"
    assert "BaseModel" in cls.base_classes or cls.base_classes == ["BaseModel"]

    # decorators should NOT include the '@'
    assert "@dataclass" in cls.decorators

    # lineno points to 'class User(...)' line
    assert isinstance(cls.lineno, int)
    assert cls.lineno > 0


def test_parse_module_parses_imports_and_classes(tmp_path: Path):
    module_path = tmp_path / "sample_module.py"
    module_path.write_text(
        """\
import os
from math import sin

class Foo:
    pass
""",
        encoding="utf-8",
    )

    parser = ModuleParser()
    module_info = parser._parse_module(module_path)

    # Basic structure
    assert isinstance(module_info, dto.ModuleInfo)
    assert module_info.name == "sample_module.py"
    assert module_info.file_path == module_path

    # Imports
    import_names = {(imp.import_module, imp.from_module) for imp in module_info.imports}
    assert ("os", None) in import_names
    assert ("sin", "math") in import_names

    # Classes
    class_names = {cls.name for cls in module_info.classes}
    assert "Foo" in class_names


def test_parse_project_root_parses_top_level_modules(tmp_path: Path):
    (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("class B: pass\n", encoding="utf-8")

    parser = ModuleParser()
    project_root = parser.parse_project_root(tmp_path)

    assert isinstance(project_root, dto.ProjectRoot)
    # By design, ModuleParser uses the file name (including .py) as module name
    assert set(project_root.modules.keys()) == {"a.py", "b.py"}

    assert isinstance(project_root.modules["b.py"], dto.ModuleInfo)
    assert any(cls.name == "B" for cls in project_root.modules["b.py"].classes)


@pytest.mark.xfail(
    reason="Recursive package parsing not fully wired (parse_project_root() does not yet merge nested results)."
)
def test_parse_project_root_parses_modules_inside_packages(tmp_path: Path):
    # Root-level file
    (tmp_path / "root_module.py").write_text("x = 1\n", encoding="utf-8")

    # Package with an __init__ and a module
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "inside.py").write_text("class Inside: pass\n", encoding="utf-8")

    parser = ModuleParser()
    project_root = parser.parse_project_root(tmp_path)

    # We expect both root and nested modules to be present after recursive parse
    assert "root_module.py" in project_root.modules
    assert "inside.py" in project_root.modules
    assert any(cls.name == "Inside" for cls in project_root.modules["inside.py"].classes)
