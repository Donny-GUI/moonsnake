from transpile.astmaker import LuaToPythonModule
from transpile.astwriter import PythonASTWriter
from transpile.sourcewriter import SourceWriter
from transpile.utility import directory_files_by_extension
from transpile.tests import LuaToPythonTranspiler as LTPT
from transpile.utility import unique_filename, set_extension
from transpile.cli import parser


def lua_file_to_python_string(path: str) -> str:
    print(f"[Transpiling]: {path}")
    # init classes for transpiler
    convert = LuaToPythonModule(None)
    writer = PythonASTWriter()
    source = SourceWriter()
    # convert the file to a python module
    mod = convert.to_module(path)
    # add the strings to source writer
    for node in mod.body:
        string = writer.visit(node)
        source.add(node, string)

    return source.dump()


def transpile_lua_file(path: str):

    print(f"[Transpiling]: {path}")
    # init classes for transpiler
    convert = LuaToPythonModule(None)
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
    with open(pyfile, "w") as f:
        source.dump(f)


def walk_transpile():
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



if __name__ == "__main__":
    DEBUG = False
    if not DEBUG:
        main()
    else:
        node_test()
    exit()