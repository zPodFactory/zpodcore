import json
import os
import random
import string


def gen_password(length=12):
    remaining = length
    pw = []

    # Grab one or two characters from UPPERCASE, DIGITS and SYMBOLS
    for char_type in [string.ascii_letters[26:], string.digits, "!"]:
        cnt = random.randint(1, 2)
        pw.extend(random.choices(char_type, k=cnt))
        remaining -= cnt
    # Add LOWERCASE for the remaining characters
    pw.extend(random.choices(string.ascii_letters[:26], k=remaining))

    # Shuffle the letters
    random.shuffle(pw)
    return "".join(pw)


def list_json_files(folder_path):
    json_files = []
    for root, _, files in os.walk(folder_path):
        json_files.extend(
            os.path.join(root, file) for file in files if file.endswith(".json")
        )
    return json_files
