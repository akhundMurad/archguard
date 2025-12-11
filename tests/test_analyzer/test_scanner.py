from archguard import dto, enums
from archguard.analyzer import Scanner


def make_module(
    name: str,
    imports: list[dto.ImportInfo] | None = None,
    classes: list[dto.ClassInfo] | None = None,
) -> dto.ModuleInfo:
    """Helper to build a ModuleInfo with minimal required fields."""
    return dto.ModuleInfo(
        name=name,
        imports=imports or [],
        classes=classes or [],
        file_path=name,
    )


def make_project_root(modules: list[dto.ModuleInfo]) -> dto.ProjectRoot:
    return dto.ProjectRoot(
        modules={m.name: m for m in modules},
    )


def make_module_rule(
    *,
    reside_in: str | None = None,
    do_not_reside_in: str | None = None,
    should_not_import_from: str | None = None,
    should_import_from: list[str] | None = None,
) -> dto.Rule:
    mr = dto.ModuleRule(
        reside_in=reside_in,
        do_not_reside_in=do_not_reside_in,
        should_not_import_from=should_not_import_from,
        should_import_from=should_import_from,
    )
    return dto.Rule(rule_type=enums.RuleType.MODULES, module_rule=mr)


def make_class_rule(
    *,
    reside_in_module: str | None = None,
    do_not_reside_in_module: str | None = None,
    should_have_name_matching: str | None = None,
    should_have_decorators: list[str] | None = None,
) -> dto.Rule:
    cr = dto.ClassRule(
        reside_in_module=reside_in_module,
        do_not_reside_in_module=do_not_reside_in_module,
        should_have_name_matching=should_have_name_matching,
        should_have_decorators=should_have_decorators,
    )
    return dto.Rule(rule_type=enums.RuleType.CLASSES, class_rule=cr)


def make_import(
    import_module: str,
    *,
    from_module: str | None = None,
    level: int = 0,
    line_no: int = 1,
) -> dto.ImportInfo:
    return dto.ImportInfo(
        import_module=import_module,
        from_module=from_module,
        level=level,
        line_no=line_no,
    )


def make_class(
    name: str,
    *,
    qualname: str | None = None,
    decorators: list[str] | None = None,
    base_classes: list[str] | None = None,
    module: str | None = None,
    lineno: int = 1,
) -> dto.ClassInfo:
    return dto.ClassInfo(
        name=name,
        qualname=qualname or name,
        decorators=decorators or [],
        base_classes=base_classes or [],
        module=module or "",
        lineno=lineno,
    )


def test_scanner_no_rules_no_violations():
    """No rules at all -> always success, empty violations."""
    project_root = make_project_root(
        [
            make_module(
                "myapp.module",
                imports=[make_import("os")],
                classes=[make_class("Foo")],
            )
        ]
    )

    scanner = Scanner(rule_set=[])

    result = scanner.scan_project_root(project_root)

    assert result.success is True
    assert result.violations == []


def test_scanner_module_rule_reside_in_matches():
    """
    ModuleRule with reside_in == module.name applies only to that module.
    Violating import should produce a violation.
    """
    imports = [
        make_import("myapp.infrastructure.repositories.order_repository"),
    ]
    module = make_module("myapp.infrastructure.repositories.order", imports=imports)
    project_root = make_project_root([module])

    rule = make_module_rule(
        reside_in="myapp.infrastructure.repositories.order",
        should_not_import_from="myapp.infrastructure.repositories.order_repository",
    )

    scanner = Scanner(rule_set=[rule])

    result = scanner.scan_project_root(project_root)

    assert result.success is False
    assert len(result.violations) == 1
    v = result.violations[0]
    assert v.violated_rule is rule
    assert v.offender_import is imports[0]


def test_scanner_module_rule_reside_in_different_module_not_applied():
    """ModuleRule with reside_in pointing to another module must not apply here."""
    imports = [make_import("myapp.other.stuff")]
    module = make_module("myapp.current", imports=imports)
    project_root = make_project_root([module])

    rule = make_module_rule(
        reside_in="myapp.somewhere_else",
        should_not_import_from="myapp.other.stuff",
    )

    scanner = Scanner(rule_set=[rule])
    result = scanner.scan_project_root(project_root)

    # Rule shouldn't apply -> no violations
    assert result.success is True
    assert result.violations == []


