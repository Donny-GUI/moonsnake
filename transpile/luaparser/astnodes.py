from enum import Enum
from typing import List, Optional
from antlr4.Token import CommonToken
from typing import TypeVar, List




Pattern = TypeVar("Pattern")
Comments = Optional[List['Comment']]


def _handle(object, attr):
    attr = getattr(object, attr)
    if isinstance(attr, (list, set, tuple)):
        return [type(x) for x in attr]
    return type(attr)

def _equal_dicts(d1, d2, ignore_keys):
    ignored = set(ignore_keys)
    for k1, v1 in d1.items():
        if k1 not in ignored and (k1 not in d2 or d2[k1] != v1):
            return False
    for k2, v2 in d2.items():
        if k2 not in ignored and k2 not in d1:
            return False
    return True


class Node:
    
    __match_args__ = ('name', 'comments', 'first_token', 'last_token') # type: tuple[str]
    """Base class for AST node."""

    def __init__(self, name: str, comments: Comments=None, first_token: Optional[CommonToken]=None, last_token: Optional[CommonToken]=None):
        """

            Args:
                name: Node display name
                comments: Optional comments
                first_token: First Antlr token
                last_token: Last Antlr token
        """
        self.types__ = []
        if comments is None:
            comments = []
        self._name: str = name
        self.comments: Comments = comments
        self._first_token: Optional[CommonToken] = first_token
        self._last_token: Optional[CommonToken] = last_token

        # We want to have nodes be serializable with pickle.
        # To allow that we must not have mutable fields such as streams.
        # Tokens have streams, create a stream-less copy of tokens.
        if self._first_token is not None:
            self._first_token = self._first_token.clone()
            self._first_token.source = CommonToken.EMPTY_SOURCE
        if self._last_token is not None:
            self._last_token = self._last_token.clone()
            self._last_token.source = CommonToken.EMPTY_SOURCE

    @property
    def display_name(self) -> str:
        return self._name

    def __eq__(self, other) -> bool:
        if isinstance(self, other.__class__):
            return _equal_dicts(self.__dict__, other.__dict__, ['_first_token', '_last_token'])
        return False

    @property
    def first_token(self) -> Optional[CommonToken]:
        """
            First token of a node.

            Note: Token is disconnected from underline source streams.
        """
        return self._first_token

    @first_token.setter
    def first_token(self, val: Optional[CommonToken]):
        if val is not None:
            self._first_token = val.clone()
            self._first_token.source = CommonToken.EMPTY_SOURCE

    @property
    def last_token(self) -> Optional[CommonToken]:
        """
            Last token of a node.

            Note: Token is disconnected from underline source streams.
        """
        return self._last_token

    @last_token.setter
    def last_token(self, val: Optional[CommonToken]):
        if val is not None:
            self._last_token = val.clone()
            self._last_token.source = CommonToken.EMPTY_SOURCE

    @property
    def start_char(self) -> Optional[int]:
        return self._first_token.start if self._first_token else None

    @property
    def stop_char(self) -> Optional[int]:
        return self._last_token.stop if self._last_token else None

    @property
    def line(self) -> Optional[int]:
        """Line number."""
        return self._first_token.line if self._first_token else None

    def to_pattern(self) -> dict:
        self.types__ = [_handle(self, t) for t in self.__match_args__]
        return {self._name: {**{self.__match_args__[idx]: val for idx, val in enumerate(self.types__)}}}

    def to_json(self) -> any:
        return {self._name: {**{k: v for k, v in self.__dict__.items() if not k.startswith('_') and v}, **{'start_char': self.start_char, 'stop_char': self.stop_char, 'line': self.line}}}

class Comment(Node):
    types__ = (str, bool) # type: tuple
    __match_args__ = ('s', 'is_multi_line') # type: tuple[str]

    def __init__(self, s: str, is_multi_line: bool=False, **kwargs):
        super().__init__('Comment', **kwargs)
        self.s: str = s
        self.is_multi_line: bool = is_multi_line

class Expression(Node):
    """Define a Lua expression."""

class Statement(Expression):
    """Base class for Lua statement."""

