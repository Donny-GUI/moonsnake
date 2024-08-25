

import ast
import transpile.luaparser.ast as last
import os
from pathlib import Path
from dataclasses import dataclass
from transpile.macros import Is
from transpile.luaparser.astnodes import Base
from typing import Callable, Any


type Method = Callable

AccessingAttribute = ast.Load()
AssigningValue = ast.Store()
ValueAsArgument = ast.Load()
RightHandValue = ast.Load()


def has_body(node: last.Node) -> bool:
    """
    Checks if a node has a non-empty body.

    Args:
        node (last.Node): The node to check.

    Returns:
        bool: True if the node has a non-empty body, None otherwise.
    """
    if hasattr(node, "body") and node.body != [] and node.body != None:
        return True


def is_class_definition(node: ast.ClassDef | Any):
    """
    Checks if a node is a class definition.

    Args:
        node (ast.AST): The node to check.

    Returns:
        bool: True if the node is a class definition, None otherwise.
    """
    if isinstance(node, ast.ClassDef):
        return True


def is_function_definition(node: ast.FunctionDef | Any):
    """
    Checks if a node is a function definition.

    Args:
        node (ast.AST): The node to check.

    Returns:
        bool: True if the node is a function definition, None otherwise.
    """
    if isinstance(node, ast.FunctionDef):
        return True


def is_call_and_anonymous_function(node: ast.Call | Any):
    """
    Checks if a node is an anonymous function.

    Args:
        node (ast.AST): The node to check.

    Returns:
        bool: True if the node is an anonymous function, None otherwise.
    """
    # Check if the node is a call expression and the first keyword argument
    # has the name "ANON". the second keyword argument is the function body
    if isinstance(node, ast.Call) and node.keywords and node.keywords[0].arg == "ANON":
        return True


@dataclass
class FindableMethod:
    key: str
    function: ast.FunctionDef


class Comment:
    def __init__(self, comment: str):
        self.string = comment


class MultiLineComment:
    def __init__(self, comment: str) -> None:
        self.string = comment

# base class


class ASTNodeConvertor:
    def __init__(self) -> None:
        self._classes = []
        self._to_find: list[FindableMethod] = []
        self._classes_map: dict[str, ast.ClassDef] = {}
        self._levels = []

        self._labels = {}
        self.current_label = None
        self._gotos = []
        self._last_if = None
        self._patterns = {}

        self.anon_func_count = 0
        self.anon_funcs = []
        self.anon_map = {}
        self.anon_signatures = []

    def convert(self, node) -> ast.AST:
        """
        Convert a given node to its corresponding Python AST node.

        Parameters:
            node (Any): The node to be converted.

        Returns:
            ast.AST: The converted Python AST node.
        """
        node_method = self._fetchMethod(node)
        n = node_method(node)
        self._fix_missing(n)
        self._go_to_labels(n)

        return n

    def _go_to_labels(self, node: ast.AST | list) -> None:
        """
        Appends a given node to the body of the current label.

        Args:
            node (ast.AST | list): The node to be appended.

        Returns:
            None
        """
        if self.current_label != None:
            self._labels[self.current_label].body.append(node)

    def _fix_missing(self, node: ast.AST):
        """
        Recursively fixes missing location information in the given AST node.

        Args:
            node (ast.AST): The node to fix missing location information for.

        Returns:
            None
        """
        if isinstance(node, list):
            for x in node:
                self._fix_missing(x)
        if isinstance(node, ast.AST):
            ast.fix_missing_locations(node)

    def _fetchMethod(self, node: last.Node) -> Method:
        """
        Fetches the conversion method for a given node.

        Parameters:
                node (last.Node): The node for which to fetch the conversion method.

        Returns:
                callable: The conversion method for the given node.
        """

        method = "convert_" + node.__class__.__name__
        try:
            convertor = getattr(self, method)
        except AttributeError as ae:
            raise Exception("Could not find a conversion method for " + method)

        return convertor


