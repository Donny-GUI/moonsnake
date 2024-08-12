from transpile.transpiler import LuaToPythonTranspiler
from transpile.tests import LuaToPythonTranspiler as LTPT
import os
import time
import shutil
from transpile.luaparser.ast import (
    parse as lparse,
    walk as lwalk,
    Call,
    Name,
    If,
    Assign,
    Function,
    Constructor,
    Initializer,
)


def delete_decompiled():
    shutil.rmtree(os.path.join(os.getcwd(), "decompiled"))


def directory_test():
    start = time.time()
    ltpt = LuaToPythonTranspiler()
    ltpt.transpile_directory(
        f"C:\\Users\\{os.getlogin()}\\Desktop\\decompiled", "decompiled"
    )
    delta = time.time() - start
    return delta


def node_test():
    ltpt = LTPT()
    for file in os.listdir(f"C:\\Users\\{os.getlogin()}\\Desktop\\decompiled"):
        if file.endswith(".lua"):
            print(file)
            ltpt.transpile(
                os.path.join(f"C:\\Users\\{os.getlogin()}\\Desktop\\decompiled", file)
            )


def local_test():
    with open(r"C:\Users\donal\Desktop\newless\tests\loc.lua", "r") as f:
        content = f.read()
    x = lparse(content)
    for node in x.body.body:
        if isinstance(node, Initializer):
            for subnode in node.body.body:
                if isinstance(subnode, If):
                    for ssubnode in lwalk(subnode):
                        print(ssubnode)
