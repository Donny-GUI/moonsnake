import re
import ast
import os


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
    names = [base.name.id for base in class_ast.bases]
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
        # source = digit_fix(source)
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
        # source = digit_fix(source)
        self.source.append(source)

        with open("temp.py", "a") as f:
            f.write(source + "\n")

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
