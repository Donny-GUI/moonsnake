import os
from pathlib import Path
from typing import TypeVar
import functools
from ast import parse



WindowsPath = TypeVar("WindowsPath", str, Path)


def filename(path: str):
    return os.path.basename(path).split(".")[0]


def set_extension(path: str, extension: str):
    if extension.startswith(".") != True:
        extension = "." + extension
    return path.rsplit(".")[0] + extension


def extension(path: str):
    return os.path.splitext(path)[1]


def unique_filename(path: str):

    def make_filename(filepath: str, index: int = None):
        ext = extension(filepath)
        file = filename(filepath)

        if index:
            file = file.rsplit("_")[0]
            file += "_" + str(index)
        file = file + ext

        return os.path.join(os.getcwd(), file)

    count = 0
    while True:
        # stop if the filename is unique
        if os.path.exists(path) == False:
            break
        # increment the ending number if not
        count += 1
        path = make_filename(path, count)

    return path


def directory_files_by_extension(
    directory: WindowsPath = f"C:\\Users\\{os.getlogin()}\\Desktop",
    extension: str = ".lua",
):

    files = []
    for root, _, fs in os.walk(directory):
        for file in fs:
            if file.endswith(extension):
                files.append(os.path.join(root, file))
    return files


def delete_files_in_directory(directory: str = ".\\converted\\"):
    for root, dirs, files in os.walk(directory):
        for file in files:
            os.remove(os.path.join(root, file))


def update(object="", action="", message=""):
    if object != "":
        object = "[\033[32m" + object + "\033[0m]"
    if action != "":
        action = "[\033[34m" + action + "\033[0m]"
    print(f"{object}{action}: {message}")


def logcall(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Log function name and arguments
        print(f"\n[Function] {func.__name__}")
        print(f"   Arguments: args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        print(f"   Returned : {result}")

        return result

    return wrapper

def comment_lines(filepath: str, line_numbers: list[int]) -> str:
    """
    Comments out the specified lines in a file, preserving the original indentation.

    Args:
        filepath (str): The path to the file.
        line_numbers (list[int]): A list of line numbers to comment out (1-based index).

    Returns:
        str: The modified content of the file with the specified lines commented out.
    """
    # Read the file lines
    with open(filepath, 'r') as file:
        lines = file.readlines()

    # Ensure all line numbers are within the valid range
    if any(line < 1 or line > len(lines) for line in line_numbers):
        raise ValueError("One or more line numbers are out of range")

    # Comment out each specified line, preserving indentation
    for line_number in line_numbers:
        original_line = lines[line_number - 1]
        leading_whitespace = len(original_line) - len(original_line.lstrip())
        lines[line_number - 1] = (' ' * leading_whitespace) + '#' + original_line.lstrip()

    # Join the lines back into a single string
    modified_content = ''.join(lines)

    return modified_content


def parsable(string: str) -> bool:
    try:
        parse(string)
        return True
    except:
        return False

    