class LuaNodeConvertor(ASTNodeConvertor):

    def __init__(self):
        super().__init__()

    def _globalize_labels(self, nodes: list[ast.AST]) -> list[ast.AST]:
        """
        Finds converted labels in the given nodes and moves the 
        corresponding variable names to the top of the class method 
        or function definitions as globals.

        Args:
            nodes (list[ast.AST]): The nodes to search for labels in.

        Returns:
            list[ast.AST]: The nodes with the labels moved to the top of the class methods.
        """
        for label, funcdef in self._labels.items():
            names = []

            # Walk the AST tree and find all the Names in the body of the function
            for item in ast.walk(funcdef.body):
                if isinstance(item, ast.Name):
                    names.append(item.id)

            # Create a Global node with the found names
            gl = ast.Global(names=names)

            # Insert the Global node at the beginning of the function body
            funcdef.body.insert(0, gl)

            # Add the function definition to the list of nodes
            nodes.append(funcdef)

        return nodes

    def convert_nodes(self, nodes: list[last.Node]) -> list[ast.AST]:
        """
        Converts a list of lua nodes into a list of Python ASTs.

        Args:
            nodes (list[Node]): The list of lua nodes to convert

        Returns:
            list[ast.AST]: The converted list of Python ASTs
        """
        # First, we need to convert all the nodes into Python ASTs
        nodes = [self.convert(x) for x in nodes]

        # Then, we need to assign methods to the converted nodes
        nodes = self.assign_methods(nodes)

        # Next, we need to move any converted labels to the top of the class methods or functions
        nodes = self._globalize_labels(nodes)
        
        mod = ast.Module(body=nodes)
        ast.fix_missing_locations(mod)
        
        return mod.body

    def _super_from_callattr(self, node: ast.Call):
        """
        Creates a `super` call from a `call` attribute.

        Args:
            node (ast.Call): The `call` attribute.

        Returns:
            ast.Call: The `super` call.
        """
        callfunc = ast.Attribute(
            value=ast.Call(
                func=ast.Name(id="super", ctx=ast.Load()), args=[], keywords=[]
            ),
            attr="__init__",
            ctx=ast.Load(),
        )

        return ast.Call(func=callfunc, args=node.args, keywords=[])

    def _check_for_super(self, node: FindableMethod):
        """
        Checks if a given node is a call to a superclass's __init__ method.

        Args:
            node (FindableMethod): The node to check.

        Returns:
            None
        """
        clss = self._classes_map[node.key]
        for arg in node.function.args.args:
            if arg.arg == "self":
                for n in node.function.body:
                    if isinstance(n, ast.Call):
                        if isinstance(n.func, ast.Attribute):
                            if n.func.attr == "init":
                                for base in clss.bases:
                                    if base.name.id == n.func.value.id:
                                        n = self._super_from_callattr(n)

    def convert_str(self, node: str):
        """
        Converts a string by replacing newline characters with commas and spaces.

        Args:
            node (str): The string to be converted.

        Returns:
            str: The converted string.
        """
        node.replace("\n", ", ")
        return node

    def convert_float(self, node: float) -> float:
        """
        Converts a float from lua to python.

        Args:
            node (float): The float to be converted.

        Returns:
            float: The converted float.
        """
        return node

    def convert_int(self, node: int) -> int:
        """
        Converts an int from lua to python.

        Args:
            node (int): The int to be converted.

        Returns:
            int: The converted int.
        """
        return node

    def convert_list(self, node: list) -> list:
        """
        Converts a list from lua to python.

        Args:
            node (list): The list to be converted.

        Returns:
            list: The converted list.
        """
        n = [self.convert(x) for x in node]
        return n

    def convert_String(self, node: last.String) -> ast.Constant:
        """
        Converts a string from lua to python.

        Args:
            node (last.String): The string to be converted.

        Returns:
            ast.Constant: The converted string.
        """
        # The string in lua is a string literal, so we need to add quotes
        # around it to make it a string in python.
        n = ast.Constant(f'{node.s}', kind="s")
        return n

    def convert_NoneType(self, node: None) -> ast.Constant:
        """
        Converts a NoneType from lua to python.

        Args:
            node (NoneType): The NoneType to be converted.

        Returns:
            ast.Constant: The converted NoneType.
        """
        return ast.Constant(None, kind=None)

    def convert_NoneType(self, node: last.Node) -> ast.Constant:
        """
        Converts a NoneType from lua to python.

        Args:
            node (Optional[last.NoneType]): The NoneType to be converted.

        Returns:
            ast.Constant: The converted NoneType.
        """
        return ast.Constant(None, kind=None)

    def convert_Number(self, node: last.Number) -> ast.Constant:
        """
        Converts a number from lua to python.

        Args:
            node (last.Number): The number to be converted.

        Returns:
            ast.Constant: The converted number.
        """
        # The number in lua is a number literal, so we need to wrap it
        # in a ast.Constant to make it a number in python.
        n = ast.Constant(str(node.n), kind="i")
        return n

    def convert_Chunk(self, node: last.Chunk) -> ast.Module:
        """
        Converts a Chunk from lua to python.

        A Chunk is a collection of statements, so we will convert it to a ast.Module
        which is a collection of statements.

        Args:
            node (last.Chunk): The Chunk to be converted.

        Returns:
            ast.Module: The converted Chunk.
        """
        body = self.convert(node.body)
        # A list of type ignore objects, empty for now
        type_ignores = []
        return ast.Module(body=body, type_ignores=type_ignores)

    def convert_Block(self, node: last.Block) -> list:
        """
        Converts a Block from lua to python.

        A Block is a list of statements, so we will convert it to a list of Python asts.

        Args:
            node (last.Block): The Block to be converted.

        Returns:
            list: The converted Block.
        """
        # Convert each statement in the Block to a Python ast
        n = [self.convert(x) for x in node.body]
        # Return the converted Block
        return n

    def convert_Assign(self, node: last.Assign = None) -> ast.Assign:
        """
        Converts an Assign node from lua to python.

        An Assign node is a statement that assigns a value to one or more variables.
        It has a list of left hand targets (variables) and a list of right hand values.
        This function converts these targets and values to Python asts and creates an Assign ast.

        Args:
            node (last.Assign): The Assign node to be converted.

        Returns:
            ast.Assign: The converted Assign node.
        """
        # Convert each left hand target to a Python ast
        targets = [self.convert(x) for x in node.targets]

        # If a target is a variable name, give it the context of storing
        for target in targets:
            if hasattr(target, "ctx"):
                target.ctx = ast.Store()

        # Convert each right hand value to a Python ast
        values = [self.convert(x) for x in node.values]
        for val in values:
            if hasattr(val, "ctx"):
                val.ctx = ast.Load()

        # Create the Assign ast with the converted targets and values
        n = ast.Assign(targets=targets, value=values, type_comment=None)

        return n

    def convert_While(self, node: last.While = None) -> ast.While:
        """
        Converts a While node from lua to python.

        A While node is a loop that executes its body until its test evaluates to false.
        This function converts the test and body of the While node to Python asts and
        creates a While ast.

        Args:
            node (last.While): The While node to be converted.

        Returns:
            ast.While: The converted While node.
        """
        # Convert the body of the While loop to a Python ast
        body = self.convert(node.body)
        # Convert the test of the While loop to a Python ast
        test = self.convert(node.test)
        # Create the While ast with the converted test and body
        n = ast.While(test=test, body=body, orelse=None)

        return n

    def convert_Do(self, node: last.Do = None) -> list[ast.AST] | None:
        """
        Converts a Do node from lua to python.

        A Do node is a collection of statements, so we will convert it to a list of Python asts.
        This function converts each statement in the Do node to a Python ast and
        returns the list of converted asts.

        Args:
            node (last.Do): The Do node to be converted.

        Returns:
            list[ast.AST] | None: The converted Do node.
        """
        items = []
        for n in node.body.body:
            items.append(self.convert(n))

        return items

    def convert_If(self, node: last.If = None):
        """
        Converts an If node from lua to python.

        This function takes an If node as input, converts its test and body to Python asts,
        and creates an If ast. The function also handles the orelse clause of the If node.

        Args:
            node (last.If): The If node to be converted.

        Returns:
            ast.If: The converted If node.
        """
        test = self.convert(node.test)
        if isinstance(node.body, last.Chunk):
            body = [self.convert(x) for x in node.body.body]
        else:
            body = self.convert(node.body)
        # orelse = self.convert(node.orelse)
        if isinstance(node.orelse, list):
            orelse = [self.convert(x) for x in node.orelse]
        elif isinstance(node.orelse, last.Block):
            orelse = [self.convert(x) for x in node.orelse.body]
        else:
            orelse = []
        n = ast.If(test=test, body=body, orelse=orelse)
        self._last_if = n
        return n

    def convert_ElseIf(self, node: last.ElseIf = None):
        """
        Converts an ElseIf node from lua to python.

        This function takes an ElseIf node as input, converts its test and body to Python asts,
        and creates an If ast. The function also handles the orelse clause of the ElseIf node.

        Args:
            node (last.ElseIf): The ElseIf node to be converted.

        Returns:
            str: An empty string.
        """
        test = self.convert(node.test)
        if isinstance(node.body, last.Chunk):
            body = [self.convert(x) for x in node.body.body]
        else:
            body = self.convert(node.body)
        # orelse = self.convert(node.orelse)
        if isinstance(node.orelse, list):
            orelse = [self.convert(x) for x in node.orelse]
        elif isinstance(node.orelse, last.ElseIf):
            orelse = [self.convert(node.orelse)]
        elif isinstance(node.orelse, last.Block):
            orelse = [self.convert(x) for x in node.orelse.body]
        else:
            orelse = self.convert(node.orelse)
        n = ast.If(test=test, body=body, orelse=orelse)
        self._last_if.orelse.append(n)
        return ""

    def convert_Label(self, node: last.Label = None):
        """
        Converts a Label node from lua to python.

        This function takes a Label node as input, sets the current label to the node's id,
        and creates a FunctionDef ast with the label's id as its name.

        Args:
            node (last.Label): The Label node to be converted.

        Returns:
            None
        """
        self.current_label = node.id
        self._labels[node.id] = ast.FunctionDef(
            name=node.id.id, args=[], body=[], decorator_list=[], returns=None
        )

    def convert_Goto(self, node: last.Goto = None):
        """
        Converts a Goto node from lua to python.

        Args:
            node (last.Goto): The Goto node to be converted.

        Returns:
            ast.Call: The converted Goto node.
        """
        return ast.Call(func=ast.Name(id=node.label.id), args=[], keywords="GOTO")

    def convert_Break(self, node: last.Break = None):
        n = ast.Break()
        return n

    def convert_Return(self, node: last.Return = None):
        """
        Converts a Return node from lua to python.

        Args:
            node (last.Return): The Return node to be converted.

        Returns:
            ast.Return: The converted Return node.
        """
        if isinstance(node.values, bool):
            kind = node.values
            value = True if node.values == True else False
            v = ast.Constant(value, kind=kind)
        else:
            n = self.convert(node.values)
            n = [x for x in n if x != None]
            v = n if len(n) > 1 else n
        n = ast.Return(value=v)

        return n

    def convert_Fornum(self, node: last.Fornum = None):
        """
        Converts a Fornum node from lua to python.

        Args:
            node (last.Fornum): The Fornum node to be converted.

        Returns:
            ast.For: The converted Fornum node.
        """
        target = self.convert(node.target)
        start = self.convert(node.start)
        stop = self.convert(node.stop)
        step = self.convert(node.step)
        body = self.convert(node.body)
        orelse = []
        n = ast.For(
            target=target,
            iter=ast.Call(
                func=ast.Name(
                    id="range",
                    ctx=ast.Load()
                ),
                args=[
                    start,
                    stop,
                    step
                ],
                keywords=[]),
            body=body,
            orelse=orelse,
        )

        return n

    def convert_Forin(self, node: last.Forin = None):
        if (
            len(node.targets) == 1
            and node.targets[0].id == "kv"
            and isinstance(node.iter, last.Call)
            and node.iter.func.identifier in ["ipairs", "pairs"]
        ):
            node.targets = [last.Name(identifier="k"),
                            last.Name(identifier="v")]

        targets: list = self.convert(node.targets)

        iter = self.convert(node.iter)
        body = self.convert(node.body)
        orelse = []
        n = ast.For(target=targets, iter=iter, body=body, orelse=[])

        return n

    def convert_Args(self, node: list[last.Name, last.Index, last.Call]):
        """converts arguments `list[Expression]` to
        ast.arguments.
        Args:
            node(list[last.Name|last.Expression]) : list of lua expressions
        Returns:
            ast.arguments object
        """
        items = []

        for x in node:
            py = self.convert(x)
            if isinstance(py, ast.Name):
                if py.id == "/":
                    break
                items.append(ast.arg(py.id))
            elif isinstance(py, ast.Constant):
                items.append(ast.arg(py.value))
            else:
                items.append(ast.arg(self.convert(x)))

        args = items

        return ast.arguments(
            posonlyargs=args,
            args=args,
            vararg=None,
            kw_defaults=[],
            kwarg=None,
            defaults=[],
            kwonlyargs=[],
        )

    def convert_funcArg(self, node: last.Name | last.Index):
        if isinstance(node, last.Name):
            return self.convert_Name(node)
        elif isinstance(node, last.Index):
            return self.convert_Index(node)

    def _is_import(self, node: last.Node):
        return (
            isinstance(node, last.Call)
            and isinstance(node.func, last.Name)
            and node.func.id == "require"
        )

    def convert_Call(self, node: last.Call = None):

        # check is pairs function
        if isinstance(node.func, last.Name) and node.func.id == "pairs":
            method_attr = ast.Attribute(
                # The object part as Python AST
                value=self.convert(node.args[0]),
                attr="items",  # The method name as a string
                ctx=ast.Load(),  # Context is load because we're accessing an attribute
            )
            call_node = ast.Call(
                func=method_attr,
                args=self.convert_Args([]),
                keywords=[],  # Lua doesn't have keyword arguments
            )
            return call_node

        func = self.convert_funcArg(node.func)
        args = self.convert_Args(node.args)
        keywords = []
        n = ast.Call(func=func, args=args, keywords=keywords)
        return n

    def convert_Invoke(self, node: last.Invoke) -> ast.Call:
        source = self.convert(node.source)
        args = self.convert_Args(node.args)
        func = self.convert(node.func)
        n = ast.Call(
            func=ast.Attribute(value=source,
                               attr=func,
                               ctx=ast.Load()),
            args=args,
            keywords=[]
        )
        return n

    def convert_Function(self, node: last.Function = None):
        name = self.convert(node.name)
        args = self.convert_Args(node.args)
        body = self.convert(node.body)
        n = ast.FunctionDef(name=name, args=args, body=body)

        self.scope = n
        
        return n

    def convert_LocalFunction(self, node: last.LocalFunction = None):

        name = self.convert(node.name)
        args = self.convert_Args(node.args)
        body = self.convert(node.body)
        n = ast.FunctionDef(name=name, args=args, body=body)

        return n

    def convert_Super(self, node: last.Invoke):
        callfunc = ast.Attribute(
            value=ast.Call(
                func=ast.Name(id="super", ctx=ast.Load()), args=[], keywords=[]
            ),
            attr="__init__",
            ctx=ast.Load(),
        )
        return ast.Call(func=callfunc, args=self.convert_Args(node.args), keywords=[])

    def convert_Initializer(self, node: last.Initializer):
        key = None
        src = self.convert(node.source)
        if isinstance(src, ast.Name):
            key = src.id
        args = self.convert_Args(node.args)
        args.args.insert(0, ast.arg("self"))

        body = []
        for bnode in node.body:
            if isinstance(bnode, last.Invoke):
                if bnode.func.id == "init":
                    body.append(self.convert_Super(bnode))
                    continue
            body.append(self.convert(bnode))

        f = ast.FunctionDef(
            name=self.convert(node.name),
            args=args,
            body=body,
            decorator_list=[],
            returns=None,
            type_comment=None,
            type_params=[],
        )
        self._to_find.append(FindableMethod(key=key, function=f))
        return f

    def convert_Method(self, node: last.Method = last.Method):
        key = None
        src = self.convert(node.source)
        if isinstance(src, ast.Name):
            key = src.id

        name = self.convert(node.name)
        # make arguments ast here
        args: ast.arguments = self.convert_Args(node.args)
        # manually add the self arg
        try:
            args.args.insert(0, ast.arg(arg="self"))
        except AttributeError as ae:
            args.insert(0, ast.arg(arg="self"))
        body = self.convert(node.body)
        if isinstance(name, ast.Name):
            name = name.id
        if name == "init":
            name == "__init__"
        n = ast.FunctionDef(
            name=name, args=args, body=body, type_params=[], decorator_list=[]
        )
        self._to_find.append(FindableMethod(key=key, function=n))
        self.scope = n
        return n

    def convert_Nil(self, node: last.Nil = None):
        n = ast.Constant(value=None, kind=None)
        return n

    def convert_TrueExpr(self, node: last.TrueExpr = None):
        n = ast.Constant(value=True, kind=bool)
        return n

    def convert_FalseExpr(self, node: last.FalseExpr = None):
        n = ast.Constant(value=False, kind=bool)
        return n

    def convert_List(self, node: last.Table):
        l = ast.List(elts=[])
        for k, v in node.fields:
            l.elts.append(self.convert(v))
        return l

    def convert_Dict(self, node: last.Table):
        d = ast.Dict(keys=[], values=[])
        for field in node.fields:
            k, v = self.convert_Field(field)
            if isinstance(k, ast.Name):
                k = ast.Constant(value=k.id, kind="s")

            d.keys.append(k)
            d.values.append(v)
        return d

    def convert_Table(self, node: last.Table = None):
        if Is.List(node) == True:
            n = self.convert_List(node)
        else:
            n = self.convert_Dict(node)

        return n

    def convert_Field(self, node: last.Field = None) -> tuple[ast.AST]:
        n = (self.convert(node.key), self.convert(node.value))

        return n

    def convert_Dots(self, node: last.Dots = None):
        n = ast.Constant(..., kind="Ellipsis")
        return n

    def convert_AnonymousFunction(self, node: last.AnonymousFunction = None):

        self.anon_func_count += 1
        args = self.convert_Args(node.args)
        body = []
        possible_name = []
        for nb in node.body.body:
            body.append(self.convert(nb))
            possible_name.append(nb.__class__.__name__)

        name = f"lambda{self.anon_func_count}"

        n = ast.Call(
            func=ast.Name(
                id=name,
                ctx=ast.Load()),
            args=[arg for arg in args.args],
            keywords=[]
        )
        
        signature = []
        for arg in args.args:
            if isinstance(arg, ast.arg):
                signature.append(arg.arg)
        for x in body:
            try:
                string = ast.unparse(x)
                signature.append(string)
            except:
                pass
        
        sig = "".join(signature)
        if sig in self.anon_signatures:
            pass
        else:    
            self.scope.body.insert(0, ast.FunctionDef(name=name,
                                              args=args,
                                              body=body))

        return n

    def convert_UnaryOp(self, node: last.UnaryOp) -> ast.UnaryOp:
        operand = self.convert(node.operand)
        if isinstance(node, last.UMinusOp):
            n = ast.UnaryOp(operand=operand, op=ast.USub())
        if isinstance(node, last.UBNotOp):
            n = ast.UnaryOp(operand=operand, op=ast.Not())
        if isinstance(node, last.ULNotOp):
            n = ast.Call(func=ast.Name(id="not"), args=[operand], keywords=[])
        if isinstance(node, last.ULengthOP):
            n = ast.Call(func=ast.Name(id="len"), args=[operand], keywords=[])

        return n

    def convert_Comment(self, node: last.Comment = None):
        if node.is_multi_line == True:
            return MultiLineComment(comment=node.s)
        return Comment(comment=node.s)

    def convert_LoOp(self, node: last.LoOp) -> ast.IfExp:
        left = self.convert(node.left)
        if isinstance(left, ast.Name):
            left.ctx = ast.Store()
        right = self.convert(node.right)
        if isinstance(right, ast.Name):
            right.ctx = ast.Load()

        n = ast.IfExp(test=right, body=right, orelse=left)

        return n

    def convert_AriOp(self, node: last.AriOp) -> ast.Compare:
        left = self.convert(node.left)
        if isinstance(left, ast.Name):
            left.ctx = ast.Store()
        right = self.convert(node.right)
        if isinstance(right, ast.Name):
            right.ctx = ast.Load()
        if isinstance(node, last.AddOp):
            n = ast.BinOp(left, ast.Add(), right)
        elif isinstance(node, last.SubOp):
            n = ast.BinOp(left, ast.Sub(), right)
        elif isinstance(node, last.MultOp):
            n = ast.BinOp(left, ast.Mult(), right)
        elif isinstance(node, last.FloatDivOp):
            n = ast.BinOp(left, ast.Div(), right)
        elif isinstance(node, last.FloorDivOp):
            n = ast.BinOp(left, ast.FloorDiv(), right)
        elif isinstance(node, last.ModOp):
            n = ast.BinOp(left, ast.Mod(), right)
        elif isinstance(node, last.ExpoOp):
            n = ast.BinOp(left, ast.Pow(), right)

        return n

    def convert_BitOp(self, node: last.BitOp) -> ast.Compare | ast.Constant | ast.Tuple:
        left = self.convert(node.left)
        if isinstance(left, ast.Name):
            left.ctx = ast.Store()
        right = self.convert(node.right)
        if isinstance(right, ast.Name):
            right.ctx = ast.Load()
        if isinstance(node, last.BAndOp):
            n = ast.BinOp(left=left, op=ast.BitAnd(), right=right)
        elif isinstance(node, last.BOrOp):
            n = ast.BinOp(left=left, op=ast.BitOr(), right=right)
        elif isinstance(node, last.BXorOp):
            n = ast.BinOp(left, ast.BitXor(), right)
        elif isinstance(node, last.BShiftLOp):
            n = ast.BinOp(left, ast.LShift(), right)
        elif isinstance(node, last.BShiftROp):
            n = ast.BinOp(left, ast.RShift(), right)

        return n

    def convert_RelOp(self, node: last.RelOp) -> ast.Compare:
        left = [self.convert(x) for x in node.left]
        if isinstance(left, ast.Name):
            left.ctx = ast.Store()
        right = [self.convert(x) for x in node.right]
        if isinstance(right, ast.Name):
            right.ctx = ast.Load()
        if isinstance(node, last.EqToOp):
            n = ast.BinOp(left=left, op=ast.Eq(), right=right)
        elif isinstance(node, last.NotEqToOp):
            n = ast.BinOp(left=left, op=ast.NotEq(), right=right)
        elif isinstance(node, last.LessThanOp):
            n = ast.BinOp(left=left, op=ast.Lt(), right=right)
        elif isinstance(node, last.LessOrEqThanOp):
            n = ast.BinOp(left=left, op=ast.LtE(), right=right)
        elif isinstance(node, last.GreaterThanOp):
            n = ast.BinOp(left=left, op=ast.Gt(), right=right)
        elif isinstance(node, last.GreaterOrEqThanOp):
            n = ast.BinOp(left=left, op=ast.GtE(), right=right)

        return n

    def convert_BinaryOp(self, node: last.BinaryOp = None):
        if isinstance(node, last.RelOp):
            n = self.convert_RelOp(node)
        elif isinstance(node, last.AriOp):
            n = self.convert_AriOp(node)
        elif isinstance(node, last.BitOp):
            n = self.convert_BitOp(node)
        elif isinstance(node, last.LoOp):
            n = self.convert_LoOp(node)

        return n

    def convert_OP(self, node: last.Op):
        if isinstance(node, last.RelOp):
            n = self.convert_RelOp(node)
        elif isinstance(node, last.AriOp):
            n = self.convert_AriOp(node)
        elif isinstance(node, last.BitOp):
            n = self.convert_BitOp(node)
        elif isinstance(node, last.LoOp):
            n = self.convert_LoOp(node)

        return n

    def convert_UnaryOp(self, node: last.UnaryOp = None):
        n = self.convert_OP(node)

        return n

    def convert_Name(self, node: last.Name = None):
        if node.id == "true":
            return ast.Constant(value=True, kind="bool")
        elif node.id == "false":
            return ast.Constant(value=False, kind="bool")

        n = ast.Name(id=node.id, ctx=ast.Load())

        return n

    def convert_valueName(self, node):
        n = self.convert_funcArg(node)
        if isinstance(n, last.Name):
            return n.id
        elif isinstance(n, last.Index):
            nn = self.convert_Index(n)
            return nn
        elif isinstance(n, last.String):
            return n.id

    def convert_Index(self, node: last.Index = None):
        if node.notation == last.IndexNotation.DOT:
            value = self.convert(node.value)
            idx = self.convert(node.idx)
            n = ast.Attribute(value=value, attr=idx)
        elif node.notation == last.IndexNotation.SQUARE:
            _value = last.to_lua_source(node.value)
            _idx = last.to_lua_source(node.idx)
            n = ast.Name(id=f"{_value}[{_idx}]", kind="i")

        return n

    def convert_Varargs(self, node: last.Varargs = None):
        n = ast.Constant(value="*args", kind="*args")

        return n

    def convert_Repeat(self, node: last.Repeat = None):
        body = self.convert(node.body)
        t = ast.If(test=self.convert(node.test), body=ast.Break(), orelse=[])
        body.append(t)
        n = ast.While(test=ast.Constant(value=True), body=body, orelse=None)

        return n

    def convert_SemiColon(self, node: last.SemiColon = None):
        return ""

    def convert_ULNotOp(self, node: last.ULNotOp):
        operand = self.convert(node.operand)
        n = ast.UnaryOp(operand=operand, op=ast.Not())
        return n

    def convert_OrLoOp(self, node: last.OrLoOp):
        """name = Expression1 or Expression2
        name = expression1 if expression1 else expression2
        Args:
            node (last.OrLoOp): _description_

        Returns:
            _type_: _description_
        """
        return ast.IfExp(
            test=self.convert(node.left),
            body=self.convert(node.left),
            orelse=self.convert(node.right),
        )

    def convert_LocalAssign(self, node: last.LocalAssign):
        """just redirect to Assign statement

        Args:
            node (last.LocalAssign): the local assign node

        Returns:
            ast.Assign
        """
        targets = [self.convert(x) for x in node.targets]
        for target in targets:
            if isinstance(target, ast.Name):
                target.ctx = ast.Load()
        values = [self.convert(x) for x in node.values]
        n = ast.Assign(targets=targets, value=values)
        return n

    def convert_EqToOp(self, node: last.EqToOp):
        left = self.convert(node.left)
        right = self.convert(node.right)
        return ast.Compare(left=left, ops=[ast.Eq(), ast.Eq()], comparators=[right])

    def convert_UMinusOp(self, node: last.UMinusOp):
        operand = self.convert(node.operand)
        return ast.UnaryOp(op=ast.USub(), operand=operand)

    def convert_MultOp(self, node: last.MultOp):
        left = self.convert(node.left)
        right = self.convert(node.right)
        return ast.BinOp(left, ast.Mult(), right)

    def convert_bool(self, node):
        return node

    def convert_AndLoOp(self, node: last.AndLoOp):
        return ast.BinOp(
            left=self.convert(node.left),
            op=ast.BitAnd(),
            right=self.convert(node.right),
        )

    def convert_AddOp(self, node: last.AddOp):
        return ast.BinOp(
            left=self.convert(node.left), right=self.convert(node.right), op=ast.Add()
        )

    def convert_FloatDivOp(self, node: last.FloatDivOp):
        return ast.BinOp(
            left=self.convert(node.left), right=self.convert(node.right), op=ast.Div()
        )

    def convert_SubOp(self, node: last.SubOp):
        return ast.BinOp(
            left=self.convert(node.left), right=self.convert(node.right), op=ast.Sub()
        )

    def convert_LessThanOp(self, node: last.LessThanOp):
        return ast.BinOp(
            left=self.convert(node.left),
            right=self.convert(node.right),
            op=ast.Lt()
        )

    def convert_Concat(self, node: last.Concat):
        return ast.BinOp(
            left=self.convert(node.left), op=ast.Add(), right=self.convert(node.right)
        )

    def convert_LessOrEqThanOp(self, node: last.LessOrEqThanOp):
        return ast.Compare(
            left=self.convert(node.left),
            ops=[ast.LtE()],
            comparators=[self.convert(node.right)],
        )

    def convert_ULengthOP(self, node: last.ULengthOP):
        return ast.Call(
            func=ast.Name(id="len",
                          ctx=ast.Load()),
            args=[self.convert(node.operand)],
            keywords=[]
        )

    def convert_NotEqToOp(self, node: last.LessOrEqThanOp):
        return ast.Compare(
            left=self.convert(node.left),
            ops=[ast.NotEq()],
            comparators=[self.convert(node.right)],
        )

    def convert_GreaterThanOp(self, node: last.GreaterThanOp):
        return ast.Compare(
            left=self.convert(node.left),
            ops=[ast.Gt()],
            comparators=[self.convert(node.right)],
        )

    def convert_GreaterOrEqThanOp(self, node: last.GreaterOrEqThanOp):
        return ast.Compare(
            left=self.convert(node.left),
            ops=[ast.GtE()],
            comparators=[self.convert(node.right)],
        )

    def convert_ModOp(self, node: last.ModOp):
        return ast.Compare(
            left=self.convert(node.left),
            ops=[ast.Mod()],
            comparators=[self.convert(node.right)],
        )

    def convert_ExpoOp(self, node: last.ExpoOp):
        return ast.Compare(
            left=self.convert(node.left),
            ops=[ast.Pow()],
            comparators=[self.convert(node.right)],
        )

    # /////////////////////////////////////////////////////////////////////
    #  NEW NODES
    # /////////////////////////////////////////////////////////////////////

    def convert_Base(self, node: last.Base) -> Base:
        return ast.Name(id=node.name)

    def convert_Constructor(self, node: last.Constructor) -> ast.ClassDef:
        c = ast.ClassDef(
            name=node.name,
            bases=[self.convert(x) for x in node.bases],
            keywords=[],
            body=[],
            decorator_list=[],
            type_params=[],
        )

        self._classes.append(c)
        self._classes_map[node.name] = c

        return c

    def convert_ForEnumerate(self, node: last.ForEnumerate) -> ast.For:
        iter_call = self.convert_Call(node.iterator)
        iter_call.func.id = "enumerate"

        return ast.For(
            target=[self.convert(x) for x in node.targets],
            iter=iter_call,
            body=[self.convert(x) for x in node.body],
            orelse=[],
            type_comment=None,
        )

    def convert_InstanceMethodCall(self, node: last.InstanceMethodCall):

        call_func = ast.Attribute(
            value=self.convert(node.source), attr=node.func.id, ctx=ast.Store()
        )

        return ast.Call(func=call_func, args=self.convert_Args(node.args), keywords=[])

    def convert_Require(self, node: last.Require) -> ast.ImportFrom | ast.Import:

        def getdelim(string):
            if "/" in string:
                return "/"
            if "." in string:
                return "."
            if "\\" in string:
                return "\\"
            return "$"

        # incase its just a require statement

        if not len(node.args) >= 1:
            return ""

        delim = getdelim(node.args[0])
        parts = node.args[0].split(delim) if delim != "$" else node.args[0]

        if isinstance(parts, str):
            return ast.Import(names=[ast.alias(name=parts[0])])
        elif len(parts) == 2:
            module, name = parts[0], ast.alias(name=parts[1])

            return ast.ImportFrom(module=module, names=[name])

        elif len(parts) >= 3:
            xparts = parts[:-1]
            module = ".".join(xparts)
            name = ast.alias(name=xparts[-1])

            return ast.ImportFrom(module=module, names=[name])

    def convert_MetaTable(self, node: last.MetaTable) -> ast.Name:
        return ast.Name(id=f"self.__class__")

    def convert_TableConstructor(self, node: last.TableConstructor) -> ast.Call:

        args = self.convert_Args(node.args)
        n = ast.Call(func=self.convert(node.func), args=args, keywords=[])

        return n

    def convert_SuperMethod(self, node: last.Invoke):
        c = self.convert_MethodCall(node)
        return self._super_from_callattr(c)

    def convert_MethodCall(self, node: last.Invoke) -> ast.Call:
        """
        Converts a Lua method call to a Python AST Call object.

        Parameters:
        node (last.Invoke): The Lua method call node to convert.

        Returns:
        ast.Call: The converted Python AST Call object.
        """

        # Convert the object part
        obj_python_ast = self.convert(node.source)

        for subnode in ast.walk(obj_python_ast):
            if isinstance(subnode, ast.Name):
                subnode.id = subnode.id.replace(":", ".")

        # Convert the method name part
        method_name = self.convert(
            node.func
        )  # This is the 'method' part of 'object:method'

        if isinstance(method_name, ast.Name):
            method_name = method_name.id
        elif isinstance(method_name, ast.Call):
            if isinstance(method_name.func, ast.Name):
                method_name = method_name.func.id
            else:
                method_name = method_name.func

        # Create an ast.Attribute for the 'object.method' part
        method_attr = ast.Attribute(
            value=obj_python_ast,  # The object part as Python AST
            attr=method_name,  # The method name as a string
            ctx=ast.Load(),  # Context is load because we're accessing an attribute
        )

        # Convert the arguments part
        args = node.args  # This should be a list of argument nodes
        args_python_ast = self.convert_Args(args)

        # Create an ast.Call for the method invocation
        call_node = ast.Call(
            func=method_attr,
            args=args_python_ast,
            keywords=[],  # Lua doesn't have keyword arguments
        )

        return call_node

    def assign_methods(self, total_nodes):
        """
        Assigns methods to their respective classes.

        Args:
            total_nodes: A list of nodes to be processed.

        Returns:
            A list of nodes with methods assigned to their respective classes.
        """
        for cl in self._to_find:
            try:
                self._classes_map[cl.key].body.append(cl.function)
                total_nodes = [x for x in total_nodes if x != cl.function]
            except:
                pass
        return total_nodes


