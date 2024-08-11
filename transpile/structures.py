
from typing import Any


Collection = (list, set, tuple)
Map = (dict, enumerate)

def delims(collection):
    if isinstance(collection, dict):
        return r"{}"
    elif isinstance(collection, list):
        return "[]"
    elif isinstance(collection, tuple):
        return "()"
    elif isinstance(collection, set):
        return r"{}"
    elif isinstance(collection, str):
        return '""'


def preceed(object, items) -> str:
    return items[0] + object + items[-1]

def listed(items:list) -> str:
    return ", ".join(items)

def organized(function):
    def wrap(items):
        return organize(function(items))
    return wrap

def organize(items:list) -> list:
    return list(set(items)).sort()

@organized
def properties(object) -> list[str]:
    return [x for x in list(object.__dict__.keys()) if not x.startswith("_")]

def find_properties(object, type):
    return [x for x in properties(object) if isinstance(x, type)]

@organized
def types(object) -> list[str]:
    return [qual(getattr(x, object)) for x in properties(object)]


def _collection(object):
    container = qual(object)
    items = []
    if isinstance(object, Collection):
        for item in object:
            if isinstance(item, Collection):
                items.append(_collection(item))
            else:
                items.append(qual(item))
    items = listed(organize(items))
    return container + preceed(items, "[]")

def qual(object) -> str:
    if isinstance(object, (str, int, float, complex, memoryview, list, set, dict, frozenset)):
        return str(type(object))[8:-2]
    else:
        return object.__class__.__name__


class Structure:
    def __init__(self, item) -> None:
        self.object: Any = item
        self.name: str = qual(self.object)
        self.properties: tuple[str] = tuple(properties(self.object))
        self.types: tuple[str] = tuple(types(self.object))
    
    def __eq__(self, object):
        if isinstance(object, Structure):
            return object.properties == self.properties and object.types == self.types
        else:
            st = Structure(object)
            return self.__eq__(st)
    
    def match_types(self, object):
        if isinstance(object, Structure):
            return object.types == self.types
        else:
            st = Structure(object)
            return self.match_types(st)
    
    def match_properties(self, object):
        if isinstance(object, Structure):
            return object.properties == self.properties
        else:
            st = Structure(object)
            return self.match_properties(st)
    
    def match_name(self, object):
        if isinstance(object, Structure):
            return object.name == self.name
        else:
            st = Structure(object)
            return self.match_name(st)




