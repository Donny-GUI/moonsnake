import re


def name_group(name: str, pattern:str):
    return rf"(?P<{name}>{pattern})"


class NamedPattern:
    def __init__(self, name: str, pattern: str):
        self.name = name
        self.pattern = name_group(self.name, pattern)

    def replace(self, repl: str, string: str):
        return re.sub(self.pattern, repl, string)    


comma_pattern = r".,(\s,)\s"
comma_repl = " None, "



class MistakeRemover:
    def __init__(self) -> None:
        self.patterns: list[str] = []
        self.replacements: dict[str, str] = {}
    
    def add(self, pattern: str, repl:str=""):
        self.patterns.append(pattern)
        self.replacements[pattern] = repl
    
    def fix(self, string: str):
        for pattern in self.patterns:
            string = re.sub(pattern, 
                            self.replacements[pattern], 
                            string)
                
        return string


mistakes = MistakeRemover()
mistakes.add(comma_pattern, " None, ")

def fix_output(string: str):


def build_pattern(str):
    from string import digits, ascii_uppercase, ascii_lowercase, punctuation, whitespace
    python_punctionation = "/\\@%~^&*()-_+={}[]|;:<>?"
    pattern = []

    for char in str:
        if char in digits:
            pattern.append(r"\d")
        elif char in ascii_uppercase:
            pattern.append(r"[A-Z]")
        elif char in ascii_lowercase:
            pattern.append(r"[a-z]")
        elif char in punctuation:
            pattern.append(r"\p")
        elif char in whitespace:
            pattern.append(r"\s")
        else:
            pattern.append(char)
    