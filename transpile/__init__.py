from .astmaker import LuaNodeConvertor
from .astwriter import PythonASTWriter
from .luaparser.ast import parse
from .utility import unique_filename, set_extension
from .errorhandler import test_transpiled_file
from .mapper import LuaToPythonMapper
from .transformer import KVForLoopTransformer, HEXTransformer, TableMethodsTransformer, StringLibraryTransformer, IPairsTransformer
from .scopetracker import get_undeclared_variables
from .formatter import format_python_code
from .utility import parsable
from ast import Module


class LuaToPythonFileTranspiler:
    def __init__(self):
        pass
    
    def transpile_file(self, path: str, outputfile: str = None) -> None:
        # 1. init classes for transpiler
        lua_node_converter              = LuaNodeConvertor()
        python_ast_writer               = PythonASTWriter()
        string_lib_transformer          = StringLibraryTransformer()
        key_value_for_loop_transformer  = KVForLoopTransformer()
        table_methods_transformer       = TableMethodsTransformer()
        hex_function_transformer        = HEXTransformer()
        lua_to_python_mapper            = LuaToPythonMapper()
        
        # 2. Read the file to convert
        with open(path, "r", errors="ignore") as f:
            content = f.read()
        # 3. parse the lua to lua ast
        lua_ast_nodes_list = parse(content).body.body
        # 4. convert the lua nodes into python ast nodes
        python_nodes_list = lua_node_converter.convert_nodes(lua_ast_nodes_list)
        # 5. convert the file to a python module
        python_module = Module(body=python_nodes_list, type_ignores=[])
        # 6. write the python ast to a string
        source = []
        for node in python_module.body:
            # 6.1 fix string library encapsulation
            node = string_lib_transformer.visit(node)
            # 6.2 fix k, v loops
            node = key_value_for_loop_transformer.visit(node)
            # 6.3 fix table methods
            node = table_methods_transformer.visit(node)
            # 6.4 fix HEX() to hex()
            node = hex_function_transformer.visit(node)
            string = python_ast_writer.visit(node)
            source.append(string)  
        
        src = "\n".join(source)
        
        # 7. fix imports to mapped equivalents
        src = lua_to_python_mapper.map_imports(src)
        
        # 8. make the unique filename
        pyfile = set_extension(path, ".py")
        pyfile = unique_filename(pyfile)
        
        # 9. Format the code
        src = format_python_code(src)
        
        # 10. write the file
        if outputfile == None:
            with open(pyfile, "w") as f:
                f.write(src)            
        else:
            with open(outputfile, "w") as f:
                f.write(src)


            # self testing starts here <<<<
            
            print(f"\033[42m {outputfile}      \033[0m")
            tempfile = "temp.py"
            with open(tempfile, "w") as f:
                f.write(src)

            terror = test_transpiled_file(tempfile)
            terror.highlight()
            
            try:
                undeclared_vars = get_undeclared_variables(tempfile)
                print("Undeclared variables:", undeclared_vars)
            except:
                pass 
            
            # parse test
            print("Is parsable: ", parsable(src))