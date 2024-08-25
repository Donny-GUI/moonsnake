from transpile.astmaker import LuaToPythonModule
from transpile.astwriter import PythonASTWriter
from transpile.utility import directory_files_by_extension
from transpile.tests import LuaToPythonTranspiler as LTPT
from transpile.utility import unique_filename, set_extension
from transpile.cli import parser
import os
from shutil import copytree


def transpile_directory(directory: str, outputdir: str = None):
    """
    Transpiles a directory of Lua files to Python.

    Args:
            directory (str): The path to the directory containing Lua files to transpile.
            outputdir (str, optional): The path to the output directory. Defaults to the current 
                                       working directory plus "output".

    Returns:
            None
    """
    if outputdir == None:
        outputdir = os.path.join(os.getcwd(), "output")
    copytree(src=directory, dst=outputdir)
    print(f"[Transpiling]: {directory}")
    for root, dirs, files in os.walk(outputdir):
        lua_paths = [os.path.join(root, f)
                     for f in files if f.endswith(".lua")]
        file_sources = [transpile_lua_file(x) for x in lua_paths]


def lua_file_to_python_string(path: str) -> str:
    """
    Converts a Lua file at the specified path to a Python string.

    Args:
        path (str): The path to the Lua file to be converted.

    Returns:
        str: The converted Python string.
    """
    print(f"[Transpiling]: {path}")
    # init classes for transpiler
    convert = LuaToPythonModule(None)
    writer = PythonASTWriter()
    # convert the file to a python module
    mod = convert.to_module(path)
    # add the strings to source writer
    for node in mod.body:
        string = writer.visit(node)
        source.add(node, string)

    return source.dump()


def transpile_lua_file(path: str, outputfile: str = None):
    """
        Transpiles a Lua file at the specified path to a Python file.

        Args:
                path (str): The path to the Lua file to be transpiled.
                outputfile (str, optional): The path to the output Python file. Defaults to None.

        Returns:
                None
    """
    print(f"[Transpiling]: {path}")
    # init classes for transpiler
    convert = LuaToPythonModule()
    writer = PythonASTWriter()
    source = SourceWriter()

    # convert the file to a python module
    mod = convert.to_module(path)

    # make the unique filename
    pyfile = set_extension(path, ".py")
    pyfile = unique_filename(pyfile)

    # add the strings to source writer
    for node in mod.body:
        string = writer.visit(node)
        source.add(node, string)

    # write the file
    if outputfile == None:
        with open(pyfile, "w") as f:
            source.dump(f)
    else:
        with open(outputfile, "w") as f:
            source.dump(f)


def walk_transpile():
    """
    Walks through all files in the specified directory and transpiles them from Lua to Python.

    Args:
        None

    Returns:
        None
    """
    for file in directory_files_by_extension():
        print(file)
        transpile_lua_file(file)


def node_test():
    ltpt = LTPT()
    for file in directory_files_by_extension():
        ltpt.transpile(file)


def main():

    p = parser()
    
    args = p.parse_args()
    
    # if help flag is set, print help
    if "-h" in args or "--help" in args:
        p.print_help()
        
    if args.path:
        if os.path.exists(args.path):
            if os.path.isdir(args.path):
                transpile_directory(args.path, args.o)
                exit()
            elif os.path.isfile(args.path):
                transpile_lua_file(args.path, args.o)
                exit()
        else:
            p.print_help()
            print(f"""\033[41m\n⚠️  Could not locate path: {args.path}\n\033[0m""")
            exit()
            
    else:
        p.print_help()
        print("""\033[41m\n⚠️  Please provide a valid path\n\033[0m""")
        
        


if __name__ == "__main__":

    main()