class LuaToPythonModule(LuaNodeConvertor):
    def __init__(self):
        super().__init__()
        self.total_nodes = []
        self.string = ""
        self.object = None
        self.o = None

    def to_module(self, object: str | last.Chunk | Path | ast.AST):
        """takes a python object and returns an ast.Module

        Args:
            object (str|last.Chunk|Path|ast.AST): converts any object to a python module

        Returns:
            ast.Module
        """
        lua_ast_object = self.ensure_object_is_iterable_nodes(object)
        python_ast_nodes = self.convert_object(lua_ast_object, [])
        total_nodes = self.assign_methods(python_ast_nodes)
        # for func in self.anon_funcs:
        #    total_nodes.insert(0, func)

        for label, funcdef in self._labels.items():
            names = []

            for item in ast.walk(funcdef.body):
                if isinstance(item, ast.Name):
                    names.append(item.id)

            gl = ast.Global(names=names)
            funcdef.body.insert(0, gl)
            total_nodes.append(funcdef)

        m = ast.Module(body=self.cleanse_nodes(total_nodes), type_ignores=[])

        return m

    def ensure_object_is_iterable_nodes(self, object):
        if isinstance(object, str):
            string = object
            if os.path.exists(string):
                with open(string, "r", errors="ignore") as f:
                    string = f.read()
            o = last.parse(string)

        elif isinstance(object, last.Chunk):
            o = object

        # elif isinstance(object, list):
        #    is_body = True
        #    for item in object:
        #        if not isinstance(item, last.Node):
        #            is_body = False
        #    if not is_body:
        #        raise Exception("not a listable object to convert")
        #    o = last.Chunk(body=last.Block(body=[object]))

        elif isinstance(object, last.Block):
            o = last.Chunk(body=object)

        return o

    def convert_object(self, o, total_nodes):
        if isinstance(o, last.Block):
            total_nodes = [self.convert(x) for x in o.body]
        elif isinstance(o, last.Chunk):
            total_nodes = [self.convert(x) for x in o.body.body]
        return total_nodes

    def assign_methods(self, total_nodes):
        """
        Assigns methods to their respective classes.

        Args:
            total_nodes: A list of nodes to be processed.

        Returns:
            A list of nodes with methods assigned to their respective classes.
        """
        for cl in self._to_find:
            try:
                self._classes_map[cl.key].body.append(cl.function)
                total_nodes = [x for x in total_nodes if x != cl.function]
            except:
                pass
        return total_nodes

    def cleanse_nodes(self, total_nodes):
        retv = []

        # cleanse the last.Node types
        for node in total_nodes:
            if isinstance(node, last.Node):
                node = self.convert(node)
            elif isinstance(node, ast.AST):
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, last.Node):
                        child = self.convert(child)
            retv.append(node)

        return retv


def lua_to_python_ast(object: str | last.Chunk | Path | ast.AST) -> ast.Module:
    """converts a lua object to a python ast"""

    l = LuaToPythonModule()
    return l.to_module(object)
