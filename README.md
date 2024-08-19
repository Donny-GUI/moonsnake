
![Screenshot 2024-08-19 140132](https://github.com/user-attachments/assets/b80f69b1-4b58-4249-bfc4-20ae97503d13)


## What is it?
Lua any version to Python[3.12] source to source transpiler

### Does it Handle classes?
yes
Converts invoke extend objects into classes and invoked functions into methods for the class.

### Does it handle imports?
Yes
Converts require statements to python local modules and has a very basic standard library mapping.

### Does it handle super?
Yes
Converts object inheritance


### Does it handle Anonymous functions
Yes, long anonymous functions are converted into actual functions to use

# Getting Started
```
git clone https://gitub.com/Donny-GUI/moonsnake.git
```

## TODO

- Fix single line call asts so that it will give the proper indentation
- fix lambda invokes
- fix import [single letter]
