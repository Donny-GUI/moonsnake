import ast
from dataclasses import dataclass


class TranspileError(SyntaxError):
    def __init__(self,
                 filepath: str,
                 end_lineno: int,
                 end_col_offset: int,
                 col_offset: int,
                 message: str,
                 line: int,
                 text: str,
                 args: tuple):

        self.filepath: str = filepath
        self.end_lineno: int = end_lineno
        self.end_offset: int = end_col_offset
        self.col_offset: int = col_offset
        self.message: str = message
        self.line: str = line
        self.text: str = text
        self.args: tuple = args


def test_output_string(string: str):
    """
    Test the output string from the transpiler. attempt to parse it into an ast
    then catch any errors and highlight them.

    Args:
        string (str): any python code that was transpiled
    """
    try:
        tree = ast.parse(string)
    except SyntaxError as e:
        e.text
        return TranspileError(message=e.msg, line=e.lineno)
