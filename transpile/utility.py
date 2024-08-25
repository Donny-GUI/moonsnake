import os
from pathlib import Path
from typing import TypeVar
import functools


WindowsPath = TypeVar("WindowsPath", str, Path)


def filename(path: str):
    return os.path.basename(path).split(".")[0]


def set_extension(path: str, extension: str):
    if extension.startswith(".") != True:
        extension = "." + extension
    return path.rsplit(".")[0] + extension


def extension(path: str):
    return os.path.splitext(path)[1]


def unique_filename(path: str):

    def make_filename(filepath: str, index: int = None):
        ext = extension(filepath)
        file = filename(filepath)

        if index:
            file = file.rsplit("_")[0]
            file += "_" + str(index)
        file = file + ext

        return os.path.join(os.getcwd(), file)

    count = 0
    while True:
        # stop if the filename is unique
        if os.path.exists(path) == False:
            break
        # increment the ending number if not
        count += 1
        path = make_filename(path, count)

    return path


def directory_files_by_extension(
    directory: WindowsPath = f"C:\\Users\\{os.getlogin()}\\Desktop",
    extension: str = ".lua",
):

    files = []
    for root, _, fs in os.walk(directory):
        for file in fs:
            if file.endswith(extension):
                files.append(os.path.join(root, file))
    return files


def delete_files_in_directory(directory: str = ".\\converted\\"):
    for root, dirs, files in os.walk(directory):
        for file in files:
            os.remove(os.path.join(root, file))


def update(object="", action="", message=""):
    if object != "":
        object = "[\033[32m" + object + "\033[0m]"
    if action != "":
        action = "[\033[34m" + action + "\033[0m]"
    print(f"{object}{action}: {message}")


def logcall(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Log function name and arguments
        print(f"\n[Function] {func.__name__}")
        print(f"   Arguments: args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        print(f"   Returned : {result}")

        return result

    return wrapper



script = """from transpile.astmaker import LuaNodeConvertor
from transpile.astwriter import PythonASTWriter
from transpile.luaparser.ast import walk, parse
from transpile.utility import directory_files_by_extension
from transpile.utility import unique_filename, set_extension
from transpile.errorhandler import test_transpiled_file, successful
from transpile.mapper import LuaToPythonMapper
from ast import Module
import os


local_example_dir = r'C:\Users\donal\Documents\GitHub\moonsnake\examples'


def delexamples():
    for item in os.listdir(local_example_dir):
        os.remove(f"{local_example_dir}\\{item}")


def deltemp():
    try:
        os.remove("temp.py")
        print("[!]temp deleted")
    except:
        pass


def change_extension(path: str, extension: str) -> str:
    '''
    Changes the extension of a file.

    Args:
        path (str): The path to the file.
        extension (str): The new extension.

    Returns:
        str: The new path with the new extension.
    '''
    return set_extension(path, extension)


def walk_transpile():
    '''
    Walks through all files in the specified directory and transpiles them from Lua to Python.

    Args:
        None

    Returns:
        None
    '''
    for file in directory_files_by_extension():
        fi = set_extension(file, ".py")

        transpile_lua_file(
            file, local_example_dir + os.sep + os.path.basename(
                fi
            )
        )


def transpile_lua_file(path: str, outputfile: str = None):
    '''
        Transpiles a Lua file at the specified path to a Python file.

        Args:
                path (str): The path to the Lua file to be transpiled.
                outputfile (str, optional): The path to the output Python file. Defaults to None.

        Returns:
                None
    '''
    # init classes for transpiler
    convert = LuaNodeConvertor()
    writer = PythonASTWriter()

    with open(path, "r", errors="ignore") as f:
        content = f.read()

    lnodes = parse(content).body.body
    pnodes = convert.convert_nodes(lnodes)
    # convert the file to a python module

    mod = Module(body=pnodes, type_ignores=[])

    source = []
    # add the strings to source writer
    
    for node in mod.body:

        string = writer.visit(node)
        string = string.replace("for kv in ipairs(", "for k, v in enumerate(")
        source.append(string)

    src = "\n".join(source)
    mapper = LuaToPythonMapper()
    src = mapper.map_imports(src)
    
    # make the unique filename
    pyfile = set_extension(path, ".py")
    pyfile = unique_filename(pyfile)


    # write the file
    if outputfile == None:

        with open(pyfile, "w") as f:
            f.write(src)
    else:

        with open(outputfile, "w") as f:
            f.write(src)

        terror = test_transpiled_file(outputfile)
        if not successful(terror):
            terror.highlight()
            input("Press Enter to continue...")


delexamples()
deltemp()
walk_transpile()
"""