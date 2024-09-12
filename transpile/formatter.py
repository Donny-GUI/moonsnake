import ast
import black


def manual_formatting(source_code: str) -> str:
    lines = source_code.split("\n")
    first_thing = 0
    for index, line in enumerate(lines):
        if line.startswith("def") or line.startswith("class"):
            first_thing = index - 1
            break
    
    lines.insert(first_thing, "\n")
    
    length = len(lines) - 1
    c = 0
    while True:
        if c == length:
            break
        
        line = lines[c]
        
        if line.startswith("if __name__ == '__main__':"):
            lines.insert(c, "\n")
            length+=1
            c+=1
        
        stripped = lines[c].strip()
        if stripped.startswith("class "):
            lines.insert(c, "\n")
            length+=1
            c+=1
        
        c+=1
    
    return "\n".join(lines)
        
    

def format_python_code(source_code: str) -> str:
    """
    Formats a Python source string using ast parsing and black formatting.

    Args:
        source_code (str): The Python code to format.

    Returns:
        str: The formatted Python code.
    """
    try:
        # Parse the code with the ast module to ensure it is valid Python code
        ast.parse(source_code)
        
        # Format the code with black, using a safe mode to prevent aggressive changes
        formatted_code = black.format_str(
            source_code, mode=black.Mode(line_length=88, preview=True)
        )
    except (SyntaxError, black.InvalidInput) as e:
        # Handle parsing errors gracefully and return the original code with an error message
        formatted_code = source_code

    return formatted_code