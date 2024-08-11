from transpile.astmaker import LuaToPythonModule
from transpile.astwriter import PythonASTWriter
from transpile.sourcewriter import SourceWriter
from transpile.luaparser.ast import parse as luaparse, Chunk as LuaSourceAst
from ast import parse as pythonparse
import os
import json


class LuaToPythonTranspiler:
    def __init__(self) -> None:
        self.lua_ast_convertor = LuaToPythonModule()
        self.python_ast_writer = PythonASTWriter()
        self.python_source_writer = SourceWriter()

    def read_file(self, file:str) -> str:
        try:
            with open(file, "r", errors="ignore") as f:
                return f.read()
        except Exception as e:
            raise e

    def make_lua_ast(self, string:str):
        return luaparse(string)

    def make_python_ast(self, string:str):
        return pythonparse(string)

    def transpile(self, file:str):
        this_python_source = SourceWriter()
        lua_source = self.read_file(file)
        lua_ast: LuaSourceAst = self.make_lua_ast(lua_source)
        py_ast = self.lua_ast_convertor.to_module(lua_ast)
        with open("patterns.json", "w") as f:
            f.write(json.dumps(self.lua_ast_convertor._patterns, indent=4))
        input()
        for node in py_ast.body:
            string = self.python_ast_writer.visit(node)
            this_python_source.add(node, string)
            self.python_source_writer.add(node, string)
        with open(f".\\data\\_{os.path.basename(file).split(".lua")[0]}.py", "w") as f:
            this_python_source.dump(f)

        


        