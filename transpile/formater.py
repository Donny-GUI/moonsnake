import re
import ast
import os
import ast
from copy import copy
import black
from pathlib import Path

indentation = r"^(?P<statement>.*:)\n(?P<indentation>(?:[ \t]+.*\n)*?)^(?P<next_statement>.*:)$"


def insert_newline_after_operator(code: str):
    # Define the regex pattern
    pattern = re.compile(r'\n(\s*)(\w+)\s*=\s*(\w+)\s*([+\-*/%])\s(\d+)\s(\w+)')
    
    # Define the replacement pattern
    replacement = r'\n\1\2 = \3 \4 \5 \n\1\6'
    
    # Perform the substitution
    result = pattern.sub(replacement, code)
    
    return result


def fix_digit_space(code:str):
    pattern = r"(\s+)([A-Za-z][A-Za-z0-9_\s]*[\=\+-]+)(\s+\d+\s+)\s([^\n]+)"
    for x in re.findall(pattern, code):
        print(x)
    return re.sub(pattern, r"\1\2\3\n\1\4", code)

def apply_black(file_path:str):
    black.format_file_in_place(Path(file_path), fast=False, mode=black.Mode())

def any_except(exception:str):
    return rf"[^{exception}]"

def match_name(name:str, pattern):
    return rf"(?P<{name}>{pattern})"

def fix_digit_name_thing(code:str):
    pattern = r"^(?P<indent>\s+)(?P<lhs>.+\d*\s)(?P<nextline>\w+)$"
    for match in re.finditer(pattern, code):
        indent = match.group("indent")
        lhs = match.group("lhs")
        nextline = match.group("nextline")
        code.replace(code[match.start():match.end()], f"{indent}{lhs}\n{indent}{indent}{nextline}")
        
    return code

def add_semicolons_to_statements(code):
    # Define the regex pattern to match function calls
    pattern = r'(\)\s*)(?=\w+\()'
    
    # Perform the substitution to add semicolons
    result = re.sub(pattern, r'\1;', code)
    
    return result

def fix_multicall_placement(code):
    # Define the regex pattern
    pattern = rf'(\s+)({optional(r"\w+\s*\=\s*")})\s*(\w+\(.+\))(\w+)'
    
    # Function to format the replacement
    def replacement(match):
        tab = match.group(1).strip()
        optional_assign = match.group(2)
        first_call = match.group(3).strip()
        second_name = match.group(4).strip()
        
        # Return the first statement followed by a newline and the second statement indented
        return f"{tab}{optional_assign}{first_call}\n{tab}{second_name}"

    # Perform the substitution
    return re.sub(pattern, replacement, code)

def fix_same_line_calls_with_functions(code: str):
    """
    Fixes the same line calls with functions in the given code.

    Args:
        code (str): The code to fix.

    Returns:
        str: The code with the same line calls with functions formatted for proper indentation.
    """
    # Define the regex pattern
    pattern = r'(def\s+\w+\s*\(.*?\)\s*:)(\w+\(.*?\))+'
    
    # Function to format the replacement
    def replacement(match):
        """
        Formats the matched function definition and function calls for proper indentation.

        Args:
            match (re.Match): The regular expression match object.

        Returns:
            str: The formatted function definition and function calls.
        """
        # Extract the function definition and function calls from the match object
        func_def = match.group(1)  # Function definition
        calls = match.group(2)  # Function calls

        # Use regular expressions to find all function calls within the calls string
        formatted_calls = "\n    ".join(re.findall(r'\w+\(.*?\)', calls))

        # Format the function definition and function calls with proper indentation
        return f"{func_def}\n    {formatted_calls}"
    
    # Perform the substitution
    return re.sub(pattern, replacement, code)

def optional(pattern):
    """
    Returns a pattern that matches the provided pattern zero or one times.

    Args:
        pattern (str): The pattern to make optional.

    Returns:
        str: A pattern that matches the provided pattern zero or one times.
    """
    # The syntax (?:pattern) is a non-capturing group.
    # The ? after the group makes it optional.
    # The non-capturing group is used to avoid capturing the pattern.

    return f"(?:{pattern})?"

def fix_string_quote_errors(code):
    double_quote = r"'" + r'"(.+)"' + r"'"
    # Remove quotes around string literals
    code = re.sub(double_quote, r"'\1'", code)

    return code

def fix_dot_call_errors(code):
    return re.sub(r"([\w\.]+)\.\(", r"\1(", code)


