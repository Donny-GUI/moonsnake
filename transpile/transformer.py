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

        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == "pairs":
            setattr(node,
                    "iter",
                    ast.Call(
                        args=[],
                        ctx=ast.Load(),
                        keywords=[],
                        func=ast.Attribute(
                            attr="items",
                            ctx=ast.Load(),
                            value=ast.Name(
                                id=node.iter.args[0].id,
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
    def visit_Call(self, node: ast.Call) -> ast.Call:
        # table.
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "table":

            if node.func.attr == "insert":
                setattr(node, "func", ast.Attribute(value=node.args[0],
                                                        attr="append",
                                                        ctx=ast.Load()))
                setattr(node, "args", node.args[1:])

            elif node.func.attr == "remove":
                setattr(node, "func", ast.Attribute(value=node.args[0],
                                                        attr="remove",
                                                        ctx=ast.Load()))
                setattr(node, "args", node.args[1:])
            
            return node

            
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, str) and node.func.value == "table":
            
            if node.func.attr == "insert":
                setattr(node, "func", ast.Attribute(value=node.args[0],
                                                    attr="append",
                                                    ctx=ast.Load()))
                setattr(node, "args", node.args[1:])

            elif node.func.attr == "remove":
                setattr(node, "func", ast.Attribute(value=node.args[0],
                                                    attr="remove",
                                                    ctx=ast.Load()))
                setattr(node, "args", node.args[1:])
            
            return node
        

        return node
