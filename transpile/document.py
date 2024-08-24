import transpile.luaparser.ast as last
from transpile.luaparser.ast import to_lua_source
from transpile.astmaker import LuaToPythonModule
import ast


class LuaNode:
    def __init__(self, node: last.Node) -> None:
        self.node = node
        self.string = to_lua_source(node)
        self.length = len(self.string)


class PythonNode:
    def __init__(self, node: ast.AST, string: str, start: int, end: int) -> None:
        self.node = node
        self.string = string
        self.length = len(self.string)
        self.start = start
        self.end = end


class Nodulizer:
    def __init__(self) -> None:
        self.file = None

    def nodulize(self, file: str):
        self.file = file
        with open(file, "r", errors="ignore") as f:
            source = f.read()
        lua_nodes = last.parse(source).body.body

        python_module = LuaToPythonModule().to_module(source)
