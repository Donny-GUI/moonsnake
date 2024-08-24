import ast
import sys
from contextlib import contextmanager, nullcontext
from enum import IntEnum, auto, _simple_enum
from transpile.luaparser.astnodes import Base
from ast import Constant


def is_singleton(obj):
    """
    Check if an object is a singleton.

    Args:
        obj: The object to check.

    Returns:
        True if the object is a singleton, False otherwise.
    """

    # Check if the object is iterable and has less than 2 items.
    # A singleton is an object that contains only one item.
    if iterable(obj) and len(obj) < 2:
        return True


def iterable(obj):
    """
    Checks if an object is iterable.

    Args:
        obj: The object to check for iterability.

    Returns:
        True if the object is iterable, False otherwise.
    """
    if isinstance(obj, (set, list, tuple)):
        return True


def non_singleton_iterable(obj):
    """
    Checks if an object is a non-singleton iterable.

    Args:
        obj: The object to check for non-singleton iterability.

    Returns:
        True if the object is a non-singleton iterable, otherwise None.
    """
    if is_singleton(obj):
        return
    if iterable(obj):
        return True


def attrhint(attr):
    """
    Generate a string of attribute hints for a given object.

    Args:
        attr (object): The object for which to generate attribute hints.

    Returns:
        str: A string of attribute hints in the format "name:hint", or "None" if the object has no attributes.
    """
    hints = []
    try:
        for name, value in attr.__dict__.items():
            hints.append(name + ":" + itemhint(value))
        return ", ".join(hints)
    except AttributeError:
        return "None"


def itemsview(item):
    """
    Returns a string representation of a list of unique item hints from the given item.

    Args:
        item: An iterable of items to generate hints for.

    Returns:
        str: A comma-separated string of unique item hints.
    """
    return ", ".join(list(set([itemhint(x) for x in item])))


def itemhint(item):
    if isinstance(item, (str, int, float, complex, bytes, type(None))):
        if isinstance(item, str):
            return "str"
        elif isinstance(item, int):
            return "int"
        elif isinstance(item, float):
            return "float"
        elif isinstance(item, complex):
            return "complex"
        elif isinstance(item, bytes):
            return f"bytes"
        elif item == None:
            return "None"

    elif isinstance(item, (list, tuple, set)):
        if isinstance(item, list):
            return f"list[{itemsview(item)}]"
        elif isinstance(item, tuple):
            return f"tuple[{itemsview(item)}]"
        elif isinstance(item, set):
            return f"set[{itemsview(item)}]"
    else:
        return str(type(item))[8:-2] + "(" + attrhint(item) + ")"


def typehint(object):
    if isinstance(object, (str, int, float, complex, bytes)):
        if isinstance(object, str):
            return f"str"
        elif isinstance(object, int):
            return f"int"
        elif isinstance(object, float):
            return f"float"
        elif isinstance(object, complex):
            return f"complex"
        elif isinstance(object, bytes):
            return f"bytes"
    elif isinstance(object, (list, tuple, set)):
        if isinstance(object, list):
            return f"list[{", ".join([itemhint(x) for x in object])}]"
        elif isinstance(object, tuple):
            return f"tuple[{", ".join([itemhint(x) for x in object])}]"
        elif isinstance(object, set):
            return f"set[{", ".join([itemhint(x) for x in object])}]"
    else:
        return str(type(object))[8:-2] + "(" + attrhint(object) + ")"


def iter_fields(node):
    """
    Yield a tuple of ``(fieldname, value)`` for each field in ``node._fields``
    that is present on *node*.
    """
    try:
        for field in node._fields:
            try:
                yield field, getattr(node, field)
            except AttributeError:
                pass
    except:
        pass


def iter_child_nodes(node):
    """
    Yield all direct child nodes of *node*, that is, all fields that are nodes
    and all items of fields that are lists of nodes.
    """
    for name, field in iter_fields(node):
        if isinstance(field, ast.AST):
            yield field
        elif isinstance(field, list):
            for item in field:
                if isinstance(item, ast.AST):
                    yield item


# We unparse those infinities to INFSTR.
_INFSTR = "1e" + repr(sys.float_info.max_10_exp + 1)


@_simple_enum(IntEnum)
class _Precedence:
    """Precedence table that originated from python grammar."""

    NAMED_EXPR = auto()  # <target> := <expr1>
    TUPLE = auto()  # <expr1>, <expr2>
    YIELD = auto()  # 'yield', 'yield from'
    TEST = auto()  # 'if'-'else', 'lambda'
    OR = auto()  # 'or'
    AND = auto()  # 'and'
    NOT = auto()  # 'not'
    CMP = auto()  # '<', '>', '==', '>=', '<=', '!=',
    # 'in', 'not in', 'is', 'is not'
    EXPR = auto()
    BOR = EXPR  # '|'
    BXOR = auto()  # '^'
    BAND = auto()  # '&'
    SHIFT = auto()  # '<<', '>>'
    ARITH = auto()  # '+', '-'
    TERM = auto()  # '*', '@', '/', '%', '//'
    FACTOR = auto()  # unary '+', '-', '~'
    POWER = auto()  # '**'
    AWAIT = auto()  # 'await'
    ATOM = auto()

    def next(self):
        try:
            return self.__class__(self + 1)
        except ValueError:
            return self


_SINGLE_QUOTES = ("'", '"')
_MULTI_QUOTES = ('"""', "'''")
_ALL_QUOTES = (*_SINGLE_QUOTES, *_MULTI_QUOTES)

_DEPRECATED_VALUE_ALIAS_MESSAGE = (
    "{name} is deprecated and will be removed in Python {remove}; use value instead"
)
_DEPRECATED_CLASS_MESSAGE = (
    "{name} is deprecated and will be removed in Python {remove}; "
    "use ast.Constant instead"
)


# If the ast module is loaded more than once, only add deprecated methods once
if not hasattr(Constant, "n"):
    # The following code is for backward compatibility.
    # It will be removed in future.

    def _n_getter(self):
        """Deprecated. Use value instead."""
        import warnings

        warnings._deprecated(
            "Attribute n", message=_DEPRECATED_VALUE_ALIAS_MESSAGE, remove=(3, 14)
        )
        return self.value

    def _n_setter(self, value):
        import warnings

        warnings._deprecated(
            "Attribute n", message=_DEPRECATED_VALUE_ALIAS_MESSAGE, remove=(3, 14)
        )
        self.value = value

    def _s_getter(self):
        """Deprecated. Use value instead."""
        import warnings

        warnings._deprecated(
            "Attribute s", message=_DEPRECATED_VALUE_ALIAS_MESSAGE, remove=(3, 14)
        )
        return self.value

    def _s_setter(self, value):
        import warnings

        warnings._deprecated(
            "Attribute s", message=_DEPRECATED_VALUE_ALIAS_MESSAGE, remove=(3, 14)
        )
        self.value = value

    Constant.n = property(_n_getter, _n_setter)
    Constant.s = property(_s_getter, _s_setter)


