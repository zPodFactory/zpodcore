import subprocess


def zpod_string(input_string):
    if isinstance(input_string, bytes):
        return input_string.decode("utf-8")
    else:
        return input_string


def cmd_execute(cmd: str, shell=True):
    """Run a shell command, streaming stdout and capturing stderr.

    Raises ``subprocess.CalledProcessError`` if the command exits with a
    non-zero return code so that callers (and the surrounding Prefect
    task) see the failure as an exception. Without this, a failed shell
    command (vcsa-deploy precheck failure, ovftool deploy failure, 7z
    extract failure, ...) would silently return a CompletedProcess with
    a non-zero ``returncode`` that the caller almost always discards,
    and the Prefect task would be marked Completed despite the failure.
    """
    print(f"[cmd_execute] Input Command: {cmd}")
    stdout: list[str] = []
    stderr_output = ""
    with subprocess.Popen(
        args=cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=shell,
        universal_newlines=True,
    ) as process:
        for stdout_line in process.stdout:
            print(stdout_line.rstrip())
            stdout.append(stdout_line)

        stderr_output = process.stderr.read()
        if stderr_output:
            print("Error output:", stderr_output)

    completed = subprocess.CompletedProcess(
        cmd,
        process.returncode,
        "\n".join(stdout),
        stderr_output,
    )
    # Surface failures as exceptions so the calling Prefect task fails
    # instead of completing silently with a swallowed non-zero exit.
    completed.check_returncode()
    return completed
