import re

from pydantic import AfterValidator, ValidationInfo
from pydantic_core import PydanticCustomError
from typing_extensions import Annotated


def IdValidator(fields, mapper=None):
    def inner(v: str, info: ValidationInfo):
        # Get column name and value.  If no equals provided, assume column is id.
        column, value = (v if "=" in v else f"id={v}").split("=")

        # Verify that specified column is valid
        if column not in fields:
            raise ValueError(f"Invalid Key: {column}")

        # Validate type for provided value
        fldtype = fields[column]
        if getattr(fldtype, "validate", None):
            fldtype.validate(value)
        elif fldtype == int:
            try:
                int(value)
            except ValueError as e:
                raise ValueError(f"value is not a valid integer: {value}") from e

        # If there is a mapper provided for the current column, use that instead
        if mapper and column in mapper:
            column = mapper[column]

        # Unless column is id, replace column with column_insensitive
        if column != "id":
            column = f"{column}_insensitive"

        return {column: value}

    return AfterValidator(inner)


IdNameType = Annotated[
    str,
    IdValidator(fields={"id": int, "name": str}),
]


def validate_fqdn(value: str):
    """
    https://en.m.wikipedia.org/wiki/Fully_qualified_domain_name
    """

    if not 1 < len(value) < 253:
        raise PydanticCustomError("value_error", "Invalid fqdn length")

    # Remove trailing dot
    if value[-1] == ".":
        value = value[:-1]

    #  Split hostname into list of DNS labels
    labels = value.split(".")

    #  Define pattern of DNS label
    #  Can begin and end with a number or letter only
    #  Can contain hyphens, a-z, A-Z, 0-9
    #  1 - 63 chars allowed
    fqdn = re.compile(r"^[a-z0-9]([a-z-0-9-]{0,61}[a-z0-9])?$", re.IGNORECASE)

    # Check that all labels match that pattern.
    if not all(fqdn.match(label) for label in labels):
        raise PydanticCustomError("value_error", "Invalid fqdn")
    return value


FQDN = Annotated[str, AfterValidator(validate_fqdn)]


def validate_hostname(value: str):
    if not 1 < len(value) < 64:
        raise PydanticCustomError("value_error", "Invalid hostname length")

    #  Define pattern of DNS label
    #  Can begin and end with a number or letter only
    #  Can contain hyphens, a-z, A-Z, 0-9
    #  1 - 63 chars allowed
    hostname_re = re.compile(r"^[a-z0-9]([a-z-0-9-]{0,61}[a-z0-9])?$", re.IGNORECASE)

    # Check that all labels match that pattern.
    if not hostname_re.match(value):
        raise PydanticCustomError("value_error", "Invalid hostname")
    return value


HOSTNAME = Annotated[str, AfterValidator(validate_hostname)]


def validate_filename(value: str):
    # Define a regex pattern for allowed characters in filenames
    # This pattern allows alphanumeric characters, underscores, hyphens, and dots
    pattern = re.compile(r"^[\w\-. ]+$")

    # Check if the filename matches the pattern
    if not pattern.match(value):
        raise PydanticCustomError("value_error", "Invalid filename")
    return value


FILENAME = Annotated[str, AfterValidator(validate_filename)]
