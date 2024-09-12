import ast
import black



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
        print(f"Error: {e}")
        formatted_code = source_code  # Return the original code if formatting fails

    return formatted_code