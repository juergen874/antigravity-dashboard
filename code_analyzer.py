#!/usr/bin/env python3
"""
Antigravity Code Analyzer
Zero-dependency Python AST parser and visual call-graph generator for Termux.
"""

import os
import ast
import json
from typing import Dict, Any, List

class CodeVisitor(ast.NodeVisitor):
    def __init__(self):
        self.imports = []
        self.functions = []
        self.classes = []
        self.function_calls = {}
        self.current_function = None

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append({
                "module": alias.name,
                "asname": alias.asname,
                "type": "import"
            })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ""
        for alias in node.names:
            self.imports.append({
                "module": module,
                "name": alias.name,
                "asname": alias.asname,
                "type": "from"
            })
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        args = [a.arg for a in node.args.args]
        docstring = ast.get_docstring(node) or ""
        prev_func = self.current_function
        self.current_function = node.name
        self.function_calls[node.name] = []

        # Find calls inside this function
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    self.function_calls[node.name].append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    self.function_calls[node.name].append(child.func.attr)

        self.functions.append({
            "name": node.name,
            "args": args,
            "docstring": docstring,
            "lineno": node.lineno,
            "end_lineno": getattr(node, "end_lineno", node.lineno),
            "is_async": False
        })
        self.generic_visit(node)
        self.current_function = prev_func

    def visit_AsyncFunctionDef(self, node):
        args = [a.arg for a in node.args.args]
        docstring = ast.get_docstring(node) or ""
        prev_func = self.current_function
        self.current_function = node.name
        self.function_calls[node.name] = []

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    self.function_calls[node.name].append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    self.function_calls[node.name].append(child.func.attr)

        self.functions.append({
            "name": node.name,
            "args": args,
            "docstring": docstring,
            "lineno": node.lineno,
            "end_lineno": getattr(node, "end_lineno", node.lineno),
            "is_async": True
        })
        self.generic_visit(node)
        self.current_function = prev_func

    def visit_ClassDef(self, node):
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append({
                    "name": item.name,
                    "args": [a.arg for a in item.args.args],
                    "lineno": item.lineno
                })
        bases = []
        for b in node.bases:
            if isinstance(b, ast.Name):
                bases.append(b.id)
            elif isinstance(b, ast.Attribute):
                bases.append(f"{getattr(b.value, 'id', '')}.{b.attr}")

        self.classes.append({
            "name": node.name,
            "bases": bases,
            "docstring": ast.get_docstring(node) or "",
            "methods": methods,
            "lineno": node.lineno,
            "end_lineno": getattr(node, "end_lineno", node.lineno)
        })
        self.generic_visit(node)

def generate_mermaid(functions: List[Dict[str, Any]], calls: Dict[str, List[str]], filename: str) -> str:
    lines = ["graph TD"]
    lines.append(f'    subgraph "{filename}"')
    
    func_names = {f["name"] for f in functions}
    for f in functions:
        name = f["name"]
        args_str = ", ".join(f["args"])
        lines.append(f'        fn_{name}["⚙️ {name}({args_str})"]')

    for caller, callee_list in calls.items():
        unique_callees = set(callee_list)
        for callee in unique_callees:
            if callee in func_names and callee != caller:
                lines.append(f"        fn_{caller} --> fn_{callee}")

    lines.append("    end")
    return "\n".join(lines)

def analyze_file(filepath: str) -> Dict[str, Any]:
    if not os.path.exists(filepath):
        return {"success": False, "error": f"File '{filepath}' not found"}

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            code = f.read()

        total_lines = len(code.splitlines())
        code_lines = len([l for l in code.splitlines() if l.strip() and not l.strip().startswith("#")])
        comment_lines = len([l for l in code.splitlines() if l.strip().startswith("#")])

        tree = ast.parse(code, filename=os.path.basename(filepath))
        visitor = CodeVisitor()
        visitor.visit(tree)

        mermaid = generate_mermaid(visitor.functions, visitor.function_calls, os.path.basename(filepath))

        return {
            "success": True,
            "filename": os.path.basename(filepath),
            "filepath": filepath,
            "stats": {
                "total_lines": total_lines,
                "code_lines": code_lines,
                "comment_lines": comment_lines,
                "functions_count": len(visitor.functions),
                "classes_count": len(visitor.classes),
                "imports_count": len(visitor.imports)
            },
            "imports": visitor.imports,
            "classes": visitor.classes,
            "functions": visitor.functions,
            "calls": visitor.function_calls,
            "mermaid": mermaid
        }
    except Exception as e:
        return {
            "success": False,
            "filename": os.path.basename(filepath),
            "filepath": filepath,
            "error": str(e)
        }

if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "server.py"
    res = analyze_file(target)
    print(json.dumps(res, indent=2))