class _ABC(type):

    def __init__(cls, *args):
        cls.__doc__ = """Deprecated AST node class. Use ast.Constant instead"""

    def __instancecheck__(cls, inst):
        if cls in _const_types:
            import warnings

            warnings._deprecated(
                f"ast.{cls.__qualname__}",
                message=_DEPRECATED_CLASS_MESSAGE,
                remove=(3, 14),
            )
        if not isinstance(inst, Constant):
            return False
        if cls in _const_types:
            try:
                value = inst.value
            except AttributeError:
                return False
            else:
                return isinstance(value, _const_types[cls]) and not isinstance(
                    value, _const_types_not.get(cls, ())
                )
        return type.__instancecheck__(cls, inst)


def _new(cls, *args, **kwargs):
    for key in kwargs:
        if key not in cls._fields:
            # arbitrary keyword arguments are accepted
            continue
        pos = cls._fields.index(key)
        if pos < len(args):
            raise TypeError(
                f"{cls.__name__} got multiple values for argument {key!r}")
    if cls in _const_types:
        import warnings

        warnings._deprecated(
            f"ast.{cls.__qualname__}", message=_DEPRECATED_CLASS_MESSAGE, remove=(3, 14)
        )
        return Constant(*args, **kwargs)
    return Constant.__new__(cls, *args, **kwargs)


class Num(Constant, metaclass=_ABC):
    _fields = ("n",)
    __new__ = _new


class Str(Constant, metaclass=_ABC):
    _fields = ("s",)
    __new__ = _new


class Bytes(Constant, metaclass=_ABC):
    _fields = ("s",)
    __new__ = _new


class NameConstant(Constant, metaclass=_ABC):
    __new__ = _new


class Ellipsis(Constant, metaclass=_ABC):
    _fields = ()

    def __new__(cls, *args, **kwargs):
        if cls is _ast_Ellipsis:
            import warnings

            warnings._deprecated(
                "ast.Ellipsis", message=_DEPRECATED_CLASS_MESSAGE, remove=(3, 14)
            )
            return Constant(..., *args, **kwargs)
        return Constant.__new__(cls, *args, **kwargs)


_ast_Ellipsis = Ellipsis

_const_types = {
    Num: (int, float, complex),
    Str: (str,),
    Bytes: (bytes,),
    NameConstant: (type(None), bool),
    Ellipsis: (type(...),),
}
_const_types_not = {
    Num: (bool,),
}

_const_node_type_names = {
    bool: "NameConstant",  # should be before int
    type(None): "NameConstant",
    int: "Num",
    float: "Num",
    complex: "Num",
    str: "Str",
    bytes: "Bytes",
    type(...): "Ellipsis",
}


        

