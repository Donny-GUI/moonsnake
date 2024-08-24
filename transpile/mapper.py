
from ast import NodeTransformer
import ast

class AnonFixer(NodeTransformer):
    stack = [None, None]
    anon = []
    last = None
    functions: list[ast.FunctionDef] = []
    
    def visit_Call(self, node):
        if node.keywords and node.keywords[0] == "ANON":
            if self.last != None:
                self.last.body.insert(0, node.keywords[1])
                node.keywords = []
        
        return node
    
    def visit_FunctionDef(self, node):
        self.last = node
        self.functions.append(node)
        return node
    
    def finalize(self, module:ast.Module):
        for index, node in enumerate(module.body):
            if isinstance(node, ast.FunctionDef):
                for func in self.functions:
                    if func.name == node.name:
                        module.body[index] = func
                        break
            if isinstance(node, ast.ClassDef):
                for bodyindex, bodynode in enumerate(node.body):
                    if isinstance(bodynode, ast.FunctionDef):
                        for func in self.functions:
                            if func.name == bodynode.name:
                                module.body[index].body[bodyindex] = func
                                break
        return module
                