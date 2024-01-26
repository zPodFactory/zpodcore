from pydantic import AfterValidator, ValidationInfo
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
