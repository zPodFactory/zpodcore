import random
import string

# Set default password length to 16 for VCF 5.2 requirements


def gen_password(length=16):
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
