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

### Fizzbuzz

```lox
for (var i = 1; i <= 100; i = i + 1) {
    if (i % 3 == 0) {
        print "Fizz";
    } else if (i % 5 == 0) {
        print "Buzz";
    } else {
        print i;
    }
}
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
python pylang/main.py examples/closure.pylang
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

## Major Differences from Lox:

- **Use of different keywords:** `def` instead of `fun`, `self` instead of `this`.
- **break and continue statements:** This were not supported in author's implementation but are supported in this implementation (this was present as a challenge in the book).
- **Classes and Inheritance:** For inheritance, token `:` is used instead of `<`. So `class Dog: Animal` instead of `class Dog < Animal`.

## Contributing

Contributions are welcome! If you have suggestions or improvements, please open an issue or submit a pull request.

1. Fork the repository.
2. Create a new branch: `git checkout -b feature-name`.
3. Commit your changes: `git commit -m 'Add feature'`.
4. Push to the branch: `git push origin feature-name`.
5. Open a pull request.


## Testing

Custom python scripts are provided in the `tests` directory to test the interpreter. To run the tests:

```bash
python tests/test.py
```

**Note:** The test suite used is from author's original implementation. Find more details in the [original repository](https://github.com/munificent/craftinginterpreters/) by Robert Nystrom (check the `test` directory).

### To add new tests:

- Add a new `.pylang` file in the `tests` directory.
- Generate its expected output by running the script `update_output_files.py`.