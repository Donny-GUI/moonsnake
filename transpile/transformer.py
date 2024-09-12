import ast


class StringStaticMethodTransformer(ast.NodeTransformer):

    def visit_Call(self, node: ast.Call) -> ast.Call:

        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "string":

            if node.func.attr == "format":
                pass
            elif node.func.attr == "match":
                pass
            elif node.func.attr == "gsub":
                pass
            elif node.func.attr == "gmatch":
                pass
            elif node.func.attr == "sub":
                # string.sub(name, target, replacement, repeats) -> name.replace(target, replacement, repeats)
                setattr(node,
                        "func",
                        ast.Attribute(attr="replace",
                                      value=ast.Name(
                                          id=node.args[0],
                                          ctx=ast.Load()),
                                      ctx=ast.Load())
                        )
                x = []
                for i in range(1, len(node.args)):
                    x.append(ast.Name(id=node.args[i], ctx=ast.Load()))
                setattr(node, "args", x)

            elif node.func.attr == "upper":
                # string.upper(name) -> name.upper()
                setattr(node, "func", ast.Attribute(
                        attr="upper",
                        value=ast.Name(
                            id=node.args[0],
                            ctx=ast.Load()),
                        ctx=ast.Load()))
                setattr(node, "args", [])

            elif node.func.attr == "lower":
                # string.lower(name) -> name.lower()
                setattr(node, "func",  ast.Attribute(
                        attr="lower",
                        value=ast.Name(
                            id=node.args[0],
                            ctx=ast.Load()),
                        ctx=ast.Load()))
                setattr(node, "args", [])

            elif node.func.attr == "find":
                # string.find(name, "substring") -> name.find("substring")
                setattr(node, "func", ast.Attribute(
                        attr="find",
                        value=ast.Name(
                            id=node.args[0],
                            ctx=ast.Load()),
                        ctx=ast.Load()))
                setattr(node, "args", [ast.Name(
                    id=node.args[1], ctx=ast.Load())])

            elif node.func.attr == "index":
                pass

        return node


class KVForLoopTransformer(ast.NodeTransformer):

    def visit_For(self, node: ast.For) -> ast.For:
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == "ipairs":
            # change ipairs to enumerate
            setattr(node,
                    "iter",
                    ast.Call(
                        func=ast.Name(
                            id="enumerate",
                            ctx=ast.Load()),
                        args=[node.iter.args[0]],
                        keywords=[])
                    )

            if isinstance(node.target, ast.Name) and len(node.target.id) % 2 == 0:
                half = len(node.target.id) // 2
                t = [ast.Name(id=node.target.id[:half], ctx=ast.Load()), ast.Name(
                    id=node.target.id[half:], ctx=ast.Load())]
                setattr(node, "target", t)

        elif isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == "pairs":
            setattr(node,
                    "iter",
                    ast.Call(args=[],
                             ctx=ast.Load(),
                             keywords=[],
                             func=ast.Attribute(attr="items",
                                                ctx=ast.Load(),
                                                value=ast.Name(id=node.iter.args[0].id,
                                                               ctx=ast.Load()
                            ))))

            if isinstance(node.target, ast.Name) and len(node.target.id) % 2 == 0:
                half = len(node.target.id) // 2
                t = [ast.Name(id=node.target.id[:half], ctx=ast.Load()), ast.Name(
                    id=node.target.id[half:], ctx=ast.Load())]
                setattr(node, "target", t)

        return node


class HEXTransformer(ast.NodeTransformer):
    def visit_Call(self, node: ast.Call) -> ast.Call:
        if isinstance(node.func, ast.Name) and node.func.id == "HEX":
            setattr(node.func, "id", "hex")

        return node


class TableMethodsTransformer(ast.NodeTransformer):
    """
    turns table.insert(instance, value) into instance.append(value) 
    for libraries based on luas table.

    """
    def visit_Call(self, node: ast.Call) -> ast.Call:
        
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == 'table' and isinstance(node.func.attr, ast.Name):
            
            if node.func.attr.id == "insert":
                if isinstance(node.args, ast.arguments):
                    node.func.value = node.args.args[0].arg
                    node.args = node.args.args[1:]
                node.func.attr.id = "append"
            
            if node.func.attr.id == "remove":
                if isinstance(node.args, ast.arguments):
                    node.func.value = node.args.args[0].arg
                    node.args = node.args.args[1:]
            
            if node.func.attr.id == "sort":
                if isinstance(node.args, ast.arguments):
                    node.func.value = node.args.args[0].arg
                    node.args = node.args.args[1:]
            
            
            
        return node


