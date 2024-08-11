import ast 

        

class DependencyVisitor(ast.NodeVisitor):
    def __init__(self):
        self.assigned_vars = set()
        self.used_vars = set()
        self.defined_classes = set()
        self.called_functions = set()
        self.defined_functions = set()
    
    def to_dict(self):
        return {
            "variables":self.assigned_vars,
            "references": self.used_vars,
            "classes":self.defined_classes,
            "functions":self.defined_functions,
            "calls": self.called_functions,
            "missing variables":self.undefined_variables,
            "missing functions":self.undefined_functions
            }

    @property
    def undefined_variables(self):
        return self.used_vars - self.assigned_vars
    
    @property 
    def undefined_functions(self):
        self.called_functions - self.defined_functions

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.defined_functions.add(node.name)
    
    def visit_Call(self, node:ast.Call):
        if isinstance(node.func, ast.Name):
            self.called_functions.add(node.func.id)

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.assigned_vars.add(target.id)
        self.generic_visit(node)

    def visit_ClassDef(self, node:ast.ClassDef):
        self.defined_classes.add(node.name)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used_vars.add(node.id)
        self.generic_visit(node)

