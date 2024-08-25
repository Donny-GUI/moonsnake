import re


lua_to_python_math = {
    "math.abs": "abs",
    "math.acos": "math.acos",
    "math.asin": "math.asin",
    "math.atan": "math.atan",
    "math.atan2": "math.atan2",
    "math.ceil": "math.ceil",
    "math.cos": "math.cos",
    "math.cosh": "math.cosh",
    "math.deg": "math.degrees",
    "math.exp": "math.exp",
    "math.floor": "math.floor",
    "math.fmod": "math.fmod",  # or "math.remainder"
    "math.frexp": "math.frexp",
    "math.huge": "float('inf')",
    "math.ldexp": "math.ldexp",
    "math.log": "math.log",
    "math.log10": "math.log10",
    "math.max": "max",
    "math.min": "min",
    "math.modf": "math.modf",
    "math.pi": "math.pi",
    "math.pow": "pow",  # or "math.pow"
    "math.rad": "math.radians",
    "math.random": "random.random",
    "math.randomseed": "random.seed",
    "math.sin": "math.sin",
    "math.sinh": "math.sinh",
    "math.sqrt": "math.sqrt",
    "math.tan": "math.tan",
    "math.tanh": "math.tanh"
}
x={
    "string.len": "len",
    "string.format": "str.format",
    "string.find": "str.find",
    "string.char": "chr",
    "string.byte": "ord",
    "string.rep": "str * n",  # Use multiplication for repetition
    "string.reverse": "str[::-1]",
    "string.sub": "str[start:end]",
    "string.lower": "str.lower",
    "string.upper": "str.upper",

}
lua_to_python_re = {
    # String functions
    "string.gmatch": "re.finditer",  # Requires regex for exact functionality
    "string.gsub": "re.sub",
    "string.match": "re.match",
}
lua_to_python_table = {
    "table.concat": "''.join",  # Use join for concatenation
    "table.insert": "list.append",  # Use append for inserting at the end
    "table.remove": "list.pop",  # Use pop for removing last element or by index
    "table.sort": "sorted",  # Use sorted for a new sorted list or list.sort for in-place
    "table.maxn": "len",  # Python list/dict doesn't have maxn, so use len
}
lua_to_python_basic = {
    # Basic functions
    "assert": "assert",
    "collectgarbage": "gc.collect",  # Python uses gc.collect for garbage collection
    "dofile": "exec(open(filename).read())",  # Execute a file (unsafe)
    "error": "raise Exception",
    "getmetatable": "Not directly available",  # Lua metatables have no direct Python equivalent
    "ipairs": "enumerate",  # For iteration with index
    "load": "eval/exec",  # Use eval or exec in Python
    "next": "next",
    "pairs": "dict.items",  # For iterating over dictionary items
    "pcall": "try-except",  # Use try-except for protected calls
    "print": "print",
    "rawequal": "==",  # Direct equality check
    "rawget": "dict.get",  # Dictionary get method
    "rawset": "dict[key] = value",  # Direct dictionary assignment
    "select": "lambda i, *args: args[i-1:]",  # Python slicing or function
    "setmetatable": "Not directly available",  # Lua metatables have no direct Python equivalent
    "tonumber": "float/int",  # Use float() or int() for number conversion
    "tostring": "str",
    "type": "type",
    "xpcall": "try-except",  # Use try-except with custom exception handling
}
lua_to_python_threading = {
    # Coroutine functions (threading in Python)
    "coroutine.create": "threading.Thread",  # Use threading for similar behavior
    "coroutine.resume": "thread.start",  # Start a thread
    "coroutine.running": "threading.current_thread",
    "coroutine.status": "thread.is_alive",  # Check if thread is alive
    #"coroutine.wrap": "Not directly available",  # Closest is threading or async
    #"coroutine.yield": "Not directly available",  # Similar to async/await or thread pausing
}
lua_to_python_tempfile = {
    # I/O functions
    "os.tmpname": "tempfile.mktemp",  # Create a temporary file name
    "io.tmpfile": "tempfile.TemporaryFile",  # Create a temporary file
}
other = {
    "io.input": "open",  # Open a file for reading
    "io.open": "open",  # Open a file
    "io.output": "open",  # Open a file for writing
    "os.exit": "sys.exit",  # Exit program
    "os.setlocale": "locale.setlocale",  # Set locale
}
lua_to_python_sys = {
    "os.exit": "sys.exit",
}

one_offs = {
    "io.output": "open",
    "io.input": "open",
    "io.open": "open",
    
}

lua_to_python_file = {
    "io.close": "file.close",  # Close a file
    "io.flush": "file.flush",  # Flush the file buffer
    "io.write": "file.write",  # Write to a file
    "io.read": "file.read",  # Read from a file
    "io.lines": "file.readlines",  # Iterate over lines in a file
}

lua_to_python_time = {   

    "os.difftime": "time.difftime",  # Difference between times
    "os.clock": "time.process_time",  # Process time
    "os.date": "time.strftime",  # Format date
    "os.time": "time.time",  # Get current time
}
lua_to_python_os = {
    "io.popen": "os.popen",  # Open a pipe to/from a command
    "os.execute": "os.system",  # Execute a system command
    "os.getenv": "os.getenv",  # Get environment variable
    "os.remove": "os.remove",  # Remove a file
    "os.rename": "os.rename",  # Rename a file
}

class LuaToPythonMapper:
    def __init__(self) -> None:
        self.string = ""
    
    def add_import(self):
        pass 
    
    def map_imports(self, source: str) -> str:
        
        self.string = source
        
        found_math = re.search(r"math\.[a-z0-9]*", self.string)
        if found_math:
            for lua, python in lua_to_python_math.items():
                self.string = self.string.replace(lua, python)
            self.string = "import math\n" + self.string
        
        found_os = re.search(r"\sos\.[a-z0-9]+", self.string)
        if found_os:
            for lua, python in lua_to_python_os.items():
                self.string = self.string.replace(lua, python)
            self.string = "import os\n" + self.string
        
        found_time = re.search(r"\s(os\.difftime|os\.clock|os\.date|os\.time)\.[a-z0-9_]+", self.string)
        if found_time:
            for lua, python in lua_to_python_time.items():
                self.string = self.string.replace(lua, python)
            self.string = "import time\n" + self.string

        found_exit = re.search(r"os\.exit", self.string)
        if found_exit:
            for lua, python in lua_to_python_sys.items():
                self.string = self.string.replace(lua, python)
            self.string = "import sys\n" + self.string
            
        garbage_found =re.search(r"collectgarbage", self.string)
        if garbage_found:
            self.string = self.string.replace("collectgarbage", "gc.collect")
            self.string = "import gc\n" + self.string
        

        # For string conversion
        self.string = self.string.replace("tostring", "str")
        
        if self.string.find("os.setlocale") != -1:
            self.string.replace("os.setlocale",  "locale.setlocale")
            self.string = "import locale\n" + self.string
        
        tempfile_search = re.compile(r"(os\.tmpname|io\.tmpfile)")
        if tempfile_search.search(self.string):
            for lua, python in lua_to_python_tempfile.items():
                self.string = self.string.replace(lua, python)
            self.string = "import tempfile\n" + self.string
        
        re_search = re.compile(r"string\.(gmatch|gsub|match)")
        if re_search.search(self.string):
            for lua, python in lua_to_python_re.items():
                self.string = self.string.replace(lua, python)
            self.string = "import re\n" + self.string
        
        
        self.string.replace(".init(", ".__init__(")
            
        return self.string
