import os


def list_json_files(folder_path):
    json_files = []
    for root, _, files in os.walk(folder_path):
        json_files.extend(
            os.path.join(root, file) for file in files if file.endswith(".json")
        )
    return json_files