class Block(Node):
    types__ = (List[Statement],) # type: tuple
    __match_args__ = ('body',) # type: tuple[str]
    """Define a Lua Block."""

    def __init__(self, body: List[Statement], **kwargs):
        super().__init__('Block', **kwargs)
        self.body: List[Statement] = body

    def __iter__(self):
        b = self.body
        while True:
            print(type(b))
            if isinstance(b, Block):
                b = b.body
            else:
                break

        return b


class Chunk(Node):
    types__ = (Block,) # type: tuple
    __match_args__ = ('body',) # type: tuple[str]
    """Define a Lua chunk.\n
       Attributes:
           body (`Block`): Chunk body.
    """

    def __init__(self, body: Block, **kwargs):
        super(Chunk, self).__init__('Chunk', **kwargs)
        self.body = body

    def __repr__(self):
        from transpile.luaparser.ast import to_pretty_str
        return to_pretty_str(self)

"""
Left Hand Side expression.
"""

class Lhs(Expression):
    """Define a Lua Left Hand Side expression."""


class Name(Lhs):
    types__ = (str,) # type: tuple
    __match_args__ = ('identifier',) # type: tuple[str]
    """Define a Lua name expression.\n
       Attributes:
           id (`string`): Id.
    """

    def __init__(self, identifier: str, **kwargs):
        super(Name, self).__init__('Name', **kwargs)
        self.id: str = identifier

class IndexNotation(Enum):
    DOT = 0
    SQUARE = 1

class Index(Lhs):
    types__ = (Expression, Name, IndexNotation) # type: tuple
    __match_args__ = ('idx', 'value', 'notation') # type: tuple[str]
    """Define a Lua index expression.\n
       Attributes:
           idx (`Expression`): Index expression.
           value (`string`): Id.
    """

    def __init__(self, idx: Expression, value: Name, notation: IndexNotation=IndexNotation.DOT, **kwargs):
        super(Index, self).__init__('Index', **kwargs)
        self.idx: Name = idx
        self.value: Expression = value
        self.notation: IndexNotation = notation

""" ----------------------------------------------------------------------- """
""" Statements                                                             """
""" ----------------------------------------------------------------------- """

class Assign(Statement):
    types__ = (List[Node], List[Node]) # type: tuple
    __match_args__ = ('targets', 'values')
    types__ = (List[Node], List[Node])
    """Lua global assignment statement.\n
       Attributes:
           targets (`list<Node>`): List of targets.
           values (`list<Node>`): List of values.\n
    """

    def __init__(self, targets: List[Node], values: List[Node], **kwargs):
        super().__init__('Assign', **kwargs)
        self.targets: List[Node] = targets
        self.values: List[Node] = values

class LocalAssign(Assign):
    types__ = (List[Node], List[Node]) # type: tuple
    __match_args__ = ('targets', 'values') # type: tuple[str]
    """Lua local assignment statement.\n
       Attributes:
           targets (`list<Node>`): List of targets.
           values (`list<Node>`): List of values.
    """

    def __init__(self, targets: List[Node], values: List[Node], **kwargs):
        super().__init__(targets, values, **kwargs)
        self._name: str = 'LocalAssign'

class While(Statement):
    types__ = (Expression, Block) # type: tuple
    __match_args__ = ('test', 'body') # type: tuple[str]
    """Lua while statement.\n
       Attributes:
           test (`Node`): Expression to test.
           body (`Block`): List of statements to execute.
    """

    def __init__(self, test: Expression, body: Block, **kwargs):
        super().__init__('While', **kwargs)
        self.test: Expression = test
        self.body: Block = body


class Do(Statement):
    types__ = (Block,) # type: tuple
    __match_args__ = ('body',) # type: tuple[str]
    """Lua do end statement.\n
       Attributes:
           body (`Block`): List of statements to execute.
    """

    def __init__(self, body: Block, **kwargs):
        super().__init__('Do', **kwargs)
        self.body: Block = body