def fix_digit_no_space(string: str):
    pattern = r"(\w+)(\.+)\w(\+|\-)\w(d+)([A-Za-z_\.\(\)])"

    def replace_pattern(match):
        tab = match.group(1)
        middle = match.group(2)
        sign = match.group(3)
        digit = match.group(4)
        nl = match.group(5)

        return f"{tab}{middle} {sign} {digit}\n{tab}{nl}"

    result = re.sub(pattern, replace_pattern, string)
    return result


def fix_kv_pairs(string: str):
    p = r"for\s(kv|k|v|_v|_k)\sin\s"
    string = re.sub(p, r"for k, v in ", string)
    return string


def fix_ipairs(string: str):
    pattern = r"\sin\sipairs\("
    string = re.sub(pattern, r" in enumerate(", string)
    return string


def indexing_table_fix(string: str):
    """
    Finds occurrences of patterns like '2[self.loc_debuff_lines] = '
    and swaps the word inside the brackets with the digit outside the brackets.

    Args:
        string (str): The input string containing the patterns to be modified.

    Returns:
        str: The modified string with swapped patterns.
    """

    def replace_pattern(match):
        """
        Replace the matched pattern with the swapped version.

        Args:
            match (re.Match): The regex match object.

        Returns:
            str: The modified string with the swapped values.
        """
        digit = match.group(1)
        word = match.group(2)
        return f"{word}[{digit}] = "

    # Define the regex pattern
    pattern = r"(\d+)\[(\w+)\] = "

    # Use re.sub to replace all occurrences using the replace_pattern function
    result = re.sub(pattern, replace_pattern, string)

    return result


def indexing_table_fix_string(string: str):
    """
    Finds occurrences of patterns like '2[self.loc_debuff_lines] = '
    and swaps the word inside the brackets with the digit outside the brackets.

    Args:
        string (str): The input string containing the patterns to be modified.

    Returns:
        str: The modified string with swapped patterns.
    """

    def replace_pattern(match):
        """
        Replace the matched pattern with the swapped version.

        Args:
            match (re.Match): The regex match object.

        Returns:
            str: The modified string with the swapped values.
        """
        string = match.group(1)
        name = match.group(2)
        return f"{name}[{string}]"

    # Define the regex pattern
    pattern = r"('\w+')\[(\w+)\]"

    # Use re.sub to replace all occurrences using the replace_pattern function
    try:
        result = re.sub(pattern, replace_pattern, string)
    except:
        pass
    return result


def integer_floating_fix(string: str) -> str:
    """
    Fixes the formatting of numeric and floating-point literals in the given string.

    This function searches for patterns where a digit is followed by an uppercase letter and a lowercase
    letter sequence ending with a period. It inserts a space after the digit to improve readability.

    Args:
        string (str): The input string to be fixed.

    Returns:
        str: The modified string with the fixed formatting.
    """
    pattern = r"\d[A-Z][a-z]+\."
    patsearch = re.search(pattern, string)
    if patsearch:
        start, stop = patsearch.span()
        string = string[: start + 1] + " " + string[start + 1 :]
    return string


def index_fix(string: str) -> str:
    """
    Fixes the indexing syntax in the given string.

    This function searches for patterns where a string literal contains indexing brackets. It reformats
    the indexing syntax to a more readable form.

    Args:
        string (str): The input string to be fixed.

    Returns:
        str: The modified string with corrected indexing syntax.
    """
    matching = r"\'.+\[.+\]\'"
    pattern = r"\'(.+)\[(.+)\]\'"
    patsearch = re.search(pattern, string)
    if patsearch:
        digit = patsearch.group(1)
        object = patsearch.group(2)
        string = re.sub(matching, f"{object}[{digit}]", string)
    return string


def digit_fix(string: str):
    pattern = r"(\d+)\[(.+)\]\s=\s"

    def replace_pattern(match):
        x = match.group(1)
        y = match.group(2)
        return rf"{y}[{x}] = "

    # Use re.sub to replace all occurrences using the replace_pattern function
    try:
        result = re.sub(pattern, replace_pattern, string)
    except:
        pass

    return result


def extract_method_arguments(method_string: str) -> str:
    """
    Extracts the arguments from a method definition string.

    This function uses regex to capture and return the arguments of a method from a method definition string.

    Args:
        method_string (str): The string containing the method definition.

    Returns:
        str: A string of the method arguments, or None if no arguments are found.
    """
    pattern = r"def\s+\w+\s*\(\s*([^)]+)\s*\):"

    if isinstance(method_string, list):
        return ""
    match = re.search(pattern, method_string)
    if match:
        return match.group(1)
    return None