def test_scanner_module_rule_do_not_reside_in_excludes_module():
    """
    ModuleRule with do_not_reside_in == module.name should NOT apply to this
    module, even if the imports would otherwise violate.
    """
    imports = [make_import("forbidden.pkg")]
    module = make_module("forbidden.module", imports=imports)
    project_root = make_project_root([module])

    rule = make_module_rule(
        do_not_reside_in="forbidden.module",
        should_not_import_from="forbidden.pkg",
    )

    scanner = Scanner(rule_set=[rule])
    result = scanner.scan_project_root(project_root)

    assert result.success is True
    assert result.violations == []


def test_scanner_module_rule_should_import_from_patterns():
    """
    should_import_from used as a list of glob patterns.
    Matching pattern -> OK; non-matching pattern -> violation.
    """
    allowed_import = make_import("myapp.service.user")
    forbidden_import = make_import("myapp.infrastructure.db")

    module = make_module(
        "myapp.service.module",
        imports=[allowed_import, forbidden_import],
    )
    project_root = make_project_root([module])

    rule = make_module_rule(
        reside_in="myapp.service.module",
        should_import_from=["myapp.service.*"],
    )

    scanner = Scanner(rule_set=[rule])
    result = scanner.scan_project_root(project_root)

    # Only forbidden_import should violate
    assert result.success is False
    assert len(result.violations) == 1
    v = result.violations[0]
    assert v.offender_import is forbidden_import
    assert v.violated_rule is rule


def test_scanner_module_rule_should_import_from_none_means_no_restriction():
    """If should_import_from is None/empty, any import is allowed."""
    imports = [
        make_import("anything.goes"),
        make_import("another.anything"),
    ]
    module = make_module("myapp.module", imports=imports)
    project_root = make_project_root([module])

    rule = make_module_rule(
        reside_in="myapp.module",
        should_import_from=None,  # no restriction
    )

    scanner = Scanner(rule_set=[rule])
    result = scanner.scan_project_root(project_root)

    assert result.success is True
    assert result.violations == []


def test_scanner_module_rule_should_not_import_from_substring_match():
    """should_not_import_from is treated as a substring for fqname."""
    imports = [
        make_import("myapp.infrastructure.db.mysql"),
        make_import("myapp.service.logic"),
    ]
    module = make_module("myapp.module", imports=imports)
    project_root = make_project_root([module])

    rule = make_module_rule(
        reside_in="myapp.module",
        should_not_import_from="myapp.infrastructure.db",
    )

    scanner = Scanner(rule_set=[rule])
    result = scanner.scan_project_root(project_root)

    assert result.success is False
    assert len(result.violations) == 1
    v = result.violations[0]
    assert v.offender_import is imports[0]


def test_scanner_resolves_relative_imports_correctly():
    """
    Relative imports should be resolved to fqname and checked by rules.
    Example: current_module = 'myapp.infrastructure.repositories.order'
             from . import qual  -> fqname 'myapp.infrastructure.repositories.qual'
    """
    rel_import = make_import(
        import_module="qual",
        from_module=None,
        level=1,  # from . import qual
    )
    module = make_module(
        "myapp.infrastructure.repositories.order",
        imports=[rel_import],
    )
    project_root = make_project_root([module])

    rule = make_module_rule(
        reside_in="myapp.infrastructure.repositories.order",
        should_not_import_from="myapp.infrastructure.repositories.qual",
    )

    scanner = Scanner(rule_set=[rule])
    result = scanner.scan_project_root(project_root)

    assert result.success is False
    assert len(result.violations) == 1
    assert result.violations[0].offender_import is rel_import


# -------------------- Class rules --------------------------------------------


def test_scanner_class_rule_name_pattern_violation():
    """
    ClassRule.should_have_name_matching uses fnmatch.
    Non-matching name -> violation.
    """
    classes = [
        make_class("OrderRepository"),
        make_class("SomeRandomClass"),
    ]
    module = make_module("myapp.domain.order", classes=classes)
    project_root = make_project_root([module])

    rule = make_class_rule(
        reside_in_module="myapp.domain.order",
        should_have_name_matching="*Repository",
    )

    scanner = Scanner(rule_set=[rule])
    result = scanner.scan_project_root(project_root)

    # Only SomeRandomClass should violate
    assert result.success is False
    assert len(result.violations) == 1
    v = result.violations[0]
    assert v.offender_class is classes[1]
    assert v.violated_rule is rule


