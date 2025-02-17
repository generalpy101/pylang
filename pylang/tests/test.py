import difflib
import os
import subprocess

from rich.console import Console
from rich.text import Text

# Directory containing .pylang test files
TEST_DIR = "test"
INTERPRETER = "../main.py"  # Change this to the path of your pylang interpreter
console = Console()


def run_pylang(file_path):
    """Runs the given pylang file and returns its output."""
    result = subprocess.run(
        ["python3", INTERPRETER, file_path], capture_output=True, text=True
    )
    return result.stdout.strip(), result.stderr.strip()


def show_diff(expected, actual):
    """Returns a formatted string showing the color-coded difference between expected and actual output."""
    diff = difflib.unified_diff(
        expected.splitlines(),
        actual.splitlines(),
        fromfile="Expected",
        tofile="Got",
        lineterm="",
    )

    diff_text = Text()

    for line in diff:
        if line.startswith("---") or line.startswith("+++"):
            diff_text.append(line + "\n", style="bold white")  # Headers in bold white
        elif line.startswith("@@"):
            diff_text.append(
                line + "\n", style="bold cyan"
            )  # Line number hints in cyan
        elif line.startswith("-"):
            diff_text.append(line + "\n", style="bold red")  # Removed lines in red
        elif line.startswith("+"):
            diff_text.append(line + "\n", style="bold green")  # Added lines in green
        else:
            diff_text.append(line + "\n", style="white")  # Unchanged text in white

    return diff_text


def run_tests():
    """Finds all .pylang tests and compares output with expected .expected.out files."""
    test_files = []
    for root, _, files in os.walk(TEST_DIR):
        for file in files:
            if file.endswith(".pylang"):
                test_files.append(os.path.join(root, file))

    passed, failed = 0, 0
    failures = []  # Store failure details

    for test_file in test_files:
        out_path = test_file.replace(".pylang", ".expected.out")

        if not os.path.exists(out_path):
            failures.append((test_file, "❌ Missing expected output file"))
            failed += 1
            continue

        expected_output = open(out_path).read().strip()
        actual_output, error_output = run_pylang(test_file)

        if actual_output == expected_output and not error_output:
            console.print(f"✅ {test_file} passed", style="bold green")
            passed += 1
        else:
            failed += 1
            diff_text = show_diff(expected_output, actual_output)
            failure_msg = f"❌ {test_file} failed"
            failures.append((test_file, failure_msg, diff_text, error_output))

    # Summary
    console.print(f"\n✅ {passed} passed, ❌ {failed} failed", style="bold yellow")

    # Print failure details at the end
    if failures:
        console.print("\n[bold red]Failing tests:[/bold red]")
        for test_file, failure_msg, diff_text, error_output in failures:
            console.print(failure_msg, style="bold red")
            if diff_text:
                console.print(diff_text)
            if error_output:
                console.print(
                    f"\n[bold red]Errors:[/bold red]\n{error_output}", style="red"
                )


if __name__ == "__main__":
    run_tests()