def first_arg_to_base(node: ast.Call) -> ast.Call:
    """
    EX: turns table.insert(instance, value) into instance.append(value)

    Args:
        node (ast.Call): any call with a attribute as its func

    Returns:
        ast.Call: _description_
    """
    
    if isinstance(node.args, ast.arguments):
        if isinstance(node.args.args[0], ast.Constant):
            node.func.value = node.args.args[0].value
        else:
            node.func.value = node.args.args[0].arg
        node.args.args.pop(0)
        
    return node

def call_is_attribute_with_method(node:ast.Call, object:str="string", method:str="upper") -> bool | None:
    
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
    and isinstance(node.func.value, ast.Name)\
    and node.func.value.id == object \
    and isinstance(node.func.attr, ast.Name)\
    and node.func.attr.id == method:
        return True 
    
    return 

def is_specific_attribute(node:ast.Attribute, object:str="string", method:str="upper") -> bool | None:
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == object and node.attr == method:
        return True
    return

def has_call_func_attribute(node:ast.Call):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        return True

def is_method_call(node:ast.AST):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        return True
    return False

def rename_method(node:ast.Call, old:str="lower", method:str="upper") -> ast.Call:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
    and isinstance(node.func.value, ast.Name)\
    and isinstance(node.func.attr, ast.Name)\
    and node.func.attr.id == old:
        node.func.attr.id = method
    return node


class StringLibraryTransformer(ast.NodeTransformer):
    """
    turns string.insert(instance, value) into instance.append(value) 
    for libraries based on luas string library.

    """
    changed = 0
        
    def visit_Call(self, node: ast.Call) -> ast.Call:
        # check if it is a method call
        if is_method_call(node) == False:
            return node
        
        self.changed+=1
        
        if call_is_attribute_with_method(node, "string", "find"):
            
            return first_arg_to_base(node)
        
        
        elif call_is_attribute_with_method(node, "string", "sub"):
            node = first_arg_to_base(node)
            node = rename_method(node, "sub", "replace")
            return node
        
        elif call_is_attribute_with_method(node, "string", "upper"):
            return first_arg_to_base(node)
        
        elif call_is_attribute_with_method(node, "string", "lower"):
            return first_arg_to_base(node)
        
        elif call_is_attribute_with_method(node, "string", "rep"):
            node = first_arg_to_base(node)
            return  rename_method(node, "rep", "replace")
        
        elif call_is_attribute_with_method(node, "string", "format"):
            return first_arg_to_base(node)
        
        
        self.changed-=1
        
        return node

class IPairsTransformer(ast.NodeTransformer):
    """ 
    turns:
    for ab in ipairs(c) 
    -> 
    for a, b in c.items():
    """
                     
    def visit_For(self, node: ast.For) -> ast.For:

        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == "ipairs":
            node.iter = ast.Call(
                func=ast.Attribute(
                    value=node.iter.args[0],
                    attr="items",
                    ctx=ast.Load(),
                ),
                args=[],
                keywords=[]
            )
            if isinstance(node.target, ast.Name):
                stringver = node.target.id 
                if stringver.startswith("_"):
                    k = stringver[0]
                    v = stringver[1:]
                    node.target = ast.Tuple(elts=[ast.Name(id=k, ctx=ast.Store()), ast.Name(id=v, ctx=ast.Store())], ctx=ast.Store())
                else:
                    names = []
                    ids = []
                    for char in stringver:
                        if char not in ids:
                            ids.append(char)
                            names.append(ast.Name(id=str(char*stringver.count(char)), ctx=ast.Store()))
                            if len(ids) == 2:
                                break
                    
                    node.target = ast.Tuple(elts=names, ctx=ast.Store())   
                    
            
        return node
