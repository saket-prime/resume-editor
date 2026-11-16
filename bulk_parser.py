"""Read spreadsheet rows without assuming column positions."""

import csv
import io
import re
from decimal import Decimal, InvalidOperation


HEADER_WORDS = {
    "name",
    "candidate name",
    "full name",
    "candidate",
    "salary",
    "package",
    "ctc",
    "salary/package",
    "email",
    "email address",
    "candidate email",
}


def parse_rows(
    text,
    validate_email,
    salary_amount,
    limit=50,
):
    """Identify one name, numeric package, and email per row.

    Supports:
    - Spreadsheet rows separated by tabs
    - CSV rows
    - Plain text such as: Jane Doe 22 jane@example.com
    - Blank cells and reordered columns
    """
    if not text.strip():
        return [], ["Paste candidate rows first."]

    candidates = []
    errors = []

    try:
        if "\t" in text:
            rows = list(
                csv.reader(
                    io.StringIO(text),
                    delimiter="\t",
                    strict=True,
                )
            )

        elif "," in text:
            rows = list(
                csv.reader(
                    io.StringIO(text),
                    strict=True,
                )
            )

        else:
            rows = [
                re.findall(r"\S+", line)
                for line in text.splitlines()
            ]

    except csv.Error:
        return [], [
            "Could not read the pasted data. "
            "Copy the cells directly from your sheet."
        ]

    # Ignore empty rows and empty cells.
    nonempty_rows = [
        (
            row_number,
            [cell.strip() for cell in row if cell.strip()],
        )
        for row_number, row in enumerate(rows, start=1)
        if any(cell.strip() for cell in row)
    ]

    # Skip an optional header row, regardless of column order.
    if nonempty_rows:
        first_cells = nonempty_rows[0][1]

        if all(
            cell.lower() in HEADER_WORDS
            for cell in first_cells
        ):
            nonempty_rows = nonempty_rows[1:]

    if not nonempty_rows:
        return [], ["No candidate rows were found."]

    if len(nonempty_rows) > limit:
        return [], [
            f"Use at most {limit} candidates per batch."
        ]

    for row_number, cells in nonempty_rows:
        emails = []
        amounts = []
        name_parts = []
        invalid_email = False

        for cell in cells:
            if "@" in cell:
                try:
                    emails.append(validate_email(cell))

                except ValueError:
                    errors.append(
                        f"Row {row_number}: "
                        f"invalid email address: {cell}"
                    )
                    invalid_email = True

                continue

            cleaned = re.sub(
                r"^(?:₹|INR\s*)",
                "",
                cell,
                flags=re.IGNORECASE,
            ).strip()

            cleaned = cleaned.replace(",", "")

            try:
                amount = Decimal(cleaned)

            except InvalidOperation:
                name_parts.append(cell)

            else:
                amounts.append(amount)

        if invalid_email:
            continue

        if (
            len(emails) != 1
            or len(amounts) != 1
            or not name_parts
        ):
            errors.append(
                f"Row {row_number}: include one name, "
                "one numeric package, and one email. "
                "Blank cells are allowed; extra numbers "
                "or emails are ambiguous."
            )
            continue

        name = " ".join(name_parts)

        if (
            len(name) > 120
            or any(ord(character) < 32 for character in name)
        ):
            errors.append(
                f"Row {row_number}: name must be "
                "1–120 characters without line breaks."
            )
            continue

        try:
            salary_amount(amounts[0])

        except ValueError as exc:
            errors.append(
                f"Row {row_number}: {exc}"
            )
            continue

        candidates.append(
            {
                "name": name,
                "package": amounts[0],
                "email": emails[0],
            }
        )

    return candidates, errors
