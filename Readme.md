# PyLang

**PyLang** is a Python-based implementation of the Lox programming language, developed for educational purposes. This project follows the interpreter design outlined in the book [*Crafting Interpreters*](https://craftinginterpreters.com/) by Robert Nystrom.


## Table of Contents

- [PyLang](#pylang)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Features](#features)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Examples](#examples)
    - [Closure Example:](#closure-example)
    - [Recursive Fibonacci:](#recursive-fibonacci)
  - [Supported Syntax](#supported-syntax)
  - [Contributing](#contributing)
  - [License](#license)


## Introduction

Lox is a dynamically-typed, interpreted language with a syntax similar to JavaScript and Python. This project, **PyLang**, serves as a learning tool to understand interpreter design and implementation.


## Features

- **Expression Evaluation:** Supports arithmetic, logical, and comparison operations.
- **Control Flow:** Implements conditional statements (`if`), loops (`while`, `for`).
- **Functions:** Allows function declarations, closures, and recursion.
- **Variables:** Supports variable declarations and scope resolution.
- **Error Handling:** Provides runtime and syntax error reporting.
- **REPL:** Interactive Read-Eval-Print Loop for testing code snippets.

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/generalpy101/pylang.git
   cd pylang
   ```

2. **Set Up a Virtual Environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```


## Usage

To run the interpreter:

```bash
python pylang.py [script.pylang]
```

- **Interactive Mode:** Run `python pylang.py` without arguments to enter the REPL.
- **Script Mode:** Provide a `.pylang` file to execute a Lox script.


## Examples

### Closure Example:

```lox
def makeCounter() {
    var count = 0;
    def increment() {
        count = count + 1;
        print count;
    }
    return increment;
}

var counter = makeCounter();
counter(); // Outputs: 1
counter(); // Outputs: 2
```

### Recursive Fibonacci:

```lox
def fib(n) {
    if (n <= 1) return n;
    return fib(n - 1) + fib(n - 2);
}

print fib(10); // Outputs: 55
```

To run an example:

```bash
python pylang.py examples/closure.pylang
```


## Supported Syntax

PyLang supports a subset of the Lox language syntax, including:

- **Variable Declarations:** `var x = 10;`
- **Arithmetic Operations:** `+`, `-`, `*`, `/`
- **Logical Operations:** `and`, `or`, `!`
- **Comparison Operators:** `==`, `!=`, `<`, `<=`, `>`, `>=`
- **Control Flow:** `if`, `else`, `while`, `for`
- **Functions:** `def myFunction() { return 42; }`
- **Closures:** First-class functions with lexical scoping
- **Print Statement:** `print "Hello, world!";`
- **Classes and Inheritance:**:

```
class Animal {
    speak() {
        print "Animal sound";
    }
}

class Dog: Animal {
    // Constructor
    init(name) {
        self.name = name;
    }
    speak() {
        super.speak();
        print "Woof! My name is " + self.name;
    }
}

var myDog = Dog("Tommy");
myDog.speak(); // Outputs: "Woof!"
```

For a complete list of supported syntax, refer to the [Lox Grammar](https://craftinginterpreters.com/appendix-i.html).


## Contributing

Contributions are welcome! If you have suggestions or improvements, please open an issue or submit a pull request.

1. Fork the repository.
2. Create a new branch: `git checkout -b feature-name`.
3. Commit your changes: `git commit -m 'Add feature'`.
4. Push to the branch: `git push origin feature-name`.
5. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