class Repeat(Statement):
    types__ = (Block, Expression) # type: tuple
    __match_args__ = ('body', 'test') # type: tuple[str]
    """Lua repeat until statement.\n
       Attributes:
           test (`Node`): Expression to test.
           body (`Block`): List of statements to execute.
    """

    def __init__(self, body: Block, test: Expression, **kwargs):
        super().__init__('Repeat', **kwargs)
        self.body: Block = body
        self.test: Expression = test

class _ElseIf:
    ...

class ElseIf(Statement):
    types__ = (Node, Block, List[Statement] | _ElseIf) # type: tuple
    __match_args__ = ('test', 'body', 'orelse') # type: tuple[str]
    """Define the elseif lua statement.

    Attributes:
        test (`Node`): Expression to test.
        body (`list<Statement>`): List of statements to execute if test is true.
        orelse (`list<Statement> or ElseIf`): List of statements or ElseIf if test is false.
    """

    def __init__(self, test: Node, body: Block, orelse, **kwargs):
        super().__init__("ElseIf", **kwargs)
        self.test: Node = test
        self.body: Block = body
        self.orelse = orelse


class If(Statement):
    types__ = (Expression, Block, List[Statement] | ElseIf) # type: tuple
    __match_args__ = ('test', 'body', 'orelse') # type: tuple[str]
    """Lua if statement.\n
       Attributes:
           test (`Node`): Expression to test.
           body (`Block`): List of statements to execute if test is true.
           orelse (`list<Statement> or ElseIf`): List of statements or ElseIf if test if false.
    """

    def __init__(self, test: Expression, body: Block, orelse: List[Statement] | ElseIf, **kwargs):
        super().__init__('If', **kwargs)
        self.test: Expression = test
        self.body: Block = body
        self.orelse = orelse

class Label(Statement):
    types__ = (Name,) # type: tuple
    __match_args__ = ('label_id',) # type: tuple[str]
    """Define the label lua statement.\n
       Attributes:
           id (`Name`): Label name.
    """

    def __init__(self, label_id: Name, **kwargs):
        super(Label, self).__init__('Label', **kwargs)
        self.id: Name = label_id

class Goto(Statement):
    types__ = (Name,) # type: tuple
    __match_args__ = ('label',) # type: tuple[str]
    """Define the goto lua statement.\n
       Attributes:
           label (`Name`): Label node.
    """

    def __init__(self, label: Name, **kwargs):
        super(Goto, self).__init__('Goto', **kwargs)
        self.label: Name = label

class SemiColon(Statement):
    types__ = () # type: tuple
    __match_args__ = () # type: tuple[str]
    """Define the semi-colon lua statement."""

    def __init__(self, **kwargs):
        super(SemiColon, self).__init__('SemiColon', **kwargs)

class Break(Statement):
    types__ = () # type: tuple
    __match_args__ = () # type: tuple[str]
    """Define the break lua statement."""

    def __init__(self, **kwargs):
        super(Break, self).__init__('Break', **kwargs)

class Fornum(Statement):
    types__ = (Name, Expression, Expression, Expression, Block) # type: tuple
    __match_args__ = ('target', 'start', 'stop', 'step', 'body') # type: tuple[str]
    """Define the numeric for lua statement.\n
       Attributes:
           target (`Name`): Target name.
           start (`Expression`): Start index value.
           stop (`Expression`): Stop index value.
           step (`Expression`): Step value.
           body (`Block`): List of statements to execute.
    """

    def __init__(self, target: Name, start: Expression, stop: Expression, step: Expression, body: Block, **kwargs):
        super(Fornum, self).__init__('Fornum', **kwargs)
        self.target: Name = target
        self.start: Expression = start
        self.stop: Expression = stop
        self.step: Expression = step
        self.body: Block = body

class Forin(Statement):
    types__ = (Block, List[Expression], List[Name]) # type: tuple
    __match_args__ = ('body', 'iter', 'targets') # type: tuple[str]
    """Define the for in lua statement.\n
       Attributes:
           body (`Block`): List of statements to execute.
           iter (`list<Expression>`): Iterable expressions.
           targets (`list<Name>`): Start index value.
    """

    def __init__(self, body: Block, iter: List[Expression], targets: List[Name], **kwargs):
        super(Forin, self).__init__('Forin', **kwargs)
        self.body: Block = body
        self.iter: List[Expression] = iter
        self.targets: List[Name] = targets

