import os
import ast
import importlib.util
from ast import Module
from shutil import copytree
from multiprocessing import Process
from transpile.astmaker import LuaNodeConvertor
from transpile.astwriter import PythonASTWriter
from transpile.luaparser.ast import parse
from transpile.utility import directory_files_by_extension, unique_filename, set_extension
from transpile.errorhandler import test_transpiled_file
from transpile.mapper import LuaToPythonMapper
from transpile.transformer import (
    KVForLoopTransformer,
    HEXTransformer,
    TableMethodsTransformer,
    StringLibraryTransformer,
    IPairsTransformer,
)
from transpile.scopetracker import find_undeclared_variables
from transpile.formatter import format_python_code
from transpile.luaparser.astnodes import Node as LuaNode


class ModuleTracker:
    """Tracks and manages Python modules within a specified root directory."""

    def __init__(self, root_directory: str):
        self.root_directory = os.path.abspath(root_directory)
        self.modules = {}
        self.module_symbols = {}

    def track_modules(self) -> None:
        """Recursively tracks all Python modules in the root directory."""
        for dirpath, dirnames, filenames in os.walk(self.root_directory):
            dirnames[:] = [
                d for d in dirnames if not d.startswith('__pycache__')]
            for filename in filenames:
                if filename.endswith('.py'):
                    module_name = self._get_module_name(dirpath, filename)
                    module_path = os.path.join(dirpath, filename)
                    self.modules[module_name] = module_path
                    self._extract_symbols(module_name, module_path)

    def _get_module_name(self, dirpath: str, filename: str) -> str:
        """Constructs the module name based on the directory path and filename."""
        relative_path = os.path.relpath(dirpath, self.root_directory)
        module_base = os.path.splitext(filename)[0]
        return module_base if relative_path == '.' else '.'.join(relative_path.split(os.sep) + [module_base])

    def _extract_symbols(self, module_name: str, module_path: str) -> None:
        """Extracts top-level symbols (functions, classes) from a module."""
        with open(module_path, 'r', encoding='utf-8') as file:
            try:
                tree = ast.parse(file.read(), filename=module_path)
                symbols = {node.name for node in ast.walk(tree) if isinstance(
                    node, (ast.FunctionDef, ast.ClassDef))}
                self.module_symbols[module_name] = symbols
            except SyntaxError as e:
                print(f"Syntax error while parsing {module_name}: {e}")

    def list_modules(self) -> None:
        """Prints the list of tracked modules and their paths."""
        for module_name, module_path in self.modules.items():
            print(f"{module_name}: {module_path}")

    def load_module(self, module_name: str):
        """Dynamically loads a module given its name."""
        if module_name not in self.modules:
            print(f"Module '{module_name}' not found in tracked modules.")
            return None

        module_path = self.modules[module_name]
        try:
            spec = importlib.util.spec_from_file_location(
                module_name, module_path)
            if spec is None:
                print(f"Failed to create a spec for module '{
                      module_name}' at {module_path}.")
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            print(f"Module '{module_name}' loaded successfully.")
            return module

        except (FileNotFoundError, ImportError, Exception) as e:
            print(f"Error loading module '{module_name}': {e}")
        return None

    def fix_missing_imports(self, module_name: str) -> None:
        """Fixes missing imports in a module by adding required imports found in other tracked modules."""
        if module_name not in self.modules:
            print(f"Module '{module_name}' is not tracked.")
            return

        module_path = self.modules[module_name]
        with open(module_path, 'r', encoding='utf-8') as file:
            tree = ast.parse(file.read(), filename=module_path)
            imported_symbols = self._get_imported_symbols(tree)
            used_symbols = self._get_used_symbols(tree)

        missing_symbols = used_symbols - imported_symbols
        needed_imports = self._find_missing_imports(missing_symbols)

        if needed_imports:
            self._add_imports_to_file(module_path, needed_imports)
            print(f"Added missing imports to {module_name}: {needed_imports}")
        else:
            print(f"No missing imports needed for {module_name}.")

    def _get_imported_symbols(self, tree: ast.AST) -> set:
        """Extracts symbols that are already imported in the module."""
        imported_symbols = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_symbols.update(alias.name.split(
                    '.')[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_symbols.add(node.module.split('.')[0])
        return imported_symbols

    def _get_used_symbols(self, tree: ast.AST) -> set:
        """Extracts all symbols used in the module."""
        return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}

    def _find_missing_imports(self, missing_symbols: set) -> dict:
        """Finds which missing symbols are defined in other tracked modules."""
        needed_imports = {}
        for symbol in missing_symbols:
            for module, symbols in self.module_symbols.items():
                if symbol in symbols:
                    needed_imports[symbol] = module
                    break
        return needed_imports

    def _add_imports_to_file(self, module_path: str, imports: dict) -> None:
        """Adds missing import statements to the top of the source file."""
        with open(module_path, 'r+', encoding='utf-8') as file:
            content = file.readlines()
            for symbol, module in imports.items():
                content.insert(0, f"from {module} import {symbol}\n")
            file.seek(0)
            file.writelines(content)


def file_to_src(file: str) -> str:
    """Converts a Lua source file to Python source code using AST transformations."""
    convert = LuaNodeConvertor()
    writer = PythonASTWriter()
    transformers = [
        StringLibraryTransformer(),
        KVForLoopTransformer(),
        TableMethodsTransformer(),
        HEXTransformer(),
    ]
    mapper = LuaToPythonMapper()

    with open(file, "r", errors="ignore") as f:
        content = f.read()
    lnodes: list[LuaNode] = parse(content).body.body
    pnodes = convert.convert_nodes(lnodes)
    mod = Module(body=pnodes, type_ignores=[])
    source = []

    for node in mod.body:
        for transformer in transformers:
            node = transformer.visit(node)
        source.append(writer.visit(node))

    src = "\n".join(source)
    src = mapper.map_imports(src)
    src = format_python_code(src)
    return src


def convert_file(root: str, file: str) -> None:
    """Converts a Lua file to Python in the specified directory."""
    path = os.path.join(root, file)
    source = file_to_src(path)
    with open(path, 'w') as f:
        f.write(source)
    os.rename(path, path.replace(".lua", ".py"))


class Transpiler:
    """Transpiles Lua code to Python."""

    def __init__(self) -> None:
        self.file = ""
        self.files = []
        self.sources = []
        self.undeclared_variables = {}
        self.module_tracker = None

    def transpile_file(self, file: str) -> str:
        """Transpiles a single Lua file to Python."""
        self.file = file
        self.files.append(file)
        convert = LuaNodeConvertor()
        writer = PythonASTWriter()
        transformers = [
            StringLibraryTransformer(),
            KVForLoopTransformer(),
            TableMethodsTransformer(),
            HEXTransformer(),
        ]
        mapper = LuaToPythonMapper()

        with open(self.file, "r", errors="ignore") as f:
            content = f.read()
        lnodes: list[LuaNode] = parse(content).body.body
        pnodes = convert.convert_nodes(lnodes)
        mod = Module(body=pnodes, type_ignores=[])
        source = []

        for node in mod.body:
            for transformer in transformers:
                node = transformer.visit(node)
            source.append(writer.visit(node))

        src = "\n".join(source)
        src = mapper.map_imports(src)
        src = format_python_code(src)
        self.undeclared_variables[self.file] = find_undeclared_variables(src)
        return src

    def transpile_directory(self, directory: str) -> None:
        """Transpiles all Lua files in a directory to Python."""
        self.root = directory
        output_root = os.path.join(os.getcwd(), "output")
        copytree(src=self.root, dst=output_root)

        processes: list[Process] = []
        for root, _, files in os.walk(output_root):
            for file in files:
                if file.endswith(".lua"):
                    proc = Process(target=convert_file, args=(root, file))
                    processes.append(proc)

        for proc in processes:
            proc.start()
        for proc in processes:
            proc.join()

        self.module_tracker = ModuleTracker(output_root)
        self.module_tracker.track_modules()

    def test_transpiled_files(self) -> None:
        """Tests each transpiled Python file for syntax errors and reports missing imports."""
        for file in self.files:
            test_transpiled_file(set_extension(file, "py"))

    def fix_imports(self) -> None:
        """Fixes missing imports for all modules tracked in the output directory."""
        for module_name in self.module_tracker.modules:
            self.module_tracker.fix_missing_imports(module_name)

    def list_undeclared_variables(self) -> None:
        """Prints undeclared variables found during transpilation."""
        for file, variables in self.undeclared_variables.items():
            print(f"Undeclared variables in {file}: {variables}")

    def run_transpilation(self, directory: str) -> None:
        """Executes the transpilation process on a given directory."""
        self.transpile_directory(directory)
        self.test_transpiled_files()
        self.fix_imports()
        self.list_undeclared_variables()
