import ast
import os
from collections import defaultdict
from typing import List, Dict, Tuple, Optional

class VariableTracker(ast.NodeVisitor):
    def __init__(self):
        self.assignments = defaultdict(list)  # Tracks where variables are assigned
        self.references = defaultdict(list)  # Tracks where variables are referenced
        self.undeclared_references = defaultdict(list)  # Tracks references before assignment
        self.imported_modules = {}  # Tracks imported modules and their aliases
        self.function_defs = defaultdict(list)  # Tracks function definitions
        self.class_defs = defaultdict(list)  # Tracks class definitions

    def visit_Import(self, node: ast.Import):
        # Track simple imports (e.g., import module)
        for alias in node.names:
            self.imported_modules[alias.asname or alias.name] = alias.name

    def visit_ImportFrom(self, node: ast.ImportFrom):
        # Track from-imports (e.g., from module import x as y)
        module = node.module
        for alias in node.names:
            import_name = f"{module}.{alias.name}"
            self.imported_modules[alias.asname or alias.name] = import_name

    def visit_Assign(self, node: ast.Assign):
        # Track assignments to variables
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.assignments[target.id].append((node.lineno, node.col_offset))
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign):
        # Track augmented assignments (e.g., x += 1)
        if isinstance(node.target, ast.Name):
            self.assignments[node.target.id].append((node.lineno, node.col_offset))
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        # Track variable references and check if they are assigned before being referenced
        if isinstance(node.ctx, ast.Load):
            if (node.id not in self.assignments and
                    node.id not in self.imported_modules and
                    node.id not in self.function_defs and
                    node.id not in self.class_defs):
                self.undeclared_references[node.id].append((node.lineno, node.col_offset))
            self.references[node.id].append((node.lineno, node.col_offset))
        elif isinstance(node.ctx, ast.Store):
            self.assignments[node.id].append((node.lineno, node.col_offset))
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Track function definitions
        self.function_defs[node.name].append((node.lineno, node.col_offset))
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        # Track class definitions
        self.class_defs[node.name].append((node.lineno, node.col_offset))
        self.generic_visit(node)

    def get_results(self) -> Tuple[
        Dict[str, List[Tuple[int, int]]],
        Dict[str, List[Tuple[int, int]]],
        Dict[str, List[Tuple[int, int]]],
        Dict[str, List[Tuple[int, int]]],
        Dict[str, str]]:
        return (self.undeclared_references, self.assignments,
                self.function_defs, self.class_defs, self.imported_modules)

def find_variable_references(filename: str, search_paths: Optional[List[str]] = None) -> None:
    search_paths = search_paths or [os.path.dirname(filename)]

    with open(filename, 'r') as file:
        source_code = file.read()

    tree = ast.parse(source_code)
    tracker = VariableTracker()
    tracker.visit(tree)

    undeclared_references, assignments, function_defs, class_defs, imported_modules = tracker.get_results()

    print(f"Assignments:\n{'-'*40}")
    for var, locations in assignments.items():
        print(f"Variable '{var}' assigned at: {locations}")

    print(f"\nUndeclared References (Referenced before assignment):\n{'-'*40}")
    for var, locations in undeclared_references.items():
        print(f"Variable '{var}' referenced before assignment at: {locations}")

    print(f"\nFunction Definitions:\n{'-'*40}")
    for func, locations in function_defs.items():
        print(f"Function '{func}' defined at: {locations}")

    print(f"\nClass Definitions:\n{'-'*40}")
    for cls, locations in class_defs.items():
        print(f"Class '{cls}' defined at: {locations}")

    print(f"\nImported Modules:\n{'-'*40}")
    for alias, module in imported_modules.items():
        print(f"Alias '{alias}' refers to module '{module}'")

    # Optional: Attempt to trace the origins of undeclared references in imported modules
    trace_imports(imported_modules, undeclared_references, search_paths)
    
    print(f"\nTracing Imports\n{'-'*40}")

def trace_imports(imported_modules: Dict[str, str], undeclared_references: Dict[str, List[Tuple[int, int]]], search_paths: List[str]) -> None:
    for alias, module_path in imported_modules.items():
        # Check if any undeclared reference might come from this module
        for ref in undeclared_references:
            if ref.startswith(alias + ".") or ref == alias:
                print(f"\nTracing '{ref}' potentially from module '{module_path}'")
                # Attempt to find the file for the module if it's within the search paths
                module_file = locate_module_file(module_path, search_paths)
                if module_file:
                    print(f"Found module file: {module_file}")
                    # Here you could recursively analyze the module to find the origin of the reference
                else:
                    print(f"Could not locate file for module '{module_path}'")

def locate_module_file(module_path: str, search_paths: List[str]) -> Optional[str]:
    # Convert module path to file path (e.g., 'package.module' -> 'package/module.py')
    module_filename = module_path.replace('.', '/') + '.py'
    for path in search_paths:
        full_path = os.path.join(path, module_filename)
        if os.path.isfile(full_path):
            return full_path
    return None

# Example usage:
find_variable_references(__file__)