class Call(Statement):
    types__ = (Expression, List[Expression]) # type: tuple
    __match_args__ = ('func', 'args') # type: tuple[str]
    """Define the function call lua statement.\n
       Attributes:
           func (`Expression`): Function to call.
           args (`list<Expression>`): Function call arguments.
    """

    def __init__(self, func: Expression, args: List[Expression], **kwargs):
        super(Call, self).__init__('Call', **kwargs)
        self.func: Expression = func
        self.args: List[Expression] = args

class Invoke(Statement):
    __match_args__ = ('source', 'func', 'args') # type: tuple[str]
    
    """Define the invoke function call lua statement (magic syntax with ':').\n
       Attributes:
           source (`Expression`): Source expression where function is invoked.
           func (`Expression`): Function to call.
           args (`list<Expression>`): Function call arguments.
    """

    def __init__(self, source: Expression, func: Expression, args: List[Expression], **kwargs):
        super(Invoke, self).__init__('Invoke', **kwargs)
        self.source: Expression = source
        self.func: Expression = func
        self.args: List[Expression] = args
        self.types__ = [type(getattr(self, t)) for t in self.__match_args__]

class Function(Statement):
    types__ = (Expression, List[Expression], Block) # type: tuple
    __match_args__ = ('name', 'args', 'body') # type: tuple[str]
    """Define the Lua function declaration statement.\n
       Attributes:
           name (`Expression`): Function name.
           args (`list<Expression>`): Function arguments.
           body (`Block`): List of statements to execute.
    """

    def __init__(self, name: Expression, args: List[Expression], body: Block, **kwargs):
        super(Function, self).__init__('Function', **kwargs)
        self.name: Expression = name
        self.args: List[Expression] = args
        self.body: Block = body

class LocalFunction(Statement):
    types__ = (Expression, List[Expression], Block) # type: tuple
    __match_args__ = ('name', 'args', 'body') # type: tuple[str]
    """Define the Lua local function declaration statement.\n
       Attributes:
           name (`Expression`): Function name.
           args (`list<Expression>`): Function arguments.
           body (`list<Statement>`): List of statements to execute.
    """

    def __init__(self, name: Expression, args: List[Expression], body: Block, **kwargs):
        super(LocalFunction, self).__init__('LocalFunction', **kwargs)
        self.name: Expression = name
        self.args: List[Expression] = args
        self.body: Block = body

class Method(Statement):
    types__ = (Expression, Expression, List[Expression], Block) # type: tuple
    __match_args__ = ('source', 'name', 'args', 'body') # type: tuple[str]
    """Define the Lua Object Oriented function statement.\n
       Attributes:
           source (`Expression`): Source expression where method is defined.
           name (`Expression`): Function name.
           args (`list<Expression>`): Function arguments.
           body (`Block`): List of statements to execute.
    """

    def __init__(self, source: Expression, name: Expression, args: List[Expression], body: Block, **kwargs):
        super(Method, self).__init__('Method', **kwargs)
        self.source: Expression = source
        self.name: Expression = name
        self.args: List[Expression] = args
        self.body: Block = body

class Return(Statement):

    """Define the Lua return statement.

    Attributes:
        values (`list<Expression>`): Values to return.
    """

    def __init__(self, values, **kwargs):
        super(Return, self).__init__("Return", **kwargs)
        self.values = values
        
""" ----------------------------------------------------------------------- """
""" Lua Expression                                                         """
""" ----------------------------------------------------------------------- """

""" ----------------------------------------------------------------------- """
""" Types and values                                                       """
""" ----------------------------------------------------------------------- """


class Nil(Expression):
    types__ = () # type: tuple
    __match_args__ = () # type: tuple[str]
    """Define the Lua nil expression."""

    def __init__(self, **kwargs):
        super(Nil, self).__init__('Nil', **kwargs)

class TrueExpr(Expression):
    types__ = () # type: tuple
    __match_args__ = () # type: tuple[str]
    """Define the Lua true expression."""

    def __init__(self, **kwargs):
        super(TrueExpr, self).__init__('True', **kwargs)


