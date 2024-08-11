import os
from transpile.astmaker import LuaToPythonModule
from transpile.astwriter import PythonASTWriter
from transpile.sourcewriter import SourceWriter
from transpile.patternmatch import LuaAstMatch
from transpile.utility import directory_files_by_extension, delete_files_in_directory
from transpile.tests import LuaToPythonTranspiler as LTPT



def transpile_lua(file, patterns=False):

    print(f"[Transpiling]: {file}")
    convert = LuaToPythonModule(None)
    writer = PythonASTWriter()
    source = SourceWriter()

    mod = convert.to_module(file)
    pyfile = os.path.basename(file)
    pyfile = pyfile.split(".")[0] + ".py"
    source.make_directory("converted")
    for node in mod.body:
        string = writer.visit(node)
        source.add(node, string)
    with open(f".\\converted\\{pyfile}", "w") as f:
        source.dump(f)

def walk_transpile():
    for file in directory_files_by_extension():
        print(file)
        transpile_lua(file)

def node_test():
    ltpt = LTPT()
    for file in directory_files_by_extension():
        ltpt.transpile(file)


if __name__ == '__main__':
    print("begin")
    node_test()
