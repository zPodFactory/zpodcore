import json

from rich import print


def handle_response(result):
    status_code = result.status_code
    content = result.content
    if status_code == 201:
        print("Record created.")
    elif status_code == 404:
        print("Record not found.")
    elif 400 <= status_code < 500:
        obj = content
        if type(obj) == bytes:
            obj = obj.decode()

        try:
            obj_json = json.loads(obj)
        except (json.JSONDecodeError, TypeError):
            print_errors(f"Unknown Error: {content}")

        if status_code == 422:
            messages = [error["msg"] for error in obj_json["detail"]]
            print_errors("  \n".join(messages))
        else:
            print_errors(obj_json["detail"])
    else:
        print(
            f"No default handler defined for status code: {status_code}\n"
            f"{result.content}"
        )


def print_errors(txt, color="bright_red"):
    print(f"[{color}]Error(s) Found:\n  {txt}[/{color}]")
