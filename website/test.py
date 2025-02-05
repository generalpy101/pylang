import subprocess

try:
    result = subprocess.run(
        ["python3", "../pylang/pylang.py", "/tmp/tmpha60n517"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        universal_newlines=True,
    )
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
except Exception as e:
    print(f"Error: {e}")