class FalseExpr(Expression):
    types__ = () # type: tuple
    __match_args__ = () # type: tuple[str]
    """Define the Lua false expression."""

    def __init__(self, **kwargs):
        super(FalseExpr, self).__init__('False', **kwargs)

NumberType = int | float

class Number(Expression):
    types__ = (NumberType,) # type: tuple
    __match_args__ = ('n',) # type: tuple[str]

    """Define the Lua number expression.
       Attributes:
           n (`int|float`): Numeric value.
    """

    def __init__(self, n: NumberType, **kwargs):
        super(Number, self).__init__('Number', **kwargs)
        self.n: NumberType = n

class Varargs(Expression):
    types__ = () # type: tuple
    __match_args__ = () # type: tuple[str]
    """Define the Lua Varargs expression (...)."""

    def __init__(self, **kwargs):
        super(Varargs, self).__init__('Varargs', **kwargs)


class StringDelimiter(Enum):
    SINGLE_QUOTE = 0
    DOUBLE_QUOTE = 1
    DOUBLE_SQUARE = 2


class String(Expression):
    types__ = (str, StringDelimiter) # type: tuple
    __match_args__ = ('s', 'delimiter') # type: tuple[str]
    """Define the Lua string expression.
       Attributes:
           s (`string`): String value.
           delimiter (`StringDelimiter`): The string delimiter
    """

    def __init__(self, s: str, delimiter: StringDelimiter=StringDelimiter.SINGLE_QUOTE, **kwargs):
        super(String, self).__init__('String', **kwargs)
        self.s: str = s
        self.delimiter: StringDelimiter = delimiter


class Field(Expression):
    types__ = (Expression, Expression, bool) # type: tuple
    __match_args__ = ('key', 'value', 'between_brackets') # type: tuple[str]
    """Define a lua table field expression\n
       Attributes:
           key (`Expression`): Key.
           value (`Expression`): Value.
    """

    def __init__(self, key: Expression, value: Expression, between_brackets: bool=False, **kwargs):
        super().__init__('Field', **kwargs)
        self.key: Expression = key
        self.value: Expression = value
        self.between_brackets: bool = between_brackets


class Table(Expression):
    types__ = (List[Field],) # type: tuple
    __match_args__ = ('fields',) # type: tuple[str]
    """Define the Lua table expression.\n
       Attributes:
           fields (`list<Field>`): Table fields.
    """

    def __init__(self, fields: List[Field], **kwargs):
        super().__init__('Table', **kwargs)
        self.fields: List[Field] = fields

class Dots(Expression):
    types__ = () # type: tuple
    __match_args__ = () # type: tuple[str]
    """Define the Lua dots (...) expression."""

    def __init__(self, **kwargs):
        super().__init__('Dots', **kwargs)

class AnonymousFunction(Expression):
    types__ = (List[Expression], Block) # type: tuple
    __match_args__ = ('args', 'body') # type: tuple[str]
    """Define the Lua anonymous function expression.\n
       Attributes:
           args (`list<Expression>`): Function arguments.
           body (`Block`): List of statements to execute.
    """

    def __init__(self, args: List[Expression], body: Block, **kwargs):
        super(AnonymousFunction, self).__init__('AnonymousFunction', **kwargs)
        self.args: List[Expression] = args
        self.body: Block = body

""" ----------------------------------------------------------------------- """
""" Operators                                                              """
""" ----------------------------------------------------------------------- """

class Op(Expression):
    """Base class for Lua operators."""


