from typing import List
from transpile.luaparser.astnodes import (
    Block,
    Call,
    Expression,
    Name,
    String,
    Invoke,
    Method,
    Statement,
    Node,
    Table,
)
import ast
from typing_extensions import Unpack


SelfArg = ast.arg("self")
METHOD_ARGUMENTS = ast.arguments(
    posonlyargs=[SelfArg],
    args=[SelfArg],
    vararg=None,
    kw_defaults=[SelfArg],
    kwarg=None,
    defaults=[],
    kwonlyargs=[],
)
NO_ARGS = ast.arguments(
    posonlyargs=[],
    args=[],
    vararg=None,
    kw_defaults=[],
    kwarg=None,
    defaults=[],
    kwonlyargs=[],
)
NO_BODY = [ast.Pass()]


class MethodDef:
    __match_args__ = ("name", "body", "args", "returns")
    __match_types__ = (str, list, ast.arguments, any)

    def __init__(
        self,
        name: str = "",
        body: list[ast.stmt] = [ast.Pass()],
        args: ast.arguments = METHOD_ARGUMENTS,
        returns=None,
    ) -> None:
        self.name: str = name
        self.body: list[ast.stmt] = body
        self.args: ast.arguments = args
        self.returns = returns


class MethodCall:
    def __init__(self, object: ast.Attribute, args: ast.arguments = NO_ARGS) -> None:
        self.object: ast.Attribute = object
        self.args: ast.arguments = args


class ClassBase(ast.AST):
    def __init__(self, name: str = "") -> None:
        super().__init__()
        self.name = ast.Name(id=name, ctx=ast.Load())


# For dealing with all Invokes


class ObjectActionArguments(ast.expr):
    __match_args__ = ("objects", "actions", "arguments")
    type__ = ("list[str]", "list[str]", "list[str]")

    def __init__(
        self, objects: list[str], actions: list[str], arguments: list[str], **kwargs
    ) -> None:
        self.objects: list[str] = objects
        self.actions: list[str] = actions
        self.arguments: list[str] = arguments


class SuperInitializer(ObjectActionArguments):
    __match_args__ = ("objects", "object_args", "actions", "action_args", "arguments")
    type__ = ("list[str]", "list[str]", "list[str]", "list[str]")

    def __init__(self, object: str, action: str, args: list[str], **kwargs) -> None:
        super().__init__(object, action, args, **kwargs)
        self.objects = ["super"]
        self.object_args = []
        self.actions = ["__init__"]
        self.action_args = args


class SuperMethod(ObjectActionArguments):
    def __init__(self, object: str, action: str, args: list[str], **kwargs) -> None:
        super().__init__(object, action, args, **kwargs)
        self._name = "SuperMethod"


class StaticMethod(ObjectActionArguments):
    def __init__(self, object: str, action: str, args: list[str], **kwargs) -> None:
        super().__init__(object, action, args, **kwargs)
        self._name = "StaticMethod"


#########################################
# LUA                                   #
#########################################


class TableConstructor(Statement):
    __match_args__ = ("func", "args", "keywords")

    def __init__(self, func: Expression, args: List[Expression], **kwargs):
        super(TableConstructor, self).__init__("TableConstructor", **kwargs)
        self.func = func
        self.args = args
        self.keywords = []


class MetaTable(Statement):
    __match_args__ = ("func", "args", "id")

    def __init__(self, func: Name, args: List[Expression], **kwargs):
        super(MetaTable, self).__init__("MetaTable", **kwargs)
        self.func = func
        self.args = args
        self.id: str = "self.__class__"


class Require(Statement):
    def __init__(self, func: Name, args: List[Expression], **kwargs):
        super(Require, self).__init__("Require", **kwargs)
        self.args: list[str] = [arg.s for arg in self.args if isinstance(arg, String)]


class MethodCall(Statement):
    __match_args__ = ("source", "func", "args")

    def __init__(
        self, source: Expression, func: Expression, args: List[Expression], **kwargs
    ):
        super(MethodCall, self).__init__("MethodCall", **kwargs)
        self.source = source
        self.func = func
        self.args = args


class Initializer(Statement):
    __match_args__ = ("source", "name", "args", "body")

    def __init__(
        self,
        source: Expression,
        name: Name,
        args: List[Expression],
        body: Block,
        **kwargs
    ):
        super(Initializer, self).__init__("Initializer", **kwargs)
        self.source = source
        self.name = name
        self.args = args
        self.body = body
        self.name.id = "__init__"