class NodeVisitor(object):
    boolops = {"And": "and", "Or": "or"}
    boolop_precedence = {"and": _Precedence.AND, "or": _Precedence.OR}
    binop_precedence = {
        "+": _Precedence.ARITH,
        "-": _Precedence.ARITH,
        "*": _Precedence.TERM,
        "@": _Precedence.TERM,
        "/": _Precedence.TERM,
        "%": _Precedence.TERM,
        "<<": _Precedence.SHIFT,
        ">>": _Precedence.SHIFT,
        "or": _Precedence.BOR,
        "^": _Precedence.BXOR,
        "and": _Precedence.BAND,
        "//": _Precedence.TERM,
        "**": _Precedence.POWER,
    }
    binop = {
        "Add": "+",
        "Sub": "-",
        "Mult": "*",
        "MatMult": "@",
        "Div": "/",
        "Mod": "%",
        "LShift": "<<",
        "RShift": ">>",
        "BitOr": "|",
        "BitXor": "^",
        "BitAnd": "&",
        "FloorDiv": "//",
        "Pow": "**",
    }
    unop = {"Invert": "~", "Not": "not", "UAdd": "+", "USub": "-"}
    cmpops = {
        "Eq": "==",
        "NotEq": "!=",
        "Lt": "<",
        "LtE": "<=",
        "Gt": ">",
        "GtE": ">=",
        "Is": "is",
        "IsNot": "is not",
        "In": "in",
        "NotIn": "not in",
        "Add": "+",
        "Sub": "-",
        "Mult": "*",
        "MatMult": "@",
        "Div": "/",
        "Mod": "%",
        "LShift": "<<",
        "RShift": ">>",
        "BitOr": "or",
        "BitXor": "^",
        "BitAnd": "and",
        "FloorDiv": "//",
        "Pow": "**",
    }
    unop_precedence = {
        "not": _Precedence.NOT,
        "~": _Precedence.FACTOR,
        "+": _Precedence.FACTOR,
        "-": _Precedence.FACTOR,
    }

    binop_rassoc = frozenset(("**",))

    nodes = []
    node_sequence:list = []

    def visit(self, node):
        """Visit a node."""
        self.nodes.append(node.__class__.__name__)
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def tab(self):
        self.write("    ")

    def within(self, node_name: str):
        for x in self._inside:
            if x == node_name:
                return True

    def outside(self, node_name: str):
        for x in self._inside:
            if x == node_name:
                return
        return True

    def insert_line_above(self, node):
        lineabove = self._source.rindex("\n")
    
    def set_last_written(self, node):
        self.last_written = node.__class__.__name__
        
    def interleave(self, inter, f, seq):
        """Call f on each item in seq, calling inter() in between."""
        seq = iter(seq)
        try:
            f(next(seq))
        except StopIteration:
            pass
        else:
            for x in seq:
                inter()
                f(x)

    def items_view(self, traverser, items):
        """Traverse and separate the given *items* with a comma and append it to
        the buffer. If *items* is a single item sequence, a trailing comma
        will be added."""
        if len(items) == 1:
            traverser(items[0])
            self.write(",")
        else:
            self.interleave(lambda: self.write(", "), traverser, items)

    def maybe_newline(self):
        """Adds a newline if it isn't the start of generated source"""
        if self._source:
            self.write("\n")

    def newline(self):
        self.write("\n")

    def add_indentation(self):
        self.write("    " * self._indent)

    def get_indentation(self):
        return "    " * self._indent

    def dedent(self):
        self._indent -= 1

    def indent(self):
        self._indent += 1

    def fill(self, text=""):
        """Indent a piece of text and append it, according to the current
        indentation level"""
        self.maybe_newline()
        self.write("    " * self._indent + text)

    def write(self, *text):
        """Add new source parts"""
        self._source.extend(text)

    @contextmanager
    def buffered(self, buffer=None):
        if buffer is None:
            buffer = []
        original_source = self._source
        self._source = buffer
        yield buffer
        self._source = original_source

    @contextmanager
    def block(self, *, extra=None):
        """A context manager for preparing the source for blocks. It adds
        the character':', increases the indentation on enter and decreases
        the indentation on exit. If *extra* is given, it will be directly
        appended after the colon character.
        """
        self.write(":")
        self._indent += 1
        yield
        self._indent -= 1

    @contextmanager
    def delimit(self, start, end):
        """A context manager for preparing the source for expressions. It adds
        *start* to the buffer and enters, after exit it adds *end*."""

        self.write(start)
        yield
        self.write(end)

    def delimit_if(self, start, end, condition):
        if condition:
            return self.delimit(start, end)
        else:
            return nullcontext()

    def require_parens(self, precedence, node):
        """Shortcut to adding precedence related parens"""
        return self.delimit_if("(", ")", self.get_precedence(node) > precedence)

    def get_precedence(self, node):
        return self._precedences.get(node, _Precedence.TEST)

    def set_list_precedence(self, precedence, listed):
        for n in listed:
            if isinstance(n, list):
                self.set_list_precedence(precedence, n)
            else:
                self._precedences[n] = precedence

    def set_precedence(self, precedence, *nodes):
        for node in nodes:
            if isinstance(node, list):
                self.set_list_precedence(precedence, node)
            else:
                self._precedences[node] = precedence

    def get_raw_docstring(self, node):
        """If a docstring node is found in the body of the *node* parameter,
        return that doctring node, None otherwise.

        Logic mirrored from ``_PyAST_GetDocString``."""
        if (
            not isinstance(
                node, (ast.AsyncFunctionDef, ast.FunctionDef,
                       ast.ClassDef, ast.Module)
            )
            or len(node.body) < 1
        ):
            return None
        node = node.body[0]
        if not isinstance(node, ast.Expr):
            return None
        node = node.value
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node

    def get_type_comment(self, node):
        comment = self._type_ignores.get(node.lineno) or node.type_comment
        if comment is not None:
            return f" # type: {comment}"

    def independent(self):
        if self._inside == []:
            return True

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        try:
            for field, value in iter_fields(node):
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, ast.AST):
                            self.visit(item)
                elif isinstance(value, ast.AST):
                    self.visit(value)
        except:
            method = "visit_" + node.__class__.__name__
            visitor = getattr(self, method)
            return visitor(node)

    def visit_Constant(self, node: ast.Constant):

        value = node.value
        type_name = _const_node_type_names.get(type(value))
        if type_name is None:
            for cls, name in _const_node_type_names.items():
                if isinstance(value, cls):
                    type_name = name
                    break
        if type_name is not None:
            method = "visit_" + type_name
            try:
                visitor = getattr(self, method)
            except AttributeError:
                pass
            else:
                import warnings

                warnings.warn(
                    f"{method} is deprecated; add visit_Constant", DeprecationWarning, 2
                )
                return visitor(node)
        return self.generic_visit(node)


