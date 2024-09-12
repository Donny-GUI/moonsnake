import ast

class VariableScopeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.scopes = []  # Stack to track current scopes
        self.declared_vars = set()  # Set to track declared variables
        self.used_vars = set()  # Set to track used variables
        self.builtins = {'print', 'str', 'int', 'len', 'range', 'list', 'dict', 'set', 'tuple', 'bool',
                         "lambda", "frozenset", "super", "self", "True", "False"}  # Add other built-ins as needed

    def visit_FunctionDef(self, node):
        # Enter a new scope for function
        self.scopes.append(set())
        self.generic_visit(node)
        # Exit the scope after function body is processed
        self.scopes.pop()

    def visit_ClassDef(self, node):
        # Enter a new scope for class
        self.scopes.append(set())
        self.generic_visit(node)
        # Exit the scope after class body is processed
        self.scopes.pop()

    def visit_Assign(self, node):
        # Track declared variables
        for target in node.targets:
            if isinstance(target, ast.Name):
                self._declare_variable(target.id)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            # Track used variables if they are not built-ins
            if node.id not in self.builtins:
                self._use_variable(node.id)
        self.generic_visit(node)

    def _declare_variable(self, var_name):
        if var_name not in self.builtins:  # Do not add built-ins as declared variables
            if self.scopes:
                self.scopes[-1].add(var_name)
            self.declared_vars.add(var_name)

    def _use_variable(self, var_name):
        if var_name not in self.builtins:  # Do not add built-ins as used variables
            self.used_vars.add(var_name)

    def report(self):
        undeclared_vars = self.used_vars - self.declared_vars
        print("Declared variables:", self.declared_vars)
        print("Used variables:", self.used_vars)
        print("Undeclared variables:", undeclared_vars)
    
    def get_undeclared_variables(self):
        return self.used_vars - self.declared_vars


def find_undeclared_variables(source_code:str):
    tree = ast.parse(source_code)
    analyzer = VariableScopeAnalyzer()
    analyzer.visit(tree)
    return analyzer.get_undeclared_variables()

def get_undeclared_variables(filepath:str):
    with open(filepath, 'r') as f:
        source_code = f.read()

    tree = ast.parse(source_code)
    analyzer = VariableScopeAnalyzer()
    analyzer.visit(tree)
    return analyzer.get_undeclared_variables()