def fix_supers(string: str) -> str:
    """
    Fixes the usage of `super()` in the given string.

    This function searches for occurrences of super calls and reformats them to include method arguments.

    Args:
        string (str): The input string to be fixed.

    Returns:
        str: The modified string with fixed super calls.
    """
    superfind = r"\:[A-Z][a-z]+\.[a-z]+\(.*\)"
    argfind = extract_method_arguments(string)
    if argfind == "":
        return string 
    string = re.sub(superfind, f":\n        super().__init__({argfind})", string)
    return string


def fix_bases_init(string: str, class_ast: ast.ClassDef) -> str:
    """
    Fixes the base class initializations in the given string based on the provided class AST.

    This function searches for base class names and updates their initialization calls with the correct arguments.

    Args:
        string (str): The input string to be fixed.
        class_ast (ast.ClassDef): The AST representation of the class.

    Returns:
        str: The modified string with corrected base class initializations.
    """
    names = [base.id for base in class_ast.bases]
    for name in names:
        pat = name + r"\.[a-z]\(.*\)"
        argfind = extract_method_arguments(string)
        string = re.sub(pat, f"\n        super().__init__({argfind})", string)
    return string


class SourceWriter:
    def __init__(self) -> None:
        """
        Initializes a new SourceWriter instance with empty source and nodes lists.
        """
        self.source = []
        self.nodes = []

    def make_directory(self, dir: str) -> None:
        """
        Creates a directory at the specified path if it does not already exist.

        Args:
            dir (str): The path of the directory to be created.
        """
        os.makedirs(dir, exist_ok=True)

    def fix(self, string: str, node: ast.AST) -> str:
        """
        Applies a series of fixes to the given string based on the provided AST node.

        Args:
            string (str): The input string to be fixed.
            node (ast.AST): The AST node used to apply specific fixes.

        Returns:
            str: The modified string after applying all fixes.
        """
        source = fix_supers(string)
        source = index_fix(source)
        source = source.replace(" 'True'", " True")
        if isinstance(node, ast.ClassDef):
            source = fix_bases_init(source, node)
        source = integer_floating_fix(source)
        source = indexing_table_fix(source)
        source = fix_digit_no_space(source)
        source = fix_kv_pairs(source)
        source = fix_ipairs(source)
        source = indexing_table_fix_string(source)
        source = fix_string_quote_errors(source)
        source = fix_dot_call_errors(source)
        source = fix_same_line_calls_with_functions(source)
        source = fix_multicall_placement(source)
        source = add_semicolons_to_statements(source)
        source = fix_digit_name_thing(source)
        #source = digit_fix(source)
        #source = fix_digit_space(source)
        source = insert_newline_after_operator(source)
        source = black.format_str(source)
        return source

    def add(self, node: ast.AST, source: str) -> None:
        """
        Adds a new node and its corresponding source code to the SourceWriter.

        Args:
            node (ast.AST): The AST node to be added.
            source (str): The source code associated with the node.
        """
        self.nodes.append(node)
        source = fix_supers(source)
        source = index_fix(source)
        source = source.replace(" 'True'", " True")
        if isinstance(node, ast.ClassDef):
            source = fix_bases_init(source, node)
        source = integer_floating_fix(source)
        source = indexing_table_fix(source)
        source = fix_digit_no_space(source)
        source = fix_kv_pairs(source)
        source = fix_ipairs(source)
        source = indexing_table_fix_string(source)
        source = fix_string_quote_errors(source)
        source = fix_dot_call_errors(source)
        source = fix_same_line_calls_with_functions(source)
        source = fix_multicall_placement(source)
        source = add_semicolons_to_statements(source)
        source = insert_newline_after_operator(source)
        self.source.append(source)

        with open("temp.py", "a") as f:
            f.write(source + "\n")
            
        apply_black("temp.py")

    def clear(self) -> None:
        """
        Clears all stored source code and nodes from the SourceWriter.
        """
        self.source.clear()
        self.nodes.clear()

    def dump(self, fp=None) -> str:
        """
        Dumps the accumulated source code to a string or a file-like object.

        Args:
            fp (file-like object, optional): If provided, the source code is written to this file-like object.

        Returns:
            str: The accumulated source code as a single string.
        """
        l = "\n".join(self.source)
        if fp:
            fp.write(l)
        return l
