import os
import subprocess

from rich.console import Console
from rich.progress import track

# Setup rich console
console = Console()

# Directory containing .pylang test files
TEST_DIR = "test"
INTERPRETER = "../main.py"  # Change this to the path of your pylang interpreter


def generate_output(file_path):
    """Runs the given pylang file and returns its output."""
    result = subprocess.run(
        ["python3", INTERPRETER, file_path], capture_output=True, text=True
    )
    return result.stdout.strip(), result.stderr.strip()


def generate_output_files():
    """Finds all .pylang tests and generates .out files."""
    # Get all .pylang files in the test directory and its subdirectories
    test_files = []
    for root, _, files in os.walk(TEST_DIR):
        for file in files:
            if file.endswith(".pylang"):
                test_files.append(os.path.join(root, file))

    for test_file in track(
        test_files, description="[yellow]Generating expected output files..."
    ):
        out_path = test_file.replace(".pylang", ".expected.out")
        console.print(
            f"[cyan][+][/cyan] Generating output for [bold]{test_file}[/bold] => [bold]{out_path}[/bold]"
        )

        actual_output, err = generate_output(test_file)
        if err:
            console.print(f"[red][-] Error while running {test_file}: {err}[/red]")

        with open(out_path, "w") as f:
            f.write(actual_output)

    console.print("[green]✅ All output files generated successfully![/green]")


if __name__ == "__main__":
    generate_output_files()
