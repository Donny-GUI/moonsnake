import argparse
import textwrap
from rich.status import Status
from typing import Callable
from sys import argv


def printerror(message):
    print(f"[\033[31m\033[1mERROR\033[0m] {message}")

def parser():
    parser = argparse.ArgumentParser(
                        prog='moonsnake',
                        description=textwrap.dedent('''\
            Transpile \033[34mLua\033[0m Files and Projects To \033[36mPython\033[33m3.11+\033[0m
        '''),   
                        epilog='Supports 3.12+ python and Lua 5+',
                        usage= '%(prog)s [PATH] [FLAGS]',
                        argument_default= None,
                        add_help= True,
                        allow_abbrev= True,
                        exit_on_error=False)
    parser.add_argument(metavar="PATH",
                        action="store",
                        dest="dest",
                        help="path to target directory or file",
                        )
    parser.add_argument('-o', 
                        '-output-path',
                        action="store_const",
                        help="flag for specifying the output directory or path, if none is given one will be made",
                        required=False
                        )
    parser.add_argument('-v', 
                        '--verbose',
                        dest="verbose",
                        action='store_true',
                        required=False
                        ) 
    args = parser.parse_args(argv)
    print(args)
    return parser
    
parser()