import transpile.luaparser.ast as last
import ast 


BLUE = "\033[34m"
GREEN = "\033[32m"
RED = "\033[31m"
E = "\033[0m"

def paint(string, color):
    if isinstance(string, list):
        return [paint(x, color) for x in string]
    return f"{color}{string}{E}"

def blue(string):
    return f"{BLUE}{string}{E}"

def make_astwriter_method(node, name, attr):
    return ast.Assign(targets=[ast.Name(id=str(name), ctx=ast.Store())], 
               value=ast.Call(func=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr=f'convert_{attr.__class__.__name__}', ctx=ast.Load()), 
                              args=[ast.Attribute(value=ast.Name(id='node', ctx=ast.Load()), attr=name, ctx=ast.Load())], keywords=[]))

NODE__CLASS__NAME__ = ast.Attribute(value=ast.Attribute(value=ast.Name(id='node', ctx=ast.Load()), attr='__class__', ctx=ast.Load()), attr='__name__', ctx=ast.Load())


class PatternMatching:...


def string(string):
    return ast.Constant(value=string, kind="s")

def integer(integer):
    return ast.Constant(value=integer, kind="i")

def classname(name):
    return ast.Name(id=name.__class__.__name__)


class LuaAstMatch(PatternMatching):
    def __init__(self) -> None:

        self.first_match = ast.Match(subject=NODE__CLASS__NAME__,
                                     cases=[])
        self.nodes = []
        self.attribute_keys = []
        self.node_match_cases = {}
        self.node_attribute_match_cases = {}

        self.count = 0
        self.nodecount = 0
   
    def matchkey(self, node_):
        key = [node.__class__.__name__ for node in last.walk(node_)]
        return ".".join(key)

    def _add_node_type_match(self, node):
        key = node.__class__.__name__
        self.nodes.append(key)
        mc_pattern = ast.MatchValue(value=ast.Constant(value=key))

        body_part = ast.Match(subject=ast.Name(id="pattern"), cases=[])
        self.node_match_cases[key] = ast.match_case(pattern=mc_pattern,
                                                    body=[body_part],)
        self.first_match.cases.append(self.node_match_cases[key])
        self.node_attribute_match_cases[node.__class__.__name__] = {}

    def new_attribute_sequence(self, name, attr):
        return ast.MatchSequence(patterns=[ast.MatchValue(value=string(name)), 
                                          ast.MatchAs(name=attr.__class__.__name__)])

    def new_attribute_match_case(self, node):
        key = []
        match_sequence = ast.MatchSequence(patterns=[])
        actions = []
        for name, attr in node.__dict__.items():
            k = name+":"
            if isinstance(attr, last.Node):
                k+=attr.__class__.__name__
                match_sequence.patterns.append(self.new_attribute_sequence(name, attr))
                key.append(k)
                actions.append(make_astwriter_method(node, name, attr))

            elif isinstance(attr, str):
                if name.startswith("_") == False:
                    k+=attr.__class__.__name__
                    match_sequence.patterns.append(self.new_attribute_sequence(name, attr))
                    key.append(k)
                    actions.append(make_astwriter_method(node, name, attr))

        return  "-".join(key), ast.match_case(pattern=match_sequence, body=actions)

    def _add_attribute_type_match(self, node: last.Node):
        attrkey, newcase = self.new_attribute_match_case(node)
        try:
            self.node_attribute_match_cases[node.__class__.__name__][attrkey]
            return
        except KeyError:
            self.add_attribute_case(node=node, attr_key=attrkey, case=newcase)
        

    def add_attribute_case(self, node: last.Node, attr_key:str, case:ast.match_case):
        try:
            self.node_attribute_match_cases[node.__class__.__name__][attr_key] = case
            self.attribute_keys.append(attr_key)
        except KeyError:
            self.node_attribute_match_cases[node.__class__.__name__] = {attr_key:case}
        self.node_match_cases[node.__class__.__name__].body[0].cases.append(self.node_attribute_match_cases[node.__class__.__name__][attr_key])

    def add_node(self, node_: last.Node):
        if isinstance(node_, list):
            for x in node_:
                self.add_node(x)
            return
        elif isinstance(node_, int):
            if "int" not in self.nodes:
                self._add_node_type_match(node_)
            return 

        ncn = node_.__class__.__name__
        if ncn not in self.nodes:
            self.nodecount+=1
            self._add_node_type_match(node_)
        self._add_attribute_type_match(node_)
        self.count+=1
    

    def show(self):
        x = ast.unparse(self.first_match)
        print(x)
    
    def save(self, name:str=None):
        print("[\033[34mLuaASTMatch\033[0m]: Saving...")
        filename = "node-attribute-patterns.py" if name is None else name
        with open(filename, "w") as f:
            f.write(ast.unparse(self.first_match))
        print("[\033[32mLuaASTMatch\033[0m]: Success.")
        self.showinfo()
    
    def showinfo(self):
        print(f"""\
====================================================================================
Node Names:          \n\t{"\n\t".join(paint(self.nodes, GREEN))}
Attribute Key Count: {paint(len(self.attribute_keys), RED)}
Nodes Assessed:      {paint(self.count, RED)}
Nodes Kept:          {paint(self.nodecount, RED)}
Last Attribute Key:  {paint(self.attribute_keys[-1], RED)}
====================================================================================
""")

        
        


