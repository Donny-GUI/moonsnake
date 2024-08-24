from transpile.astmaker import LuaToPythonModule, LuaNodeConvertor
from transpile.astwriter import PythonASTWriter
from transpile.luaparser.ast import parse, walk
import ast


def get_python_nodes(filepath:str):
    converter = LuaNodeConvertor()
    with open(filepath, "r", errors="ignore") as f:
        content = f.read()
    chunk = parse(content)
    lnodes = [x for x in chunk.body.body]
    pynodes = converter.assign_methods([converter.convert(x) for x in lnodes])
    
    tree = []
    for index, x in enumerate(pynodes):
        tree.extend(
            [(index, subindex, y) for subindex, y in enumerate(ast.walk(x))]
            )
    
    for index, snode in enumerate(tree):
            if isinstance(snode, ast.Call) and snode.keywords and isinstance(snode.keywords, list) and snode.keywords[0] == "ANON":
                i = index 
                while i > 0:
                    i-=1
                    if isinstance(pynodes[i], ast.FunctionDef):
                        break            
                pynodes[i].body.insert(0, snode.keywords[1])
                snode.keywords = []
                
    
    for node in walk(chunk):
         
    luanodes = LuaToPythonModule().to_module(filepath)
    
    python_source = PythonASTWriter().visit()