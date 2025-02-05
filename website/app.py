import os
import random
import string
import subprocess

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

app = Flask(__name__)

PYLANG_EXECUTABLE = os.environ.get("PYLANG_EXECUTABLE", "python3 pylang.py")


def generate_random_string(length=10):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def run_code(code):
    try:
        # Save the code to a temporary file
        temp_file_name = generate_random_string()
        temp_file_path = f"/tmp/{temp_file_name}.py"
        with open(temp_file_path, "w+") as f:
            f.write(code)

        executable_path = (
            PYLANG_EXECUTABLE.split()
        )  # Make sure PYLANG_EXECUTABLE is correct
        print(
            f"Running command: {' '.join([*executable_path, f.name])}"
        )  # Debugging command
        # Run the code with a timeout
        result = subprocess.run(
            [*executable_path, f.name],
            capture_output=True,
            text=True,
            timeout=10,
        )

        print("Return code:", result.returncode)  # Debugging return code

        stdout = result.stdout
        stderr = result.stderr

        print("STDOUT:", stdout)  # Debugging stdout
        print("STDERR:", stderr)  # Debugging stderr

        return {"stdout": stdout, "stderr": stderr}
    except subprocess.TimeoutExpired:
        print("Error: Execution timed out (Possible infinite loop)")
        return {"stderr": "Error: Execution timed out (Possible infinite loop)"}
    except Exception as e:
        return {"stderr": str(e)}  # Catch and return any other errors


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/run", methods=["POST"])
def execute_code():
    data = request.json
    code = data.get("code", "")

    if not code.strip():
        return jsonify({"error": "Code cannot be empty"}), 400

    output = run_code(code)
    return jsonify(output)


if __name__ == "__main__":
    app.run(debug=True)
