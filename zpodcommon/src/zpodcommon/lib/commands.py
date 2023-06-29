import subprocess


def zpod_string(input_string):
    if isinstance(input_string, bytes):
        return input_string.decode("utf-8")
    else:
        return input_string


def cmd_execute(cmd: str, shell=True, debug=False):
    print(f"[cmd_execute] Input Command: {cmd}")
    try:
        result = subprocess.run(
            args=cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=shell,
            check=True,
        )

        print(
            "[cmd_execute] CompletedProcess information:\n"
            f"args: {result.args}\n"
            f"returncode: {result.returncode}\n"
            f"stdout: {zpod_string(result.stdout)}\n"
            f"stderr: {zpod_string(result.stderr)}\n"
        )
        return result

    except subprocess.CalledProcessError as e:
        print(
            "[cmd_execute] CalledProcessError information:\n"
            f"cmd: {e.cmd}\n"
            f"returncode: {e.returncode}\n"
            f"output: {e.output}\n"
            f"stdout: {zpod_string(e.stdout)}\n"
            f"stderr: {zpod_string(e.stderr)}\n"
        )
        raise e
