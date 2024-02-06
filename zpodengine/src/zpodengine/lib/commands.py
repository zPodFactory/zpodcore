import subprocess


def zpod_string(input_string):
    if isinstance(input_string, bytes):
        return input_string.decode("utf-8")
    else:
        return input_string


def cmd_execute(cmd: str, shell=True):
    print(f"[cmd_execute] Input Command: {cmd}")
    with subprocess.Popen(
        args=cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=shell,
        universal_newlines=True,
    ) as process:
        stdout = []
        for stdout_line in process.stdout:
            print(stdout_line.rstrip())
            stdout.append(stdout_line)

        if stderr_output := process.stderr.read():
            print("Error output:", stderr_output)

    return subprocess.CompletedProcess(
        cmd,
        process.returncode,
        "\n".join(stdout),
        stderr_output,
    )
