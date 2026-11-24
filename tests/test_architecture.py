import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "boxoffice"
MODULES = ["core", "analytics", "audit"]
LAYERS = ["domain", "application", "infrastructure", "presentation"]


def imports_of(path: Path) -> set[str]:
    found = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
    return found


def files_of(module: str, layer: str | None = None):
    base = SRC / "modules" / module / (layer or "")
    return [p for p in base.rglob("*.py")]


def test_modules_import_other_modules_only_through_their_public_contract():
    violations = []
    for module in MODULES:
        for file in files_of(module):
            for imp in imports_of(file):
                if not imp.startswith("boxoffice.modules."):
                    continue
                other = imp.split(".")[2]
                if other != module and not (imp == f"boxoffice.modules.{other}.contract"
                                            or imp.startswith(f"boxoffice.modules.{other}.contract.")):
                    violations.append(f"{module}/{file.name} imports {imp}")
    assert not violations, "\n".join(violations)


def test_cross_module_imports_live_only_in_acl_or_module_file():
    violations = []
    for module in MODULES:
        for file in files_of(module):
            for imp in imports_of(file):
                if imp.startswith("boxoffice.modules.") and imp.split(".")[2] != module:
                    rel = file.relative_to(SRC / "modules" / module)
                    if not (rel.parts[:2] == ("infrastructure", "acl") or rel.name == "module.py"):
                        violations.append(f"{module}/{rel} imports {imp}")
    assert not violations, "\n".join(violations)


def test_layers_inside_each_module_respect_dependency_rule():
    forbidden = {
        "domain": {"sqlalchemy", "fastapi", "pydantic", "jwt", "starlette", "application", "infrastructure", "presentation"},
        "application": {"sqlalchemy", "fastapi", "pydantic", "jwt", "infrastructure", "presentation"},
        "presentation": {"sqlalchemy", "infrastructure"},
    }
    violations = []
    for module in MODULES:
        for layer, banned in forbidden.items():
            for file in files_of(module, layer):
                for imp in imports_of(file):
                    parts = imp.split(".")
                    inner = parts[3] if imp.startswith(f"boxoffice.modules.{module}.") and len(parts) > 3 else None
                    if parts[0] in banned or inner in banned:
                        violations.append(f"{module}/{layer}/{file.name} imports {imp}")
    assert not violations, "\n".join(violations)


def test_shared_kernel_does_not_depend_on_modules():
    for file in (SRC / "shared").glob("*.py"):
        assert not any(i.startswith("boxoffice.modules") for i in imports_of(file)), file.name