class BinaryOp(Op):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Base class for Lua 'Left Op Right' Operators.

    Attributes:
        left (`Expression`): Left expression.
        right (`Expression`): Right expression.
    """

    def __init__(self, name, left: Expression, right: Expression, **kwargs):
        super(BinaryOp, self).__init__(name, **kwargs)
        self.left: Expression = left
        self.right: Expression = right

class AriOp(BinaryOp):
    """Base class for Arithmetic Operators"""

class AddOp(AriOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Add expression.
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('AddOp', left, right, **kwargs)

class SubOp(AriOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Substract expression.\n
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('SubOp', left, right, **kwargs)

class MultOp(AriOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Multiplication expression.\n
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('MultOp', left, right, **kwargs)

class FloatDivOp(AriOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Float division expression.\n
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('FloatDivOp', left, right, **kwargs)

class FloorDivOp(AriOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Floor division expression.\n
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('FloorDivOp', left, right, **kwargs)

class ModOp(AriOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Modulo expression.\n
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('ModOp', left, right, **kwargs)

class ExpoOp(AriOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Exponent expression.\n
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('ExpoOp', left, right, **kwargs)



class BitOp(BinaryOp):
    """Base class for bitwise Operators."""

class BAndOp(BitOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Bitwise and expression.\n
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('BAndOp', left, right, **kwargs)

class BOrOp(BitOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Bitwise or expression.\n
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('BOrOp', left, right, **kwargs)

class BXorOp(BitOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Bitwise xor expression.\n
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('BXorOp', left, right, **kwargs)

class BShiftROp(BitOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Bitwise right shift expression.\n
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('BShiftROp', left, right, **kwargs)

class BShiftLOp(BitOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Bitwise left shift expression.\n
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('BShiftLOp', left, right, **kwargs)

""" ----------------------------------------------------------------------- """
""" 3.4.4 – Relational Operators                                           """
""" ----------------------------------------------------------------------- """

class RelOp(BinaryOp):...
"""Base class for Lua relational operators."""

class LessThanOp(RelOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Less than expression.\n
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('RLtOp', left, right, **kwargs)

class GreaterThanOp(RelOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Greater than expression.\n
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('RGtOp', left, right, **kwargs)

class LessOrEqThanOp(RelOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Less or equal expression.\n
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('RLtEqOp', left, right, **kwargs)

class GreaterOrEqThanOp(RelOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Greater or equal expression.\n
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('RGtEqOp', left, right, **kwargs)

class EqToOp(RelOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Equal to expression.\n
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('REqOp', left, right, **kwargs)

class NotEqToOp(RelOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Not equal to expression.\n
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('RNotEqOp', left, right, **kwargs)

""" ----------------------------------------------------------------------- """
""" 3.4.5 – Logical Operators                                              """
""" ----------------------------------------------------------------------- """

class LoOp(BinaryOp):
    """Base class for logical operators."""

class AndLoOp(LoOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Logical and expression.\n
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('LAndOp', left, right, **kwargs)

class OrLoOp(LoOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Logical or expression.\n
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('LOrOp', left, right, **kwargs)

""" ----------------------------------------------------------------------- """
""" 3.4.6 Concat operators                                                 """
""" ----------------------------------------------------------------------- """

class Concat(BinaryOp):
    types__ = (Expression, Expression) # type: tuple
    __match_args__ = ('left', 'right') # type: tuple[str]
    """Concat expression.\n
       Attributes:
           left (`Expression`): Left expression.
           right (`Expression`): Right expression.
    """

    def __init__(self, left: Expression, right: Expression, **kwargs):
        super().__init__('Concat', left, right, **kwargs)

""" ----------------------------------------------------------------------- """
""" Unary operators                                                        """
""" ----------------------------------------------------------------------- """

class UnaryOp(Expression):
    types__ = (str, Expression) # type: tuple
    __match_args__ = ('name', 'operand') # type: tuple[str]
    """Base class for Lua unitary operator.\n
       Attributes:
           operand (`Expression`): Operand.
    """

    def __init__(self, name: str, operand: Expression, **kwargs):
        super().__init__(name, **kwargs)
        self.operand = operand

class UMinusOp(UnaryOp):
    types__ = (Expression,) # type: tuple
    __match_args__ = ('operand',) # type: tuple[str]
    """Lua minus unitary operator.\n
       Attributes:
           operand (`Expression`): Operand.
    """

    def __init__(self, operand: Expression, **kwargs):
        super().__init__('UMinusOp', operand, **kwargs)

class UBNotOp(UnaryOp):
    types__ = (Expression,) # type: tuple
    __match_args__ = ('operand',) # type: tuple[str]
    """Lua binary not unitary operator.\n
       Attributes:
           operand (`Expression`): Operand.
    """

    def __init__(self, operand: Expression, **kwargs):
        super().__init__('UBNotOp', operand, **kwargs)

class ULNotOp(UnaryOp):
    types__ = (Expression,) # type: tuple
    __match_args__ = ('operand',) # type: tuple[str]
    """Logical not operator.\n
       Attributes:
           operand (`Expression`): Operand.
    """

    def __init__(self, operand: Expression, **kwargs):
        super().__init__('ULNotOp', operand, **kwargs)

""" ----------------------------------------------------------------------- """
""" 3.4.7 – The Length Operator                                             """
""" ----------------------------------------------------------------------- """

class ULengthOP(UnaryOp):
    types__ = (Expression,) # type: tuple
    __match_args__ = ('operand',) # type: tuple[str]
    """Length operator."""

    def __init__(self, operand: Expression, **kwargs):
        super().__init__('ULengthOp', operand, **kwargs)


"""-------------------------------------------------------------------------"""
"""               POLYMORPHISM                                              """
"""-------------------------------------------------------------------------"""

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
        self.id:str = "self.__class__"

class Require(Statement):
    def __init__(self, func: Name, args: List[Expression], **kwargs):
        super(Require, self).__init__("Require", **kwargs)
        self.func = func 
        self.args: list[str] = [arg.s for arg in args if isinstance(arg, String)]

class MethodCall(Statement):
    __match_args__ = ("source", "func", "args")
    def __init__(self, source: Expression, func: Expression, args: List[Expression], **kwargs):
        super(MethodCall, self).__init__("MethodCall", **kwargs)
        self.source = source
        self.func = func
        self.args = args

class Initializer(Statement):
    __match_args__ = ("source", "name", "args", "body")
    def __init__(self, source: Expression, name: Name, args: List[Expression], body: list[Statement], **kwargs):
        super(Initializer, self).__init__("Initializer", **kwargs)
        self.source = source
        self.name = name
        self.args = args
        self.body: list[Statement] = body
        if isinstance(self.body, Block):
            self.body = body.body
        self.name.id = "__init__"

class Base(Expression):
    def __init__(self, string:str, **kwargs):
        super(Base, self).__init__("Base", **kwargs)
        name = string.split(":")[0]
        if name == "Object":
            name = name.lower()
        self.name: str = name

class Constructor(Statement):
    """ Class Constructor Statement

    Bases:
        Statement (Statement): Base class
    
    """

    def __init__(self, targets: List[Node], values: List[Node], **kwargs):

        super(Constructor, self).__init__("Constructor", **kwargs)
        self.targets: List[Node] = targets
        self.values: List[Node] = values
        self.bases: List[Base] = []
        self.names = [node for node in self.targets if isinstance(node, (Name, Call))]
        self.name = self.names[0].id
        # extend(base)
        for node in self.values:
            if isinstance(node, Invoke) and isinstance(node.source, Name):
                self.bases.append(Base(node.source.id))
            
class SuperMethod(Statement):
    __match_args__ = ("func", "args", "super_args")
    def __init__(self, func:Name, args:list[Name], super_args: list[Name], **kwargs):
        super(SuperMethod, self).__init__("SuperMethod", **kwargs)
        self.func = func
        self.args = args
        self.super_args = super_args


# TODO make these creatable in the builder.py file

class InstanceMethodCall(Statement):
    def __init__(self, source: Index, func: Name, args: list[Name], **kwargs) -> None:
        super(InstanceMethodCall, self).__init__("InstanceMethodCall", **kwargs)
        self.source = source
        self.func = func
        self.args = args
        
class ForEnumerate(Statement):
    __match_args__ = ("targets", "iterator", "body")
    def __init__(self, targets: List[Name], iterator: Name, body:list[Statement], **kwargs) -> None:
        super(ForEnumerate, self).__init__("ForEnumerate", **kwargs)
        self.targets: List[Name] = targets
        self.iterator: Name = iterator
        self.body: list[Statement] = body
        self.orelse = []

