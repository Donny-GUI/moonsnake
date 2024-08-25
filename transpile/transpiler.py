from transpile.astmaker import LuaToPythonModule
from transpile.astwriter import PythonASTWriter
from transpile.luaparser.ast import parse as luaparse, Chunk as LuaSourceAst
from transpile.dependency_checker import DependencyVisitor
from ast import parse as pythonparse
from dataclasses import dataclass
from ast import Module as PythonModule
from shutil import rmtree
import os
from typing import TypeVar
from shutil import copytree
from multiprocessing import Process, Queue


DATA_ATTRIBUTES = ("file", "source", "ast")

@dataclass
class LuaData:
    file: str
    source: str
    ast: LuaSourceAst

@dataclass
class PythonData:
    file: str
    source: str
    ast: PythonModule

DataType = TypeVar("DataType", *(PythonData,LuaData))
AbstractTreeType = TypeVar("AbstractTreeType", *(LuaSourceAst, PythonModule))

_datatypes = {"python":PythonData, "lua":LuaData}


class TranspileNode:
    def __init__(self, input: DataType, output: DataType) -> None:
        self.input = input
        self.output = output

class Collection:
    def __init__(self, name:str) -> None:
        self.name: str = name
        self.files = []
        self.directories = []
        self.sources = {}
        self.asts = {}

        self.datum = {}
    
    def add(self, file: str, source: str, ast:AbstractTreeType):
        self.files.append(file)
        self.directories.append(os.path.dirname(file))
        self.sources[file] = source
        self.asts[file] = ast
        self.datum[file] = _datatypes[self.name](file, source, ast)
    
    def node(self, file):
        return self.datum[file]


class TranspilerCollector:
    def __init__(self, input_language:str="lua", output_language:str="python") -> None:
        
        self.origin = Collection(input_language)
        self.output = Collection(output_language)
    
    def add(self,
            origin_source:str,
            origin_file:str, 
            origin_ast:AbstractTreeType, 
            output_file:str=None, 
            output_ast:AbstractTreeType=None, 
            output_source: str="") -> None:
        
        self.origin.add(origin_file, origin_source, origin_ast)
        self.output.add(output_file, output_source, output_ast)


class LuaToPythonTranspiler:
    def __init__(self, collection:bool=False) -> None:
        self.lua_ast_convertor = LuaToPythonModule()
        self.python_ast_writer = PythonASTWriter()
        self.is_collecting = collection
        if self.is_collecting == True:
            self.collection = TranspilerCollector() 

    def read_file(self, file:str) -> str:
        try:
            with open(file, "r", errors="ignore") as f:
                return f.read()
        except Exception as e:
            raise e

    def make_lua_ast(self, string:str) -> AbstractTreeType:
        return luaparse(string)

    def make_python_ast(self, string:str) -> AbstractTreeType:
        return pythonparse(string)

    def transpile_file(self, file:str, output_file:str):

        lua_source = self.read_file(file)
        lua_ast: LuaSourceAst = self.make_lua_ast(lua_source)
        try:
            py_ast = self.lua_ast_convertor.to_module(lua_ast)
        except:
            py_ast = PythonModule(body=[])
        finally:
            for node in py_ast.body:
                string = self.python_ast_writer.visit(node)


    def transpile_directory(self, directory:str, output_directory:str):
        if os.path.exists(directory) == False:
            raise Exception(f"Transpile source directory {directory} doesnt exist")

        # copy directory
        try:
            copytree(src=directory, dst=output_directory)
        except:
            rmtree(output_directory)
            copytree(src=directory, dst=output_directory)
            
        # get all files to be transpiled
        args = []
        procs:list[Process] = []
        for root, dirs, files in os.walk(output_directory):
            for file in files:
                filepath = os.path.join(root, file)
                
                if file.endswith(".lua"):
                    filename, ext = file.split(".")
                    python_basename = filename + ".py"
                    python_path = os.path.join(root, python_basename)
                    args.append((filepath, python_path))
                    
        # save one file for main process
        mine, pymine = args.pop()
        # build processes
        for arg in args:
            proc = Process(target=mp_transpile_file, args=arg)
            procs.append(proc)

        # run processes
        for proc in procs:
            proc.start()

        # do main work
        mp_transpile_file(mine, pymine)
        args.append((mine, pymine))

        # build the next set of processes
        depends_procs: list[Process] = []
        dq = Queue()
        for arg in args:
            proc = Process(target=get_dependencies, args=(arg[1], dq))
            depends_procs.append(proc)

        # join transpile processes
        for p in procs:
            p.join()
        
        # begin dependency procs
        for p in depends_procs:
            p.start()
        # join dependency procs
        for p in depends_procs:
            p.join()

        # build dependency map
        dependency_map = {}
        for arg in args:
            deps = dq.get()
            dependency_map[deps[0]] = deps[1]
        
        # find needed fixes to imports
        dependency_fixes_map = {}

        for file, depends in dependency_map.items():
            
            dependency_fixes_map[file] = {
                "variable fixes":{}, 
                "function fixes":{}
            }

            if depends['missing variables'] != None:
                for missing_variable in depends["missing variables"]:
                    for other_file, other_dependencies in dependency_map.items():
                        if missing_variable in other_dependencies["variables"]:
                            dependency_fixes_map[file]["variable fixes"][missing_variable] = other_file
            
            if depends["missing functions"] != None:
                for missing_function in depends["missing functions"]:
                    for other_file, other_dependencies in dependency_map.items():
                        if missing_function in other_dependencies["functions"]:
                            dependency_fixes_map[file]["function fixes"][missing_function] = other_file
            
        # apply the fixes to the file
        for file in dependency_map.keys():
            vfix = []
            ffix = []
            fixes = dependency_fixes_map[file]

            variables: dict[str, str] = fixes["variable fixes"]
            
            for name, module in variables:
                reference = module.strip(output_directory).split(".")[0]
                vfix.append(f"from {reference.replace("\\", ".")} import {name}")
            
            functions: dict[str, str] = fixes["function fixes"]

            for name, module in functions:
                reference = module.strip(output_directory).split(".")[0]
                ffix.append(f"from {reference.replace("\\", ".")} import {name}")

            with open(file, "r") as f:
                content = f.read()

            xcontent = "\n".join(vfix) + "\n".join(ffix) + "\n" + content
            
            with open(file, "w") as f:
                f.write(xcontent)
        
        
def get_dependencies(filename, q:Queue):
    with open(filename, "r", errors="ignore") as f:
        tree = pythonparse(f.read())
    depv = DependencyVisitor()
    depv.visit(tree)
    q.put((filename, depv.to_dict()))

def mp_transpile_file(file: str, output_file:str):
        self = LuaToPythonTranspiler()
        

        lua_source = self.read_file(file)
        lua_ast: LuaSourceAst = self.make_lua_ast(lua_source)
        try:
            py_ast = self.lua_ast_convertor.to_module(lua_ast)
        except:
            py_ast = PythonModule(body=[])
        finally:
            for node in py_ast.body:
                string = self.python_ast_writer.visit(node)



        os.remove(file)
        
