import json


def show_error(obj):
    if type(obj) == bytes:
        obj = obj.decode()

    try:
        obj_json = json.loads(obj)
    except TypeError:
        print("Unknown Error")
        return
    except json.JSONDecodeError:
        print(f"Error: {obj}")
        return

    if 'detail' in obj_json:
        print(f"Error: {obj_json['detail']}")
    else:
        print(f"Error: {obj_json}")