def test_scanner_class_rule_name_pattern_no_requirement():
    """If should_have_name_matching is None, class names are unrestricted."""
    classes = [
        make_class("Anything"),
        make_class("ReallyAnything"),
    ]
    module = make_module("myapp.domain", classes=classes)
    project_root = make_project_root([module])

    rule = make_class_rule(
        reside_in_module="myapp.domain",
        should_have_name_matching=None,
    )

    scanner = Scanner(rule_set=[rule])
    result = scanner.scan_project_root(project_root)

    assert result.success is True
    assert result.violations == []


def test_scanner_class_rule_decorators_all_required_present():
    """All decorators listed in should_have_decorators must be present."""
    classes = [
        make_class("MyService", decorators=["dataclass", "service"]),
    ]
    module = make_module("myapp.services", classes=classes)
    project_root = make_project_root([module])

    rule = make_class_rule(
        reside_in_module="myapp.services",
        should_have_decorators=["dataclass", "service"],
    )

    scanner = Scanner(rule_set=[rule])
    result = scanner.scan_project_root(project_root)

    assert result.success is True
    assert result.violations == []


def test_scanner_class_rule_decorators_missing_one():
    """Missing one of the required decorators -> violation."""
    good = make_class("GoodOne", decorators=["dataclass", "service"])
    bad = make_class("BadOne", decorators=["dataclass"])

    module = make_module("myapp.services", classes=[good, bad])
    project_root = make_project_root([module])

    rule = make_class_rule(
        reside_in_module="myapp.services",
        should_have_decorators=["dataclass", "service"],
    )

    scanner = Scanner(rule_set=[rule])
    result = scanner.scan_project_root(project_root)

    assert result.success is False
    assert len(result.violations) == 1
    v = result.violations[0]
    assert v.offender_class is bad
    assert v.violated_rule is rule


def test_scanner_class_rule_decorators_none_means_no_restriction():
    """If should_have_decorators is None/empty, decorators are unrestricted."""
    classes = [
        make_class("One", decorators=[]),
        make_class("Two", decorators=["whatever"]),
    ]
    module = make_module("myapp.services", classes=classes)
    project_root = make_project_root([module])

    rule = make_class_rule(
        reside_in_module="myapp.services",
        should_have_decorators=None,
    )

    scanner = Scanner(rule_set=[rule])
    result = scanner.scan_project_root(project_root)

    assert result.success is True
    assert result.violations == []


def test_scanner_class_rule_do_not_reside_in_excludes_module():
    """
    ClassRule.do_not_reside_in_module == module.name should exclude this module
    from validation, even if classes would otherwise violate.
    """
    bad_class = make_class("BadName", decorators=[])
    module = make_module("forbidden.module", classes=[bad_class])
    project_root = make_project_root([module])

    rule = make_class_rule(
        do_not_reside_in_module="forbidden.module",
        should_have_name_matching="Good*",
    )

    scanner = Scanner(rule_set=[rule])
    result = scanner.scan_project_root(project_root)

    assert result.success is True
    assert result.violations == []


def test_scanner_multiple_modules_and_rule_types_combined():
    """
    End-to-end: project with multiple modules, module + class rules mixed.
    Ensures Scanner aggregates violations across modules and rule types.
    """
    # Module 1: one bad import
    m1_imports = [
        make_import("myapp.infrastructure.db"),
        make_import("myapp.service.ok"),
    ]
    m1_classes = [make_class("OrderRepository", decorators=["dataclass", "service"])]
    m1 = make_module("myapp.service.order", imports=m1_imports, classes=m1_classes)

    # Module 2: one bad class name
    m2_imports = [make_import("myapp.service.order")]
    m2_classes = [make_class("RandomName", decorators=["dataclass"])]
    m2 = make_module("myapp.domain.order", imports=m2_imports, classes=m2_classes)

    project_root = make_project_root([m1, m2])

    module_rule = make_module_rule(
        reside_in="myapp.service.order",
        should_not_import_from="myapp.infrastructure.db",
    )

    class_rule = make_class_rule(
        reside_in_module="myapp.domain.order",
        should_have_name_matching="*Repository",
    )

    scanner = Scanner(rule_set=[module_rule, class_rule])
    result = scanner.scan_project_root(project_root)

    assert result.success is False
    # One import violation and one class violation
    assert len(result.violations) == 2

    offenders_imports = [v.offender_import for v in result.violations if hasattr(v, "offender_import")]
    offenders_classes = [v.offender_class for v in result.violations if hasattr(v, "offender_class")]

    assert m1_imports[0] in offenders_imports
    assert m2_classes[0] in offenders_classes
