from transpile.astmaker import LuaNodeConvertor
from transpile.astwriter import PythonASTWriter
from transpile.luaparser.ast import parse, walk 
import ast


def stringformat(item):
    return "'" + item + "'"

class SubNode:
    def __init__(self, node, position, character_index) -> None:
        self.node = node
        

class Comment:...

class HtmlNode:
    def __init__(self, node: ast.AST, position: str, character_index: int) -> None:
        self.node = node
        self.source = PythonASTWriter().visit(node)
        self.end_index = character_index + len(self.source)
        if isinstance(self.node, ast.stmt):
            base = "'stmt'"
        elif isinstance(self.node, Comment):
            base = "'comment'"
        else:
            base = "'expr'"
        self.tag =\
            "<{} class={}, id={}, start={}><p>{}</p>"\
                .format( base,  self.node.__class__.__name__.lstrip("ast."), position, character_index, PythonASTWriter().visit(self.node))
        self.content = []
        self.end_index = character_index
        for index, subnode in enumerate(ast.walk(node)[1:]):
            self.end_index+=len(PythonASTWriter().visit(subnode))
            self.content.append(HtmlNode(subnode, index, self.end_index))
        self.endtag ="\n</{}>".format(base)
        
    def write(self):
        retv = [self.tag]
        for x in self.content:
            t = "\n\t" + "\n\t".join(x.write().split("\n"))
            retv.append(t)
        retv.append(self.endtag)
        return "".join(retv)

class LuaToPythonConvertor(LuaNodeConvertor):

    def __init__(self, filepath:str):
        super().__init__()
        self.filepath = filepath
        with open(self.filepath, "r", errors="ignore") as f:
            self.lua_source = f.read()
        # get lua tree 
        self.lua_nodes = parse(self.lua_source).body.body
        # convert to python nodes list
        self.python_nodes = self.convert_nodes(self.lua_nodes)
        
        # Flatten the nodes
        self.tree = []
        for index, x in enumerate(self.python_nodes):
            self.tree.extend([(index, subindex, y) 
                               for subindex, y 
                               in enumerate(ast.walk(x))])
    
        # put the anonymous function definitions in the right place scopwise (tough!)
        for xnode in self.tree:
            snode = xnode[-1]
            if isinstance(snode, ast.Call) and snode.keywords and isinstance(snode.keywords, list) and snode.keywords[0] == "ANON":
                i = xnode[0]
                t = xnode[1]
                while True:
                    i-=1
                    if i < 0:
                        self.python_nodes.insert(0, snode)
                        break
                    elif isinstance(self.python_nodes[i], ast.FunctionDef):            
                        self.python_nodes[i].body.insert(0, snode.keywords[1])
                        snode.keywords = []
                        break
        
        del self.tree
        self.writer = PythonASTWriter()
        
        self.strings = [self.writer.visit(node) for node in self.python_nodes]
        
        
    
    def to_string(self):
        return "\n".join(self.strings)
        
    
