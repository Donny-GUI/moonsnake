import os
from pathlib import Path
from typing import TypeVar
import functools


WindowsPath = TypeVar("WindowsPath", str,Path)


def directory_files_by_extension(directory: WindowsPath=f"C:\\Users\\{os.getlogin()}\\Desktop", extension:str=".lua"):

    files = []
    for root, _, fs in os.walk(directory):
        for file in fs:
            if file.endswith(extension):
                files.append(os.path.join(root, file))
    return files

def delete_files_in_directory(directory:str=".\\converted\\"):
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
