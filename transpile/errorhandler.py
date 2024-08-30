import ast
from dataclasses import dataclass


HIGHLIGHT = "\033[46m\033[31m\033[3m"
E = "\033[0m"


def successful(object):
    return isinstance(object, Success)


class TranspileError(SyntaxError):
    def __init__(self,
                 filepath: str,
                 end_lineno: int,
                 end_col_offset: int,
                 col_offset: int,
                 message: str,
                 line: int,
                 lineno:int,
                 text: str,
                 args: tuple,
                 source:str):

        self.source = source
        self.filepath: str = filepath
        self.end_lineno: int = end_lineno
        self.end_offset: int = end_col_offset
        self.col_offset: int = col_offset
        self.message: str = message
        self.line: str = line
        self.lineno: int = lineno
        self.text: str = text
        self.args: tuple = args
        self.offender = self.source[self.col_offset-1:self.end_offset-1]
        if self.lineno == None:            
            self.lineno = self.end_lineno
            self.end_lineno+=1
    
    def get_error(self):
        return self.text
        
    def show(self):
        print("Message:  ",  self.message)
        print("Text:     ", self.text)
        print("Line:     ", self.lineno)
        print("End Line: ", self.end_lineno)
        print("Line:     ", self.line)
        print("Col Offset: ", self.col_offset)
        print("End Col Offset: ", self.end_offset)
        
    def highlight(self):
        retv = self.text
        beginning = retv[0:self.col_offset-1]
        middle = retv[self.col_offset-1:self.end_offset-1]
        end = retv[self.end_offset-1:]
        indent = " "* len(str(self.end_lineno)) + " "
        
        above = indent + " "*len(beginning) + "v"*len(middle) + " "*len(end)
        highlighted =f"{self.end_lineno}|" +  beginning + HIGHLIGHT + middle + E + end
        below = indent + " "*len(beginning) + "~"*len(middle) + " " + self.message
        
        print(above)
        print(highlighted)
        print(below)
        print(self.message)
        return highlighted
    
    def remove_error(self):
        with open(self.filepath, "r") as f:
            lines = f.readlines()

            linerange = range(self.lineno, self.end_lineno)
            comment_index = 0
            for i in linerange:
                comment_index = 0
                for char in lines[i]:
                    if char != ' ':
                        break
                    comment_index += 1
                lines[i] = lines[i][:comment_index] + f"#ERROR {self.offset} - {self.col_offset}" + lines[i][comment_index:]
        
        return "\n".join(lines)
    
        def get_indent(line):
            c = 0
            for char in line:
                if char == " ":
                    c += 1
                elif char == "\t":
                    c += 4
                else:
                    break
            return c*" "
        
        ind = get_indent(lines[self.end_lineno])
        lines.insert(self.end_lineno-1, f'{ind}"""')
        lines.insert(self.end_lineno+1, f'{ind}"""')
        
        return "\n".join(lines)
    
        

class Success:
    def __init__(self) -> None:
        print("success!")
    
    def get_error_string(self):
        return None
    
    def show(self):
        print("success")
        
    def highlight(self):
        return


def test_transpiled_file(filepath:str) -> Success|TranspileError:
    """
    Test the output string from the transpiler. attempt to parse it into an ast
    then catch any errors and highlight them.

    Args:
        string (str): any python code that was transpiled
    """
    with open(filepath, "r", errors="ignore") as f:
        string = f.read()
        
    try:
        tree = ast.parse(string)
        return Success()
    except SyntaxError as e:
        return TranspileError(filepath=filepath, 
                              end_lineno=e.end_lineno,
                              end_col_offset=e.end_offset,
                              message=e.msg,
                              lineno=e.lineno,
                              line=e.lineno, 
                              text=e.text,
                              args=e.args,
                              source=string,
                              col_offset=e.offset)



class ErrorFixer:
    def __init__(self) -> None:
        self.error = None
    
    def fix(self, terror:TranspileError):
        self.error = terror
        length = len(terror.offender)
        target_area = terror.source[terror.col_offset-1:terror.end_offset-1]