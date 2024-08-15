
## What is it?
Lua any version to Python[3.12] source to source transpiler

### Does it Handle classes?
yes
Converts invoke extend objects into classes and invoked functions into methods for the class.

### Does it handle imports?
Yes
Converts require statements to python local modules and has a very basic standard library mapping.

# Getting Started
```
git clone https://gitub.com/Donny-GUI/less.git
```

within your script

```python3
from less.tranpiler import LuaPythonTranpiler as lpt
python_script = lpt.from_file("myfile.lua")
```


# Features
Structural Pattern Matching
- creates a match case block for optimizing the transpiler

