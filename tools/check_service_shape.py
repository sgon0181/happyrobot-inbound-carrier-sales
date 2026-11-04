"""Enforce the service size and Radon complexity gates in architecture section 14."""

import ast
from pathlib import Path

from radon.complexity import cc_visit  # type: ignore[import-untyped]


def violations(path: Path) -> list[str]:
    source = path.read_text()
    issues = []
    if len(source.splitlines()) > 300:
        issues.append(f"{path} exceeds 300 lines")
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if (
            not isinstance(node, ast.ClassDef)
            and node.end_lineno
            and node.end_lineno - node.lineno + 1 > 50
        ):
            issues.append(f"{path}:{node.lineno} {node.name} exceeds 50 lines")
        # Walking the AST includes every closure and nested class, which cc_visit omits.
        block = cc_visit(ast.unparse(node))[0]
        if block.complexity > 10:
            issues.append(f"{path}:{node.lineno} {node.name} complexity {block.complexity}")
    return list(dict.fromkeys(issues))


if __name__ == "__main__":
    issues = [
        message
        for path in sorted(Path("service").rglob("*.py"))
        if "tests" not in path.parts
        for message in violations(path)
    ]
    if issues:
        raise SystemExit("\n".join(issues))
    print("Production service meets the module, function and Radon complexity gates.")
