import transpile.luaparser.ast as last



class Is:

    def Node(node):
        return isinstance(node, last.Node)

    def Name(node:last.Node):
        return isinstance(node, last.Name)

    def Attribute(node:last.Node):
        if isinstance(node, last.Index):
            if node.notation == last.IndexNotation.DOT:
                return True
        return

    def Index(node:last.Node):
        if isinstance(node, last.Index):
            if node.notation == last.IndexNotation.SQUARE:
                return True
        return
    
    def List(node:last.Table):
        if isinstance(node, last.Table) == False:
            return
        for field in node.fields:
            if field.key == None:
                return True
            return
    
    def Dict(node:last.Table):
        if isinstance(node, last.Table) == False:
            return
        return not Is.List(node)
        
    def ClassDef(node:last.Node):
        if isinstance(node, last.Assign):
            for v in node.values:
                if isinstance(v, last.Invoke) == True:
                    if isinstance(v.func, last.Name) == True:
                        if v.func.id == "extend":
                            return True
        return
    
    def Localize(node:last.Assign):
        if isinstance(node, last.Assign):
            for v in node.values:
                if isinstance(v, last.Invoke) == True:
                    for key, value in v.__dict__.items():
                        if key == "func":
                            if isinstance(value, last.Name):
                                if value.id == "localize":
                                    return True
                            if isinstance(value, last.Call):
                                if isinstance(value.func, last.Name):
                                    if value.func.id == "localize":
                                        return True

                    if isinstance(v.func, last.Call) == True:
                        if v.func.id == "localize":
                            return True
        return

    def Joinable(listed):
        try:
            "".join(listed)
            return True
        except:
            pass

    def Uniform(iterable):
        if len(iterable) >= 1:
            check = type(iterable[0])
            for item in iterable:
                if not isinstance(item, check):
                    return
            return True
        return 
    
    def Require(node):
        if isinstance(node.func, last.Name):
            if node.func.id == "require":
                return True
        if isinstance(node, last.Name):
            if node.id == "require":
                return True
        
        