class PythonASTWriter(NodeVisitor):

    def __init__(self, *, _avoid_backslashes=False):
        self._source = []
        self._precedences = {}
        self._type_ignores = {}
        self._indent = 0
        self._avoid_backslashes = _avoid_backslashes

        self._in_try_star = False
        self._inside_class = False
        self._inside_method = False
        self._current_class = None
        self._inside = []
        self._last = [None, None]

    def writelines(self, lines):
        self._source.extend(lines)

    def splitlines(self, src: str):
        """
        Splits a given string into a list of lines.

        Parameters:
            src (str): The input string to be split.

        Returns:
            list: A list of strings, each representing a line from the input string.
        """
        return src.split("\n")

    def wrapline(self, line):
        """
        Returns a string with the given line wrapped with the appropriate indentation.

        Parameters:
            line (str): The line to be wrapped.

        Returns:
            str: The wrapped line with the appropriate indentation.
        """
        return self.get_indentation() + line + "\n"

    def to_lines(self, node):
        return [self.wrapline(x) for x in self.splitlines(self.make(node))]

    def make(self, node):
        vis = PythonASTWriter()
        return vis.visit(node)

    def traverse(self, node):
        l = None
        if issubclass(type(node), ast.stmt):
            self._inside.append(node.__class__.__name__)
            l = len(self._inside) - 1
        if isinstance(node, list):
            for x in node:
                self.traverse(x)
        else:
            super().visit(node)

        if l != None:
            self._inside.pop(l)

    def visit_list(self, node):
        self._indent += 1
        for x in node:
            self.traverse(x)
        self._indent -= 1

    def visit(self, node):
        """Outputs a source code string that, if converted back to an ast
        (using ast.parse) will generate an AST equivalent to *node*"""
        self._source = []
        self._inside = []
        self.traverse(node)
        self._last.append(node.__class__.__name__)
        return "".join(self._source)

    def write_block(self, block: list):
        """write list of statments with a block
        like this:

        for i in range(10)<ENTRY POINT>
            {block}

        Args:
            block (list): _description_
        """
        if block == []:
            return
        self.write(":")
        self.newline()
        self.indent()
        for n in block:
            self.writelines(self.to_lines(n))
        self.dedent()

    def visit_orelse(self, node):
        """
        Visits the <node>.orelse subnode in the abstract syntax tree.

        Args:
            node: The <node> to visit.

        Returns:
            None
        """
        if node.orelse == [] or node.orelse == None:
            return
        self.fill("else")
        self.write(":")
        self.newline()
        self.indent()
        for b in node.orelse:
            lines = self.to_lines(b)
            self.writelines(self.to_lines(b))
        self.dedent()

    def visit_body(self, node):
        if hasattr(node, "body") and node.body != [] and node.body != None:
            self.write(":")
            self.newline()
            self.indent()
            for b in node.body:
                self.writelines(self.to_lines(b))
            self.dedent()

    def _write_arguments(self, node):
        """Write arguments when given a node

        Args:
            node (ast.AST): any ast node
        """
        with self.delimit("(", ")"):
            comma = False
            for e in self._arg_helper(node.args):
                if comma:
                    self.write(", ")
                else:
                    comma = True
                self.traverse(e)

    def _write_arguments_and_keywords(self, node):
        """write out all the arguments and keywords

        Args:
            node (_type_): any node that is an AST
        """
        with self.delimit("(", ")"):
            comma = False
            for e in self._arg_helper(node.args):
                if comma:
                    self.write(", ")
                else:
                    comma = True
                self.traverse(e)
            if node.keywords:
                for e in node.keywords:
                    if comma:
                        self.write(", ")
                    else:
                        comma = True
                    self.traverse(e)

    def _write_docstring_and_traverse_body(self, node):
        if docstring := self.get_raw_docstring(node):
            self._write_docstring(docstring)
            self.traverse(node.body[1:])
        else:
            self.visit_body(node)

    def visit_Module(self, node: ast.Module):

        try:
            self._type_ignores = {
                ignore.lineno: f"ignore{ignore.tag}" for ignore in node.type_ignores
            }
        except:
            pass

        self._write_docstring_and_traverse_body(node)
        self._type_ignores.clear()

    def visit_FunctionType(self, node: ast.FunctionType):

        with self.delimit("(", ")"):
            self.interleave(lambda: self.write(", "),
                            self.traverse, node.argtypes)

        self.write(" -> ")
        self.traverse(node.returns)

    def visit_Base(self, node: Base):
        print(node.name)
        self.write(node.name)

    def visit_Expr(self, node: ast.Expr):
        self.fill()
        self.set_precedence(_Precedence.YIELD, node.value)
        self.traverse(node.value)

    def visit_NamedExpr(self, node: ast.NamedExpr):
        with self.require_parens(_Precedence.NAMED_EXPR, node):
            self.set_precedence(_Precedence.ATOM, node.target, node.value)
            self.traverse(node.target)
            self.write(" := ")
            self.traverse(node.value)

    def visit_Import(self, node: ast.Import):
        self.interleave(lambda: self.write(", "), self.traverse, node.names)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        self.fill("from ")
        self.write("." * (node.level or 0))
        if node.module != []:
            self.write(node.module)
        self.write(" import ")
        self.interleave(lambda: self.write(", "), self.traverse, node.names)
        self.set_last_written("ImportFrom")

    def visit_MultiAssign(self, node: ast.Assign):
        """
        Visits a MultiAssign node in the abstract syntax tree.

        Parameters:
        node (ast.Assign): The Assign node to visit.

        Returns:
        None
        """
        self.fill()
        self.interleave(lambda: self.write(", "), self.traverse, node.targets)
        self.write(" = ")
        if isinstance(node.value, list):
            self.interleave(lambda: self.write(", "),
                            self.traverse, node.value)
        else:
            self.traverse(node.value)

    def visit_SplitAssign(self, node: ast.Assign):
        self.fill()
        self.interleave(lambda: self.write(", "), self.traverse, node.targets)
        self.write(" = ")
        self.traverse(node.value)

    def visit_JoinAssign(self, node: ast.Assign):
        self.fill()
        for target in node.targets:
            self.set_precedence(_Precedence.TUPLE, target)
            self.traverse(target)
            self.write(" = ")
        self.interleave(lambda: self.write(", "), self.traverse, node.value)

    def visit_Assign(self, node: ast.Assign) -> str:

        # x, y, z = a, b, c
        if non_singleton_iterable(node.targets) and non_singleton_iterable(node.value):
            self.visit_MultiAssign(node)
        # x = a, b, c
        elif is_singleton(node.targets) and non_singleton_iterable(node.value):
            self.visit_JoinAssign(node)
        # x, y, z = a
        elif non_singleton_iterable(node.targets) and (
            is_singleton(node.value) or isinstance(node.value, list) != True
        ):
            self.visit_SplitAssign(node)
        else:
            self.fill()
            for target in node.targets:
                self.set_precedence(_Precedence.TUPLE, target)
                self.traverse(target)
                self.write(" = ")
            self.traverse(node.value)
            if type_comment := self.get_type_comment(node):
                self.write(type_comment)

    def visit_AugAssign(self, node: ast.AugAssign):
        self.fill()
        self.traverse(node.target)
        self.write(" " + self.binop[node.op.__class__.__name__] + "= ")
        self.traverse(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        self.fill()
        with self.delimit_if(
            "(", ")", not node.simple and isinstance(node.target, ast.Name)
        ):
            self.traverse(node.target)
        self.write(": ")
        self.traverse(node.annotation)
        if node.value == []:
            node.value = None
        if node.value != None:
            self.write(" = ")
            self.traverse(node.value)

    def visit_Return(self, node: ast.Return):
        self.fill("return")
        if node.value == []:
            node.value = None
        if node.value != None:
            self.write(" ")
            self.traverse(node.value)

    def visit_Pass(self, node: ast.Pass):
        self.fill("pass")

    def visit_Break(self, node: ast.Break):
        self.fill("break")

    def visit_Continue(self, node: ast.Continue):
        self.fill("continue")

    def visit_Delete(self, node: ast.Delete):
        self.fill("del ")
        self.interleave(lambda: self.write(", "), self.traverse, node.targets)

    def visit_Assert(self, node: ast.Assert):
        self.fill("assert ")
        self.traverse(node.test)
        if node.msg != None:
            self.write(", ")
            self.traverse(node.msg)

    def visit_Global(self, node: ast.Global):
        self.fill("global ")
        self.interleave(lambda: self.write(", "), self.write, node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal):
        self.fill("nonlocal ")
        self.interleave(lambda: self.write(", "), self.write, node.names)

    def visit_Await(self, node: ast.Await):
        with self.require_parens(_Precedence.AWAIT, node):
            self.write("await")
            node.value = node.value if node.value != [] else None
            if node.value:
                self.write(" ")
                self.set_precedence(_Precedence.ATOM, node.value)
                self.traverse(node.value)

    def visit_Yield(self, node: ast.Yield):
        with self.require_parens(_Precedence.YIELD, node):
            self.write("yield")
            node.value = node.value if node.value != [] else None
            if node.value:
                self.write(" ")
                self.set_precedence(_Precedence.ATOM, node.value)
                self.traverse(node.value)

    def visit_YieldFrom(self, node: ast.YieldFrom):
        with self.require_parens(_Precedence.YIELD, node):
            self.write("yield from ")
            if not node.value:
                raise ValueError(
                    "Node can't be used without a value attribute.")
            self.set_precedence(_Precedence.ATOM, node.value)
            self.traverse(node.value)

    def visit_Raise(self, node: ast.Raise):
        self.fill("raise")
        if not node.exc:
            if node.cause:
                raise ValueError(f"Node can't use cause without an exception.")
            return
        self.write(" ")
        self.traverse(node.exc)
        if node.cause:
            self.write(" from ")
            self.traverse(node.cause)

    def do_visit_try(self, node: ast.Try):
        self.fill("try")
        self.visit_body(node)
        for ex in node.handlers:
            self.traverse(ex)
        node.orelse = node.orelse if node.orelse != [] else None
        self.visit_orelse(node)
        if node.finalbody != []:
            self.fill("finally")
            self.write_block(node.finalbody)

    def visit_Try(self, node: ast.Try):
        prev_in_try_star = self._in_try_star
        try:
            self._in_try_star = False
            self.do_visit_try(node)
        finally:
            self._in_try_star = prev_in_try_star

    def visit_TryStar(self, node: ast.TryStar):
        prev_in_try_star = self._in_try_star
        try:
            self._in_try_star = True
            self.do_visit_try(node)
        finally:
            self._in_try_star = prev_in_try_star

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self.fill("except*" if self._in_try_star else "except")
        if node.type:
            self.write(" ")
            self.traverse(node.type)
        if node.name:
            self.write(" as ")
            self.write(node.name)
        with self.block():
            self.traverse(node.body)

    def visit_ClassDef(self, node: ast.ClassDef):

        self._inside_class = True
        self._current_class = node
        self.maybe_newline()
        if hasattr(node, "decorator_list"):
            for deco in node.decorator_list:
                self.fill("@")
                self.traverse(deco)

        self.fill("class " + node.name)

        if hasattr(node, "type_params"):
            self._type_params_helper(node.type_params)

        with self.delimit("(", ")"):
            comma = None
            for base in node.bases:
                if comma:
                    self.write(", ")
                else:
                    comma = True
                if isinstance(base, Base):
                    self.write(base.name)
                elif isinstance(base, ast.Name):
                    self.write(base.id)

            if node.keywords != [] and node.keywords != None:
                comma = None
                for e in node.keywords:
                    if comma:
                        self.write(", ")
                    else:
                        comma = True

                    self.traverse(e)

        self.visit_body(node)

        self.maybe_newline()

        self._inside_class = False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self._inside_class == True:
            self._inside_method = True
        self._function_helper(node, "def")
        self._inside_method = False

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._function_helper(node, "async def")

    def _function_helper(self, node: ast.FunctionDef, fill_suffix):
        try:
            for deco in node.decorator_list:
                self.fill("@")
                self.traverse(deco)
        except:
            pass

        if isinstance(node.name, ast.Attribute):
            if isinstance(node.name.attr, ast.Name):
                def_str = fill_suffix + " " + node.name.attr.id
            else:
                def_str = fill_suffix + " " + node.name.attr
        elif isinstance(node.name, ast.Name):
            def_str = fill_suffix + " " + node.name.id
        elif isinstance(node.name, ast.Constant):
            def_str = fill_suffix + " " + node.id
        else:
            def_str = fill_suffix + " " + node.name

        self.fill(def_str)
        if hasattr(node, "type_params"):
            self._type_params_helper(node.type_params)
        with self.delimit("(", ")"):
            self.traverse(node.args)
        if node.returns:
            self.write(" -> ")
            self.traverse(node.returns)

        self.visit_body(node)

    def _type_params_helper(self, type_params):
        if type_params is not None and len(type_params) > 0:
            with self.delimit("[", "]"):
                self.interleave(lambda: self.write(", "),
                                self.traverse, type_params)

    def visit_TypeVar(self, node: ast.TypeVar):
        self.write(node.name)
        if node.bound:
            self.write(": ")
            self.traverse(node.bound)

    def visit_TypeVarTuple(self, node: ast.TypeVarTuple):
        self.write("*" + node.name)

    def visit_ParamSpec(self, node: ast.ParamSpec):
        self.write("**" + node.name)

    def visit_TypeAlias(self, node: ast.TypeAlias):
        self.fill("type ")
        self.traverse(node.name)
        self._type_params_helper(node.type_params)
        self.write(" = ")
        self.traverse(node.value)

    def visit_For(self, node: ast.For):
        self._for_helper("for ", node)

    def visit_AsyncFor(self, node: ast.AsyncFor):
        self._for_helper("async for ", node)

    def _for_helper(self, fill, node: ast.For):
        self.fill(fill)
        self.set_precedence(_Precedence.TUPLE, node.target)
        self.traverse(node.target)
        self.write(" in ")
        self.traverse(node.iter)
        self.visit_body(node)
        self.visit_orelse(node)

    def visit_Elif(self, node: ast.If):
        self.fill("elif ")
        self.set_precedence(_Precedence.TEST, node.test)
        self.traverse(node.test)
        self.visit_body(node)

    def visit_If(self, node: ast.If):
        self.fill("if ")
        self.set_precedence(_Precedence.TEST, node.test)
        self.traverse(node.test)
        self.visit_body(node)
        orelse = []
        if isinstance(node.orelse, list):
            for subnode in node.orelse:
                if isinstance(subnode, ast.If):
                    self.visit_Elif(subnode)
                else:
                    orelse.append(subnode)
            if orelse != []:
                node.orelse = orelse 
                self.visit_orelse(node)
                
    def visit_While(self, node: ast.While):
        self.fill("while ")
        self.traverse(node.test)
        self.visit_body(node)
        self.visit_orelse(node)

    def visit_With(self, node: ast.With):
        self.fill("with ")
        self.interleave(lambda: self.write(", "), self.traverse, node.items)
        self.write_block(node.body)

    def visit_AsyncWith(self, node: ast.AsyncWith):
        self.fill("async with ")
        self.interleave(lambda: self.write(", "), self.traverse, node.items)
        self.write_block(node.body)

    def _str_literal_helper(
        self, string, *, quote_types=_ALL_QUOTES, escape_special_whitespace=False
    ):
        """Helper for writing string literals, minimizing escapes.
        Returns the tuple (string literal to write, possible quote types).
        """

        def escape_char(c):
            # \n and \t are non-printable, but we only escape them if
            # escape_special_whitespace is True
            if not escape_special_whitespace and c in "\n\t":
                return c
            # Always escape backslashes and other non-printable characters
            if c == "\\" or not c.isprintable():
                return c.encode("unicode_escape").decode("ascii")
            return c

        escaped_string = "".join(map(escape_char, string))
        possible_quotes = quote_types
        if "\n" in escaped_string:
            possible_quotes = [
                q for q in possible_quotes if q in _MULTI_QUOTES]
        possible_quotes = [
            q for q in possible_quotes if q not in escaped_string]
        if not possible_quotes:
            # If there aren't any possible_quotes, fallback to using repr
            # on the original string. Try to use a quote from quote_types,
            # e.g., so that we use triple quotes for docstrings.
            string = repr(string)
            quote = next((q for q in quote_types if string[0] in q), string[0])
            return string[1:-1], [quote]
        if escaped_string:
            # Sort so that we prefer '''"''' over """\""""
            possible_quotes.sort(key=lambda q: q[0] == escaped_string[-1])
            # If we're using triple quotes and we'd need to escape a final
            # quote, escape it
            if possible_quotes[0][0] == escaped_string[-1]:
                assert len(possible_quotes[0]) == 3
                escaped_string = escaped_string[:-
                                                1] + "\\" + escaped_string[-1]
        return escaped_string, possible_quotes

    def _write_str_avoiding_backslashes(self, string, *, quote_types=_ALL_QUOTES):
        """Write string literal value with a best effort attempt to avoid backslashes."""
        string, quote_types = self._str_literal_helper(
            string, quote_types=quote_types)
        quote_type = quote_types[0]
        self.write(f"{quote_type}{string}{quote_type}")

    def visit_JoinedStr(self, node: ast.JoinedStr):
        self.write("f")
        fstring_parts = []
        for value in node.values:
            with self.buffered() as buffer:
                self._write_fstring_inner(value)
            fstring_parts.append(
                ("".join(buffer), isinstance(value, ast.Constant)))

        new_fstring_parts = []
        quote_types = list(_ALL_QUOTES)
        fallback_to_repr = False
        for value, is_constant in fstring_parts:
            if is_constant:
                value, new_quote_types = self._str_literal_helper(
                    value,
                    quote_types=quote_types,
                    escape_special_whitespace=True,
                )
                if set(new_quote_types).isdisjoint(quote_types):
                    fallback_to_repr = True
                    break
                quote_types = new_quote_types
            elif "\n" in value:
                quote_types = [q for q in quote_types if q in _MULTI_QUOTES]
                assert quote_types
            new_fstring_parts.append(value)

        if fallback_to_repr:
            # If we weren't able to find a quote type that works for all parts
            # of the JoinedStr, fallback to using repr and triple single quotes.
            quote_types = ["'''"]
            new_fstring_parts.clear()
            for value, is_constant in fstring_parts:
                if is_constant:
                    # force repr to use single quotes
                    value = repr('"' + value)
                    expected_prefix = "'\""
                    assert value.startswith(expected_prefix), repr(value)
                    value = value[len(expected_prefix): -1]
                new_fstring_parts.append(value)

        value = "".join(new_fstring_parts)
        quote_type = quote_types[0]
        self.write(f"{quote_type}{value}{quote_type}")

    def _write_fstring_inner(self, node, is_format_spec=False):
        if isinstance(node, ast.JoinedStr):
            # for both the f-string itself, and format_spec
            for value in node.values:
                self._write_fstring_inner(value, is_format_spec=is_format_spec)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = node.value.replace("{", "{{").replace("}", "}}")

            if is_format_spec:
                value = value.replace("\\", "\\\\")
                value = value.replace("'", "\\'")
                value = value.replace('"', '\\"')
                value = value.replace("\n", "\\n")
            self.write(value)
        elif isinstance(node, ast.FormattedValue):
            self.visit_FormattedValue(node)
        else:
            raise ValueError(f"Unexpected node inside JoinedStr, {node!r}")

    def visit_FormattedValue(self, node: ast.FormattedValue):

        def unparse_inner(inner):
            unparser = type(self)()
            unparser.set_precedence(_Precedence.TEST.next(), inner)
            return unparser.visit(inner)

        with self.delimit("{", "}"):
            expr = unparse_inner(node.value)
            if expr.startswith("{"):
                # Separate pair of opening brackets as "{ {"
                self.write(" ")
            self.write(expr)
            if node.conversion != -1:
                self.write(f"!{chr(node.conversion)}")
            if node.format_spec:
                self.write(":")
                self._write_fstring_inner(
                    node.format_spec, is_format_spec=True)

    def _static_method_helper(self, node):
        if ":" in node.id:
            self.fill(node.id.replace(":", "."))
        else:
            self.write(node.id)

    def visit_Name(self, node: ast.Name):
        self._static_method_helper(node)

    def _write_docstring(self, node):
        self.fill()
        if node.kind == "u":
            self.write("u")
        self._write_str_avoiding_backslashes(
            node.value, quote_types=_MULTI_QUOTES)

    def _write_constant(self, value):
        if isinstance(value, (float, complex)):
            # Substitute overflowing decimal literal for AST infinities,
            # and inf - inf for NaNs.
            self.write(
                repr(value)
                .replace("inf", _INFSTR)
                .replace("nan", f"({_INFSTR}-{_INFSTR})")
            )
        elif self._avoid_backslashes and isinstance(value, str):
            self._write_str_avoiding_backslashes(value)
        else:
            self.write(repr(value))

    def visit_Constant(self, node: ast.Constant):
        value = node.value
        if isinstance(value, tuple):
            with self.delimit("(", ")"):
                self.items_view(self._write_constant, value)
        elif value is ...:
            self.write("...")
        else:
            if node.kind == "u":
                self.write("u")
            elif node.kind == "s":
                self._write_constant(node.value)

            elif node.kind == "i":
                self.write(node.value)
                return
            else:
                self.write(str(node.value))

    def visit_List(self, node: ast.List):

        with self.delimit("[", "]"):
            self.interleave(lambda: self.write(", "), self.traverse, node.elts)

    def visit_ListComp(self, node: ast.ListComp):

        with self.delimit("[", "]"):
            self.traverse(node.elt)
            for gen in node.generators:
                self.traverse(gen)

    def visit_GeneratorExp(self, node: ast.GeneratorExp):

        with self.delimit("(", ")"):
            self.traverse(node.elt)
            for gen in node.generators:
                self.traverse(gen)

    def visit_SetComp(self, node: ast.SetComp):

        with self.delimit("{", "}"):
            self.traverse(node.elt)
            for gen in node.generators:
                self.traverse(gen)

    def visit_DictComp(self, node: ast.DictComp):

        with self.delimit("{", "}"):
            self.traverse(node.key)
            self.write(": ")
            self.traverse(node.value)
            for gen in node.generators:
                self.traverse(gen)

    def visit_comprehension(self, node: ast.comprehension):

        if node.is_async:
            self.write(" async for ")
        else:
            self.write(" for ")
        self.set_precedence(_Precedence.TUPLE, node.target)
        self.traverse(node.target)
        self.write(" in ")
        self.set_precedence(_Precedence.TEST.next(), node.iter, *node.ifs)
        self.traverse(node.iter)
        for if_clause in node.ifs:
            self.write(" if ")
            self.traverse(if_clause)

    def visit_IfExp(self, node: ast.IfExp):

        with self.require_parens(_Precedence.TEST, node):
            self.set_precedence(_Precedence.TEST.next(), node.body, node.test)
            self.traverse(node.body)
            self.write(" if ")
            self.traverse(node.test)
            self.write(" else ")
            self.set_precedence(_Precedence.TEST, node.orelse)
            self.traverse(node.orelse)

    def visit_Set(self, node: ast.Set):

        if node.elts != [] and node.elts != None:
            with self.delimit("{", "}"):
                self.interleave(lambda: self.write(", "),
                                self.traverse, node.elts)
        else:
            # `{}` would be interpreted as a dictionary literal, and
            # `set` might be shadowed. Thus:
            self.write("{*()}")

    def visit_Dict(self, node: ast.Dict):

        def write_key_value_pair(k, v):
            self.traverse(k)
            self.write(": ")
            self.traverse(v)

        def write_item(item):
            k, v = item
            if k is None:
                # for dictionary unpacking operator in dicts {**{'y': 2}}
                # see PEP 448 for details
                self.write("**")
                self.set_precedence(_Precedence.EXPR, v)
                self.traverse(v)
            else:
                write_key_value_pair(k, v)

        with self.delimit("{", "}"):
            self.interleave(
                lambda: self.write(", "), write_item, zip(
                    node.keys, node.values)
            )

    def visit_Tuple(self, node: ast.Tuple):

        with self.delimit_if(
            "(",
            ")",
            len(node.elts) == 0 or self.get_precedence(
                node) > _Precedence.TUPLE,
        ):
            self.items_view(self.traverse, node.elts)

    def visit_UnaryOp(self, node: ast.UnaryOp):

        operator = self.unop[node.op.__class__.__name__]
        operator_precedence = self.unop_precedence[operator]
        with self.require_parens(operator_precedence, node):
            self.write(operator)
            # factor prefixes (+, -, ~) shouldn't be separated
            # from the value they belong, (e.g: +1 instead of + 1)
            if operator_precedence is not _Precedence.FACTOR:
                self.write(" ")
            self.set_precedence(operator_precedence, node.operand)
            self.traverse(node.operand)

    def visit_BinOp(self, node: ast.BinOp):

        try:
            operator = self.binop[node.op.__class__.__name__]
            operator_precedence = self.binop_precedence[operator]
            with self.require_parens(operator_precedence, node):
                if operator in self.binop_rassoc:
                    left_precedence = operator_precedence.next()
                    right_precedence = operator_precedence
                else:
                    left_precedence = operator_precedence
                    right_precedence = operator_precedence.next()

                self.set_precedence(left_precedence, node.left)
                self.traverse(node.left)
                self.write(f" {operator} ")
                self.set_precedence(right_precedence, node.right)
                self.traverse(node.right)
        except:
            operator = self.cmpops[node.op.__class__.__name__]
            self.traverse(node.left)
            self.write(f" {operator} ")
            self.traverse(node.right)

    def visit_Compare(self, node: ast.Compare):

        with self.require_parens(_Precedence.CMP, node):
            self.set_precedence(_Precedence.CMP.next(),
                                node.left, *node.comparators)
            self.traverse(node.left)
            for o, e in zip(node.ops, node.comparators):
                self.write(" " + self.cmpops[o.__class__.__name__] + " ")
                self.traverse(e)

    def visit_BoolOp(self, node: ast.BoolOp):

        operator = self.boolops[node.op.__class__.__name__]
        operator_precedence = self.boolop_precedence[operator]

        def increasing_level_traverse(node):
            nonlocal operator_precedence
            operator_precedence = operator_precedence.next()
            self.set_precedence(operator_precedence, node)
            self.traverse(node)

        with self.require_parens(operator_precedence, node):
            s = f" {operator} "
            self.interleave(
                lambda: self.write(s), increasing_level_traverse, node.values
            )

    def visit_Attribute(self, node: ast.Attribute):
        if self._last[-1] == "Assign":
            self.fill()
        self.set_precedence(_Precedence.ATOM, node.value)
        self.traverse(node.value)
        # Special case: 3.__abs__() is a syntax error, so if node.value
        # is an integer literal then we need to either parenthesize
        # it or add an extra space to get 3 .__abs__().
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, int):
            self.write(" ")
        self.write(".")
        self.traverse(node.attr)

    def _arg_helper(self, args):
        if isinstance(args, ast.Dict):
            return [args]
        if isinstance(args, list):
            return args
        elif isinstance(args, ast.arguments):
            return args.args

    def visit_SuperMethod(self, node: ast.Call):
        # check if node.func.value is a base class
        if isinstance(self._current_class.bases, list) == False:
            self._current_class.bases = [self._current_class.bases]

        if node.func.value.id in [x.id for x in self._current_class.bases]:
            node.func.value.id = self.fill("super()")

            if node.func.attr.id == "init":
                node.func.attr.id = "__init__"

            self.write(".")
            self.write(node.func.attr.id)
            self._write_arguments(node)

    def visit_Call(self, node: ast.Call):

        self.set_precedence(_Precedence.ATOM, node.func)
        # Goto Check
        if node.keywords and node.keywords[0] == "GOTO":
            print("GOTO")
            self.fill()
            self.traverse(node.func)
            return
        if node.keywords and node.keywords[0] == "ANON":
            definition = self.make(node.keywords[1])
            buffer = []
            
            for line in self.splitlines(definition):
                buffer.append(self.wrapline(line))
        # super check
        if (
            self._inside_class == True
            and self._inside_method == True
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
        ):
            self.visit_SuperMethod(node)
            return
        
        if isinstance(node.func, ast.Attribute):

            self.traverse(node.func.value)
            self.write(".")
            if isinstance(node.func.attr, ast.Name):
                self.traverse(node.func.attr)
            else:
                self.write(str(node.func.attr))

            with self.delimit("(", ")"):
                self.traverse(node.args)
            return

        self.traverse(node.func)
        self._write_arguments_and_keywords(node)
        return

    def visit_Subscript(self, node: ast.Subscript):

        def is_non_empty_tuple(slice_value):
            return isinstance(slice_value, ast.Tuple) and slice_value.elts

        self.set_precedence(_Precedence.ATOM, node.value)
        self.traverse(node.value)
        with self.delimit("[", "]"):
            if is_non_empty_tuple(node.slice):
                # parentheses can be omitted if the tuple isn't empty
                self.items_view(self.traverse, node.slice.elts)
            else:
                self.traverse(node.slice)

    def visit_Starred(self, node: ast.Starred):
        self.write("*")
        self.set_precedence(_Precedence.EXPR, node.value)
        self.traverse(node.value)

    def visit_Ellipsis(self, node: ast.Ellipsis):
        self.write("...")

    def visit_Slice(self, node: ast.Slice):

        if node.lower != None:
            self.traverse(node.lower)
        self.write(":")
        if node.upper != None:
            self.traverse(node.upper)
        if node.step != None:
            self.write(":")
            self.traverse(node.step)

    def visit_Match(self, node: ast.Match):
        self.fill("match ")
        self.traverse(node.subject)
        with self.block():
            for case in node.cases:
                self.traverse(case)

    def visit_arg(self, node: ast.arg):
        if isinstance(node.arg, (ast.Attribute, ast.Call)):
            self.traverse(node.arg)
        elif isinstance(node.arg, (str, int, float, dict, list)):
            self.write(str(node.arg))
        else:
            self.traverse(node.arg)

    def visit_arguments(self, node: ast.arguments):

        first = True
        # normal arguments
        all_args = node.posonlyargs
        defaults = [None] * \
            (len(all_args) - len(node.defaults)) + node.defaults
        for index, elements in enumerate(zip(all_args, defaults), 1):
            a, d = elements
            if first:
                first = False
            else:
                self.write(", ")
            self.traverse(a)
            if d:
                self.write("=")
                self.traverse(d)

        # varargs, or bare '*' if no varargs but keyword-only arguments present
        if node.vararg != None or node.kwonlyargs != []:
            if first:
                first = False
            else:
                self.write(", ")
            self.write("*")
            if node.vararg:
                self.write(node.vararg.arg)
                if node.vararg.annotation:
                    self.write(": ")
                    self.traverse(node.vararg.annotation)

        # keyword-only arguments
        if node.kwonlyargs != []:
            for a, d in zip(node.kwonlyargs, node.kw_defaults):
                self.write(", ")
                self.traverse(a)
                if d:
                    self.write("=")
                    self.traverse(d)

        # kwargs
        if node.kwarg != None:
            if first:
                first = False
            else:
                self.write(", ")
            self.write("**" + node.kwarg.arg)
            if node.kwarg.annotation:
                self.write(": ")
                self.traverse(node.kwarg.annotation)

    def visit_keyword(self, node: ast.keyword):

        if node.arg is None:
            self.write("**")
        else:
            self.write(node.arg)
            self.write("=")
        self.traverse(node.value)

    def visit_Lambda(self, node: ast.Lambda):

        with self.require_parens(_Precedence.TEST, node):
            self.write("lambda")
            with self.buffered() as buffer:
                self.traverse(node.args)
            if buffer:
                self.write(" ", *buffer)
            self.set_precedence(_Precedence.TEST, node.body)
            self.write_block(node.body)

    def visit_alias(self, node: ast.alias):

        self.write(node.name)
        if node.asname:
            self.write(" as " + node.asname)

    def visit_withitem(self, node: ast.withitem):

        self.traverse(node.context_expr)
        if node.optional_vars:
            self.write(" as ")
            self.traverse(node.optional_vars)

    def visit_match_case(self, node: ast.match_case):
        self.fill("case ")
        self.traverse(node.pattern)
        if node.guard:
            self.write(" if ")
            self.traverse(node.guard)
        self.write_block(node.body)

    def visit_MatchValue(self, node: ast.MatchValue):
        self.traverse(node.value)

    def visit_MatchSingleton(self, node: ast.MatchSingleton):
        self._write_constant(node.value)

    def visit_MatchSequence(self, node: ast.MatchSequence):
        with self.delimit("[", "]"):
            self.interleave(lambda: self.write(", "),
                            self.traverse, node.patterns)

    def visit_MatchStar(self, node: ast.MatchStar):
        name = node.name
        if name is None:
            name = "_"
        self.write(f"*{name}")

    def visit_MatchMapping(self, node: ast.MatchMapping):
        def write_key_pattern_pair(pair):
            k, p = pair
            self.traverse(k)
            self.write(": ")
            self.traverse(p)

        with self.delimit("{", "}"):
            keys = node.keys
            self.interleave(
                lambda: self.write(", "),
                write_key_pattern_pair,
                zip(keys, node.patterns, strict=True),
            )
            rest = node.rest
            if rest is not None:
                if keys:
                    self.write(", ")
                self.write(f"**{rest}")

    def visit_MatchClass(self, node: ast.MatchClass):
        self.set_precedence(_Precedence.ATOM, node.cls)
        self.traverse(node.cls)
        with self.delimit("(", ")"):
            patterns = node.patterns
            self.interleave(lambda: self.write(", "), self.traverse, patterns)
            attrs = node.kwd_attrs
            if attrs:

                def write_attr_pattern(pair):
                    attr, pattern = pair
                    self.write(f"{attr}=")
                    self.traverse(pattern)

                if patterns:
                    self.write(", ")
                self.interleave(
                    lambda: self.write(", "),
                    write_attr_pattern,
                    zip(attrs, node.kwd_patterns, strict=True),
                )

    def visit_MatchAs(self, node: ast.MatchAs):
        name = node.name
        pattern = node.pattern
        if name is None:
            self.write("_")
        elif pattern is None:
            self.write(node.name)
        else:
            with self.require_parens(_Precedence.TEST, node):
                self.set_precedence(_Precedence.BOR, node.pattern)
                self.traverse(node.pattern)
                self.write(f" as {node.name}")

    def visit_MatchOr(self, node: ast.MatchOr):
        with self.require_parens(_Precedence.BOR, node):
            self.set_precedence(_Precedence.BOR.next(), *node.patterns)
            self.interleave(lambda: self.write(" | "),
                            self.traverse, node.patterns)

    def visit_Comment(self, node):
        self.write("# " + node.comment)
    
    def visit_MultiLineComment(self, node):
        lines = node.comment.split("\n")
        self.newline()
        self.add_indentation()
        self.write('"""\n')
        ind = self.get_indentation()
        for line in lines:
            self.write(ind + line + "\n")
        self.add_indentation()
        self.write('"""\n')
        